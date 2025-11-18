"""
Authentication service for Streamlit frontend
Handles communication with backend API and session management
"""

import streamlit as st
import requests
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Backend API URL - Use environment variable or default to localhost for local development
# For demo purposes, allow offline authentication
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").lower() == "true"  # Enable offline demo mode


class AuthService:
    """Service for handling authentication in Streamlit"""

    @staticmethod
    def init_session_state():
        """Initialize session state variables for authentication"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

        if "user" not in st.session_state:
            st.session_state.user = None

        if "token" not in st.session_state:
            st.session_state.token = None

        if "permissions" not in st.session_state:
            st.session_state.permissions = {}

    @staticmethod
    def signup(
        email: str, full_name: str, password: str, role: str
    ) -> tuple[bool, str, Optional[Dict]]:
        """
        Register a new user

        Args:
            email: User email
            full_name: User full name
            password: User password
            role: User role

        Returns:
            Tuple of (success, message, user_data)
        """
        # Offline mode for demo/testing
        if OFFLINE_MODE:
            st.session_state.authenticated = True
            user_data = {"email": email, "full_name": full_name, "role": role}
            st.session_state.user = user_data
            st.session_state.token = f"demo_token_{email}"
            AuthService.load_permissions()
            return True, "Registration successful!", user_data

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/signup",
                json={"email": email, "full_name": full_name, "password": password, "role": role},
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                st.session_state.authenticated = True
                st.session_state.user = data["user"]
                st.session_state.token = data["access_token"]

                # Get permissions
                AuthService.load_permissions()

                return True, "Registration successful!", data["user"]
            else:
                error_detail = response.json().get("detail", "Registration failed")
                return False, error_detail, None

        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to server. Please ensure the backend is running.", None
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return False, f"An error occurred: {str(e)}", None

    @staticmethod
    def login(email: str, password: str) -> tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user and create session

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (success, message, user_data)
        """
        # Offline mode for demo/testing - any non-empty credentials work
        if OFFLINE_MODE:
            if not email or not password:
                return False, "Please fill in all fields", None

            st.session_state.authenticated = True
            # Determine role based on email patterns
            role = "manager"
            if "analyst" in email.lower():
                role = "data_analyst"
            elif "agent" in email.lower():
                role = "agent_sav"
            elif "client" in email.lower():
                role = "client_sav"

            user_data = {
                "email": email,
                "full_name": email.split("@")[0].replace(".", " ").title(),
                "role": role,
            }
            st.session_state.user = user_data
            st.session_state.token = f"demo_token_{email}"
            AuthService.load_permissions()
            return True, "Login successful!", user_data

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.authenticated = True
                st.session_state.user = data["user"]
                st.session_state.token = data["access_token"]

                # Get permissions
                AuthService.load_permissions()

                return True, "Login successful!", data["user"]
            else:
                error_detail = response.json().get("detail", "Login failed")
                return False, error_detail, None

        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to server. Please ensure the backend is running.", None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, f"An error occurred: {str(e)}", None

    @staticmethod
    def logout():
        """Logout user and clear session"""
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.token = None
        st.session_state.permissions = {}

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get("authenticated", False)

    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """Get current user information"""
        return st.session_state.get("user", None)

    @staticmethod
    def get_user_role() -> Optional[str]:
        """Get current user role"""
        user = AuthService.get_current_user()
        return user.get("role") if user else None

    @staticmethod
    def get_token() -> Optional[str]:
        """Get current auth token"""
        return st.session_state.get("token", None)

    @staticmethod
    def load_permissions():
        """Load user permissions from backend"""
        try:
            token = AuthService.get_token()
            if not token:
                return

            response = requests.get(
                f"{BACKEND_URL}/api/auth/me/permissions",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.permissions = data.get("permissions", {})

        except Exception as e:
            logger.error(f"Error loading permissions: {e}")

    @staticmethod
    def has_permission(permission: str) -> bool:
        """Check if user has a specific permission"""
        permissions = st.session_state.get("permissions", {})
        return permissions.get(permission, False)

    @staticmethod
    def verify_token() -> bool:
        """Verify if current token is still valid"""
        try:
            token = AuthService.get_token()
            if not token:
                return False

            response = requests.post(
                f"{BACKEND_URL}/api/auth/verify-token",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("valid", False)

            return False

        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False

    @staticmethod
    def require_auth(allowed_roles: Optional[list] = None):
        """
        Decorator/helper to require authentication for a page

        Args:
            allowed_roles: List of roles allowed to access the page (None = all roles)
        """
        AuthService.init_session_state()

        if not AuthService.is_authenticated():
            st.warning("Please login to access this page")
            st.stop()

        # Verify token is still valid
        if not AuthService.verify_token():
            st.error("Your session has expired. Please login again.")
            AuthService.logout()
            st.stop()

        # Check role permission
        if allowed_roles is not None:
            current_role = AuthService.get_user_role()
            if current_role not in allowed_roles:
                st.error("You don't have permission to access this page")
                st.stop()

    @staticmethod
    def get_role_display_name(role: str) -> str:
        """Get human-readable role name"""
        role_names = {
            "client_sav": "Client SAV",
            "agent_sav": "Agent SAV",
            "data_analyst": "Data Analyst",
            "manager": "Manager",
        }
        return role_names.get(role, role)

    @staticmethod
    def get_role_icon(role: str) -> str:
        """Get Font Awesome icon for each role (academic-appropriate)"""
        role_icons = {
            "client_sav": '<i class="fas fa-user" style="color: #2E86DE;"></i>',
            "agent_sav": '<i class="fas fa-headset" style="color: #10AC84;"></i>',
            "data_analyst": '<i class="fas fa-chart-bar" style="color: #F79F1F;"></i>',
            "manager": '<i class="fas fa-user-tie" style="color: #EE5A6F;"></i>',
        }
        return role_icons.get(role, '<i class="fas fa-user"></i>')
