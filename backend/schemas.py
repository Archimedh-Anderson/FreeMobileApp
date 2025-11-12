"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict
from datetime import datetime
from backend.models import UserRole

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.CLIENT_SAV

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for JWT token"""
    access_token: str
    token_type: str = "bearer"

class SignupResponse(BaseModel):
    """Schema for signup response"""
    user: UserResponse
    access_token: str

class LoginResponse(BaseModel):
    """Schema for login response"""
    user: UserResponse
    access_token: str

class PermissionsResponse(BaseModel):
    """Schema for permissions response"""
    permissions: Dict[str, bool]

class TokenVerifyResponse(BaseModel):
    """Schema for token verification response"""
    valid: bool

