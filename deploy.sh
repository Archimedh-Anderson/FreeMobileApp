#!/bin/bash

###############################################################################
# Script de déploiement pour FreeMobilaChat sur AWS EC2
# Usage: bash deploy.sh
# Prérequis: Exécuté sur le serveur EC2 en tant qu'ec2-user
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
APP_DIR="/home/ec2-user/FreeMobileApp"
STREAMLIT_DIR="${APP_DIR}/streamlit_app"
SERVICE_NAME="streamlit.service"
LOG_FILE="/var/log/streamlit.log"
BACKUP_DIR="${APP_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
            streamlit_app
        
        log_success "Sauvegarde créée: backup_${TIMESTAMP}.tar.gz"
    fi
    
    # Garder seulement les 5 dernières sauvegardes
    cd "${BACKUP_DIR}"
    ls -t backup_*.tar.gz | tail -n +6 | xargs -r rm --
}

###############################################################################
# Fonction: Récupération du code depuis GitHub
###############################################################################
pull_code() {
    log_info "Récupération du code depuis GitHub..."
    
    cd "${APP_DIR}"
    
    # Sauvegarde des modifications locales non committées
    if ! git diff-index --quiet HEAD --; then
        log_warning "Modifications locales détectées - sauvegarde avec git stash"
        git stash save "Auto-stash before deploy ${TIMESTAMP}"
    fi
    
    # Récupération des modifications
    git fetch origin main
    
    # Affichage des changements
    log_info "Changements à appliquer:"
    git log HEAD..origin/main --oneline --decorate=short
    
    # Mise à jour vers la dernière version
    git reset --hard origin/main
    
    # Affichage du commit actuel
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    log_success "Code mis à jour - Commit: ${CURRENT_COMMIT}"
}

###############################################################################
# Fonction: Installation des dépendances Python
###############################################################################
install_dependencies() {
    log_info "Installation des dépendances Python..."
    
    cd "${STREAMLIT_DIR}"
    
    # Activation de l'environnement virtuel (s'il existe)
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_warning "Environnement virtuel non trouvé - utilisation de Python système"
    fi
    
    # Mise à jour de pip
    python3 -m pip install --upgrade pip --quiet
    
    # Installation des packages
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt --quiet
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
    
    # Vérification du fichier .env
    if [ ! -f ".env" ]; then
        log_warning "Fichier .env manquant - création d'un fichier template"
        cat > .env << EOF
# Configuration FreeMobilaChat
GEMINI_API_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
STREAMLIT_PORT=8503
ENVIRONMENT=production
EOF
        log_warning "Pensez à configurer vos clés API dans .env"
    else
        log_success "Fichier .env présent"
    fi
    
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
# Fonction: Redémarrage du service Streamlit
###############################################################################
restart_service() {
    log_info "Redémarrage du service Streamlit..."
    
    # Redémarrage du service
    if sudo systemctl restart ${SERVICE_NAME}; then
        log_success "Service redémarré"
    else
        log_error "Échec du redémarrage du service"
        sudo journalctl -u ${SERVICE_NAME} -n 20 --no-pager
        exit 1
    fi
    
    # Attente du démarrage
    sleep 5
    
    # Vérification du statut
    if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
        log_success "Service Streamlit actif"
        sudo systemctl status ${SERVICE_NAME} --no-pager --lines=0
    else
        log_error "Le service n'est pas démarré correctement"
        log_error "Consultez les logs: sudo journalctl -u ${SERVICE_NAME} -f"
        exit 1
    fi
}

###############################################################################
# Fonction: Affichage des logs
###############################################################################
show_logs() {
    log_info "Dernières lignes de log (${LOG_FILE}):"
    
    if [ -f "${LOG_FILE}" ]; then
        sudo tail -n 30 "${LOG_FILE}"
    else
        log_warning "Fichier de log non trouvé: ${LOG_FILE}"
    fi
}

###############################################################################
# Fonction: Test de santé de l'application
###############################################################################
health_check() {
    log_info "Test de santé de l'application..."
    
    # Attente que l'application soit prête
    sleep 3
    
    # Test de connexion HTTP
    if curl -f http://localhost:8503 > /dev/null 2>&1; then
        log_success "Application accessible sur http://localhost:8503"
    else
        log_warning "Application non accessible via HTTP (normal si derrière un proxy)"
    fi
    
    # Vérification des processus Streamlit
    if pgrep -f "streamlit run" > /dev/null; then
        log_success "Processus Streamlit en cours d'exécution"
        log_info "PID: $(pgrep -f 'streamlit run')"
    else
        log_error "Aucun processus Streamlit trouvé"
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
    echo "   🚀 DÉPLOIEMENT FreeMobilaChat - $(date)"
    echo "=================================================================="
    echo ""
    
    # Vérification que le script est exécuté depuis le bon utilisateur
    if [ "$(whoami)" != "ec2-user" ]; then
        log_error "Ce script doit être exécuté en tant qu'ec2-user"
        exit 1
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
    log_info "Application accessible sur: http://13.37.186.191:8503"
    log_info "Logs en temps réel: sudo journalctl -u ${SERVICE_NAME} -f"
    log_info "Logs applicatifs: sudo tail -f ${LOG_FILE}"
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
        sudo systemctl status ${SERVICE_NAME}
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
        echo "  status   - Statut du service"
        echo "  restart  - Redémarrage du service uniquement"
        echo "  health   - Test de santé de l'application"
        exit 1
        ;;
esac
