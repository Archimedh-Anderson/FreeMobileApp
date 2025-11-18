@echo off
REM Script de démarrage pour FreeMobilaChat en local
REM Usage: start_app.bat

echo ==========================================
echo FreeMobilaChat - Demarrage Local
echo ==========================================
echo.

REM Verifier que le venv existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERREUR] Environnement virtuel non trouve.
    echo Veuillez creer un venv: python -m venv venv
    pause
    exit /b 1
)

REM Activer le venv
echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Verifier que .env existe
if not exist ".env" (
    echo [ERREUR] Fichier .env non trouve.
    echo Veuillez creer un fichier .env avec vos cles API.
    pause
    exit /b 1
)

REM Verifier les dependances
echo [2/3] Verification des dependances...
pip install -q -r streamlit_app\requirements.txt
if errorlevel 1 (
    echo [ERREUR] Installation des dependances echouee.
    pause
    exit /b 1
)

REM Demarrer Streamlit
echo [3/3] Demarrage de l'application...
echo.
echo ==========================================
echo Application disponible sur: http://localhost:8502
echo ==========================================
echo.

streamlit run streamlit_app\app.py --server.port 8502 --server.address localhost

pause

