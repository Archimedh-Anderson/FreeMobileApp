#!/bin/bash
# ============================================================================
# FreeMobilaChat - Application Startup Script (Linux/macOS)
# Version: 2.0.0
# ============================================================================

set -e  # Exit on error

echo ""
echo "========================================"
echo "  FreeMobilaChat - Starting Application"
echo "========================================"
echo ""

# Change to project root directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[WARNING] Virtual environment not found!"
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "[OK] Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    if [ -f ".env.example" ]; then
        echo "[INFO] Copying .env.example to .env..."
        cp .env.example .env
        echo "[OK] .env file created from .env.example"
        echo "[INFO] Please edit .env file with your API keys before continuing"
        echo ""
        read -p "Press Enter to continue..."
    elif [ -f "ENV_SETUP.md" ]; then
        echo "[INFO] Please create .env file using ENV_SETUP.md as reference"
        echo "[INFO] Press Enter to continue anyway..."
        read -p ""
    else
        echo "[ERROR] .env.example not found. Please create .env manually"
        exit 1
    fi
fi

# Check Python version
echo "[OK] Checking Python version..."
python3 --version

# Install/upgrade dependencies if needed
echo "[OK] Checking dependencies..."
pip install --quiet --upgrade pip

if [ -f "requirements.production.txt" ]; then
    pip install --quiet -r requirements.production.txt
elif [ -f "requirements-academic.txt" ]; then
    pip install --quiet -r requirements-academic.txt
elif [ -f "streamlit_app/requirements.txt" ]; then
    pip install --quiet -r streamlit_app/requirements.txt
else
    echo "[ERROR] No requirements file found!"
    exit 1
fi

# Create necessary directories
echo "[OK] Creating necessary directories..."
mkdir -p logs
mkdir -p exports
mkdir -p data/processed
mkdir -p streamlit_app/cache

# Check if Ollama is running (optional, for Mistral)
echo "[OK] Checking Ollama availability (optional)..."
if command -v ollama &> /dev/null; then
    echo "[INFO] Ollama found. Checking if service is running..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[OK] Ollama service is running"
    else
        echo "[WARNING] Ollama service not running. Start it with: ollama serve"
    fi
else
    echo "[INFO] Ollama not found. Mistral local will not be available."
    echo "[INFO] You can use Gemini API instead (configure GEMINI_API_KEY in .env)"
fi

echo ""
echo "========================================"
echo "  Starting Streamlit Application"
echo "========================================"
echo ""
echo "[INFO] Application will start on: http://localhost:8502"
echo "[INFO] Press Ctrl+C to stop the application"
echo ""

# Start Streamlit application
streamlit run streamlit_app/app.py --server.port=8502 --server.headless=true



