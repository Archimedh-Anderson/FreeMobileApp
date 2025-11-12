"""
FreeMobileApp Backend API
FastAPI backend for authentication and user management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.database import engine, Base
from backend.routers import auth

# Create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass

# Initialize FastAPI app
app = FastAPI(
    title="FreeMobileApp API",
    description="Backend API for FreeMobileApp - Authentication and User Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
# Get Streamlit Cloud URL from environment or use default
STREAMLIT_URL = os.getenv(
    "STREAMLIT_URL",
    "https://freemobileapp-lihc6p3rkjeba8avbsuh3v.streamlit.app"
)

# Local development URLs
LOCAL_URLS = [
    "http://localhost:8501",
    "http://localhost:8502",
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502"
]

# Combine all allowed origins
allowed_origins = [STREAMLIT_URL] + LOCAL_URLS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "message": "FreeMobileApp API is running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FreeMobileApp API"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

