"""
Configuration settings for FreeMobileApp Backend
"""

import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "FreeMobileApp API"
    VERSION: str = "1.0.0"
    
    # Security - Railway variables
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    JWT_SECRET: str = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Database - Railway injects DATABASE_URL automatically
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # CORS
    STREAMLIT_URL: str = os.getenv(
        "STREAMLIT_URL",
        "https://freemobileapp-lihc6p3rkjeba8avbsuh3v.streamlit.app"
    )
    
    # Password validation
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    
    # User roles
    ROLES: list = ["client_sav", "agent_sav", "data_analyst", "manager"]
    
    # Permissions by role
    PERMISSIONS: dict = {
        "client_sav": {
            "view_own_tickets": True,
            "create_ticket": True,
            "view_analytics": False
        },
        "agent_sav": {
            "view_all_tickets": True,
            "update_tickets": True,
            "view_analytics": True,
            "export_data": False
        },
        "data_analyst": {
            "view_analytics": True,
            "export_data": True,
            "view_all_tickets": False,
            "update_tickets": False
        },
        "manager": {
            "view_all_tickets": True,
            "update_tickets": True,
            "view_analytics": True,
            "export_data": True,
            "manage_users": True,
            "all_permissions": True
        }
    }

settings = Settings()

