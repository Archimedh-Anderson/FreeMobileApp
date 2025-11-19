#!/bin/bash
# Script de démarrage pour FreeMobilaChat (dev & production)
# Usage: ./start_app.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

log() {
    echo "[start_app] $1"
}

log "=========================================="
log "FreeMobilaChat - Démarrage"
log "=========================================="

# Variables
PORT="${PORT:-8502}"
ADDRESS="${ADDRESS:-0.0.0.0}"
ENV_FILE="${ENV_FILE:-.env}"
VENV_PATH="${VENV_PATH:-venv}"
REQUIREMENTS_FILE="streamlit_app/requirements.txt"

# Vérifier que le venv existe
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    log "[ERREUR] Environnement virtuel non trouvé (${VENV_PATH})."
    log "Créez-le avec: python -m venv ${VENV_PATH}"
    exit 1
fi

# Activer le venv
log "[1/3] Activation de l'environnement virtuel..."
source "${VENV_PATH}/bin/activate"

# Vérifier que .env existe
if [ ! -f "${ENV_FILE}" ]; then
    log "[ERREUR] Fichier ${ENV_FILE} non trouvé."
    log "Veuillez créer un fichier .env avec vos clés API."
    exit 1
fi

# Vérifier les dépendances
log "[2/3] Vérification des dépendances..."
pip install -q -r "${REQUIREMENTS_FILE}"

# Démarrer Streamlit
log "[3/3] Démarrage de l'application..."
log "Application disponible sur: http://${ADDRESS}:${PORT}"

exec streamlit run streamlit_app/app.py \
    --server.port "${PORT}" \
    --server.address "${ADDRESS}" \
    --server.headless true \
    --browser.gatherUsageStats false \
    --logger.level info
