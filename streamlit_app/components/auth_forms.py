"""
Authentication forms for login and signup
Provides UI components for user authentication
"""

import streamlit as st
import re
from services.auth_service import AuthService


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    return True, ""


def login_form():
    """Render login form"""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #CC0000; font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;">
                Welcome Back
            </h2>
            <p style="color: #666; font-size: 1.1rem;">
                Sign in to access your dashboard
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="Enter your registered email address",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Your secure password",
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submit:
            # Validate inputs
            if not email or not password:
                st.error("Please fill in all fields")
                return

            if not validate_email(email):
                st.error("Please enter a valid email address")
                return

            # Attempt login
            with st.spinner("Signing in..."):
                success, message, user = AuthService.login(email, password)

            if success:
                st.success(message)
                st.balloons()
                # DOM stability delay before rerun
                import time

                time.sleep(0.3)
                # Reload page to update authentication state
                st.rerun()
            else:
                st.error(message)


def signup_form():
    """Render signup form"""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #CC0000; font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;">
                Create Account
            </h2>
            <p style="color: #666; font-size: 1.1rem;">
                Join FreeMobilaChat today
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input("Full Name", placeholder="John Doe", help="Enter your full name")

        email = st.text_input(
            "Email Address", placeholder="your.email@example.com", help="Enter your email address"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            help="Must be at least 8 characters with uppercase, lowercase, and numbers",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            help="Must match the password above",
        )

        role = st.selectbox(
            "Account Type",
            options=[
                ("client_sav", "Client SAV - Customer support client"),
                ("agent_sav", "Agent SAV - Customer support agent"),
                ("data_analyst", "Data Analyst - Data analysis professional"),
                ("manager", "Manager - Team manager"),
            ],
            format_func=lambda x: x[1],
            help="Select your role in the organization",
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button(
                "Create Account", type="primary", use_container_width=True
            )

        if submit:
            # Validate inputs
            if not all([full_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return

            if not validate_email(email):
                st.error("Please enter a valid email address")
                return

            if password != confirm_password:
                st.error("Passwords do not match")
                return

            is_valid, error_msg = validate_password(password)
            if not is_valid:
                st.error(error_msg)
                return

            # Attempt signup
            with st.spinner("Creating your account..."):
                success, message, user = AuthService.signup(
                    email=email,
                    full_name=full_name,
                    password=password,
                    role=role[0],  # Get role code from tuple
                )

            if success:
                st.success(message)
                st.balloons()
                # DOM stability delay before rerun
                import time

                time.sleep(0.3)
                # Reload page to update authentication state
                st.rerun()
            else:
                st.error(message)


def render_auth_page():
    """Render the main authentication page with tabs for login/signup"""
    # Custom CSS for auth page
    st.markdown(
        """
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            height: 4rem;
            padding: 1rem 3rem;
            font-size: 1.2rem;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #CC0000 0%, #8B0000 100%);
            color: white;
            border-radius: 10px 10px 0 0;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Add some spacing
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])

    with tab1:
        st.markdown("<div style='padding: 2rem;'></div>", unsafe_allow_html=True)
        login_form()

    with tab2:
        st.markdown("<div style='padding: 2rem;'></div>", unsafe_allow_html=True)
        signup_form()

    # Add footer info
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 10px; margin-top: 2rem;">
            <p style="color: #666; font-size: 0.9rem; margin: 0;">
                By signing up, you agree to our Terms of Service and Privacy Policy
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )
