"""
Database configuration and session management
Railway PostgreSQL compatible
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from Railway (automatically injected)
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, use SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./freemobileapp.db"

# Handle PostgreSQL URL format from Railway
# Railway provides postgresql:// but SQLAlchemy 2.0+ prefers postgresql+psycopg2://
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Keep postgresql:// for Railway compatibility
    pass
elif DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Convert old postgres:// to postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling for PostgreSQL
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10
    )
else:
    # SQLite for local development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

