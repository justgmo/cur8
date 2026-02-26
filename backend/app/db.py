from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

settings = get_settings()

# SQL engine and session
engine = create_engine(
    settings.database_url,
    echo=False,  # sql logging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for ORM model
Base = declarative_base()

def get_db():
    """Dependency: yield session, close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()