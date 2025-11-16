#!/bin/bash

###############################################################################
# Script de Déploiement Automatisé - FreeMobilaChat
# Version: 1.0
# Description: Déploiement vers Streamlit Cloud avec validation
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
PROJECT_NAME="FreeMobilaChat"
REPO_URL="https://github.com/Anderson-Archimede/FreeMobilaChat.git"
BRANCH="main"
PYTHON_VERSION="3.10"
APP_FILE="streamlit_app/app.py"

###############################################################################
# FONCTIONS UTILITAIRES
###############################################################################

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          DÉPLOIEMENT FREEMOBILACHAT                          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERREUR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "Commande '$1' non trouvée. Installation requise."
        exit 1
    fi
}

###############################################################################
# ÉTAPE 1: VÉRIFICATIONS PRÉALABLES
###############################################################################

check_prerequisites() {
    print_step "Vérification des prérequis..."
    
    # Vérifier Git
    check_command git
    print_success "Git installé"
    
    # Vérifier Python
    check_command python3
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python $PYTHON_VER installé"
    
    # Vérifier pip
    check_command pip3
    print_success "pip installé"
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -f "$APP_FILE" ]; then
        print_error "Fichier $APP_FILE non trouvé. Êtes-vous dans le bon répertoire?"
        exit 1
    fi
    print_success "Structure projet validée"
}

###############################################################################
# ÉTAPE 2: VALIDATION DU CODE
###############################################################################

validate_code() {
    print_step "Validation du code..."
    
    # Créer environnement virtuel temporaire
    if [ -d "venv_deploy" ]; then
        rm -rf venv_deploy
    fi
    
    python3 -m venv venv_deploy
    source venv_deploy/bin/activate
    
    # Installer dépendances
    print_step "Installation des dépendances..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements-academic.txt
    
    # Vérifier imports critiques
    print_step "Vérification des imports..."
    python3 -c "
import sys
sys.path.append('streamlit_app')
from services.mistral_classifier import MistralClassifier
from services.dynamic_classifier import IntentionClassifier
from services.batch_processor import BatchProcessor
from services.enhanced_kpis_vizualizations import compute_business_kpis
print('✓ Tous les imports OK')
" || {
        print_error "Erreur d'import détectée"
        deactivate
        rm -rf venv_deploy
        exit 1
    }
    
    print_success "Imports validés"
    
    # Désactiver environnement
    deactivate
    rm -rf venv_deploy
}

###############################################################################
# ÉTAPE 3: TESTS AUTOMATISÉS
###############################################################################

run_tests() {
    print_step "Exécution des tests..."
    
    # Créer environnement de test
    python3 -m venv venv_test
    source venv_test/bin/activate
    
    # Installer dépendances test
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements-academic.txt
    pip install --quiet pytest pytest-cov
    
    # Lancer tests critiques
    pytest tests/test_unit_classifier.py tests/test_unit_preprocessing.py -v --tb=short --maxfail=5 || {
        print_warning "Certains tests ont échoué. Voulez-vous continuer? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_error "Déploiement annulé"
            deactivate
            rm -rf venv_test
            exit 1
        fi
    }
    
    print_success "Tests validés"
    
    deactivate
    rm -rf venv_test
}

###############################################################################
# ÉTAPE 4: NETTOYAGE ET PRÉPARATION
###############################################################################

prepare_deployment() {
    print_step "Préparation du déploiement..."
    
    # Nettoyer fichiers temporaires
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name ".DS_Store" -delete 2>/dev/null || true
    
    print_success "Fichiers temporaires nettoyés"
    
    # Vérifier .gitignore
    if [ ! -f ".gitignore" ]; then
        print_warning "Fichier .gitignore manquant"
    else
        print_success ".gitignore présent"
    fi
    
    # Vérifier requirements
    if [ ! -f "requirements-academic.txt" ]; then
        print_error "requirements-academic.txt manquant"
        exit 1
    fi
    print_success "requirements-academic.txt présent"
}

###############################################################################
# ÉTAPE 5: GIT COMMIT ET PUSH
###############################################################################

