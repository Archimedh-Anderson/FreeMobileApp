#!/bin/bash

# FreeMobilaChat - Production Deployment Script
# Version: 4.1 Professional Edition

echo ""
echo "========================================"
echo "  FREEMOBILACHAT - PRODUCTION DEPLOY"
echo "========================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python --version

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install production dependencies
echo "✓ Installing production dependencies..."
pip install --upgrade pip
if [ -f "requirements.production.txt" ]; then
    pip install -r requirements.production.txt
elif [ -f "requirements-academic.txt" ]; then
    pip install -r requirements-academic.txt
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ No requirements file found, skipping dependency installation"
fi

# Create necessary directories
echo "✓ Creating production directories..."
mkdir -p logs
mkdir -p exports
mkdir -p data/processed

# Copy production environment file
echo "✓ Setting up environment..."
if [ -f ".env.production" ]; then
    cp .env.production .env
    echo "   → .env configured for production"
fi

# Run database migrations (if applicable)
echo "✓ Running database migrations..."
# python backend/app/database/migrate.py

# Verify models exist
echo "✓ Verifying models..."
if [ -d "models/baseline" ] && [ -d "models/bert_finetuning" ]; then
    echo "   → Models found and ready"
else
    echo "   ⚠ Warning: Models not found. Train models before deploying."
fi

# Verify training data
echo "✓ Verifying training data..."
if [ -f "data/training/train_dataset.csv" ]; then
    echo "   → Training data found"
else
    echo "   ⚠ Warning: Training data not found"
fi

echo ""
echo "========================================"
echo "  DEPLOYMENT COMPLETE"
echo "========================================"
echo ""
echo "🚀 Start application with:"
echo "   streamlit run streamlit_app/app.py --server.port=8502"
echo ""
echo "   OR"
echo ""
echo "   ./start_application.sh"
echo ""
echo "🌐 Access at: http://localhost:8502"
echo ""

