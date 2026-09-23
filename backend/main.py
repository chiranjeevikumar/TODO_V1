from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
import os

# Load .env file for local development (no-op if python-dotenv not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .database import engine, get_db
from . import models
from .schemas import TodoCreate, TodoUpdate, TodoResponse
from .email_service import send_reminder_email, email_configured

# ── Create all tables on startup ──────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# Auto-migrate: ensure email_sent column exists in existing tables
try:
    with engine.connect() as conn:
        from sqlalchemy import text
        from .database import DATABASE_URL
        if DATABASE_URL.startswith("sqlite"):
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(todos)")).fetchall()]
            if "email_sent" not in cols:
                conn.execute(text("ALTER TABLE todos ADD COLUMN email_sent BOOLEAN DEFAULT 0"))
                conn.commit()
        else:
            conn.execute(text("ALTER TABLE todos ADD COLUMN IF NOT EXISTS email_sent BOOLEAN DEFAULT FALSE"))
            conn.commit()
except Exception:
    pass

# ── App setup ─────────────────────────────────────────────────────────────────
# root_path="/api" tells FastAPI that it is mounted under /api on Vercel,
# so Swagger docs and redirects work correctly.
IS_VERCEL = os.environ.get("VERCEL", False)

app = FastAPI(
    title="Todo Reminder API",
    description="A simple Todo + Reminder API built with FastAPI and SQLite",
    version="1.0.0",
    root_path="/api" if IS_VERCEL else "",
)

@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    path = request.scope.get("path", "")
    if path.startswith("/api/"):
        request.scope["path"] = path[4:]
    elif path == "/api":
        request.scope["path"] = "/"
    return await call_next(request)

# Allow the HTML/JS frontend (served from a file or any port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # For production lock this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health endpoint ───────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    """Simple health check."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── Todo CRUD endpoints ────────────────────────────────────────────────────────

@app.post("/todos", response_model=TodoResponse, status_code=201, tags=["Todos"])
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """
    Create a new todo item.

    - **title**: Required. Short title for the task.
    - **description**: Optional details.
    - **due_date**: Optional date in `YYYY-MM-DD` format.
    - **reminder_time**: Optional time in `HH:MM` format.
    """
    db_todo = models.Todo(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.get("/todos", response_model=List[TodoResponse], tags=["Todos"])
def get_todos(
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all todos.

    - Optionally filter by **completed** status: `?completed=true` or `?completed=false`
    """
    query = db.query(models.Todo)
    if completed is not None:
        query = query.filter(models.Todo.completed == completed)
    return query.order_by(models.Todo.id.desc()).all()


@app.get("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a single todo by its ID."""
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
def update_todo(todo_id: int, updates: TodoUpdate, db: Session = Depends(get_db)):
    """
    Update an existing todo.

    Only the fields you provide will be changed.
    """
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", tags=["Todos"])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Permanently delete a todo by its ID."""
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    db.delete(todo)
    db.commit()
    return {"message": f"Todo {todo_id} deleted successfully"}


@app.patch("/todos/{todo_id}/complete", response_model=TodoResponse, tags=["Todos"])
def mark_complete(todo_id: int, db: Session = Depends(get_db)):
    """Toggle a todo's completed status."""
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    todo.completed = not todo.completed
    db.commit()
    db.refresh(todo)
    return todo


# ── Reminder endpoint ──────────────────────────────────────────────────────────

@app.get("/reminders/due", response_model=List[TodoResponse], tags=["Reminders"])
def get_due_reminders(db: Session = Depends(get_db)):
    """
    Returns todos whose due_date is today or in the past and are not yet completed.

    Call this endpoint periodically from the frontend to show reminder alerts.
    """
    today = date.today().isoformat()   # e.g. "2026-09-23"
    due = (
        db.query(models.Todo)
        .filter(
            models.Todo.completed == False,
            models.Todo.due_date != None,
            models.Todo.due_date <= today,
        )
        .all()
    )
    return due


@app.api_route("/reminders/send-emails", methods=["GET", "POST"], tags=["Reminders"])
def send_reminder_emails(db: Session = Depends(get_db)):
    """
    Scan for todos that are overdue (due_date < today) or whose reminder_time
    has arrived today, are not yet completed, and haven't had an email sent yet.

    Sends an urgent "pending task — please complete ASAP" Gmail alert for each.

    Callable via:
    - Vercel Cron Job (GET)
    - Manual or frontend triggers (POST / GET)

    Returns a summary of emails sent.
    """
    if not email_configured():
        raise HTTPException(
            status_code=503,
            detail="Gmail credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD env vars."
        )

    now          = datetime.now()
    today_str    = now.strftime("%Y-%m-%d")
    current_hhmm = now.strftime("%H:%M")

    # ── Candidate 1: fully overdue todos (due_date in the past) ──────────────
    overdue_todos = (
        db.query(models.Todo)
        .filter(
            models.Todo.completed  == False,
            models.Todo.email_sent == False,
            models.Todo.due_date   != None,
            models.Todo.due_date   < today_str,
        )
        .all()
    )

    # ── Candidate 2: due today, and reminder_time has arrived ────────────────
    due_today_todos = (
        db.query(models.Todo)
        .filter(
            models.Todo.completed  == False,
            models.Todo.email_sent == False,
            models.Todo.due_date   == today_str,
            (models.Todo.reminder_time == None) | (models.Todo.reminder_time <= current_hhmm),
        )
        .all()
    )

    candidates = overdue_todos + due_today_todos

    sent     = []
    failures = []

    for todo in candidates:
        # Determine urgency label for the email
        is_overdue = todo.due_date and todo.due_date < today_str
        try:
            send_reminder_email(
                title         = todo.title,
                description   = todo.description,
                due_date      = todo.due_date,
                reminder_time = todo.reminder_time,
                is_overdue    = is_overdue,
            )
            todo.email_sent = True
            db.commit()
            sent.append({"id": todo.id, "title": todo.title, "overdue": is_overdue})
        except Exception as exc:
            db.rollback()
            failures.append({"id": todo.id, "title": todo.title, "error": str(exc)})

    return {
        "checked_at": now.isoformat(),
        "candidates": len(candidates),
        "sent":       sent,
        "failures":   failures,
    }


@app.get("/reminders/email-status", tags=["Reminders"])
def email_status():
    """
    Returns whether Gmail email alerts are configured and ready.
    Useful for the frontend to show/hide the email feature indicator.
    """
    return {
        "email_configured": email_configured(),
        "sender": os.environ.get("GMAIL_USER", "") or None,
        "recipient": os.environ.get("NOTIFICATION_EMAIL", "") or None,
    }


# ── Mount frontend static files when running locally ──────────────────────────
if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

