from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base


class Todo(Base):
    """
    SQLAlchemy model for the todos table.

    Fields:
        id           - Auto-incremented primary key
        title        - Short title of the todo (required)
        description  - Optional longer description
        due_date     - Optional ISO date string (e.g. "2026-09-25")
        reminder_time- Optional time string (e.g. "19:00")
        completed    - Whether the todo is done (default False)
        created_at   - Timestamp when the record was created
    """
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(String, nullable=True)       # stored as "YYYY-MM-DD"
    reminder_time = Column(String, nullable=True)  # stored as "HH:MM"
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
