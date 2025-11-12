"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import (
    UserCreate,
    UserLogin,
    SignupResponse,
    LoginResponse,
    PermissionsResponse,
    TokenVerifyResponse,
    UserResponse
)
from backend.security import verify_password, get_password_hash, create_access_token, decode_access_token
from backend.dependencies import get_current_user
from backend.config import settings

router = APIRouter()

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Returns:
        User data and access token
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email})
    
    return SignupResponse(
        user=UserResponse.model_validate(db_user),
        access_token=access_token
    )

@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token
    
    Returns:
        User data and access token
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return LoginResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token
    )

@router.get("/me/permissions", response_model=PermissionsResponse)
def get_permissions(current_user: User = Depends(get_current_user)):
    """
    Get permissions for current user
    
    Returns:
        User permissions based on role
    """
    permissions = settings.PERMISSIONS.get(current_user.role.value, {})
    return PermissionsResponse(permissions=permissions)

@router.post("/verify-token", response_model=TokenVerifyResponse)
def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify if current token is valid
    
    Returns:
        Token validity status
    """
    return TokenVerifyResponse(valid=True)

