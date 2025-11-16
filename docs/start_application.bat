@echo off
REM ============================================================================
REM FreeMobilaChat - Application Startup Script
REM Version: 2.0.0
REM ============================================================================

echo.
echo ========================================
echo   FreeMobilaChat - Starting Application
echo ========================================
echo.

REM Change to project root directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo [WARNING] Virtual environment not found!
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [OK] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo [INFO] Copying .env.example to .env...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] .env file created from .env.example
        echo [INFO] Please edit .env file with your API keys before continuing
        echo.
        pause
    ) else (
        echo [ERROR] .env.example not found. Please create .env manually
        pause
        exit /b 1
    )
)

REM Check Python version
echo [OK] Checking Python version...
python --version

REM Install/upgrade dependencies if needed
echo [OK] Checking dependencies...
pip install --quiet --upgrade pip
if exist "requirements.production.txt" (
    pip install --quiet -r requirements.production.txt
) else if exist "requirements-academic.txt" (
    pip install --quiet -r requirements-academic.txt
) else (
    echo [WARNING] No requirements file found. Installing from streamlit_app/requirements.txt...
    if exist "streamlit_app\requirements.txt" (
        pip install --quiet -r streamlit_app\requirements.txt
    ) else (
        echo [ERROR] No requirements file found!
        pause
        exit /b 1
    )
)

REM Create necessary directories
echo [OK] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "data\processed" mkdir data\processed
if not exist "streamlit_app\cache" mkdir streamlit_app\cache

REM Check if Ollama is running (optional, for Mistral)
echo [OK] Checking Ollama availability (optional)...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama not found. Mistral local will not be available.
    echo [INFO] You can use Gemini API instead (configure GEMINI_API_KEY in .env)
) else (
    echo [INFO] Ollama found. Checking if service is running...
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Ollama service not running. Start it with: ollama serve
    ) else (
        echo [OK] Ollama service is running
    )
)

echo.
echo ========================================
echo   Starting Streamlit Application
echo ========================================
echo.
echo [INFO] Application will start on: http://localhost:8502
echo [INFO] Press Ctrl+C to stop the application
echo.

REM Start Streamlit application
streamlit run streamlit_app/app.py --server.port=8502 --server.headless=true

REM If we get here, the application has stopped
echo.
echo [INFO] Application stopped
pause



