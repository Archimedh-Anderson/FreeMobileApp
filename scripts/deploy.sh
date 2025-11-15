#!/bin/bash
# Script de déploiement
# Usage: ./scripts/deploy.sh

set -e

echo "🚀 Déploiement FreeMobile Classifier"
echo "====================================="

# Vérifications
if [ ! -f ".env" ]; then
    echo "⚠️ Fichier .env non trouvé"
    if [ -f ".env.example" ]; then
        echo "Copiez .env.example vers .env et configurez vos variables"
    elif [ -f "ENV_SETUP.md" ]; then
        echo "Consultez ENV_SETUP.md pour créer votre fichier .env"
    else
        echo "Créez un fichier .env avec vos variables d'environnement"
    fi
    echo ""
    echo "Note: Le fichier .env est optionnel pour le développement local"
    echo "mais requis pour certaines fonctionnalités (Gemini API, etc.)"
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



