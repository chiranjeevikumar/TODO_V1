import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Database URL ───────────────────────────────────────────────────────────────
# In production (Vercel) this env var is set to the Neon PostgreSQL URL.
# Locally it falls back to a SQLite file so local dev needs no extra setup.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./todo.db")

# Neon (and most cloud PG providers) give URLs that start with "postgres://",
# but SQLAlchemy 2.x requires "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Engine ─────────────────────────────────────────────────────────────────────
# SQLite needs check_same_thread=False; PostgreSQL does not accept that arg.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