git_deploy() {
    print_step "Déploiement Git..."
    
    # Vérifier statut Git
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        print_warning "Modifications non commitées détectées"
        
        # Afficher fichiers modifiés
        echo "Fichiers modifiés:"
        git status --short
        
        echo -e "\n${YELLOW}Voulez-vous commiter ces changements? (y/n)${NC}"
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            # Commit automatique
            TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
            git add -A
            git commit -m "deploy: Automated deployment - $TIMESTAMP"
            print_success "Changements commitées"
        fi
    else
        print_success "Aucune modification à commiter"
    fi
    
    # Push vers GitHub
    print_step "Push vers GitHub..."
    CURRENT_BRANCH=$(git branch --show-current)
    
    git push origin $CURRENT_BRANCH || {
        print_error "Échec du push Git"
        exit 1
    }
    
    print_success "Code poussé vers GitHub ($CURRENT_BRANCH)"
}

###############################################################################
# ÉTAPE 6: GÉNÉRATION DE MÉTADONNÉES
###############################################################################

generate_metadata() {
    print_step "Génération des métadonnées..."
    
    # Créer fichier de build info
    cat > .deployment_info << EOF
{
  "project": "$PROJECT_NAME",
  "version": "1.0.0",
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "git_commit": "$(git rev-parse --short HEAD)",
  "git_branch": "$(git branch --show-current)",
  "python_version": "$PYTHON_VER",
  "dependencies": "requirements-academic.txt"
}
EOF
    
    print_success "Métadonnées générées (.deployment_info)"
}

###############################################################################
# ÉTAPE 7: INSTRUCTIONS STREAMLIT CLOUD
###############################################################################

show_streamlit_instructions() {
    print_step "Instructions Streamlit Cloud..."
    
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     ÉTAPES MANUELLES STREAMLIT CLOUD DEPLOYMENT             ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n1. ${GREEN}Accéder à Streamlit Cloud${NC}"
    echo "   → https://share.streamlit.io/"
    
    echo -e "\n2. ${GREEN}Connectez-vous avec GitHub${NC}"
    echo "   → Autoriser l'accès au repository"
    
    echo -e "\n3. ${GREEN}Créer une nouvelle app${NC}"
    echo "   → Cliquer 'New app'"
    
    echo -e "\n4. ${GREEN}Configuration de l'app${NC}"
    echo "   Repository: $REPO_URL"
    echo "   Branch: $(git branch --show-current)"
    echo "   Main file path: $APP_FILE"
    echo "   Python version: $PYTHON_VERSION"
    
    echo -e "\n5. ${GREEN}Settings avancés${NC}"
    echo "   Requirements file: requirements-academic.txt"
    echo "   Packages file: streamlit_app/packages.txt"
    
    echo -e "\n6. ${GREEN}Secrets (optionnel)${NC}"
    echo "   → Ajouter API keys si nécessaire:"
    echo "   ANTHROPIC_API_KEY=sk-xxx"
    echo "   OPENAI_API_KEY=sk-xxx"
    
    echo -e "\n7. ${GREEN}Déployer${NC}"
    echo "   → Cliquer 'Deploy'"
    echo "   → Attendre 5-10 minutes"
    
    echo -e "\n8. ${GREEN}URL de l'application${NC}"
    echo "   → https://freemobilachat.streamlit.app"
    
    echo -e "\n${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}\n"
}

###############################################################################
# ÉTAPE 8: VÉRIFICATION POST-DÉPLOIEMENT
###############################################################################

post_deployment_check() {
    print_step "Vérification post-déploiement..."
    
    echo -e "\n${YELLOW}Checklist finale:${NC}"
    echo "  [ ] Code poussé sur GitHub"
    echo "  [ ] Tests passent (>90%)"
    echo "  [ ] requirements-academic.txt à jour"
    echo "  [ ] Configuration Streamlit Cloud complétée"
    echo "  [ ] Application accessible publiquement"
    echo "  [ ] Fonctionnalités principales testées"
    echo "  [ ] Monitoring activé"
    
    print_success "Script de déploiement terminé!"
}

###############################################################################
# FONCTION PRINCIPALE
###############################################################################

main() {
    print_header
    
    # Exécution séquentielle
    check_prerequisites
    validate_code
    
    # Demander si lancer les tests (optionnel)
    echo -e "\n${YELLOW}Lancer les tests automatisés? (y/n)${NC}"
    read -r run_tests_response
    if [[ "$run_tests_response" =~ ^[Yy]$ ]]; then
        run_tests
    else
        print_warning "Tests ignorés"
    fi
    
    prepare_deployment
    git_deploy
    generate_metadata
    show_streamlit_instructions
    post_deployment_check
    
    echo -e "\n${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ DÉPLOIEMENT PRÉPARÉ AVEC SUCCÈS!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}\n"
}

# Lancer le script
main
