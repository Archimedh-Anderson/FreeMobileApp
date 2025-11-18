"""
FreeMobilaChat - Système de Classification Automatisé
=====================================================

Système de classification automatique de réclamations clients développé dans le cadre
d'un mémoire de Master en Data Science et Intelligence Artificielle.

Architecture Multi-Modèles:
- Mistral AI (LLM) via Ollama
- BERT (Deep Learning) pour classification de sentiment
- Classificateur basé sur règles métier
- Google Gemini API (classification externe)

Fonctionnalités principales:
- Classification par lots avec traitement optimisé
- Support multi-providers (Mistral local, Gemini API externe)
- Gestion complète des erreurs et fallback automatique
- Interface utilisateur professionnelle avec Font Awesome
- Export des résultats en multiples formats

Version: 2.0.0 - Production Ready
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import logging
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json
import html
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

from utils.helpers import (
    fetch_remote_dataset,
    format_file_size,
    persist_remote_dataset,
)

# Configuration du logging (doit être avant l'utilisation de logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env
# Chercher le fichier .env à la racine du projet (avec override pour forcer le rechargement)
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
    logger.info(f"Fichier .env chargé depuis: {env_path}")
    # Vérifier que GEMINI_API_KEY est bien chargé
    if os.getenv("GEMINI_API_KEY"):
        logger.info("✓ GEMINI_API_KEY détectée dans .env")
else:
    # Essayer aussi à la racine du workspace
    root_env = Path(__file__).parent.parent.parent.parent / '.env'
    if root_env.exists():
        load_dotenv(root_env, override=True)
        logger.info(f"Fichier .env chargé depuis: {root_env}")
        # Vérifier que GEMINI_API_KEY est bien chargé
        if os.getenv("GEMINI_API_KEY"):
            logger.info("✓ GEMINI_API_KEY détectée dans .env")
    else:
        logger.warning("Fichier .env non trouvé, utilisation des variables d'environnement système")

# Configuration des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

ROOT_DIR = Path(__file__).resolve().parents[2]
REMOTE_UPLOAD_DIR = ROOT_DIR / "uploads" / "remote"
REMOTE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Imports du ProviderManager et du composant provider_selector
try:
    from services.provider_manager import provider_manager
    from components.provider_selector import (
        render_provider_selector,
        render_provider_configuration_modal
    )
    PROVIDER_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ProviderManager non disponible: {e}")
    provider_manager = None
    render_provider_selector = None
    render_provider_configuration_modal = None
    PROVIDER_MANAGER_AVAILABLE = False

# ==============================================================================
# LAZY LOADING - OPTIMISATION CRITIQUE
# ==============================================================================

@st.cache_resource(show_spinner=False)
def _load_classification_modules():
    """
    Charge les modules de classification avec cache et gestion gracieuse des erreurs.
    
    Gère l'absence de PyTorch et autres dépendances de manière conditionnelle.
    Retourne des informations détaillées sur les modules disponibles/indisponibles.
    """
    # Recharger le .env avant de charger les modules pour s'assurer que les clés API sont à jour
    try:
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
            logger.debug(f"Fichier .env rechargé depuis: {env_path}")
        else:
            root_env = Path(__file__).parent.parent.parent.parent / '.env'
            if root_env.exists():
                load_dotenv(root_env, override=True)
                logger.debug(f"Fichier .env rechargé depuis: {root_env}")
    except Exception as e:
        logger.debug(f"Erreur rechargement .env (non bloquant): {e}")
    
    modules_status = {
        'available': False,
        'modules': {},
        'errors': {},
        'warnings': []
    }
    
    # Module 1: TweetCleaner (toujours disponible)
    try:
        from services.tweet_cleaner import TweetCleaner
        modules_status['modules']['TweetCleaner'] = TweetCleaner
        logger.info("✓ TweetCleaner chargé")
    except Exception as e:
        modules_status['errors']['TweetCleaner'] = str(e)
        logger.error(f"✗ TweetCleaner: {e}")
    
    # Module 2: RuleClassifier (toujours disponible)
    try:
        from services.rule_classifier import EnhancedRuleClassifier
        modules_status['modules']['EnhancedRuleClassifier'] = EnhancedRuleClassifier
        logger.info("✓ RuleClassifier chargé")
    except Exception as e:
        modules_status['errors']['EnhancedRuleClassifier'] = str(e)
        logger.error(f"✗ RuleClassifier: {e}")
    
    # Module 3: BERTClassifier (nécessite PyTorch)
    try:
        from services.bert_classifier import BERTClassifier, TORCH_AVAILABLE
        if TORCH_AVAILABLE:
            modules_status['modules']['BERTClassifier'] = BERTClassifier
            modules_status['modules']['torch_available'] = True
            logger.info("✓ BERTClassifier disponible (PyTorch installé)")
        else:
            modules_status['errors']['BERTClassifier'] = "PyTorch non installé"
            modules_status['warnings'].append({
                'module': 'BERTClassifier',
                'message': 'PyTorch requis pour BERT',
                'solution': 'pip install torch transformers'
            })
            logger.warning("✗ BERTClassifier: PyTorch non disponible")
    except ImportError as e:
        modules_status['errors']['BERTClassifier'] = f"Import error: {str(e)}"
        modules_status['warnings'].append({
            'module': 'BERTClassifier',
            'message': 'PyTorch requis pour BERT',
            'solution': 'pip install torch transformers'
        })
        logger.warning(f"✗ BERTClassifier: {e}")
    except Exception as e:
        modules_status['errors']['BERTClassifier'] = str(e)
        logger.error(f"✗ BERTClassifier: {e}")
    
    # Module 4: MistralClassifier
    try:
        from services.mistral_classifier import (
            MistralClassifier,
            check_ollama_availability,
            list_available_models
        )
        modules_status['modules']['MistralClassifier'] = MistralClassifier
        modules_status['modules']['check_ollama_availability'] = check_ollama_availability
        modules_status['modules']['list_available_models'] = list_available_models
        logger.info("✓ MistralClassifier chargé")
    except ImportError as e:
        modules_status['errors']['MistralClassifier'] = f"Import error: {str(e)}"
        modules_status['warnings'].append({
            'module': 'MistralClassifier',
            'message': 'Module ollama requis',
            'solution': 'pip install ollama'
        })
        logger.warning(f"✗ MistralClassifier: {e}")
    except Exception as e:
        modules_status['errors']['MistralClassifier'] = str(e)
        logger.error(f"✗ MistralClassifier: {e}")
    
    # Module 5: GeminiClassifier
    try:
        from services.gemini_classifier import (
            GeminiClassifier,
            check_gemini_availability
        )
        modules_status['modules']['GeminiClassifier'] = GeminiClassifier
        modules_status['modules']['check_gemini_availability'] = check_gemini_availability
        logger.info("✓ GeminiClassifier chargé")
    except ImportError as e:
        modules_status['errors']['GeminiClassifier'] = f"Import error: {str(e)}"
        modules_status['warnings'].append({
            'module': 'GeminiClassifier',
            'message': 'Module google-generativeai requis',
            'solution': 'pip install google-generativeai'
        })
        logger.warning(f"✗ GeminiClassifier: {e}")
    except Exception as e:
        modules_status['errors']['GeminiClassifier'] = str(e)
        logger.error(f"✗ GeminiClassifier: {e}")
    
    # Module 6: MultiModelOrchestrator (peut fonctionner sans BERT)
    try:
        from services.multi_model_orchestrator import MultiModelOrchestrator
        modules_status['modules']['MultiModelOrchestrator'] = MultiModelOrchestrator
        logger.info("✓ MultiModelOrchestrator chargé")
    except Exception as e:
        modules_status['errors']['MultiModelOrchestrator'] = str(e)
        logger.error(f"✗ MultiModelOrchestrator: {e}")
    
    # Déterminer si le système est utilisable (au moins TweetCleaner et RuleClassifier)
    core_modules = ['TweetCleaner', 'EnhancedRuleClassifier']
    has_core = all(m in modules_status['modules'] for m in core_modules)
    
    modules_status['available'] = has_core
    
    # Format de retour compatible avec l'ancien code
    result = {
        'available': modules_status['available'],
        'modules_status': modules_status,
        'error': None
    }
    
    # Ajouter les modules chargés pour compatibilité
    for key, value in modules_status['modules'].items():
        if key != 'torch_available':
            result[key] = value
    
    # Si erreur principale, l'ajouter
    if not has_core and modules_status['errors']:
        main_error = list(modules_status['errors'].values())[0]
        result['error'] = main_error
    
    return result

@st.cache_resource(show_spinner=False)
def _load_role_system():
    """Charge le système de rôles avec cache"""
    try:
        from services.role_manager import initialize_role_system, get_current_role, check_permission
        from services.auth_service import AuthService
        
        return {
            'initialize_role_system': initialize_role_system,
            'get_current_role': get_current_role,
            'check_permission': check_permission,
            'AuthService': AuthService,
            'available': True
        }
    except Exception as e:
        logger.warning(f"Role system not available: {e}")
        return {'available': False}

# ==============================================================================
# CONFIGURATION PAGE
# ==============================================================================
st.set_page_config(
    page_title="Système de Classification | FreeMobilaChat",
    page_icon=":brain:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

def main():
    """
    Point d'entrée principal de l'application de classification.
    
    Cette fonction orchestre le chargement des composants, l'initialisation
    du système de rôles et le routage entre les différentes sections de l'interface.
    """
    
    _load_modern_css()
    
    # Initialisation du système de rôles avec chargement différé
    role_system = _load_role_system()
    if role_system['available']:
        try:
            role_manager, role_ui_manager = role_system['initialize_role_system']()
            current_role = role_system['get_current_role']()
            if not current_role:
                role_manager.set_current_role("manager")
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation du système de rôles: {e}")
    
    _render_header()
    _render_sidebar_complete()
    _render_workflow_indicator()
    
    # Gestion du workflow en trois étapes
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 'upload'
    
    # Routage vers la section appropriée selon l'étape du workflow
    if st.session_state.workflow_step == 'upload':
        _section_upload()
    elif st.session_state.workflow_step == 'classify':
        _section_classification()
    elif st.session_state.workflow_step == 'results':
        _section_results()

# ==============================================================================
# CSS MODERNE - FONT AWESOME UNIQUEMENT
# ==============================================================================

def _load_modern_css():
    """
    Charge les styles CSS personnalisés modernes pour l'interface utilisateur.
    
    Design premium avec glassmorphism, animations fluides et palette de couleurs moderne.
    """
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    :root {
        --primary: #667eea;
        --primary-dark: #764ba2;
        --secondary: #2E86DE;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --info: #3B82F6;
        --light: #F8FAFC;
        --dark: #0F172A;
        --gray-50: #F8FAFC;
        --gray-100: #F1F5F9;
        --gray-200: #E2E8F0;
        --gray-300: #CBD5E1;
        --gray-400: #94A3B8;
        --gray-500: #64748B;
        --gray-600: #475569;
        --gray-700: #334155;
        --gray-800: #1E293B;
        --gray-900: #0F172A;
        
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        
        --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-sizing: border-box;
    }
    
    .main {
        background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 50%, #F1F5F9 100%);
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 100vh;
    }
    
    @keyframes fadeIn {
        from { 
            opacity: 0;
            transform: translateY(10px);
        }
        to { 
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }
    
    /* Provider Cards Hover Effect */
    .provider-card {
        transition: all var(--transition-normal);
        cursor: pointer;
    }
    
    .provider-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl) !important;
    }
    
    /* Buttons modernes */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.875rem 2rem;
        font-weight: 600;
        font-size: 0.9375rem;
        box-shadow: var(--shadow-md);
        transition: all var(--transition-normal);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left var(--transition-slow);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Progress bars modernes */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 50%, var(--success) 100%);
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
        height: 8px;
        border-radius: var(--radius-lg);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* File uploader moderne */
    .stFileUploader > div {
        border: 2px dashed var(--gray-300);
        border-radius: var(--radius-lg);
        padding: 2rem;
        background: linear-gradient(135deg, var(--gray-50) 0%, white 100%);
        transition: all var(--transition-normal);
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary);
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, white 100%);
        box-shadow: var(--shadow-md);
    }
    
    /* Expander moderne */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--gray-50) 0%, white 100%);
        border-radius: var(--radius-md);
        padding: 0.75rem 1rem;
        font-weight: 600;
        color: var(--gray-800);
        transition: all var(--transition-fast);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, white 100%);
    }
    
    /* Spinner moderne */
    .stSpinner > div {
        border: 3px solid var(--gray-200);
        border-top-color: var(--primary);
        animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-weight: 800;
        font-size: 2rem;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sidebar moderne */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, white 0%, var(--gray-50) 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Scrollbar moderne */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--gray-100);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gray-400);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gray-500);
    }
    
    /* Animations pour les éléments qui apparaissent */
    [data-testid="stMarkdownContainer"] {
        animation: slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Amélioration des inputs */
    .stTextInput > div > div > input {
        border-radius: var(--radius-md);
        border: 1px solid var(--gray-300);
        transition: all var(--transition-fast);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Radio buttons modernes */
    .stRadio > div {
        gap: 0.75rem;
    }
    
    .stRadio > div > label {
        padding: 0.75rem 1rem;
        border-radius: var(--radius-md);
        border: 2px solid var(--gray-200);
        transition: all var(--transition-fast);
        cursor: pointer;
    }
    
    .stRadio > div > label:hover {
        border-color: var(--primary);
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* Selectbox moderne */
    .stSelectbox > div > div {
        border-radius: var(--radius-md);
        border: 1px solid var(--gray-300);
    }
    
    /* Checkbox moderne */
    .stCheckbox > label {
        cursor: pointer;
        transition: color var(--transition-fast);
    }
    
    .stCheckbox > label:hover {
        color: var(--primary);
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# HEADER
# ==============================================================================

def _render_header():
    """
    Affiche l'en-tête principal de l'application.
    
    Présente le titre, le statut du système et l'étape actuelle du workflow.
    """
    st.markdown("""
    <div style="text-align: right; margin-bottom: -10px;">
        <span style="background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
                     color: white; padding: 0.5rem 1.5rem; border-radius: 25px;
                     font-weight: 700; font-size: 0.85rem; letter-spacing: 1px;
                     box-shadow: 0 4px 12px rgba(46, 134, 222, 0.3);">
            VERSION 4.5 | FINAL EDITION
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### Système de Classification Automatisé")
        st.markdown("**NLP Avancé avec Mistral AI, BERT et Classification par Règles**")
    
    with col2:
        # Statut système
        modules = _load_classification_modules()
        status_icon = "<i class='fas fa-check-circle' style='color:#10AC84;'></i>" if modules.get('available') else "<i class='fas fa-times-circle' style='color:#EE5A6F;'></i>"
        status_text = "Opérationnel" if modules.get('available') else "Erreur"
        st.metric("Statut Système", "", help="État des modules de classification")
        st.markdown(f"<div style='text-align: center; margin-top: -20px; font-weight: 600;'>{status_icon} {status_text}</div>", unsafe_allow_html=True)
    
    with col3:
        # Étape workflow
        step = st.session_state.get('workflow_step', 'upload')
        step_names = {'upload': 'Upload', 'classify': 'Classification', 'results': 'Résultats'}
        step_icons = {
            'upload': "<i class='fas fa-upload'></i>",
            'classify': "<i class='fas fa-cogs'></i>",
            'results': "<i class='fas fa-chart-bar'></i>"
        }
        st.metric("Étape Actuelle", "", help="Progression workflow")
        step_display = step_names.get(step, 'N/A')
        step_icon = step_icons.get(step, "<i class='fas fa-list'></i>")
        st.markdown(f"<div style='text-align: center; margin-top: -20px; font-weight: 600;'>{step_icon} {step_display}</div>", unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# WORKFLOW INDICATOR
# ==============================================================================

def _render_workflow_indicator():
    """
    Affiche un indicateur visuel de progression dans le workflow.
    
    Montre les trois étapes principales (Upload, Classification, Résultats)
    et met en évidence l'étape courante ainsi que les étapes complétées.
    """
    current_step = st.session_state.get('workflow_step', 'upload')
    
    steps = {
        'upload': {'num': 1, 'name': 'Upload & Nettoyage', 'icon': 'fa-upload'},
        'classify': {'num': 2, 'name': 'Classification', 'icon': 'fa-cogs'},
        'results': {'num': 3, 'name': 'Résultats & Export', 'icon': 'fa-chart-bar'}
    }
    
    cols = st.columns(3)
    
    for idx, (step_key, step_info) in enumerate(steps.items()):
        with cols[idx]:
            is_current = (step_key == current_step)
            is_completed = (
                (step_key == 'upload' and current_step in ['classify', 'results']) or
                (step_key == 'classify' and current_step == 'results')
            )
            
            if is_current:
                st.info(f"**[{step_info['num']}] {step_info['name']}**\n\nEn cours...")
            elif is_completed:
                st.success(f"**[{step_info['num']}] {step_info['name']}**\n\nTerminé")
            else:
                st.caption(f"[{step_info['num']}] {step_info['name']}")
    
    st.markdown("---")

# ==============================================================================
# SIDEBAR COMPLÈTE - AVEC TOUS LES ONGLETS
# ==============================================================================

def _render_sidebar_complete():
    """
    Affiche la barre latérale complète avec tous les paramètres de configuration.
    
    Inclut la sélection du provider API (Mistral/Gemini), les modes de classification,
    les paramètres de nettoyage et la gestion des rôles utilisateurs.
    """
    with st.sidebar:
        # Mode de classification
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h3 style="font-size: 1.15rem; font-weight: 700; color: #1E293B; margin-bottom: 0.5rem; 
                        display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-sliders-h" style="color: #667eea;"></i>
                Mode de Classification
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        mode = st.radio(
            "Sélectionnez votre stratégie:",
            options=['fast', 'balanced', 'precise'],
            format_func=lambda x: {
                'fast': 'RAPIDE (20s)',
                'balanced': 'ÉQUILIBRÉ (2min)',
                'precise': 'PRÉCIS (10min)'
            }[x],
            index=1,
            key='classification_mode_radio'
        )
        
        # Info du mode
        mode_details = {
            'fast': {'models': 'BERT + Règles', 'precision': '75%', 'time': '20s', 'desc': 'Tests rapides'},
            'balanced': {'models': 'BERT + Règles + Mistral (20%)', 'precision': '88%', 'time': '2min', 'desc': 'Recommandé - Production'},
            'precise': {'models': 'BERT + Mistral (100%)', 'precision': '95%', 'time': '10min', 'desc': 'Analyses critiques'}
        }
        
        detail = mode_details[mode]
        
        st.info(f"""
**Mode {mode.upper()}**

Modèles: {detail['models']}  
Précision: {detail['precision']}  
Temps: {detail['time']}

{detail['desc']}
        """)
        
        st.markdown("---")
        
        # Modern Provider Selection with ProviderManager
        if PROVIDER_MANAGER_AVAILABLE and render_provider_selector:
            # Utiliser le nouveau composant provider_selector
            render_provider_selector()
            
            # Mapper le provider sélectionné au format attendu
            selected_provider_name = st.session_state.get('selected_provider')
            if selected_provider_name:
                if "Mistral" in selected_provider_name:
                    selected_provider = 'mistral'
                elif "Gemini" in selected_provider_name:
                    selected_provider = 'gemini'
                else:
                    selected_provider = 'auto'
            else:
                selected_provider = 'auto'
            
            st.session_state.config = {
                'mode': mode,
                'provider': selected_provider
            }
        else:
            # Fallback vers l'ancien système si ProviderManager n'est pas disponible
            st.markdown("""
            <div style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #1E293B; margin-bottom: 0.75rem; 
                            display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-microchip" style="color: #667eea;"></i>
                    Fournisseur de Traitement
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Check provider availability (ancien système)
            mistral_status = _check_mistral_availability()
            gemini_status = _check_gemini_availability()
            
            # Provider selection with modern toggle buttons
            col1, col2 = st.columns(2)
            
            with col1:
                mistral_available = mistral_status.get('available', False)
                
                if st.button(
                    "Local (Mistral)",
                    key="provider_mistral",
                    disabled=not mistral_available,
                    use_container_width=True
                ):
                    st.session_state.selected_provider = 'mistral'
                    st.rerun()
                
                # Status indicator
                if mistral_available:
                    st.success("Disponible", icon="✓")
                else:
                    st.warning("Non disponible", icon="⚠")
            
            with col2:
                gemini_available = gemini_status.get('available', False)
                
                if st.button(
                    "Cloud (Gemini)",
                    key="provider_gemini",
                    disabled=not gemini_available,
                    use_container_width=True
                ):
                    st.session_state.selected_provider = 'gemini'
                    st.rerun()
                
                # Status indicator
                if gemini_available:
                    st.success("Disponible", icon="✓")
                else:
                    st.info("Configuration requise", icon="ℹ")
            
            # Show selected provider
            selected_provider = st.session_state.get('selected_provider', 'auto')
            
            if selected_provider == 'mistral' and mistral_available:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
                            padding: 0.75rem 1rem; border-radius: 10px; margin-top: 0.5rem;
                            border-left: 4px solid #10B981;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-check-circle" style="color: #10B981;"></i>
                        <span style="font-weight: 600; color: #059669; font-size: 0.875rem;">
                            Traitement local avec Mistral AI
                        </span>
                    </div>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #047857;">
                        Vos données restent sur votre machine
                    </p>
                </div>
                """, unsafe_allow_html=True)
            elif selected_provider == 'gemini' and gemini_available:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
                            padding: 0.75rem 1rem; border-radius: 10px; margin-top: 0.5rem;
                            border-left: 4px solid #3B82F6;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-cloud" style="color: #3B82F6;"></i>
                        <span style="font-weight: 600; color: #2563EB; font-size: 0.875rem;">
                            Traitement cloud avec Google Gemini
                        </span>
                    </div>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #1D4ED8;">
                        Précision maximale avec l'IA de Google
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Auto mode or no provider available
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(100, 116, 139, 0.1) 0%, rgba(71, 85, 105, 0.05) 100%);
                            padding: 0.75rem 1rem; border-radius: 10px; margin-top: 0.5rem;
                            border-left: 4px solid #64748B;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-magic" style="color: #64748B;"></i>
                        <span style="font-weight: 600; color: #475569; font-size: 0.875rem;">
                            Sélection automatique
                        </span>
                    </div>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #334155;">
                        Le meilleur fournisseur sera choisi automatiquement
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.session_state.config = {
                'mode': mode,
                'provider': selected_provider
            }
        
        st.markdown("---")
        
        # Paramètres de nettoyage
        with st.expander("⚙️ Paramètres de Nettoyage", expanded=False):
            st.caption("Options de prétraitement des données")
            
            remove_duplicates = st.checkbox("Supprimer les doublons", value=True)
            remove_urls = st.checkbox("Supprimer les URLs", value=True)
            remove_mentions = st.checkbox("Supprimer les @mentions", value=True)
            remove_hashtags = st.checkbox("Supprimer les #hashtags", value=False)
            convert_emojis = st.checkbox("Convertir les emojis en texte", value=True)
            
            st.session_state.cleaning_config = {
                'remove_duplicates': remove_duplicates,
                'remove_urls': remove_urls,
                'remove_mentions': remove_mentions,
                'remove_hashtags': remove_hashtags,
                'convert_emojis': convert_emojis
            }
        
        # Informations système (en bas de sidebar)
        with st.expander("ℹ️ Informations Système", expanded=False):
            _render_system_info_tab()
        
        # Gestion des rôles
        with st.expander("👥 Gestion des Rôles", expanded=False):
            _render_role_management_tab()
        
        # Footer compact
        st.markdown("---")
        st.caption(f"💻 FreeMobilaChat v2.0 | {datetime.now().strftime('%Y-%m-%d')}")
        
        # Afficher la modal de configuration si nécessaire
        if PROVIDER_MANAGER_AVAILABLE and render_provider_configuration_modal:
            render_provider_configuration_modal()

