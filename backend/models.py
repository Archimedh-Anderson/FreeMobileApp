"""
Database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum

class UserRole(str, enum.Enum):
    """User roles enum"""
    CLIENT_SAV = "client_sav"
    AGENT_SAV = "agent_sav"
    DATA_ANALYST = "data_analyst"
    MANAGER = "manager"

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.CLIENT_SAV, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"

