@echo off
REM FreeMobilaChat - Production Deployment Script
REM Version: 4.1 Professional Edition

echo.
echo ========================================
echo   FREEMOBILACHAT - PRODUCTION DEPLOY
echo ========================================
echo.

REM Check Python version
echo [OK] Checking Python version...
python --version

REM Create virtual environment if not exists
if not exist "venv" (
    echo [OK] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [OK] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install production dependencies
echo [OK] Installing production dependencies...
python -m pip install --upgrade pip
if exist "requirements.production.txt" (
    pip install -r requirements.production.txt
) else if exist "requirements-academic.txt" (
    pip install -r requirements-academic.txt
) else (
    echo [ERROR] No requirements file found!
    exit /b 1
)

REM Create necessary directories
echo [OK] Creating production directories...
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "data\processed" mkdir data\processed

REM Copy production environment file
echo [OK] Setting up environment...
if exist ".env.production" (
    copy .env.production .env
    echo    [OK] .env configured for production
)

REM Verify models exist
echo [OK] Verifying models...
if exist "models\baseline" (
    if exist "models\bert_finetuning" (
        echo    [OK] Models found and ready
    )
) else (
    echo    [WARNING] Models not found. Train models before deploying.
)

REM Verify training data
echo [OK] Verifying training data...
if exist "data\training\train_dataset.csv" (
    echo    [OK] Training data found
) else (
    echo    [WARNING] Training data not found
)

echo.
echo ========================================
echo   DEPLOYMENT COMPLETE
echo ========================================
echo.
echo [START] Start application with:
echo    streamlit run streamlit_app/app.py --server.port=8502
echo.
echo    OR
echo.
echo    start_application.bat
echo.
echo [URL] Access at: http://localhost:8502
echo.
pause

