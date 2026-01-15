"""
Database Connection and Session Management
Sets up SQLAlchemy engine and session factory
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine
# echo=True would print all SQL queries (useful for debugging)
engine = create_engine(settings.database_url, echo=False)

# Session factory - creates new database sessions
# autocommit=False: Changes must be explicitly committed
# autoflush=False: Prevents automatic flushing before queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI
    Provides a database session for each request
    Automatically closes session after request completes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Called during startup to ensure schema exists
    """
    from app.models import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")
