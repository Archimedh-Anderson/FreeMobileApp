#!/bin/bash
###############################################################################
# Script de déploiement pour FreeMobilaChat sur AWS Lightsail
# Usage: bash deploy_lightsail.sh
# Prérequis: Exécuté sur le serveur Lightsail en tant que freemobila
###############################################################################

set -e  # Arrêt en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables de configuration
APP_DIR="$HOME/FreeMobileApp"
STREAMLIT_DIR="${APP_DIR}/streamlit_app"
VENV_DIR="${APP_DIR}/venv"
BACKUP_DIR="${APP_DIR}/backups"
LOG_DIR="${APP_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PM2_APP_NAME="freemobile-app"

###############################################################################
# Fonction: Création d'une sauvegarde avant déploiement
###############################################################################
create_backup() {
    log_info "Création d'une sauvegarde..."
    
    # Créer le répertoire de backup s'il n'existe pas
    mkdir -p "${BACKUP_DIR}"
    
    # Sauvegarde du code actuel
    if [ -d "${STREAMLIT_DIR}" ]; then
        tar -czf "${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz" \
            -C "${APP_DIR}" \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            --exclude='logs' \
            --exclude='backups' \
            streamlit_app 2>/dev/null || true
        
        log_success "Sauvegarde créée: backup_${TIMESTAMP}.tar.gz"
    fi
    
    # Garder seulement les 5 dernières sauvegardes
    cd "${BACKUP_DIR}"
    ls -t backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f || true
}

###############################################################################
# Fonction: Récupération du code depuis GitHub
###############################################################################
pull_code() {
    log_info "Récupération du code depuis GitHub..."
    
    cd "${APP_DIR}"
    
    # Sauvegarde des modifications locales non committées
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warning "Modifications locales détectées - sauvegarde avec git stash"
        git stash save "Auto-stash before deploy ${TIMESTAMP}" || true
    fi
    
    # Récupération des modifications
    git fetch origin main || git fetch origin master || {
        log_error "Échec de la récupération depuis GitHub"
        exit 1
    }
    
    # Affichage des changements
    log_info "Changements à appliquer:"
    git log HEAD..origin/main --oneline --decorate=short 2>/dev/null || \
    git log HEAD..origin/master --oneline --decorate=short 2>/dev/null || true
    
    # Mise à jour vers la dernière version
    BRANCH=$(git branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's/origin\///' | xargs)
    if [ -z "$BRANCH" ]; then
        BRANCH="main"
    fi
    
    git reset --hard "origin/${BRANCH}" || {
        log_error "Échec de la mise à jour du code"
        exit 1
    }
    
    # Affichage du commit actuel
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    log_success "Code mis à jour - Commit: ${CURRENT_COMMIT}"
}

###############################################################################
# Fonction: Installation des dépendances Python
###############################################################################
install_dependencies() {
    log_info "Installation des dépendances Python..."
    
    # Créer l'environnement virtuel s'il n'existe pas
    if [ ! -d "${VENV_DIR}" ]; then
        log_warning "Environnement virtuel non trouvé - création..."
        python3 -m venv "${VENV_DIR}" || {
            log_error "Échec de la création de l'environnement virtuel"
            exit 1
        }
    fi
    
    # Activation de l'environnement virtuel
    source "${VENV_DIR}/bin/activate" || {
        log_error "Échec de l'activation de l'environnement virtuel"
        exit 1
    }
    
    # Mise à jour de pip
    python3 -m pip install --upgrade pip --quiet
    
    # Installation des packages
    if [ -f "${STREAMLIT_DIR}/requirements.txt" ]; then
        python3 -m pip install -r "${STREAMLIT_DIR}/requirements.txt" --quiet || {
            log_error "Échec de l'installation des dépendances"
            exit 1
        }
        log_success "Dépendances installées avec succès"
    else
        log_error "Fichier requirements.txt introuvable!"
        exit 1
    fi
}

###############################################################################
# Fonction: Vérification de la configuration
###############################################################################
check_configuration() {
    log_info "Vérification de la configuration..."
    
    cd "${STREAMLIT_DIR}"
    
    # Vérification du fichier principal
    if [ ! -f "app.py" ]; then
        log_error "Fichier app.py introuvable!"
        exit 1
    fi
    
    # Test de syntaxe Python
    log_info "Vérification de la syntaxe Python..."
    if python3 -m py_compile app.py 2>/dev/null; then
        log_success "Syntaxe Python validée"
    else
        log_error "Erreur de syntaxe dans app.py"
        exit 1
    fi
}

