import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Database URL ───────────────────────────────────────────────────────────────
# Priority:
#   1. DATABASE_URL env var  → used for PostgreSQL (Neon) in production
#   2. VERCEL env var set    → use /tmp/todo.db  (Vercel fs is read-only except /tmp)
#   3. Local dev             → use ./todo.db in the project root
_IS_VERCEL = os.environ.get("VERCEL", "")
_default_db = "sqlite:////tmp/todo.db" if _IS_VERCEL else "sqlite:///./todo.db"
DATABASE_URL = os.environ.get("DATABASE_URL", _default_db)


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
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
