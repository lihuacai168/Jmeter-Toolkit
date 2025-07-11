"""Database base configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# Create database engine
engine = create_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True, pool_recycle=300)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