def _check_mistral_availability() -> dict:
    """
    Vérifie si Mistral/Ollama est disponible avec détails.
    
    Returns:
        dict avec 'available', 'message', 'details', 'solution'
    """
    result = {
        'available': False,
        'message': 'Mistral non disponible',
        'details': '',
        'solution': '',
        'icon': 'fa-times-circle',
        'color': '#EE5A6F'
    }
    
    try:
        modules = _load_classification_modules()
        modules_dict = modules.get('modules', {})
        modules_status = modules.get('modules_status', {})
        
        # Vérifier si MistralClassifier est chargé
        if 'MistralClassifier' not in modules_dict:
            error_msg = modules_status.get('errors', {}).get('MistralClassifier', 'Erreur inconnue')
            result['message'] = 'Module MistralClassifier non chargé'
            result['details'] = str(error_msg)[:100]  # Limiter la longueur
            if 'ollama' in str(error_msg).lower() or 'import' in str(error_msg).lower():
                result['solution'] = 'Installation: pip install ollama'
            else:
                result['solution'] = 'Vérifiez que le module mistral_classifier.py existe et est valide'
            return result
        
        # Vérifier Ollama
        check_ollama = modules_dict.get('check_ollama_availability')
        if not check_ollama:
            result['message'] = 'Fonction check_ollama_availability non disponible'
            result['details'] = 'Le module MistralClassifier ne fournit pas la fonction de vérification'
            result['solution'] = 'Vérifiez l\'implémentation de mistral_classifier.py'
            return result
        
        # Tester la connexion Ollama
        try:
            is_available = check_ollama()
            if is_available:
                result['available'] = True
                result['message'] = 'Mistral disponible via Ollama'
                result['details'] = 'Service Ollama actif et opérationnel'
                result['icon'] = 'fa-check-circle'
                result['color'] = '#10AC84'
                result['solution'] = ''
            else:
                result['message'] = 'Ollama non disponible'
                result['details'] = 'Le service Ollama n\'est pas démarré ou inaccessible'
                result['solution'] = 'Démarrez Ollama avec: ollama serve\nOu installez: https://ollama.ai'
        except Exception as e:
            result['message'] = 'Erreur lors de la vérification Ollama'
            result['details'] = str(e)[:100]
            result['solution'] = 'Vérifiez que Ollama est installé: pip install ollama\nPuis démarrez: ollama serve'
            
    except Exception as e:
        logger.warning(f"Erreur vérification Mistral: {e}")
        result['details'] = str(e)
        result['solution'] = 'Vérifiez les logs pour plus de détails'
    
    return result

def _check_gemini_availability() -> dict:
    """
    Vérifie si l'API Gemini est disponible avec détails.
    
    Returns:
        dict avec 'available', 'message', 'details', 'solution'
    """
    result = {
        'available': False,
        'message': 'Gemini API non disponible',
        'details': '',
        'solution': '',
        'icon': 'fa-times-circle',
        'color': '#F79F1F'
    }
    
    # S'assurer que le .env est chargé avant la vérification
    try:
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
            logger.debug(f"Fichier .env rechargé depuis: {env_path}")
        else:
            root_env = Path(__file__).parent.parent.parent.parent / '.env'
            if root_env.exists():
                load_dotenv(root_env, override=True)
                logger.debug(f"Fichier .env rechargé depuis: {root_env}")
    except Exception as e:
        logger.debug(f"Erreur lors du chargement .env (non bloquant): {e}")
    
    try:
        modules = _load_classification_modules()
        modules_dict = modules.get('modules', {})
        
        # Vérifier si GeminiClassifier est chargé
        if 'GeminiClassifier' not in modules_dict:
            error_msg = modules.get('modules_status', {}).get('errors', {}).get('GeminiClassifier', 'Erreur inconnue')
            result['message'] = 'Module GeminiClassifier non chargé'
            result['details'] = str(error_msg)[:100]
            if 'google-generativeai' in str(error_msg).lower() or 'import' in str(error_msg).lower():
                result['solution'] = 'Installation: pip install google-generativeai'
            else:
                result['solution'] = 'Vérifiez que le module gemini_classifier.py existe et est valide'
            return result
        
        # Utiliser la fonction check_gemini_availability du module si disponible
        check_gemini = modules_dict.get('check_gemini_availability')
        if check_gemini:
            try:
                is_available = check_gemini()
                if is_available:
                    result['available'] = True
                    result['message'] = 'Gemini API disponible'
                    result['details'] = 'Clé API configurée et valide'
                    result['icon'] = 'fa-check-circle'
                    result['color'] = '#10AC84'
                    result['solution'] = ''
                else:
                    # Vérifier directement la clé API
                    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                    if not api_key:
                        result['message'] = 'Gemini API non configurée'
                        result['details'] = 'La clé API Gemini n\'est pas définie'
                        result['solution'] = 'Ajoutez GEMINI_API_KEY=votre_cle dans le fichier .env à la racine du projet\nObtenez votre clé sur: https://makersuite.google.com/app/apikey'
                    else:
                        result['message'] = 'Gemini API non accessible'
                        result['details'] = 'La clé API semble invalide ou le service est inaccessible'
                        result['solution'] = 'Vérifiez votre clé API sur: https://makersuite.google.com/app/apikey'
            except Exception as e:
                result['message'] = 'Erreur lors de la vérification Gemini'
                result['details'] = str(e)[:100]
                result['solution'] = 'Vérifiez la configuration de votre clé API'
        else:
            # Fallback: vérifier directement la clé API
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                result['available'] = True
                result['message'] = 'Gemini API configurée'
                result['details'] = 'Clé API trouvée (validation non disponible)'
                result['icon'] = 'fa-check-circle'
                result['color'] = '#10AC84'
            else:
                result['message'] = 'Gemini API non configurée'
                result['details'] = 'La clé API Gemini n\'est pas définie'
                result['solution'] = 'Ajoutez GEMINI_API_KEY=votre_cle dans le fichier .env à la racine du projet\nObtenez votre clé sur: https://makersuite.google.com/app/apikey'
    
    except Exception as e:
        logger.warning(f"Erreur vérification Gemini: {e}")
        # Fallback: vérifier directement la clé API
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            result['available'] = True
            result['message'] = 'Gemini API configurée'
            result['details'] = 'Clé API trouvée'
            result['icon'] = 'fa-check-circle'
            result['color'] = '#10AC84'
        else:
            result['message'] = 'Gemini API non configurée'
            result['details'] = str(e)[:100]
            result['solution'] = 'Ajoutez GEMINI_API_KEY=votre_cle dans le fichier .env\nObtenez votre clé sur: https://makersuite.google.com/app/apikey'
    
    try:
        from services.gemini_classifier import check_gemini_availability
        
        try:
            is_available = check_gemini_availability()
            if is_available:
                result['available'] = True
                result['message'] = 'Gemini API disponible'
                result['details'] = 'Clé API configurée et valide'
                result['icon'] = 'fa-check-circle'
                result['color'] = '#10AC84'
                result['solution'] = ''
            else:
                if api_key:
                    result['message'] = 'Gemini API non accessible'
                    result['details'] = 'La clé API est présente mais la connexion échoue'
                    result['solution'] = 'Vérifiez que la clé est valide et que google-generativeai est installé'
                else:
                    result['message'] = 'Gemini API non configurée'
                    result['details'] = 'La clé API Gemini n\'est pas définie'
                    result['solution'] = 'Ajoutez GEMINI_API_KEY=votre_cle dans le fichier .env à la racine du projet'
        except Exception as e:
            result['message'] = 'Erreur lors de la vérification Gemini'
            result['details'] = str(e)[:100]
            if 'google-generativeai' in str(e).lower() or 'import' in str(e).lower():
                result['solution'] = 'Installez: pip install google-generativeai'
            else:
                result['solution'] = 'Vérifiez la configuration de la clé API'
            
    except ImportError as e:
        result['message'] = 'Module GeminiClassifier non disponible'
        result['details'] = str(e)[:100]
        result['solution'] = 'Vérifiez que le module gemini_classifier.py existe et que google-generativeai est installé'
    except Exception as e:
        logger.warning(f"Erreur vérification Gemini: {e}")
        result['details'] = str(e)[:100]
        result['solution'] = 'Vérifiez les logs pour plus de détails'
    
    return result

