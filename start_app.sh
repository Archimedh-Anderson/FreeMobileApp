#!/bin/bash
# Script de démarrage pour FreeMobilaChat en local
# Usage: ./start_app.sh

echo "=========================================="
echo "FreeMobilaChat - Démarrage Local"
echo "=========================================="
echo ""

# Vérifier que le venv existe
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERREUR] Environnement virtuel non trouvé."
    echo "Veuillez créer un venv: python -m venv venv"
    exit 1
fi

# Activer le venv
echo "[1/3] Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier que .env existe
if [ ! -f ".env" ]; then
    echo "[ERREUR] Fichier .env non trouvé."
    echo "Veuillez créer un fichier .env avec vos clés API."
    exit 1
fi

# Vérifier les dépendances
echo "[2/3] Vérification des dépendances..."
pip install -q -r streamlit_app/requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERREUR] Installation des dépendances échouée."
    exit 1
fi

# Démarrer Streamlit
echo "[3/3] Démarrage de l'application..."
echo ""
echo "=========================================="
echo "Application disponible sur: http://localhost:8502"
echo "=========================================="
echo ""

# Pour développement local, utiliser localhost
# Pour production, utiliser 0.0.0.0
streamlit run streamlit_app/app.py --server.port 8502 --server.address 0.0.0.0
