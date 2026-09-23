from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ──────────────────────────────────────────────
# Request body schemas (what the client sends)
# ──────────────────────────────────────────────

class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None        # "YYYY-MM-DD"
    reminder_time: Optional[str] = None   # "HH:MM"


class TodoUpdate(BaseModel):
    """Schema for updating an existing todo (all fields optional)."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    reminder_time: Optional[str] = None
    completed: Optional[bool] = None


# ──────────────────────────────────────────────
# Response schemas (what the server returns)
# ──────────────────────────────────────────────

class TodoResponse(BaseModel):
    """Schema for a todo returned in API responses."""
    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    reminder_time: Optional[str] = None
    completed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True   # Allows SQLAlchemy models → Pydantic
