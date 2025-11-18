@echo off
REM Script de configuration locale pour FreeMobilaChat
REM Usage: setup_local.bat

echo ==========================================
echo FreeMobilaChat - Configuration Locale
echo ==========================================
echo.

REM Creer venv si inexistant
if not exist "venv" (
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Creation du venv echouee.
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree.
) else (
    echo [1/4] Environnement virtuel deja present.
)

REM Activer le venv
echo [2/4] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dependances
echo [3/4] Installation des dependances...
pip install --upgrade pip
pip install -r streamlit_app\requirements.txt
if errorlevel 1 (
    echo [ERREUR] Installation des dependances echouee.
    pause
    exit /b 1
)
echo [OK] Dependances installees.

REM Creer .env si inexistant
if not exist ".env" (
    echo [4/4] Creation du fichier .env...
    (
        echo ENV=development
        echo.
        echo PORT=8502
        echo HOST=localhost
        echo DOMAIN=localhost
        echo.
        echo REM Cles API - A remplacer par vos vraies cles
        echo MISTRAL_API_KEY=votre_cle_mistral
        echo GEMINI_API_KEY=votre_cle_gemini
        echo OLLAMA_BASE_URL=http://localhost:11434
    ) > .env
    echo [OK] Fichier .env cree.
    echo [ATTENTION] Veuillez remplir vos vraies cles API dans .env
) else (
    echo [4/4] Fichier .env deja present.
)

REM Creer dossier .streamlit si inexistant
if not exist ".streamlit" (
    mkdir .streamlit
)

echo.
echo ==========================================
echo Configuration terminee avec succes!
echo ==========================================
echo.
echo Prochaines etapes:
echo 1. Editez le fichier .env avec vos cles API
echo 2. Lancez l'application: start_app.bat
echo.
pause