def _render_system_status():
    """
    Affiche le statut système avec design épuré et professionnel.
    
    Présente le statut de manière concise sans surcharge visuelle.
    """
    modules = _load_classification_modules()
    modules_status = modules.get('modules_status', {})
    
    # Statut global simplifié
    overall_status = modules.get('available', False)
    status_color = '#10AC84' if overall_status else '#EE5A6F'
    status_icon = 'fa-check-circle' if overall_status else 'fa-exclamation-triangle'
    status_text = 'Opérationnel' if overall_status else 'Partiellement Disponible'
    
    st.markdown(f"""
    <div style="background: {'#F0FDF4' if overall_status else '#FEF2F2'};
                padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;
                border-left: 3px solid {status_color};">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas {status_icon}" style="color: {status_color}; font-size: 1rem;"></i>
            <span style="font-weight: 600; color: #1E3A5F; font-size: 0.9rem;">{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Liste compacte des modules
    available_modules = modules_status.get('modules', {})
    error_modules = modules_status.get('errors', {})
    
    # Afficher uniquement les modules avec erreurs dans un expander
    if error_modules:
        with st.expander(f"⚠️ Modules indisponibles ({len(error_modules)})", expanded=False):
            for module_key, error_msg in list(error_modules.items())[:3]:  # Limiter à 3 pour ne pas surcharger
                module_names = {
                    'BERTClassifier': 'BERT',
                    'MistralClassifier': 'Mistral',
                    'TweetCleaner': 'Tweet Cleaner',
                    'EnhancedRuleClassifier': 'Rule Classifier',
                    'MultiModelOrchestrator': 'Orchestrator'
                }
                name = module_names.get(module_key, module_key)
                st.caption(f"**{name}**: {error_msg[:60]}{'...' if len(error_msg) > 60 else ''}")
            
            if len(error_modules) > 3:
                st.caption(f"... et {len(error_modules) - 3} autre(s)")
            
            # Aide compacte
            if 'BERTClassifier' in error_modules:
                st.caption("💡 Solution: `pip install torch transformers`")

def _render_provider_cards():
    """
    Affiche les cards visuelles modernes avec design glassmorphism pour les providers Mistral et Gemini.
    
    Design premium avec animations, gradients et effets de profondeur.
    """
    mistral_status = _check_mistral_availability()
    gemini_status = _check_gemini_availability()
    
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.25rem; font-weight: 700; color: #1E293B; margin-bottom: 0.5rem; 
                    display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-plug" style="color: #667eea;"></i>
            Provider de Classification
        </h3>
        <p style="color: #64748B; font-size: 0.875rem; margin: 0;">Sélectionnez votre modèle d'IA préféré</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cards modernes avec glassmorphism
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        # Card Mistral - Design premium avec glassmorphism
        mistral_available = mistral_status.get('available', False)
        mistral_color = '#10B981' if mistral_available else '#EF4444'
        mistral_bg_gradient = 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)' if mistral_available else 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%)'
        mistral_icon = 'fa-check-circle' if mistral_available else 'fa-exclamation-circle'
        mistral_message = mistral_status.get('message', 'Non disponible')
        mistral_status_text = 'Disponible' if mistral_available else 'Indisponible'
        
        st.markdown(f"""
        <div class="provider-card" style="
            background: {mistral_bg_gradient};
            backdrop-filter: blur(10px);
            border: 1px solid {'rgba(16, 185, 129, 0.2)' if mistral_available else 'rgba(239, 68, 68, 0.2)'};
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px {'rgba(16, 185, 129, 0.15)' if mistral_available else 'rgba(239, 68, 68, 0.15)'};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: 0; right: 0; width: 100px; height: 100px; 
                        background: radial-gradient(circle, {'rgba(16, 185, 129, 0.1)' if mistral_available else 'rgba(239, 68, 68, 0.1)'} 0%, transparent 70%);
                        border-radius: 50%; transform: translate(30px, -30px);"></div>
            
            <div style="display: flex; align-items: flex-start; justify-content: space-between; 
                        margin-bottom: 1rem; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="
                        width: 48px; height: 48px;
                        background: {'linear-gradient(135deg, #10B981 0%, #059669 100%)' if mistral_available else 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'};
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px {'rgba(16, 185, 129, 0.3)' if mistral_available else 'rgba(239, 68, 68, 0.3)'};
                    ">
                        <i class="fas fa-robot" style="color: white; font-size: 1.25rem;"></i>
                    </div>
                    <div>
                        <div style="font-weight: 700; color: #0F172A; font-size: 1rem; margin-bottom: 0.25rem;">
                            Mistral AI
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">
                            <i class="fas fa-server" style="margin-right: 0.25rem;"></i>Local via Ollama
                        </div>
                    </div>
                </div>
                <div style="
                    padding: 0.375rem 0.75rem;
                    background: {'rgba(16, 185, 129, 0.15)' if mistral_available else 'rgba(239, 68, 68, 0.15)'};
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 0.375rem;
                ">
                    <i class="fas {mistral_icon}" style="color: {mistral_color}; font-size: 0.75rem;"></i>
                    <span style="font-size: 0.75rem; font-weight: 600; color: {mistral_color};">
                        {mistral_status_text}
                    </span>
                </div>
            </div>
            
            <div style="font-size: 0.8125rem; color: #475569; line-height: 1.5; position: relative; z-index: 1;
                        padding-top: 0.75rem; border-top: 1px solid {'rgba(16, 185, 129, 0.1)' if mistral_available else 'rgba(239, 68, 68, 0.1)'};">
                <i class="fas fa-info-circle" style="color: #64748B; margin-right: 0.375rem; font-size: 0.75rem;"></i>
                {mistral_message}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Card Gemini - Design premium avec glassmorphism
        gemini_available = gemini_status.get('available', False)
        gemini_color = '#10B981' if gemini_available else '#F59E0B'
        gemini_bg_gradient = 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)' if gemini_available else 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%)'
        gemini_icon = 'fa-check-circle' if gemini_available else 'fa-exclamation-circle'
        gemini_message = gemini_status.get('message', 'Non disponible')
        gemini_status_text = 'Disponible' if gemini_available else 'Configuration requise'
        
        st.markdown(f"""
        <div class="provider-card" style="
            background: {gemini_bg_gradient};
            backdrop-filter: blur(10px);
            border: 1px solid {'rgba(16, 185, 129, 0.2)' if gemini_available else 'rgba(245, 158, 11, 0.2)'};
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px {'rgba(16, 185, 129, 0.15)' if gemini_available else 'rgba(245, 158, 11, 0.15)'};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: 0; right: 0; width: 100px; height: 100px; 
                        background: radial-gradient(circle, {'rgba(16, 185, 129, 0.1)' if gemini_available else 'rgba(245, 158, 11, 0.1)'} 0%, transparent 70%);
                        border-radius: 50%; transform: translate(30px, -30px);"></div>
            
            <div style="display: flex; align-items: flex-start; justify-content: space-between; 
                        margin-bottom: 1rem; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="
                        width: 48px; height: 48px;
                        background: {'linear-gradient(135deg, #10B981 0%, #059669 100%)' if gemini_available else 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'};
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px {'rgba(16, 185, 129, 0.3)' if gemini_available else 'rgba(245, 158, 11, 0.3)'};
                    ">
                        <i class="fas fa-cloud" style="color: white; font-size: 1.25rem;"></i>
                    </div>
                    <div>
                        <div style="font-weight: 700; color: #0F172A; font-size: 1rem; margin-bottom: 0.25rem;">
                            Gemini API
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">
                            <i class="fas fa-globe" style="margin-right: 0.25rem;"></i>Google Cloud
                        </div>
                    </div>
                </div>
                <div style="
                    padding: 0.375rem 0.75rem;
                    background: {'rgba(16, 185, 129, 0.15)' if gemini_available else 'rgba(245, 158, 11, 0.15)'};
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 0.375rem;
                ">
                    <i class="fas {gemini_icon}" style="color: {gemini_color}; font-size: 0.75rem;"></i>
                    <span style="font-size: 0.75rem; font-weight: 600; color: {gemini_color};">
                        {gemini_status_text}
                    </span>
                </div>
            </div>
            
            <div style="font-size: 0.8125rem; color: #475569; line-height: 1.5; position: relative; z-index: 1;
                        padding-top: 0.75rem; border-top: 1px solid {'rgba(16, 185, 129, 0.1)' if gemini_available else 'rgba(245, 158, 11, 0.1)'};">
                <i class="fas fa-info-circle" style="color: #64748B; margin-right: 0.375rem; font-size: 0.75rem;"></i>
                {gemini_message}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Messages d'aide compacts uniquement si nécessaire
    if not gemini_available and gemini_status.get('solution'):
        with st.expander("💡 Configuration Gemini", expanded=False):
            st.caption(gemini_status.get('solution', ''))
    
    if not mistral_available and mistral_status.get('solution'):
        with st.expander("💡 Configuration Mistral", expanded=False):
            st.caption(mistral_status.get('solution', ''))
    
    # Sélection du provider
    provider_options = []
    provider_labels = {}
    
    if mistral_available:
        provider_options.append('mistral')
        provider_labels['mistral'] = 'Mistral (Local)'
    
    if gemini_available:
        provider_options.append('gemini')
        provider_labels['gemini'] = 'Gemini API'
    
    # Si aucun provider disponible, ajouter quand même les options
    if not provider_options:
        provider_options = ['mistral', 'gemini']
        provider_labels = {
            'mistral': 'Mistral (Local) - Non disponible',
            'gemini': 'Gemini API - Non disponible'
        }
    
    selected_provider = st.radio(
        "Choisissez le modèle:",
        options=provider_options,
        format_func=lambda x: provider_labels.get(x, x),
        index=0 if 'mistral' in provider_options else (1 if 'gemini' in provider_options else 0),
        key='api_provider_selector',
        help="Mistral: Local via Ollama | Gemini: API externe Google"
    )
    
    # Sauvegarder le provider sélectionné
    st.session_state.selected_api_provider = selected_provider
    
    return selected_provider

def _render_classifiers_tab():
    """
    Affiche l'onglet des classificateurs disponibles avec affichage structuré.
    
    Liste tous les modèles de classification disponibles (BERT, Règles, Mistral, etc.)
    et affiche leur statut ainsi que les modèles Ollama disponibles si applicable.
    Utilise la nouvelle structure de modules avec gestion gracieuse des erreurs.
    """
    modules = _load_classification_modules()
    modules_status = modules.get('modules_status', {})
    available_modules = modules_status.get('modules', {})
    error_modules = modules_status.get('errors', {})
    
    # Header avec statut
    if modules.get('available'):
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(16, 172, 132, 0.15) 0%, rgba(16, 172, 132, 0.08) 100%);
                    padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 1rem;
                    border-left: 4px solid #10AC84;">
            <strong style="color: #10AC84;"><i class="fas fa-check-circle"></i> Classificateurs Disponibles</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(238, 90, 111, 0.15) 0%, rgba(238, 90, 111, 0.08) 100%);
                    padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 1rem;
                    border-left: 4px solid #EE5A6F;">
            <strong style="color: #EE5A6F;"><i class="fas fa-exclamation-triangle"></i> Modules Partiellement Disponibles</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Liste des classificateurs avec statut détaillé
    classificateurs_info = {
        'TweetCleaner': ('Tweet Cleaner', 'Nettoyage et préprocessing', True),
        'EnhancedRuleClassifier': ('Rule Classifier', 'Classification par règles métier', True),
        'BERTClassifier': ('BERT Classifier', 'Deep Learning - Analyse de sentiment', False),
        'MistralClassifier': ('Mistral Classifier', 'LLM Mistral AI via Ollama', False),
        'MultiModelOrchestrator': ('Multi-Model Orchestrator', 'Orchestration intelligente', False)
    }
    
    # Afficher les classificateurs disponibles
    available_count = len([k for k in available_modules.keys() if k in classificateurs_info and k != 'torch_available'])
    if available_count > 0:
        with st.expander(f"Classificateurs Disponibles ({available_count})", expanded=True):
            for module_key, (name, desc, essential) in classificateurs_info.items():
                if module_key in available_modules:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(16, 172, 132, 0.1) 0%, rgba(16, 172, 132, 0.05) 100%);
                                padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;
                                border-left: 3px solid #10AC84;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-check-circle" style="color: #10AC84;"></i>
                            <div style="flex: 1;">
                                <div style="font-weight: 700; color: #1E3A5F; font-size: 0.95rem;">{name}</div>
                                <div style="font-size: 0.8rem; color: #666;">{desc}</div>
                            </div>
                            <span style="background: #10AC84; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600;">Actif</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Afficher les classificateurs indisponibles
    if error_modules:
        error_count = len([k for k in error_modules.keys() if k in classificateurs_info])
        if error_count > 0:
            with st.expander(f"Classificateurs Indisponibles ({error_count})", expanded=False):
                for module_key, error_msg in error_modules.items():
                    if module_key in classificateurs_info:
                        name, desc, essential = classificateurs_info[module_key]
                        error_color = '#EE5A6F' if essential else '#F79F1F'
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {error_color}15 0%, {error_color}08 100%);
                                    padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;
                                    border-left: 3px solid {error_color};">
                            <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                                <i class="fas fa-times-circle" style="color: {error_color}; margin-top: 0.2rem;"></i>
                                <div style="flex: 1;">
                                    <div style="font-weight: 700; color: #1E3A5F; font-size: 0.95rem;">{name}</div>
                                    <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">{desc}</div>
                                    <div style="font-size: 0.75rem; color: {error_color}; margin-top: 0.5rem; font-weight: 600;">
                                        <i class="fas fa-exclamation-circle"></i> {error_msg[:80]}{'...' if len(error_msg) > 80 else ''}
                                    </div>
                                </div>
                                <span style="background: {error_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600;">{'Critique' if essential else 'Optionnel'}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # ONGLET MODÈLES OLLAMA
    try:
        check_ollama = modules.get('check_ollama_availability')
        list_models = modules.get('list_available_models')
        
        if check_ollama:
            try:
                ollama_available = check_ollama()
                if ollama_available:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(16, 172, 132, 0.15) 0%, rgba(16, 172, 132, 0.08) 100%);
                                padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 1rem;
                                border-left: 4px solid #10AC84;">
                        <strong style="color: #10AC84;"><i class="fas fa-check-circle"></i> Ollama actif</strong>
                        <span style="color: #666;"> | Service LLM opérationnel</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if list_models:
                        models = list_models()
                        if models:
                            with st.expander(f"Modèles LLM Disponibles ({len(models)})", expanded=False):
                                for idx, model in enumerate(models):
                                    status = "Recommandé" if idx == 0 else "Disponible"
                                    st.markdown(f"""
                                    <div style="background: #F8F9FA; padding: 0.75rem; border-radius: 8px;
                                                margin-bottom: 0.5rem; border-left: 3px solid #2E86DE;">
                                        <div style="font-weight: 700; color: #1E3A5F;">{model}</div>
                                        <div style="font-size: 0.75rem; color: #10AC84; font-weight: 600;">
                                            {status}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(238, 90, 111, 0.15) 0%, rgba(238, 90, 111, 0.08) 100%);
                                padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 1rem;
                                border-left: 4px solid #EE5A6F;">
                        <strong style="color: #EE5A6F;"><i class="fas fa-exclamation-circle"></i> Ollama inactif</strong>
                        <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                            Service LLM non disponible
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <i class="fas fa-terminal"></i> <code style="font-size: 0.75rem;">ollama serve</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                logger.warning(f"Ollama check error: {e}")
                st.warning(f"Erreur lors de la vérification Ollama: {str(e)[:100]}")
    except Exception as e:
        logger.warning(f"Ollama check error: {e}")

def _render_system_info_tab():
    """
    Affiche les informations système de manière simple et moderne.
    """
    try:
        import sys
        import platform
        
        # Version Python
        st.markdown("**🐍 Environnement Python**")
        st.caption(f"Version: {sys.version.split()[0]}")
        st.caption(f"Plateforme: {platform.system()} {platform.release()}")
        
        # Modules de classification
        modules = _load_classification_modules()
        modules_dict = modules.get('modules', {})
        
        st.markdown("---")
        st.markdown("**🤖 Modules Chargés**")
        
        # Afficher statut simple des modules
        module_names = {
            'TweetCleaner': '✓ Nettoyage de texte',
            'EnhancedRuleClassifier': '✓ Classification par règles',
            'BERTClassifier': '✓ BERT (Deep Learning)',
            'MistralClassifier': '✓ Mistral AI (LLM)',
            'GeminiClassifier': '✓ Gemini API',
            'MultiModelOrchestrator': '✓ Orchestrateur'
        }
        
        available_count = 0
        for key, label in module_names.items():
            if key in modules_dict:
                st.caption(label)
                available_count += 1
            else:
                st.caption(label.replace('✓', '✗'))
        
        st.markdown("---")
        st.caption(f"📊 {available_count}/{len(module_names)} modules disponibles")
        
        # Info BERT si disponible
        if 'BERTClassifier' in modules_dict:
            try:
                BERTClassifier = modules_dict['BERTClassifier']
                bert = BERTClassifier(use_gpu=False)
                info = bert.get_model_info()
                
                st.markdown("---")
                st.markdown("**🧠 Configuration BERT**")
                st.caption(f"Device: {info['device'].upper()}")
                st.caption(f"Batch size: {info['batch_size']}")
            except:
                pass
            
    except Exception as e:
        st.error(f"Erreur: {str(e)[:80]}")

def _render_role_management_tab():
    """
    Affiche la gestion des rôles utilisateurs (version simplifiée).
    
    Permet de changer de rôle et affiche les permissions associées.
    """
    role_system = _load_role_system()
    
    if not role_system.get('available'):
        st.info("🔒 Système de rôles non disponible")
        return
    
    st.markdown("**👥 Rôle Utilisateur**")
    
    try:
        initialize_role_system = role_system['initialize_role_system']
        get_current_role = role_system['get_current_role']
        
        role_manager, role_ui_manager = initialize_role_system()
        roles = role_manager.get_all_roles()
        role_options = {role.display_name: role.role_id for role in roles}
        
        current_role = get_current_role()
        current_display = None
        if current_role:
            config = role_manager.get_role_config(current_role)
            current_display = config.display_name if config else None
        
        selected_display = st.selectbox(
            "Changer de rôle:",
            options=list(role_options.keys()),
            index=list(role_options.values()).index(current_role) if current_role and current_role in role_options.values() else 1,
            key='role_selector_sidebar'
        )
        
        selected_role = role_options[selected_display]
        role_manager.set_current_role(selected_role)
        
        # Afficher info rôle
        role_config = role_manager.get_role_config(selected_role)
        if role_config:
            st.markdown(f"""
            <div style="background: {role_config.color}22; padding: 1rem; border-radius: 8px;
                        border-left: 4px solid {role_config.color};">
                <div style="font-weight: 700; color: {role_config.color};">
                    <i class="fas {role_config.icon}"></i> {role_config.display_name}
                </div>
                <p style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                    {role_config.description}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Permissions clés
            st.markdown("**Permissions:**")
            key_perms = {
                'export_data': "Exporter Données",
                'view_all_stats': "Voir Toutes Stats",
                'access_advanced_analytics': "Analytics Avancées",
                'create_reports': "Créer Rapports"
            }
            
            for perm_key, perm_label in key_perms.items():
                has_perm = perm_key in role_config.permissions or "all" in role_config.permissions
                icon = "<i class='fas fa-check' style='color:#10AC84;'></i>" if has_perm else "<i class='fas fa-times' style='color:#95A5A6;'></i>"
                st.markdown(f"{icon} {perm_label}", unsafe_allow_html=True)
            
            st.caption(f"<i class='fas fa-th'></i> {len(role_config.features)} features disponibles", unsafe_allow_html=True)
            
    except Exception as e:
        st.warning(f"Erreur système de rôles: {e}")

# ==============================================================================
# SECTION UPLOAD - AVEC GESTION ERREUR 403 COMPLÈTE
# ==============================================================================

def _section_upload():
    """Section upload avec design moderne et gestion complète des erreurs"""
    # Header moderne avec gradient
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: 0; right: 0; width: 200px; height: 200px; 
                    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                    border-radius: 50%; transform: translate(50px, -50px);"></div>
        <div style="position: relative; z-index: 1;">
            <h2 style="color: white; font-size: 1.75rem; font-weight: 800; margin: 0 0 0.5rem 0; 
                       display: flex; align-items: center; gap: 0.75rem;">
                <i class="fas fa-cloud-upload-alt" style="font-size: 1.5rem;"></i>
                Étape 1 | Upload et Nettoyage des Données
            </h2>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.9375rem; margin: 0; font-weight: 400;">
                Importez vos données CSV pour commencer l'analyse automatique
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions modernes avec design card
    with st.expander("📋 Instructions d'Utilisation", expanded=False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
            <h4 style="color: #1E293B; font-weight: 700; margin-bottom: 1rem; 
                      display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-file-csv" style="color: #667eea;"></i>
                Préparation des données
            </h4>
            <div style="display: grid; gap: 0.75rem;">
                <div style="display: flex; align-items: start; gap: 0.75rem;">
                    <div style="width: 24px; height: 24px; background: #667eea; border-radius: 6px; 
                               display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span style="color: white; font-weight: 700; font-size: 0.75rem;">1</span>
                    </div>
                    <div>
                        <strong style="color: #1E293B;">Format requis:</strong> Fichier CSV
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 0.75rem;">
                    <div style="width: 24px; height: 24px; background: #667eea; border-radius: 6px; 
                               display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span style="color: white; font-weight: 700; font-size: 0.75rem;">2</span>
                    </div>
                    <div>
                        <strong style="color: #1E293B;">Contenu:</strong> Au moins une colonne de texte contenant les tweets à analyser
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 0.75rem;">
                    <div style="width: 24px; height: 24px; background: #667eea; border-radius: 6px; 
                               display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span style="color: white; font-weight: 700; font-size: 0.75rem;">3</span>
                    </div>
                    <div>
                        <strong style="color: #1E293B;">Taille maximale:</strong> 500 MB (limite augmentée pour éviter les erreurs d'accès)
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 0.75rem;">
                    <div style="width: 24px; height: 24px; background: #667eea; border-radius: 6px; 
                               display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span style="color: white; font-weight: 700; font-size: 0.75rem;">4</span>
                    </div>
                    <div>
                        <strong style="color: #1E293B;">Encodage:</strong> UTF-8 recommandé (détection automatique de 6 encodages supportés)
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
                    padding: 1.25rem; border-radius: 12px; border-left: 4px solid #F59E0B;
                    margin-top: 1rem;">
            <h4 style="color: #92400E; font-weight: 700; margin-bottom: 0.75rem; 
                      display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-exclamation-triangle" style="color: #F59E0B;"></i>
                En cas d'erreur 403 (Accès Interdit)
            </h4>
            <div style="color: #78350F; font-size: 0.875rem; line-height: 1.75;">
                <div style="margin-bottom: 0.5rem;">
                    <i class="fas fa-check-circle" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Vérifier que la taille du fichier est inférieure à 500 MB
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <i class="fas fa-sync-alt" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Rafraîchir la page (touche F5)
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <i class="fas fa-file-alt" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Vérifier que le fichier n'est pas en lecture seule
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <i class="fas fa-trash-alt" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Vider le cache du navigateur (Ctrl+Shift+Del)
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <i class="fas fa-shield-alt" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Désactiver temporairement l'anti-virus si nécessaire
                </div>
                <div>
                    <i class="fas fa-redo" style="color: #F59E0B; margin-right: 0.5rem;"></i>
                    Redémarrer l'application si le problème persiste
                </div>
            </div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(245, 158, 11, 0.2);">
                <code style="background: rgba(0,0,0,0.05); padding: 0.5rem 1rem; border-radius: 6px; 
                            display: inline-block; color: #78350F; font-size: 0.8125rem;">
                    streamlit run streamlit_app/app.py --server.port=8503
                </code>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Zone d'upload moderne
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="font-size: 1.25rem; font-weight: 700; color: #1E293B; margin-bottom: 0.5rem;
                   display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-folder-open" style="color: #667eea;"></i>
            Sélection du Fichier
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    _render_remote_importer()
    
    # FILE UPLOADER ROBUSTE
    try:
        uploaded_file = st.file_uploader(
            "Déposez votre fichier CSV ici",
            type=['csv'],
            help="Glissez-déposez ou cliquez pour parcourir. Max: 500 MB",
            label_visibility="collapsed"
        )
    except Exception as e:
        logger.error(f"File uploader error: {e}", exc_info=True)
        
        if "403" in str(e) or "Forbidden" in str(e):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                        padding: 1.5rem; border-radius: 12px; border-left: 4px solid #EF4444;
                        margin: 1rem 0; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);">
                <h4 style="color: #991B1B; font-weight: 700; margin-bottom: 1rem;
                           display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-ban" style="color: #EF4444; font-size: 1.25rem;"></i>
                    Erreur 403 - Accès Interdit
                </h4>
                <p style="color: #7F1D1D; margin-bottom: 1rem; line-height: 1.6;">
                    Cette erreur indique un problème de permissions. Solutions recommandées:
                </p>
                <div style="display: grid; gap: 0.5rem; color: #7F1D1D;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-weight" style="color: #EF4444;"></i>
                        Vérifier que la taille du fichier est inférieure à 500 MB
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-sync" style="color: #EF4444;"></i>
                        Rafraîchir la page (F5)
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-trash" style="color: #EF4444;"></i>
                        Vider le cache du navigateur
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-redo" style="color: #EF4444;"></i>
                        Redémarrer Streamlit
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                        padding: 1.5rem; border-radius: 12px; border-left: 4px solid #EF4444;
                        margin: 1rem 0; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);">
                <h4 style="color: #991B1B; font-weight: 700; margin-bottom: 0.5rem;
                           display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-exclamation-circle" style="color: #EF4444;"></i>
                    Erreur lors du chargement
                </h4>
                <p style="color: #7F1D1D; margin: 0;">{str(e)}</p>
            </div>
            """, unsafe_allow_html=True)
        return
    
    if uploaded_file:
        _handle_upload_robust(uploaded_file)


def _render_remote_importer():
    """Interface moderne pour importer un CSV via API/URL sécurisée."""
    status = st.session_state.get("remote_import_status")
    if status:
        color = "#d1fae5" if status.get("type") == "success" else "#fee2e2"
        border = "#10B981" if status.get("type") == "success" else "#EF4444"
        icon = "fa-cloud-arrow-down" if status.get("type") == "success" else "fa-triangle-exclamation"
        title = "Import distant réussi" if status.get("type") == "success" else "Import distant échoué"
        detail = ""
        if status.get("type") == "success":
            meta = status.get("details", {})
            detail = f"""
            <div style="color:#065F46;font-size:0.9rem;margin-top:0.5rem;">
                <strong>{meta.get('filename','')}</strong> • {meta.get('size','--')}
                <div style="font-size:0.8rem;color:#047857;">Stocké: {meta.get('saved_path','')}</div>
            </div>
            """
        st.markdown(f"""
        <div style="background:{color};border-left:4px solid {border};border-radius:12px;
                    padding:1rem 1.25rem;margin:0.5rem 0 1.25rem 0;">
            <div style="display:flex;align-items:center;gap:0.5rem;color:{border};font-weight:600;">
                <i class="fas {icon}"></i> {title}
            </div>
            <div style="color:#1F2937;font-size:0.9rem;margin-top:0.35rem;">
                {status.get('message','')}
            </div>
            {detail}
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("Importer via une API / un lien sécurisé", expanded=False):
        remote_url = st.text_input(
            "Lien API ou URL CSV",
            key="remote_import_url",
            placeholder="https://data.exemple.com/export.csv"
        )
        
        col_method, col_timeout = st.columns([1, 1])
        method = col_method.selectbox("Méthode", ["GET", "POST"], key="remote_import_method")
        timeout = col_timeout.slider("Timeout (secondes)", min_value=5, max_value=60, value=15, key="remote_import_timeout")
        
        col_token, col_header = st.columns(2)
        token = col_token.text_input("Token / API Key (optionnel)", type="password", key="remote_import_token")
        header_name = col_header.text_input("Nom du header (ex: Authorization)", value="Authorization", key="remote_import_header")
        
        payload = ""
        if method == "POST":
            payload = st.text_area(
                "Payload JSON (optionnel)",
                key="remote_import_payload",
                placeholder='{"filter": "last_30_days"}',
                height=110
            )
        
        max_size = st.slider(
            "Taille maximale autorisée (MB)",
            min_value=50,
            max_value=500,
            value=200,
            step=10,
            key="remote_import_size"
        )
        
        fetching = st.session_state.get("remote_import_loading", False)
        fetch_btn = st.button(
            "Importer via l'API",
            type="primary",
            use_container_width=True,
            disabled=fetching
        )
        
        if fetch_btn:
            if not remote_url:
                st.warning("Merci de renseigner un lien valide.")
                return
            
            st.session_state["remote_import_loading"] = True
            headers = {}
            if token:
                header_key = (header_name or "Authorization").strip() or "Authorization"
                header_value = token.strip()
                if header_key.lower() == "authorization" and header_value and not header_value.lower().startswith("bearer"):
                    header_value = f"Bearer {header_value}"
                headers[header_key] = header_value
            
            try:
                with st.spinner("Connexion à la source distante..."):
                    dataset = fetch_remote_dataset(
                        url=remote_url,
                        method=method,
                        headers=headers if headers else None,
                        payload=payload if payload else None,
                        timeout=timeout,
                        max_size_mb=max_size,
                    )
                
                st.session_state["remote_import_status"] = {
                    "type": "success",
                    "message": "Dataset importé depuis la source distante.",
                    "details": {
                        "filename": dataset.get("filename", "remote_dataset.csv"),
                        "size": format_file_size(dataset.get("size", 0)),
                    }
                }
                saved_path = persist_remote_dataset(dataset, base_dir=REMOTE_UPLOAD_DIR)
                st.session_state["remote_import_status"]["details"]["saved_path"] = str(saved_path)
                _handle_upload_robust(dataset["uploaded_file"])
            except Exception as exc:
                message = str(exc)
                st.session_state["remote_import_status"] = {
                    "type": "error",
                    "message": message,
                }
                st.error(f"Impossible de récupérer le fichier distant: {message}")
            finally:
                st.session_state["remote_import_loading"] = False

def _handle_upload_robust(uploaded_file):
    """
    Gère l'upload de fichier avec gestion robuste des erreurs.
    
    Implémente une détection automatique de l'encodage, une validation de la taille
    et une gestion complète des erreurs 403 (accès interdit).
    
    Args:
        uploaded_file: Objet fichier uploadé via Streamlit
    """
    try:
        # Vérification taille AVANT lecture (éviter 403)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > 500:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                        padding: 1.25rem; border-radius: 12px; border-left: 4px solid #EF4444;
                        margin: 1rem 0; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                    <i class="fas fa-exclamation-triangle" style="color: #EF4444; font-size: 1.25rem;"></i>
                    <h4 style="color: #991B1B; font-weight: 700; margin: 0;">Fichier trop volumineux</h4>
                </div>
                <p style="color: #7F1D1D; margin: 0 0 0.75rem 0;">
                    Taille actuelle: <strong>{file_size_mb:.1f} MB</strong> | Maximum autorisé: <strong>500 MB</strong>
                </p>
                <p style="color: #7F1D1D; margin: 0; font-size: 0.875rem;">
                    <i class="fas fa-lightbulb" style="color: #F59E0B; margin-right: 0.375rem;"></i>
                    Réduisez la taille du fichier ou filtrez les données avant l'upload
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Info fichier avec design moderne
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                    padding: 1.25rem; border-radius: 12px; border-left: 4px solid #10B981;
                    margin: 1rem 0; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
                    display: flex; align-items: center; gap: 1rem;">
            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                       border-radius: 12px; display: flex; align-items: center; justify-content: center;
                       box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); flex-shrink: 0;">
                <i class="fas fa-check-circle" style="color: white; font-size: 1.5rem;"></i>
            </div>
            <div style="flex: 1;">
                <div style="font-weight: 700; color: #065F46; font-size: 1rem; margin-bottom: 0.25rem;">
                    Fichier accepté avec succès
                </div>
                <div style="color: #047857; font-size: 0.875rem;">
                    <i class="fas fa-file-csv" style="margin-right: 0.375rem;"></i>
                    <strong>{uploaded_file.name}</strong> • {file_size_mb:.1f} MB
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Lecture robuste avec multi-encodage
        with st.spinner("Lecture du fichier en cours..."):
            df = None
            
            # Détection automatique d'encodage avec chardet (si disponible)
            detected_encoding = None
            try:
                import chardet  # type: ignore
                # Lire un échantillon pour détecter l'encodage
                sample = uploaded_file.read(10000)
                uploaded_file.seek(0)  # Reset file pointer
                result = chardet.detect(sample)
                if result and result['encoding'] and result['confidence'] > 0.7:
                    detected_encoding = result['encoding']
                    logger.info(f"Encodage détecté par chardet: {detected_encoding} (confiance: {result['confidence']:.2f})")
            except ImportError:
                logger.debug("chardet non disponible, utilisation de la détection manuelle")
            except Exception as e:
                logger.warning(f"Erreur détection chardet: {e}")
            
            # Liste des encodages à essayer (chardet en premier si détecté)
            encodings_to_try = []
            if detected_encoding:
                encodings_to_try.append(detected_encoding)
            encodings_to_try.extend(['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252'])
            
            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines='skip')
                    logger.info(f"Lecture réussie avec encodage: {encoding}")
                    st.caption(f"<i class='fas fa-check'></i> Encodage détecté: {encoding}", unsafe_allow_html=True)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Erreur avec {encoding}: {e}")
                    continue
            
            if df is None:
                st.error("Impossible de lire le fichier")
                st.info("Essayez de sauvegarder le CSV avec encodage UTF-8 dans Excel")
                return
        
        if df.empty:
            st.error("Fichier vide")
            return
        
        st.success(f"Chargé avec succès: {len(df):,} lignes • {len(df.columns)} colonnes")
        
        # Preview
        with st.expander("Aperçu des Données (10 premières lignes)", expanded=True):
            st.dataframe(df.head(10), use_container_width=True, height=300)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Lignes", f"{len(df):,}")
            with col2:
                st.metric("Colonnes", len(df.columns))
            with col3:
                memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
                st.metric("Mémoire", f"{memory_mb:.1f} MB")
        
        # Sélection colonne
        st.markdown("### Sélection de la Colonne de Texte")
        
        text_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not text_columns:
            st.error("Aucune colonne de texte trouvée")
            return
        
        selected_column = st.selectbox(
            "Choisissez la colonne contenant le texte:",
            options=text_columns,
            key='text_column_selector'
        )
        
        st.session_state.selected_text_column = selected_column
        st.session_state.df_original = df
        
        # Sample texte
        sample = str(df[selected_column].iloc[0])
        st.info(f"**Exemple de texte:**\n\n{sample[:300]}...")
        
        # Stats colonne
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Textes valides", f"{df[selected_column].notna().sum():,}")
        with col2:
            avg_length = df[selected_column].astype(str).str.len().mean()
            st.metric("Longueur moyenne", f"{avg_length:.0f} car.")
        with col3:
            duplicates = df[selected_column].duplicated().sum()
            st.metric("Doublons", f"{duplicates:,}")
        
        # Bouton nettoyage
        st.markdown("### Démarrer le Nettoyage")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("Nettoyer et Préparer les Données", type="primary", use_container_width=True):
                with st.spinner("Nettoyage des données en cours..."):
                    modules = _load_classification_modules()
                    
                    if modules.get('available'):
                        TweetCleaner = modules['TweetCleaner']
                        cleaner = TweetCleaner()
                        
                        progress_bar = st.progress(0)
                        progress_bar.progress(0.3)
                        
                        df_cleaned, stats = cleaner.process_dataframe(df.copy(), selected_column)
                        
                        progress_bar.progress(1.0)
                        
                        st.session_state.df_cleaned = df_cleaned
                        st.session_state.cleaning_stats = stats
                        st.session_state.workflow_step = 'classify'
                        
                        st.success("Nettoyage terminé!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Modules de nettoyage non disponibles")
        
        with col2:
            if st.button("Réinitialiser", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith('df_') or key == 'selected_text_column':
                        del st.session_state[key]
                st.rerun()
                
    except Exception as e:
        st.error("Erreur lors du traitement:")
        st.code(str(e))
        logger.error(f"Upload handling error: {e}", exc_info=True)
        
        # Détection erreur 403 spécifique
        error_str = str(e).lower()
        if "403" in error_str or "forbidden" in error_str or "permission" in error_str:
            st.error("""
            <h4><i class='fas fa-ban'></i> Erreur 403 - Accès Interdit Détecté</h4>
            
            <strong><i class='fas fa-tools'></i> Solutions recommandées par ordre de priorité:</strong>
            
            1. <strong><i class='fas fa-sync-alt'></i> Rafraîchir la page</strong>
               - Appuyez sur F5
               - Ou cliquez sur l'icône de rafraîchissement du navigateur
            
            2. <strong><i class='fas fa-weight'></i> Vérifier la taille du fichier</strong>
               - Limite: 500 MB maximum
               - Votre fichier: {:.1f} MB
            
            3. <strong><i class='fas fa-trash-alt'></i> Vider le cache du navigateur</strong>
               - Chrome: Ctrl+Shift+Del
               - Sélectionner "Images et fichiers en cache"
               - Cliquer "Effacer les données"
            
            4. <strong><i class='fas fa-lock-open'></i> Vérifier les permissions du fichier</strong>
               - Le fichier ne doit pas être en lecture seule
               - Propriétés → Décocher "Lecture seule"
            
            5. <strong><i class='fas fa-shield-alt'></i> Désactiver temporairement l'anti-virus</strong>
               - Certains anti-virus bloquent les uploads
               - Réessayer après désactivation
            
            6. <strong><i class='fas fa-redo'></i> Redémarrer l'application</strong>
               ```
               taskkill /F /IM python.exe
               streamlit run streamlit_app/app.py --server.port=8502
               ```
            
            <strong><i class='fas fa-book'></i> Documentation complète:</strong> Voir le guide d'utilisation
            """.format(uploaded_file.size / (1024 * 1024) if 'uploaded_file' in locals() else 0), icon="error")

# ==============================================================================
# SECTION CLASSIFICATION  
# ==============================================================================

def _section_classification():
    """Section classification avec support multi-modèles"""
    st.markdown("## Étape 2 | Classification Intelligente Multi-Modèle")
    
    if 'df_cleaned' not in st.session_state:
        st.warning("Aucune donnée nettoyée trouvée")
        if st.button("Retour à l'upload", type="secondary"):
            st.session_state.workflow_step = 'upload'
            st.rerun()
        return
    
    df_cleaned = st.session_state.df_cleaned
    text_col = st.session_state.selected_text_column
    stats = st.session_state.get('cleaning_stats', {})
    
    # Résumé nettoyage
    st.markdown("### Résumé du Nettoyage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tweets Originaux", f"{stats.get('total_original', 0):,}")
    with col2:
        st.metric("Tweets Nettoyés", f"{stats.get('total_cleaned', 0):,}",
                 delta=f"-{stats.get('duplicates_removed', 0):,} doublons", delta_color="inverse")
    with col3:
        reduction_pct = (1 - stats.get('total_cleaned', 1)/stats.get('total_original', 1)) * 100 if stats.get('total_original', 0) > 0 else 0
        st.metric("Réduction", f"{reduction_pct:.1f}%")
    with col4:
        st.metric("Prêt", f"{len(df_cleaned):,}", delta="Validé")
    
    # Aperçu
    with st.expander("Aperçu Données Nettoyées", expanded=False):
        key_cols = ['text_cleaned', 'date', 'time', 'content_type']
        available = [c for c in key_cols if c in df_cleaned.columns]
        
        if available:
            st.dataframe(df_cleaned[available].head(10), use_container_width=True, height=300)
        else:
            st.dataframe(df_cleaned.head(10), use_container_width=True, height=300)
    
    st.markdown("---")
    
    # Configuration
    config = st.session_state.config
    mode = config.get('mode', 'balanced')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Récupérer le provider sélectionné
        selected_provider = st.session_state.get('selected_api_provider', 'mistral')
        config_provider = config.get('provider', selected_provider)
        selected_provider = config_provider if config_provider else selected_provider
        
        provider_name = "Gemini API" if selected_provider == 'gemini' else "Mistral (Local)"
        
        st.info(f"""
**⚙️ Mode {mode.upper()} sélectionné**

📊 Dataset: **{len(df_cleaned):,}** tweets  
🤖 Provider: **{provider_name}**  
🤖 Modèles: {'BERT + Règles' if mode == 'fast' else 'BERT + Règles + ' + provider_name + ' (20%)' if mode == 'balanced' else 'BERT + ' + provider_name + ' (100%)'}  
⏱️ Temps estimé: {'~20s' if mode == 'fast' else '~2min' if mode == 'balanced' else '~10min'}  
📈 Précision: {'75%' if mode == 'fast' else '88%' if mode == 'balanced' else '95%'}
        """)
    
    with col2:
        use_optimized = st.checkbox("Ultra-Optimisé V2", value=True)
        st.caption("Batch processing (50)")
        st.caption("Cache multi-niveau")
    
    # Lancement
    st.markdown("### Lancer la Classification")
    
    if st.button("Démarrer la Classification Intelligente", type="primary", use_container_width=True):
        _perform_classification(df_cleaned, text_col, mode, use_optimized)

def _perform_classification(df, text_col, mode, use_optimized):
    """
    Exécute la classification des données avec support multi-providers.
    
    Supporte à la fois Gemini API (externe) et Mistral (local via Ollama).
    Implémente un système de fallback automatique en cas d'échec.
    
    Args:
        df: DataFrame contenant les données à classifier
        text_col: Nom de la colonne contenant le texte à classifier
        mode: Mode de classification ('fast', 'balanced', 'precise')
        use_optimized: Booléen indiquant si le classificateur optimisé doit être utilisé
    """
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # ✅ VÉRIFICATION CRITIQUE: S'assurer qu'au moins un provider est disponible
        if PROVIDER_MANAGER_AVAILABLE and provider_manager:
            if not provider_manager.is_any_provider_available():
                st.error("""
                <div style="
                    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                    padding: 2rem;
                    border-radius: 16px;
                    border-left: 4px solid #EF4444;
                    box-shadow: 0 8px 32px rgba(239, 68, 68, 0.25);
                    margin: 1rem 0;
                ">
                    <h3 style="color: #991B1B; font-weight: 700; margin-bottom: 1rem;
                               display: flex; align-items: center; gap: 0.75rem;">
                        <i class="fas fa-exclamation-triangle" style="color: #EF4444; font-size: 1.5rem;"></i>
                        ❌ Aucun Provider de Classification Disponible
                    </h3>
                    <p style="color: #7F1D1D; margin-bottom: 1.5rem; line-height: 1.6; font-size: 1rem;">
                        Aucun provider de classification n'est disponible ou configuré. 
                        Veuillez configurer au moins l'un des éléments suivants:
                    </p>
                    <div style="display: grid; gap: 1rem; margin-bottom: 1.5rem;">
                        <div style="
                            background: rgba(16, 185, 129, 0.1);
                            border-left: 3px solid #10B981;
                            padding: 1rem;
                            border-radius: 8px;
                        ">
                            <h4 style="color: #059669; font-weight: 700; margin-bottom: 0.5rem;
                                       display: flex; align-items: center; gap: 0.5rem;">
                                <i class="fas fa-server" style="color: #10B981;"></i>
                                1. Mistral Local (Ollama)
                            </h4>
                            <p style="color: #047857; margin: 0; font-size: 0.9375rem;">
                                <strong>Installation:</strong>
                            </p>
                            <ul style="color: #047857; margin: 0.5rem 0 0 1.5rem; font-size: 0.9375rem;">
                                <li>Téléchargez Ollama: <a href="https://ollama.ai" target="_blank" style="color: #059669;">https://ollama.ai</a></li>
                                <li>Installez le modèle: <code style="background: rgba(5, 150, 105, 0.2); padding: 0.2rem 0.4rem; border-radius: 4px;">ollama pull mistral</code></li>
                                <li>Lancez le serveur: <code style="background: rgba(5, 150, 105, 0.2); padding: 0.2rem 0.4rem; border-radius: 4px;">ollama serve</code></li>
                            </ul>
                            <p style="color: #047857; margin: 0.5rem 0 0 0; font-size: 0.9375rem;">
                                <strong>Ou utilisez Docker:</strong>
                            </p>
                            <code style="
                                background: rgba(5, 150, 105, 0.2);
                                padding: 0.75rem 1rem;
                                border-radius: 6px;
                                display: block;
                                margin-top: 0.5rem;
                                color: #065F46;
                                font-size: 0.875rem;
                            ">docker run -d --name ollama -p 11434:11434 ollama/ollama<br>docker exec ollama ollama pull mistral</code>
                        </div>
                        <div style="
                            background: rgba(59, 130, 246, 0.1);
                            border-left: 3px solid #3B82F6;
                            padding: 1rem;
                            border-radius: 8px;
                        ">
                            <h4 style="color: #2563EB; font-weight: 700; margin-bottom: 0.5rem;
                                       display: flex; align-items: center; gap: 0.5rem;">
                                <i class="fas fa-cloud" style="color: #3B82F6;"></i>
                                2. Gemini API (Google Cloud)
                            </h4>
                            <p style="color: #1D4ED8; margin: 0; font-size: 0.9375rem;">
                                <strong>Étapes:</strong>
                            </p>
                            <ul style="color: #1D4ED8; margin: 0.5rem 0 0 1.5rem; font-size: 0.9375rem;">
                                <li>Créez un compte Google Cloud: <a href="https://console.cloud.google.com" target="_blank" style="color: #2563EB;">https://console.cloud.google.com</a></li>
                                <li>Générez une clé API: <a href="https://ai.google.dev/api" target="_blank" style="color: #2563EB;">https://ai.google.dev/api</a></li>
                                <li>Ajoutez la clé dans le fichier <code style="background: rgba(37, 99, 235, 0.2); padding: 0.2rem 0.4rem; border-radius: 4px;">.env</code> à la racine du projet</li>
                                <li>Ou configurez-la via le sidebar → Configuration Provider</li>
                            </ul>
                        </div>
                    </div>
                    <p style="color: #7F1D1D; margin: 0; font-size: 0.9375rem;">
                        <strong>💡 Astuce:</strong> Utilisez le bouton "⚙️ Configuration Provider" dans le sidebar pour configurer facilement vos providers.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                status.empty()
                progress_bar.empty()
                st.stop()
        
        status.info("Chargement des modules...")
        progress_bar.progress(0.1)
        
        # Récupérer le provider sélectionné
        selected_provider = st.session_state.get('selected_api_provider', 'mistral')
        config = st.session_state.get('config', {})
        selected_provider = config.get('provider', selected_provider)
        
        # Mapper depuis le nom du provider si nécessaire (nouveau système)
        if PROVIDER_MANAGER_AVAILABLE and provider_manager:
            selected_provider_name = st.session_state.get('selected_provider')
            if selected_provider_name:
                if "Mistral" in selected_provider_name:
                    selected_provider = 'mistral'
                elif "Gemini" in selected_provider_name:
                    selected_provider = 'gemini'
                else:
                    selected_provider = config.get('provider', 'mistral')
            
            # Vérifier que le provider sélectionné est disponible
            if selected_provider == 'mistral':
                mistral_status = provider_manager.get_provider_status("Mistral Local (Ollama)")
                if not mistral_status or not mistral_status.available:
                    st.warning("⚠️ Mistral n'est pas disponible. Basculement vers Gemini ou fallback...")
                    # Essayer Gemini
                    gemini_status = provider_manager.get_provider_status("Gemini API (Google Cloud)")
                    if gemini_status and gemini_status.available:
                        selected_provider = 'gemini'
                        logger.info("Basculement vers Gemini car Mistral n'est pas disponible")
                    else:
                        st.error("❌ Aucun provider disponible. Impossible de classifier.")
                        status.empty()
                        progress_bar.empty()
                        st.stop()
            elif selected_provider == 'gemini':
                gemini_status = provider_manager.get_provider_status("Gemini API (Google Cloud)")
                if not gemini_status or not gemini_status.available:
                    st.warning("⚠️ Gemini n'est pas disponible. Basculement vers Mistral ou fallback...")
                    # Essayer Mistral
                    mistral_status = provider_manager.get_provider_status("Mistral Local (Ollama)")
                    if mistral_status and mistral_status.available:
                        selected_provider = 'mistral'
                        logger.info("Basculement vers Mistral car Gemini n'est pas disponible")
                    else:
                        st.error("❌ Aucun provider disponible. Impossible de classifier.")
                        status.empty()
                        progress_bar.empty()
                        st.stop()
        
        logger.info(f"Provider sélectionné: {selected_provider}")
        
        # Si Gemini est sélectionné, utiliser GeminiClassifier
        if selected_provider == 'gemini':
            try:
                from services.gemini_classifier import GeminiClassifier
                
                status.info("Initialisation Gemini API...")
                progress_bar.progress(0.15)
                
                # Initialiser GeminiClassifier avec paramètres optimaux
                gemini_classifier = GeminiClassifier(
                    batch_size=50,
                    temperature=0.3,  # Optimisé selon documentation
                    max_retries=3,
                    model_name='gemini-2.0-flash-exp'  # Modèle optimal
                )
                
                status.info("Classification avec Gemini API...")
                progress_bar.progress(0.2)
                
                # Classification avec Gemini
                df_classified = gemini_classifier.classify_dataframe(
                    df,
                    text_column=f'{text_col}_cleaned' if f'{text_col}_cleaned' in df.columns else text_col,
                    show_progress=False
                )
                
                # Normaliser et compléter les champs KPI requis
                df_classified = _normalize_kpi_fields(df_classified)
                
                progress_bar.progress(0.95)
                logger.info("Classification Gemini terminée avec succès")
                
                # Gemini a réussi, passer directement au calcul des métriques
                # Calcul rapport
                status.info("🤖 Calcul des métriques...")
                progress_bar.progress(0.95)
                
                report = _calculate_metrics(df_classified)
                
                # Sauvegarder
                st.session_state.df_classified = df_classified
                st.session_state.classification_report = report
                st.session_state.classification_mode = mode
                st.session_state.workflow_step = 'results'
                
                progress_bar.progress(1.0)
                status.success("✅ Classification terminée avec succès")
                
                time.sleep(0.5)
                st.rerun()
                
            except Exception as e:
                logger.error(f"Erreur classification Gemini: {e}")
                st.warning(f"Erreur avec Gemini API: {str(e)}. Basculement vers Mistral...")
                # Fallback vers Mistral
                selected_provider = 'mistral'
        
        # Si Mistral est sélectionné ou fallback depuis Gemini
        if selected_provider == 'mistral':
            modules = _load_classification_modules()
            
            if not modules.get('available'):
                st.error(f"Modules non disponibles: {modules.get('error')}")
                st.warning("Classification par règles de base utilisée...")
                df_classified = _classify_fallback(df, text_col)
            else:
                if use_optimized:
                    try:
                        from services.ultra_optimized_classifier import UltraOptimizedClassifier
                        
                        status.info("Classificateur ultra-optimisé...")
                        progress_bar.progress(0.2)
                        
                        classifier = UltraOptimizedClassifier(
                            batch_size=50,
                            max_workers=4,
                            use_cache=True
                        )
                        
                        def update_progress(msg, pct):
                            progress_bar.progress(0.2 + pct * 0.7)
                            status.info(msg)
                        
                        start = time.time()
                        results, benchmark = classifier.classify_tweets_batch(
                            df,
                            f'{text_col}_cleaned',
                            mode=mode,
                            progress_callback=update_progress
                        )
                        elapsed = time.time() - start
                        
                        df_classified = results
                        st.session_state.classification_benchmark = benchmark
                        
                    except Exception as e:
                        logger.warning(f"Ultra-optimized fallback: {e}")
                        MultiModelOrchestrator = modules['MultiModelOrchestrator']
                        orchestrator = MultiModelOrchestrator(mode=mode, provider=selected_provider)
                        
                        status.info("🤖 Classification multi-modèles en cours...")
                        df_classified = orchestrator.classify_intelligent(
                            df,
                            text_col,
                            progress_callback=lambda msg, pct: progress_bar.progress(0.2 + pct * 0.7)
                        )
                else:
                    MultiModelOrchestrator = modules['MultiModelOrchestrator']
                    orchestrator = MultiModelOrchestrator(mode=mode, provider=selected_provider)
                    
                    status.info("🤖 Classification multi-modèles en cours...")
                    df_classified = orchestrator.classify_intelligent(
                        df,
                        text_col,
                        progress_callback=lambda msg, pct: progress_bar.progress(0.2 + pct * 0.7)
                    )
        
        # Normaliser et compléter les champs KPI pour tous les providers
        df_classified = _normalize_kpi_fields(df_classified)
        
        # Calcul rapport
        status.info("📊 Calcul des métriques...")
        progress_bar.progress(0.95)
        
        report = _calculate_metrics(df_classified)
        
        # Sauvegarder
        st.session_state.df_classified = df_classified
        st.session_state.classification_report = report
        st.session_state.classification_mode = mode
        st.session_state.workflow_step = 'results'
        
        progress_bar.progress(1.0)
        status.success("✅ Classification terminée avec succès")
        
        time.sleep(0.5)
        st.rerun()
        
    except Exception as e:
        st.error(f"Erreur lors de la classification: {str(e)}")
        logger.error(f"Classification error: {e}", exc_info=True)
        
        with st.expander("Détails de l'erreur"):
            st.code(str(e))

def _classify_fallback(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """
    Classification de secours basée sur des règles métier.
    
    Utilisée lorsque les modèles LLM ne sont pas disponibles.
    Implémente une logique de classification basée sur des mots-clés et patterns.
    
    Args:
        df: DataFrame contenant les données
        text_col: Colonne contenant le texte à classifier
        
    Returns:
        DataFrame enrichi avec les classifications
    """
    df_copy = df.copy()
    
    def classify_row(text):
        t = str(text).lower()
        
        # CORRECTION: "réclamation" au lieu de "claim"
        is_claim = 'oui' if any(w in t for w in ['panne', '@free', 'problème', 'bug']) else 'non'
        
        if any(w in t for w in ['merci', 'super', 'bravo', 'excellent']): sentiment = 'positif'
        elif any(w in t for w in ['panne', 'nul', 'mauvais', 'honte']): sentiment = 'negatif'
        else: sentiment = 'neutre'
        
        urgence = 'haute' if any(w in t for w in ['panne', 'urgent', 'critique']) else 'moyenne' if is_claim == 'oui' else 'faible'
        
        topics = 'fibre' if 'fibre' in t else 'mobile' if 'mobile' in t else 'facture' if 'facture' in t else 'autre'
        
        incident = 'incident_reseau' if 'panne' in t else 'facturation' if 'facture' in t else 'autre'
        
        return pd.Series({
            'is_claim': is_claim,
            'sentiment': sentiment,
            'urgence': urgence,
            'topics': topics,
            'incident': incident,
            'confidence': 0.75
        })
    
    classifications = df_copy[text_col].apply(classify_row)
    return pd.concat([df_copy, classifications], axis=1)

def _normalize_kpi_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise et complète les champs KPI requis dans le DataFrame classifié.
    
    Cette fonction garantit que toutes les colonnes nécessaires pour le calcul
    des KPIs sont présentes et normalisées, avec des valeurs par défaut
    appropriées pour les champs manquants.
    
    Args:
        df: DataFrame avec les résultats de classification
        
    Returns:
        DataFrame avec les champs KPI normalisés et complétés
    """
    df = df.copy()
    
    # 1. Normaliser la colonne sentiment
    if 'sentiment' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['sentiment_label', 'sentiment_class', 'Sentiment']:
            if col in df.columns:
                df['sentiment'] = df[col]
                break
        else:
            df['sentiment'] = 'neutre'
    else:
        # Normaliser les valeurs de sentiment en LOWERCASE pour matching dynamique
        df['sentiment'] = df['sentiment'].astype(str).str.lower().str.strip()
        df['sentiment'] = df['sentiment'].replace({
            'positive': 'positif',
            'pos': 'positif',
            'good': 'positif',
            'happy': 'positif',
            'negative': 'negatif',
            'neg': 'negatif',
            'bad': 'negatif',
            'angry': 'negatif',
            'négatif': 'negatif',
            'neutral': 'neutre',
            'neu': 'neutre',
            'ok': 'neutre'
        })
    
    # 2. Normaliser la colonne is_claim
    if 'is_claim' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['is_claim', 'reclamation', 'réclamation', 'claim', 'is_reclamation']:
            if col in df.columns:
                df['is_claim'] = df[col]
                break
        else:
            df['is_claim'] = 'non'
    else:
        # Normaliser les valeurs en LOWERCASE pour matching dynamique
        df['is_claim'] = df['is_claim'].astype(str).str.lower().str.strip()
        df['is_claim'] = df['is_claim'].replace({
            'yes': 'oui',
            'true': 'oui',
            '1': 'oui',
            'oui': 'oui',
            'no': 'non',
            'false': 'non',
            '0': 'non',
            'non': 'non'
        })
    
    # 3. Normaliser la colonne urgence (PRESERVER LOWERCASE POUR MATCHING DYNAMIQUE)
    if 'urgence' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['priority', 'urgence', 'urgency', 'Priority', 'Urgence']:
            if col in df.columns:
                df['urgence'] = df[col]
                break
        else:
            df['urgence'] = 'faible'
    else:
        # Normaliser les valeurs d'urgence en LOWERCASE pour matching dynamique
        df['urgence'] = df['urgence'].astype(str).str.lower().str.strip()
        # Mapping intelligent qui préserve les valeurs des classificateurs (lowercase)
        df['urgence'] = df['urgence'].replace({
            'critical': 'haute',
            'critique': 'haute',
            'urgent': 'haute',
            'très haute': 'haute',
            'tres haute': 'haute',
            'high': 'haute',
            'elevee': 'haute',
            'élevée': 'haute',
            'élevée': 'haute',
            'medium': 'moyenne',
            'moyenne': 'moyenne',
            'moderee': 'moyenne',
            'modéré': 'moyenne',
            'modéré': 'moyenne',
            'low': 'faible',
            'faible': 'faible',
            'basse': 'faible',
            'normale': 'faible'
        })
        # Si valeur invalide, inférer depuis is_claim si disponible
        invalid_mask = ~df['urgence'].isin(['haute', 'moyenne', 'faible'])
        if invalid_mask.any() and 'is_claim' in df.columns:
            is_claim_col = df['is_claim'].astype(str).str.lower().str.strip()
            sentiment_col = df['sentiment'].astype(str).str.lower().str.strip() if 'sentiment' in df.columns else pd.Series()
            
            # Inférer urgence depuis is_claim et sentiment
            for idx in df[invalid_mask].index:
                if idx < len(is_claim_col):
                    is_claim_val = is_claim_col.iloc[idx] if idx < len(is_claim_col) else 'non'
                    sentiment_val = sentiment_col.iloc[idx] if 'sentiment' in df.columns and idx < len(sentiment_col) else 'neutre'
                    
                    if is_claim_val in ['oui', 'yes', '1', 'true'] and sentiment_val in ['negatif', 'negative', 'neg']:
                        df.loc[idx, 'urgence'] = 'haute'
                    elif is_claim_val in ['oui', 'yes', '1', 'true']:
                        df.loc[idx, 'urgence'] = 'moyenne'
                    else:
                        df.loc[idx, 'urgence'] = 'faible'
        else:
            # Valeur par défaut pour valeurs invalides
            df.loc[invalid_mask, 'urgence'] = 'faible'
    
    # 4. Normaliser la colonne theme/topic
    if 'theme' not in df.columns and 'topics' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['Thème principal', 'category', 'Category', 'theme', 'topics', 'topic']:
            if col in df.columns:
                df['theme'] = df[col]
                break
        else:
            df['theme'] = 'AUTRE'
    
    # 5. Normaliser la colonne incident (PRESERVER LOWERCASE POUR MATCHING DYNAMIQUE)
    if 'incident' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['Incident principal', 'incident', 'incident_type', 'type_incident']:
            if col in df.columns:
                df['incident'] = df[col]
                break
        else:
            df['incident'] = 'aucun'
    else:
        # Normaliser les valeurs d'incident en LOWERCASE pour matching dynamique
        df['incident'] = df['incident'].astype(str).str.lower().str.strip()
        # Préserver les valeurs des classificateurs (panne_connexion, bug_freebox, etc.)
        # Ne remplacer que les valeurs vraiment invalides ou vides
        valid_incidents = [
            'panne_connexion', 'bug_freebox', 'probleme_facturation', 'probleme_mobile',
            'retard_activation', 'debit_insuffisant', 'information', 'aucun', 'non_specifie',
            'autre', 'incident_reseau', 'facturation', 'reseau', 'mobile'
        ]
        invalid_mask = ~df['incident'].isin(valid_incidents) & (df['incident'] != '') & (df['incident'] != 'nan')
        
        # Si incident invalide, inférer depuis is_claim si disponible
        if invalid_mask.any() and 'is_claim' in df.columns:
            is_claim_col = df['is_claim'].astype(str).str.lower().str.strip()
            for idx in df[invalid_mask].index:
                if idx < len(is_claim_col):
                    is_claim_val = is_claim_col.iloc[idx] if idx < len(is_claim_col) else 'non'
                    if is_claim_val in ['oui', 'yes', '1', 'true']:
                        df.loc[idx, 'incident'] = 'non_specifie'
                    else:
                        df.loc[idx, 'incident'] = 'aucun'
        else:
            # Valeur par défaut pour valeurs invalides
            df.loc[invalid_mask, 'incident'] = 'non_specifie'
        
        # Remplacer les valeurs vides ou NaN
        df['incident'] = df['incident'].fillna('aucun')
        df.loc[df['incident'].isin(['', 'nan', 'None']), 'incident'] = 'aucun'
    
    # 6. Normaliser la colonne confidence
    if 'confidence' not in df.columns:
        # Chercher des colonnes alternatives
        for col in ['confidence', 'score_confiance', 'confiance', 'confidence_score']:
            if col in df.columns:
                df['confidence'] = pd.to_numeric(df[col], errors='coerce')
                break
        else:
            df['confidence'] = 0.5
    else:
        # S'assurer que confidence est numérique
        df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(0.5)
        # Limiter entre 0 et 1
        df['confidence'] = df['confidence'].clip(0.0, 1.0)
    
    # 7. Compléter les valeurs manquantes avec des valeurs par défaut appropriées (LOWERCASE)
    if 'sentiment' in df.columns:
        df['sentiment'] = df['sentiment'].fillna('neutre')
    if 'is_claim' in df.columns:
        df['is_claim'] = df['is_claim'].fillna('non')
    if 'urgence' in df.columns:
        df['urgence'] = df['urgence'].fillna('faible')
    if 'theme' in df.columns:
        df['theme'] = df['theme'].fillna('autre')
    if 'incident' in df.columns:
        df['incident'] = df['incident'].fillna('aucun')
    
    return df

def _calculate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule tous les indicateurs clés de performance (KPIs).
    
    Calcule les métriques de réclamations, sentiments, urgence, topics et incidents
    à partir du DataFrame classifié.
    
    Utilise un matching robuste case-insensitive pour gérer tous les formats de valeurs.
    
    Args:
        df: DataFrame contenant les données classifiées
        
    Returns:
        Dictionnaire contenant toutes les métriques calculées
    """
    # Fonction helper pour matching robuste case-insensitive
    def count_matches(df, column, values):
        """Compte les occurrences en ignorant la casse"""
        if column not in df.columns:
            return 0
        # Normaliser la colonne en lowercase pour comparaison
        normalized = df[column].astype(str).str.lower().str.strip()
        # Normaliser les valeurs de recherche en lowercase
        values_lower = [str(v).lower().strip() for v in values]
        return int(normalized.isin(values_lower).sum())
    
    total = len(df)
    
    # Réclamations: supporter 'oui', 'OUI', 'yes', 'YES', '1', 'true', 'TRUE'
    reclamations_count = count_matches(df, 'is_claim', ['oui', 'yes', '1', 'true'])
    
    # Sentiments négatifs: supporter 'negatif', 'NEGATIF', 'negative', 'NEGATIVE', 'neg', 'NEG'
    negative_count = count_matches(df, 'sentiment', ['negatif', 'negative', 'neg'])
    
    # Urgence haute: supporter 'haute', 'HAUTE', 'high', 'HIGH', 'elevee', 'ELEVEE', 'critique', 'CRITIQUE'
    urgence_haute_count = count_matches(df, 'urgence', ['haute', 'high', 'elevee', 'élevée', 'critique', 'critical'])
    
    return {
        'total_tweets': total,
        'reclamations_count': reclamations_count,
        'reclamations_percentage': (reclamations_count / total * 100) if total > 0 else 0,
        'negative_count': negative_count,
        'negative_percentage': (negative_count / total * 100) if total > 0 else 0,
        'urgence_haute_count': urgence_haute_count,
        'urgence_haute_percentage': (urgence_haute_count / total * 100) if total > 0 else 0,
        'confidence_avg': df['confidence'].mean() if 'confidence' in df.columns else 0,
        'sentiment_dist': df['sentiment'].value_counts() if 'sentiment' in df.columns else pd.Series(),
        'urgence_dist': df['urgence'].value_counts() if 'urgence' in df.columns else pd.Series(),
        'topics_dist': df['topics'].value_counts() if 'topics' in df.columns else pd.Series(),
        'incident_dist': df['incident'].value_counts() if 'incident' in df.columns else pd.Series()
    }

# ==============================================================================
# SECTION RÉSULTATS - COMPLÈTE AVEC TOUS LES ONGLETS ET BOUTON COMPLET
# ==============================================================================

def _section_results():
    """Section résultats avec visualisations complètes"""
    st.markdown("## Étape 3 | Résultats et Export")
    
    df = st.session_state.df_classified
    report = st.session_state.get('classification_report', {})
    mode = st.session_state.get('classification_mode', 'balanced')
    
    # Header avec bouton affichage complet
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"**Mode {mode.upper()}** | **{len(df):,}** tweets classifiés avec succès")
    
    with col2:
        # NOUVEAU: Bouton affichage complet des indicateurs
        if 'show_all_indicators' not in st.session_state:
            st.session_state.show_all_indicators = False
        
        if st.button("Tout Afficher" if not st.session_state.show_all_indicators else "Réduire", 
                    use_container_width=True):
            st.session_state.show_all_indicators = not st.session_state.show_all_indicators
            st.rerun()
    
    # KPIs principaux avec pourcentages
    st.markdown("### Indicateurs Clés de Performance")
    _render_quality_summary(df, report)
    
    # CORRECTION: "Réclamations" au lieu de "Claims"
    if st.session_state.show_all_indicators:
        # MODE COMPLET: Tous les indicateurs avec pourcentages
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Réclamations",
                f"{report.get('reclamations_count', 0):,}",
                delta=f"{report.get('reclamations_percentage', 0):.1f}% du total"
            )
        
        with col2:
            st.metric(
                "Sentiment Négatif",
                f"{report.get('negative_count', 0):,}",
                delta=f"{report.get('negative_percentage', 0):.1f}% du total"
            )
        
        with col3:
            st.metric(
                "Urgence Haute",
                f"{report.get('urgence_haute_count', 0):,}",
                delta=f"{report.get('urgence_haute_percentage', 0):.1f}% du total"
            )
        
        # Ligne 2: Indicateurs supplémentaires
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.metric(
                "Confiance Moyenne",
                f"{report.get('confidence_avg', 0):.3f}",
                delta="Score 0-1"
            )
        
        with col5:
            if not report.get('topics_dist', pd.Series()).empty:
                top_topic = report['topics_dist'].index[0]
                top_topic_count = report['topics_dist'].iloc[0]
                st.metric(
                    "Thème Principal",
                    top_topic,
                    delta=f"{top_topic_count:,} tweets"
                )
        
        with col6:
            if 'incident' in df.columns:
                # Compter les incidents avec case-insensitive matching
                incident_normalized = df['incident'].astype(str).str.lower().str.strip()
                
                # Filtrer les incidents réels (exclure "aucun", "non", etc.)
                non_incidents = ['aucun', 'non', 'none', 'n/a', 'na', '']
                incidents_reels = incident_normalized[~incident_normalized.isin(non_incidents)]
                
                if len(incidents_reels) > 0:
                    # Obtenir l'incident le plus fréquent (hors "aucun")
                    top_incident_raw = incidents_reels.value_counts().index[0]
                    top_incident_count = incidents_reels.value_counts().iloc[0]
                    
                    # Capitaliser pour affichage
                    top_incident_display = str(top_incident_raw).capitalize()
                    if len(top_incident_display) > 15:
                        top_incident_display = top_incident_display[:15] + "..."
                    
                    st.metric(
                        "Incident Principal",
                        top_incident_display,
                        delta=f"{top_incident_count:,} tweets"
                    )
                else:
                    # Aucun incident réel détecté
                    total_aucun = len(df) - len(incidents_reels)
                    st.metric(
                        "Incident Principal",
                        "aucun",
                        delta=f"{total_aucun:,} tweets"
                    )
            elif not report.get('incident_dist', pd.Series()).empty:
                # Fallback vers le rapport si disponible
                top_incident = report['incident_dist'].index[0]
                top_incident_count = report['incident_dist'].iloc[0]
                st.metric(
                    "Incident Principal",
                    top_incident,
                    delta=f"{top_incident_count:,} tweets"
                )
        
    else:
        # MODE COMPACT: KPIs essentiels
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Réclamations",
                f"{report.get('reclamations_count', 0):,}",
                delta=f"{report.get('reclamations_percentage', 0):.1f}%"
            )
        
        with col2:
            st.metric(
                "Sentiment Négatif",
                f"{report.get('negative_count', 0):,}",
                delta=f"{report.get('negative_percentage', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                "Confiance",
                f"{report.get('confidence_avg', 0):.0%}"
            )
    
    st.markdown("---")
    
    # DASHBOARD BUSINESS COMPLET (RESTAURÉ)
    _display_business_dashboard_mistral(df, report)
    
    st.markdown("---")
    
    # TOUS LES ONGLETS DE VISUALISATION (RESTAURÉS + NOUVEAU TAB ANALYTICS)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Visualisations Analytiques",
        "Sentiment",
        "Réclamations",
        "Urgence",
        "Topics",
        "Incidents",
        "Données"
    ])
    
    with tab1:
        _render_analytics_visualizations(df)
    
    with tab2:
        _render_sentiment_chart(df)
    
    with tab3:
        _render_reclamations_chart(df)  # CORRECTION: réclamations
    
    with tab4:
        _render_urgence_chart(df)
    
    with tab5:
        _render_topics_chart(df)
    
    with tab6:
        _render_incidents_chart(df)
    
    with tab7:
        st.markdown("### Tableau Détaillé")
        display_cols = ['text_cleaned', 'sentiment', 'is_claim', 'urgence', 'topics', 'incident', 'confidence']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            st.dataframe(df[available_cols], use_container_width=True, height=450)
            st.caption(f"<i class='fas fa-info-circle'></i> Affichage de {len(df)} lignes", unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True, height=450)
    
    st.markdown("---")
    
    # Export avec permissions
    _render_export_section(df, report)


