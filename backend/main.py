from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional

from .database import engine, get_db
from . import models
from .schemas import TodoCreate, TodoUpdate, TodoResponse

# ── Create all tables on startup ──────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Todo Reminder API",
    description="A simple Todo + Reminder API built with FastAPI and SQLite",
    version="1.0.0",
)

# Allow the HTML/JS frontend (served from a file or any port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # For production lock this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health endpoints ───────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def home():
    """Root endpoint — confirms the API is alive."""
    return {"message": "Todo Reminder API is running!", "version": "1.0.0"}


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