###############################################################################
# Fonction: Redémarrage du service avec PM2
###############################################################################
restart_service() {
    log_info "Redémarrage du service avec PM2..."
    
    cd "${APP_DIR}"
    
    # Vérifier si PM2 est installé
    if ! command -v pm2 &> /dev/null; then
        log_warning "PM2 non trouvé - installation..."
        npm install -g pm2 || {
            log_error "Échec de l'installation de PM2"
            exit 1
        }
    fi
    
    # Redémarrage ou démarrage de l'application
    if pm2 describe "${PM2_APP_NAME}" &>/dev/null; then
        pm2 restart "${PM2_APP_NAME}" || {
            log_error "Échec du redémarrage du service"
            pm2 logs "${PM2_APP_NAME}" --lines 50 --nostream
            exit 1
        }
    else
        log_info "Application non trouvée - démarrage initial..."
        pm2 start ecosystem.config.js || {
            log_error "Échec du démarrage du service"
            exit 1
        }
    fi
    
    # Attente du démarrage
    sleep 5
    
    # Vérification du statut
    pm2 status
    
    if pm2 describe "${PM2_APP_NAME}" | grep -q "online"; then
        log_success "Service PM2 actif"
    else
        log_error "Le service n'est pas démarré correctement"
        log_error "Consultez les logs: pm2 logs ${PM2_APP_NAME} -f"
        pm2 logs "${PM2_APP_NAME}" --lines 50 --nostream
        exit 1
    fi
}

###############################################################################
# Fonction: Affichage des logs
###############################################################################
show_logs() {
    log_info "Dernières lignes de log:"
    
    if command -v pm2 &> /dev/null; then
        pm2 logs "${PM2_APP_NAME}" --lines 30 --nostream || true
    fi
    
    if [ -d "${LOG_DIR}" ]; then
        LATEST_LOG=$(ls -t "${LOG_DIR}"/startup_*.log 2>/dev/null | head -1)
        if [ -n "${LATEST_LOG}" ]; then
            log_info "Log de démarrage:"
            tail -n 20 "${LATEST_LOG}" || true
        fi
    fi
}

###############################################################################
# Fonction: Test de santé de l'application
###############################################################################
health_check() {
    log_info "Test de santé de l'application..."
    
    # Attente que l'application soit prête
    sleep 3
    
    # Vérification des processus PM2
    if pm2 describe "${PM2_APP_NAME}" | grep -q "online"; then
        log_success "Application PM2 en ligne"
    else
        log_error "Application PM2 non en ligne"
        pm2 logs "${PM2_APP_NAME}" --lines 50 --nostream
        exit 1
    fi
    
    # Test de connexion HTTP
    if curl -f -s http://localhost:8502 > /dev/null 2>&1; then
        log_success "Application accessible sur http://localhost:8502"
    else
        log_warning "Application non accessible via HTTP (normal si derrière un proxy)"
    fi
    
    # Vérification des processus Streamlit
    if pgrep -f "streamlit run" > /dev/null; then
        log_success "Processus Streamlit en cours d'exécution"
        log_info "PID: $(pgrep -f 'streamlit run')"
    else
        log_warning "Aucun processus Streamlit trouvé directement (peut être géré par PM2)"
    fi
}

###############################################################################
# Fonction: Restauration depuis une sauvegarde
###############################################################################
rollback() {
    log_warning "Restauration depuis la dernière sauvegarde..."
    
    LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "${LATEST_BACKUP}" ]; then
        log_error "Aucune sauvegarde trouvée"
        exit 1
    fi
    
    log_info "Restauration depuis: $(basename ${LATEST_BACKUP})"
    
    # Extraction de la sauvegarde
    tar -xzf "${LATEST_BACKUP}" -C "${APP_DIR}"
    
    log_success "Code restauré depuis la sauvegarde"
    
    # Redémarrage du service
    restart_service
}

###############################################################################
# MENU PRINCIPAL
###############################################################################
main() {
    echo "=================================================================="
    echo "   🚀 DÉPLOIEMENT FreeMobilaChat sur Lightsail - $(date)"
    echo "=================================================================="
    echo ""
    
    # Vérification que le script est exécuté depuis le bon utilisateur
    if [ "$(whoami)" != "freemobila" ]; then
        log_warning "Ce script est conçu pour l'utilisateur 'freemobila' (utilisateur actuel: $(whoami))"
    fi
    
    # Exécution des étapes de déploiement
    create_backup
    pull_code
    install_dependencies
    check_configuration
    restart_service
    health_check
    show_logs
    
    echo ""
    echo "=================================================================="
    echo "   ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
    echo "=================================================================="
    echo ""
    log_info "Application accessible sur: http://$(hostname -I | awk '{print $1}'):8502"
    log_info "Logs en temps réel: pm2 logs ${PM2_APP_NAME} -f"
    log_info "Statut: pm2 status"
    log_info "Redémarrer: pm2 restart ${PM2_APP_NAME}"
    echo ""
}

###############################################################################
# Gestion des arguments de ligne de commande
###############################################################################
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    logs)
        show_logs
        ;;
    status)
        pm2 status
        ;;
    restart)
        restart_service
        ;;
    health)
        health_check
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|logs|status|restart|health}"
        echo ""
        echo "Commandes:"
        echo "  deploy   - Déploiement complet (par défaut)"
        echo "  rollback - Restauration depuis la dernière sauvegarde"
        echo "  logs     - Affichage des logs"
        echo "  status   - Statut du service PM2"
        echo "  restart  - Redémarrage du service uniquement"
        echo "  health   - Test de santé de l'application"
        exit 1
        ;;
esac