def _render_quality_summary(df: pd.DataFrame, report: Dict[str, Any]):
    """Affiche un encart de qualité/couverture pour rassurer l'utilisateur."""
    total = len(df)
    claims = report.get('reclamations_count', 0)
    sentiments_covered = len(df['sentiment'].dropna()) if 'sentiment' in df.columns else 0
    
    # Calcul des incidents critiques - MATCHING DYNAMIQUE ROBUSTE
    incidents_detected = 0
    if 'incident' in df.columns:
        # Normaliser en lowercase pour matching
        incident_normalized = df['incident'].astype(str).str.lower().str.strip()
        # Liste des incidents critiques (lowercase pour matching)
        critical_incidents = [
            'panne_connexion', 'bug_freebox', 'probleme_facturation', 'probleme_mobile',
            'retard_activation', 'debit_insuffisant', 'incident_reseau', 'facturation'
        ]
        # Filtrer les incidents critiques (exclure 'aucun', 'non_specifie', 'autre', 'information')
        non_critical = ['aucun', 'non_specifie', 'autre', 'information', 'non_specifié', 'nan', 'none', '']
        incidents_mask = incident_normalized.isin(critical_incidents) & ~incident_normalized.isin(non_critical)
        incidents_detected = int(incidents_mask.sum())
    
    # Alternative : calculer depuis urgence haute + incident
    if incidents_detected == 0 and 'urgence' in df.columns and 'incident' in df.columns:
        # Compter les cas avec urgence haute ET incident réel
        urgence_normalized = df['urgence'].astype(str).str.lower().str.strip()
        incident_normalized = df['incident'].astype(str).str.lower().str.strip()
        high_urgency_mask = urgence_normalized.isin(['haute', 'high', 'elevee', 'élevée', 'critique', 'critical'])
        has_incident_mask = ~incident_normalized.isin(['aucun', 'non_specifie', 'autre', 'information', 'non_specifié', 'nan', 'none', ''])
        incidents_detected = int((high_urgency_mask & has_incident_mask).sum())
    
    st.markdown("""
    <div style="background: #f5f7ff; border: 1px solid #dbe0ff; border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.2rem;">
        <strong>🛡️  Contrôle Qualité KPI</strong><br/>
        Les compteurs ci-dessous permettent de vérifier rapidement la couverture obtenue.
    </div>
    """, unsafe_allow_html=True)
    
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        coverage = (claims / total * 100) if total else 0
        st.metric("Couverture Réclamations", f"{coverage:.1f}%", f"{claims:,} détectées")
    with col_q2:
        st.metric("Tweets avec Sentiment", f"{(sentiments_covered/total*100 if total else 0):.1f}%", f"{sentiments_covered:,}/{total:,}")
    with col_q3:
        st.metric("Incidents critiques", f"{incidents_detected:,}", "pannes/facturation")

