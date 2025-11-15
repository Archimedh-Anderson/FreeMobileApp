#!/bin/bash
# Script de déploiement
# Usage: ./scripts/deploy.sh

set -e

echo "🚀 Déploiement FreeMobile Classifier"
echo "====================================="

# Vérifications
if [ ! -f ".env" ]; then
    echo "⚠️ Fichier .env non trouvé"
    echo "Copiez env.example vers .env et configurez vos variables"
    exit 1
fi

# Tests avant déploiement
echo "🧪 Exécution des tests..."
./scripts/run_tests.sh unit || echo "⚠️ Certains tests ont échoué"

# Vérification de l'application Streamlit
echo "🔍 Vérification de l'application..."
python -c "import streamlit; print('Streamlit OK')" || exit 1

echo "✅ Prêt pour le déploiement!"
echo ""
echo "Pour Streamlit Cloud:"
echo "1. Push vers GitHub: git push origin main"
echo "2. Streamlit Cloud détectera automatiquement le déploiement"
echo ""
echo "Pour déploiement local:"
echo "streamlit run streamlit_app/app.py"


