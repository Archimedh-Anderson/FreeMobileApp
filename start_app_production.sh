#!/bin/bash
# Script de démarrage pour FreeMobilaChat en production (Lightsail)
# Usage: ./start_app_production.sh
# Ce script est utilisé par PM2 pour démarrer l'application en production

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMLIT_DIR="${SCRIPT_DIR}/streamlit_app"
VENV_DIR="${SCRIPT_DIR}/venv"
PORT="${PORT:-8502}"
ADDRESS="${ADDRESS:-0.0.0.0}"

# Logging
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/startup_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "🚀 Démarrage de FreeMobilaChat en production..."
log "Répertoire: ${SCRIPT_DIR}"
log "Port: ${PORT}"
log "Adresse: ${ADDRESS}"

# Vérifier que le répertoire streamlit_app existe
if [ ! -d "${STREAMLIT_DIR}" ]; then
    log "❌ ERREUR: Répertoire streamlit_app introuvable: ${STREAMLIT_DIR}"
    exit 1
fi

# Vérifier et activer l'environnement virtuel
if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    log "⚠️  Environnement virtuel non trouvé - création..."
    python3 -m venv "${VENV_DIR}" || {
        log "❌ ERREUR: Échec de la création de l'environnement virtuel"
        exit 1
    }
fi

log "🔧 Activation de l'environnement virtuel..."
source "${VENV_DIR}/bin/activate" || {
    log "❌ ERREUR: Échec de l'activation de l'environnement virtuel"
    exit 1
}

# Vérifier que les dépendances sont installées
log "📦 Vérification des dépendances..."
if [ -f "${STREAMLIT_DIR}/requirements.txt" ]; then
    pip install -q -r "${STREAMLIT_DIR}/requirements.txt" || {
        log "⚠️  Certaines dépendances n'ont pas pu être installées"
    }
else
    log "⚠️  Fichier requirements.txt introuvable"
fi

# Vérifier que app.py existe
if [ ! -f "${STREAMLIT_DIR}/app.py" ]; then
    log "❌ ERREUR: Fichier app.py introuvable: ${STREAMLIT_DIR}/app.py"
    exit 1
fi

# Test de syntaxe Python
log "🔍 Vérification de la syntaxe Python..."
python3 -m py_compile "${STREAMLIT_DIR}/app.py" || {
    log "❌ ERREUR: Erreur de syntaxe dans app.py"
    exit 1
}

# Démarrer Streamlit en production
log "🌐 Démarrage de Streamlit..."
log "=========================================="
log "Application disponible sur: http://${ADDRESS}:${PORT}"
log "=========================================="

cd "${STREAMLIT_DIR}"

# Démarrer Streamlit avec les paramètres de production
exec streamlit run app.py \
    --server.port "${PORT}" \
    --server.address "${ADDRESS}" \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    --browser.gatherUsageStats false \
    --logger.level info