def _render_analytics_visualizations(df):
    """
    Visualisations Analytiques - Graphiques interactifs pour analyser les tendances et patterns
    Matching exact style from screenshots provided by user
    """
    # En-tête moderne
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0 2rem 0; padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px;">
        <h2 style="font-size: 2rem; font-weight: 700; color: #1a202c; margin: 0;">
            📊 Visualisations Analytiques
        </h2>
        <p style="color: #4a5568; font-size: 1rem; margin-top: 0.5rem; font-weight: 500;">
            Graphiques interactifs pour analyser les tendances et patterns
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # SECTION 1: Distribution des Thèmes et Incidents (cote à cote)
    st.markdown("### Distribution des Thèmes")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("#### Top 10 Thème principal")
        
        if 'topics' in df.columns:
            # Calculer les top 10 themes avec percentages
            theme_counts = df['topics'].value_counts().head(10)
            total = len(df)
            percentages = (theme_counts / total * 100).round(2)
            
            # Couleurs gradient rouge (du plus foncé au plus clair)
            colors = [
                '#8B0000',  # Dark red (le plus fréquent)
                '#A52A2A',  # Brown red  
                '#CD5C5C',  # Indian red
                '#DC143C',  # Crimson
                '#F08080',  # Light coral
                '#FA8072',  # Salmon
                '#FFA07A',  # Light salmon
                '#FFB6C1',  # Light pink
                '#FFC0CB',  # Pink
                '#FFE4E1'   # Misty rose (le moins fréquent)
            ][:len(theme_counts)]
            
            # Créer labels avec count et pourcentage
            text_labels = [f"{count}<br>({pct}%)" for count, pct in zip(theme_counts.values, percentages)]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=theme_counts.index,
                    y=theme_counts.values,
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1.5)
                    ),
                    text=text_labels,
                    textposition='outside',
                    textfont=dict(size=11, color='#1a202c', family='Arial, sans-serif'),
                    hovertemplate="<b>%{x}</b><br>Nombre: %{y:,}<br>Pourcentage: %{customdata:.2f}%<extra></extra>",
                    customdata=percentages,
                    showlegend=False
                )
            ])
            
            # Ajouter colorbar à droite
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(
                    colorscale=[[0, '#8B0000'], [1, '#FFE4E1']],
                    showscale=True,
                    cmin=0,
                    cmax=theme_counts.max(),
                    colorbar=dict(
                        title="Nombre",
                        tickmode="linear",
                        thickness=15,
                        len=0.7,
                        x=1.12
                    )
                ),
                hoverinfo='skip',
                showlegend=False
            ))
            
            fig.update_layout(
                xaxis=dict(
                    title="Thème principal",
                    showgrid=False,
                    title_font=dict(size=12, color='#4a5568'),
                    tickangle=-45,
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    title="Nombre de Tweets",
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.08)',
                    title_font=dict(size=12, color='#4a5568'),
                    range=[0, theme_counts.max() * 1.15]
                ),
                height=500,
                template="plotly_white",
                margin=dict(l=80, r=150, t=60, b=120),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True, key='analytics_theme_dist')
        else:
            st.info("⚠️ Aucune donnée de thèmes disponible")
    
    with col2:
        st.markdown("#### Distribution des Incidents Principaux")
        
        if 'incident' in df.columns:
            # Calculer tous les incidents avec percentages
            incident_counts = df['incident'].value_counts()
            total = len(df)
            percentages = (incident_counts / total * 100).round(2)
            
            # Couleurs sémantiques par type d'incident
            def get_incident_color(incident_name):
                incident_lower = str(incident_name).lower()
                if 'aucun' in incident_lower or 'non' in incident_lower:
                    return '#28a745'  # Vert pour "aucun"
                elif 'information' in incident_lower:
                    return '#17a2b8'  # Bleu pour "information"
                else:
                    return '#dc3545'  # Rouge pour incidents réels
            
            colors = [get_incident_color(inc) for inc in incident_counts.index]
            
            # Labels avec count et pourcentage
            text_labels = [f"{count} ({pct}%)" for count, pct in zip(incident_counts.values, percentages)]
            
            fig = go.Figure(data=[
                go.Bar(
                    y=incident_counts.index,  # Horizontal bars
                    x=incident_counts.values,
                    orientation='h',
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1.5)
                    ),
                    text=text_labels,
                    textposition='outside',
                    textfont=dict(size=11, color='#1a202c', family='Arial, sans-serif'),
                    hovertemplate="<b>%{y}</b><br>Nombre: %{x:,}<br>Pourcentage: %{customdata:.2f}%<extra></extra>",
                    customdata=percentages,
                    showlegend=False
                )
            ])
            
            fig.update_layout(
                xaxis=dict(
                    title="Nombre de Tweets",
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.08)',
                    title_font=dict(size=12, color='#4a5568'),
                    range=[0, incident_counts.max() * 1.25]
                ),
                yaxis=dict(
                    title="Type d'Incident",
                    showgrid=False,
                    categoryorder='total ascending',
                    title_font=dict(size=12, color='#4a5568'),
                    tickfont=dict(size=10)
                ),
                height=500,
                template="plotly_white",
                margin=dict(l=180, r=120, t=60, b=60),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True, key='analytics_incident_dist')
        else:
            st.info("⚠️ Aucune donnée d'incidents disponible")
    
        # SECTION 2: Distribution des Sentiments (donut chart)
    # Cette section est désormais affichée dans l'onglet "Sentiment" pour éviter les doublons.
    st.caption("ℹ️ La répartition détaillée des sentiments est disponible dans l'onglet **Sentiment**.")

def _render_sentiment_chart(df):
    """Graphique de distribution des sentiments"""
    st.markdown("#### Distribution des Sentiments")
    
    if 'sentiment' in df.columns:
        sentiment_normalized = df['sentiment'].astype(str).str.lower().str.strip()
        neg_count = int(sentiment_normalized.isin(['negatif', 'négatif', 'negative', 'neg']).sum())
        neu_count = int(sentiment_normalized.isin(['neutre', 'neutral', 'neu']).sum())
        pos_count = int(sentiment_normalized.isin(['positif', 'positive', 'pos']).sum())
        total = len(df)
        
        labels = ['Négatif', 'Neutre', 'Positif']
        values = [neg_count, neu_count, pos_count]
        colors = ['#E74C3C', '#95A5A6', '#10AC84']
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color='white', width=3)),
                textinfo='label+percent',
                textfont=dict(size=14, color='white'),
                textposition='inside',
                hovertemplate="<b>%{label}</b><br>Tweets: %{value:,}<br>Pourcentage: %{percent}<extra></extra>"
            )
        ])
        
        fig.update_layout(
            height=450,
            template="plotly_white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(t=20, b=100, l=40, r=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats quick cards
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.metric("Tweets analysés", f"{total:,}")
        with stat_col2:
            if 'is_claim' in df.columns:
                claims_normalized = df['is_claim'].astype(str).str.lower().str.strip()
                claims_count = int(claims_normalized.isin(['oui', 'yes', '1', 'true']).sum())
                st.metric("Réclamations détectées", f"{claims_count:,}", f"{(claims_count/total*100 if total else 0):.1f}%")
            else:
                st.metric("Réclamations détectées", "0", "0%")
        with stat_col3:
            st.metric("Sentiments négatifs", f"{neg_count:,}", f"{(neg_count/total*100 if total else 0):.1f}%")
        with stat_col4:
            if 'urgence' in df.columns:
                urgence_normalized = df['urgence'].astype(str).str.lower().str.strip()
                urgent_count = int(urgence_normalized.isin(['haute', 'high', 'elevee', 'élevée', 'critique', 'critical']).sum())
                st.metric("Urgence haute", f"{urgent_count:,}", f"{(urgent_count/total*100 if total else 0):.1f}%")
            else:
                st.metric("Urgence haute", "0", "0%")
        
        st.caption(f"<i class='fas fa-info-circle'></i> Total: {len(df)} tweets analysés", unsafe_allow_html=True)

def _render_reclamations_chart(df):
    """Graphique de répartition des réclamations - Style exact du screenshot"""
    st.markdown("### Répartition Réclamations vs Non-Réclamations")
    
    if 'is_claim' in df.columns:
        # Calcul robuste avec case-insensitive matching
        claims_normalized = df['is_claim'].astype(str).str.lower().str.strip()
        
        # Compter réclamations et non-réclamations
        reclamations_count = int(claims_normalized.isin(['oui', 'yes', '1', 'true']).sum())
        non_reclamations_count = len(df) - reclamations_count
        total = len(df)
        
        # Calculer les pourcentages
        reclamations_pct = (reclamations_count / total * 100) if total > 0 else 0
        non_reclamations_pct = (non_reclamations_count / total * 100) if total > 0 else 0
        
        # Donut chart style coral/red du screenshot
        fig = go.Figure(data=[go.Pie(
            labels=['Réclamations', 'Non-Réclamations'],
            values=[reclamations_count, non_reclamations_count],
            hole=0.5,  # Donut
            marker=dict(
                colors=['#E74C3C', '#E74C3C'],  # Même couleur coral pour correspondre au screenshot
                line=dict(color='white', width=3)
            ),
            textinfo='label+percent',
            textfont=dict(size=14, family='Arial, sans-serif', color='white'),
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>Nombre: %{value:,}<br>Pourcentage: %{percent}<extra></extra>"
        )])
        
        fig.update_layout(
            height=450,
            template="plotly_white",
            showlegend=False,
            margin=dict(t=40, b=40, l=40, r=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True, key='reclamations_donut')
        
        # Statistiques en dessous du graphique
        st.markdown(f"""
        <div style="text-align: left; color: #6c757d; font-size: 0.95rem; margin-top: 1rem;">
            <i class="fas fa-info-circle"></i> {reclamations_count:,} réclamations ({reclamations_pct:.1f}%)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("⚠️ Aucune donnée de réclamations disponible")

def _render_urgence_chart(df):
    """Graphique de distribution des niveaux d'urgence - Style exact du screenshot"""
    st.markdown("### Niveaux d'Urgence")
    
    if 'urgence' in df.columns:
        # Normalisation case-insensitive pour compter correctement
        urgence_normalized = df['urgence'].astype(str).str.lower().str.strip()
        
        # Mapping vers catégories standard
        urgence_map = {
            'faible': 'FAIBLE',
            'low': 'FAIBLE',
            'basse': 'FAIBLE',
            'haute': 'HAUTE',
            'high': 'HAUTE',
            'elevee': 'HAUTE',
            'élevée': 'HAUTE',
            'critique': 'HAUTE',
            'critical': 'HAUTE',
            'moyenne': 'MOYENNE',
            'medium': 'MOYENNE',
            'modérée': 'MOYENNE',
            'moderee': 'MOYENNE'
        }
        
        # Appliquer le mapping
        urgence_categorized = urgence_normalized.map(lambda x: urgence_map.get(x, 'FAIBLE'))
        
        # Compter les catégories
        counts = urgence_categorized.value_counts()
        
        # S'assurer que toutes les catégories sont présentes (même avec 0)
        all_categories = ['FAIBLE', 'HAUTE', 'MOYENNE']
        for cat in all_categories:
            if cat not in counts:
                counts[cat] = 0
        
        # Réordonner pour correspondre au screenshot (FAIBLE, HAUTE, MOYENNE)
        counts = counts.reindex(all_categories)
        
        # Couleurs gradient rouge (du plus foncé au plus clair) selon valeurs
        max_val = counts.max()
        colors_map = {
            'FAIBLE': '#8B0000',   # Dark red (généralement le plus élevé)
            'HAUTE': '#FA8072',    # Salmon (moyen)
            'MOYENNE': '#FFB6C1'   # Light pink (le plus faible)
        }
        
        # Utiliser gradient proportionnel aux valeurs
        colors = [colors_map[cat] for cat in counts.index]
        
        # Créer le graphique à barres verticales
        fig = go.Figure(data=[
            go.Bar(
                x=counts.index,
                y=counts.values,
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1.5),
                    colorscale='Reds',
                    showscale=False
                ),
                text=counts.values,
                textposition='outside',
                textfont=dict(size=13, color='#1a202c', family='Arial, sans-serif'),
                hovertemplate="<b>%{x}</b><br>Nombre: %{y:,}<extra></extra>",
                showlegend=False
            )
        ])
        
        fig.update_layout(
            xaxis=dict(
                title="x",
                showgrid=False,
                title_font=dict(size=12, color='#4a5568'),
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                title="y",
                showgrid=True,
                gridcolor='rgba(0,0,0,0.08)',
                title_font=dict(size=12, color='#4a5568'),
                range=[0, max(counts.values) * 1.15] if max(counts.values) > 0 else [0, 10]
            ),
            height=450,
            template="plotly_white",
            margin=dict(l=60, r=40, t=40, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, key='urgence_chart')
        
        st.caption(f"<i class='fas fa-info-circle'></i> Distribution sur {len(df)} tweets", unsafe_allow_html=True)
    else:
        st.info("⚠️ Aucune donnée d'urgence disponible")

def _render_topics_chart(df):
    """Graphique de distribution des thèmes"""
    st.markdown("#### Distribution des Thèmes")
    
    if 'topics' in df.columns:
        counts = df['topics'].value_counts().head(10)
        
        fig = px.bar(
            y=counts.index,
            x=counts.values,
            orientation='h',
            title="",
            text=counts.values
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"<i class='fas fa-info-circle'></i> Top 10 thèmes sur {len(df['topics'].unique())} différents", unsafe_allow_html=True)

def _render_incidents_chart(df):
    """Graphique de distribution des types d'incidents"""
    st.markdown("#### Types d'Incidents")
    
    if 'incident' in df.columns:
        counts = df['incident'].value_counts()
        
        fig = px.pie(
            values=counts.values,
            names=counts.index,
            title=""
        )
        fig.update_traces(textinfo='label+percent', textfont_size=12)
        fig.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"<i class='fas fa-info-circle'></i> {len(df['incident'].unique())} types identifiés", unsafe_allow_html=True)

def _display_business_dashboard_mistral(df, report):
    """
    Affiche le tableau de bord business avec KPIs avancés.
    
    Présente des visualisations et statistiques détaillées pour l'analyse métier
    des réclamations et de la satisfaction client.
    
    Args:
        df: DataFrame contenant les données classifiées
        report: Dictionnaire contenant le rapport de classification
    """
    try:
        # Importer le module de KPIs avancés
        try:
            from services import enhanced_kpis_vizualizations as ekv
            from services.enhanced_kpis_vizualizations import (
                compute_business_kpis,
                render_business_kpis
            )
            kpis_available = True
        except ImportError:
            kpis_available = False
        
        if not kpis_available:
            logger.warning("Module enhanced_kpis_vizualizations non disponible")
            return
        
        st.markdown("---")
        st.markdown("## Tableau de Bord Business - KPIs Avancés")
        st.caption("Indicateurs clés de performance, statistiques détaillées et pourcentages complets")
        
        # Préparer données pour KPIs business
        df_business = df.copy()
        
        # Conversion sentiments
        sentiment_map = {
            'positif': 'positive',
            'neutre': 'neutral',
            'negatif': 'negative',
            'pos': 'positive',
            'neu': 'neutral',
            'neg': 'negative'
        }
        if 'sentiment' in df_business.columns:
            df_business['sentiment'] = df_business['sentiment'].map(
                lambda x: sentiment_map.get(str(x).lower(), str(x))
            )
        
        # Renommages pour compatibilité
        if 'urgence' in df_business.columns and 'priority' not in df_business.columns:
            df_business['priority'] = df_business['urgence']
        
        if 'incident' in df_business.columns and 'category' not in df_business.columns:
            df_business['category'] = df_business['incident']
        
        # Calculer KPIs avancés
        business_kpis = compute_business_kpis(df_business)
        
        # Afficher KPIs avec styling professionnel
        render_business_kpis(business_kpis)
        
        # Visualisations avancées
        ekv.render_enhanced_visualizations(df_business, business_kpis)
        
        # Afficher statistiques détaillées
        with st.expander("Statistiques Détaillées et Pourcentages", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Tweets",
                    f"{len(df):,}",
                    delta="100%"
                )
            
            with col2:
                if 'is_claim' in df.columns:
                    # Matching robuste case-insensitive pour is_claim
                    claims_normalized = df['is_claim'].astype(str).str.lower().str.strip()
                    claims = int(claims_normalized.isin(['oui', 'yes', '1', 'true']).sum())
                    claims_pct = (claims / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Réclamations",
                        f"{claims:,}",
                        delta=f"{claims_pct:.1f}%"
                    )
            
            with col3:
                if 'sentiment' in df.columns:
                    # Matching robuste case-insensitive pour sentiment négatif
                    sentiment_normalized = df['sentiment'].astype(str).str.lower().str.strip()
                    neg = int(sentiment_normalized.isin(['negatif', 'negative', 'neg']).sum())
                    neg_pct = (neg / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Sentiments Négatifs",
                        f"{neg:,}",
                        delta=f"{neg_pct:.1f}%"
                    )
            
            with col4:
                if 'urgence' in df.columns:
                    # Matching robuste case-insensitive pour urgence haute
                    urgence_normalized = df['urgence'].astype(str).str.lower().str.strip()
                    urgent = int(urgence_normalized.isin(['haute', 'high', 'elevee', 'élevée', 'critique', 'critical']).sum())
                    urgent_pct = (urgent / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Urgence Haute",
                        f"{urgent:,}",
                        delta=f"{urgent_pct:.1f}%"
                    )
        
    except Exception as e:
        logger.error(f"Erreur dashboard business: {e}")
        st.warning("Certains KPIs avancés ne sont pas disponibles")

def _render_export_section(df, report):
    """Section export avec vérification des permissions"""
    st.markdown("### Export des Résultats")
    
    # Vérifier permissions
    role_system = _load_role_system()
    can_export = True
    
    if role_system.get('available'):
        try:
            check_permission = role_system['check_permission']
            can_export = check_permission("export_data")
        except:
            can_export = True
    
    if not can_export:
        st.warning("Permission d'export requise")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Export CSV",
            csv,
            f"classification_{timestamp}.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        json_data = json.dumps(report, indent=2, ensure_ascii=False, default=str)
        st.download_button(
            "Export JSON",
            json_data,
            f"metrics_{timestamp}.json",
            "application/json",
            use_container_width=True
        )
    
    with col3:
        # Export Excel
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Classification', index=False)
        
        st.download_button(
            "Export Excel",
            buffer.getvalue(),
            f"classification_{timestamp}.xlsx",
            "application/vnd.ms-excel",
            use_container_width=True
        )
    
    with col4:
        if st.button("Nouvelle Classification", use_container_width=True):
            for key in ['df_cleaned', 'df_classified', 'classification_report', 'cleaning_stats']:
                st.session_state.pop(key, None)
            st.session_state.workflow_step = 'upload'
            st.rerun()

# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

if __name__ == '__main__':
    main()
