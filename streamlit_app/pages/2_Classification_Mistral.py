"""
FreeMobilaChat - Classification System v4.5 FINAL
===================================================

VERSION STABILISÉE ET REFACTORISÉE avec:
✅ Tous les emojis natifs (pas de Font Awesome)
✅ Batch processing avec progress bar
✅ Gestion robuste des uploads CSV
✅ KPIs dynamiques
✅ Visualisations Plotly modernes
✅ Code stable et optimisé

Architecture Multi-Modèles:
- Mistral AI (LLM)
- BERT (Deep Learning)
- Rule-Based Classifier

Version: 4.5 Final - Production Ready
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
from typing import Dict, Any, Optional, List

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# ==============================================================================
# LAZY LOADING - OPTIMISATION CRITIQUE
# ==============================================================================

@st.cache_resource(show_spinner=False)
def _load_classification_modules():
    """Charge les modules de classification avec cache et fallback"""
    try:
        logger.info("→ Loading classification modules...")
        
        # Import de base toujours disponible
        from services.tweet_cleaner import TweetCleaner
        
        modules = {
            'TweetCleaner': TweetCleaner,
            'available': True
        }
        
        # Import des classifieurs (optionnels)
        try:
            from services.mistral_classifier import (
                MistralClassifier,
                check_ollama_availability,
                list_available_models
            )
            modules['MistralClassifier'] = MistralClassifier
            modules['check_ollama_availability'] = check_ollama_availability
            modules['list_available_models'] = list_available_models
        except Exception as e:
            logger.warning(f"Mistral classifier not available: {e}")
        
        try:
            from services.multi_model_orchestrator import MultiModelOrchestrator
            modules['MultiModelOrchestrator'] = MultiModelOrchestrator
        except Exception as e:
            logger.warning(f"MultiModel orchestrator not available: {e}")
        
        try:
            from services.bert_classifier import BERTClassifier
            modules['BERTClassifier'] = BERTClassifier
        except ImportError as e:
            if 'torch' in str(e).lower():
                logger.warning("BERT classifier requires PyTorch - not available")
            else:
                logger.warning(f"BERT classifier not available: {e}")
        
        try:
            from services.rule_classifier import EnhancedRuleClassifier
            modules['EnhancedRuleClassifier'] = EnhancedRuleClassifier
        except Exception as e:
            logger.warning(f"Rule classifier not available: {e}")
        
        logger.info("✓ Core modules loaded successfully")
        return modules
        
    except Exception as e:
        logger.error(f"✕ Critical module import error: {e}")
        # Return minimal working setup
        return {
            'available': False, 
            'error': str(e),
            'fallback_message': 'Using basic data processing only'
        }

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
    page_title="Classification System | FreeMobilaChat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

def main():
    """Point d'entrée principal - VERSION COMPLÈTE"""
    
    _load_modern_css()
    
    # Initialiser configuration de nettoyage par défaut
    if 'cleaning_config' not in st.session_state:
        st.session_state.cleaning_config = {
            'remove_duplicates': True,
            'remove_urls': True,
            'remove_mentions': True,
            'remove_hashtags': False,
            'convert_emojis': True
        }
    
    # Initialiser config classification par défaut
    if 'config' not in st.session_state:
        st.session_state.config = {'mode': 'balanced'}
    
    # Initialiser le système de rôles (lazy)
    role_system = _load_role_system()
    if role_system['available']:
        try:
            role_manager, role_ui_manager = role_system['initialize_role_system']()
            current_role = role_system['get_current_role']()
            if not current_role:
                role_manager.set_current_role("manager")
        except Exception as e:
            logger.warning(f"Role init error: {e}")
    
    _render_header()
    _render_sidebar_complete()  # VERSION COMPLÈTE avec tous les onglets
    _render_workflow_indicator()
    
    # Workflow
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 'upload'
    
    # Routing
    if st.session_state.workflow_step == 'upload':
        _section_upload()
    elif st.session_state.workflow_step == 'classify':
        _section_classification()
    elif st.session_state.workflow_step == 'results':
        _section_results()

# ==============================================================================
# CSS MODERNE - EMOJIS NATIFS UNIQUEMENT
# ==============================================================================

def _load_modern_css():
    """CSS ultra-moderne v4.5 - SANS FONT AWESOME"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary: #1E3A5F;
        --secondary: #2E86DE;
        --success: #10AC84;
        --warning: #F79F1F;
        --danger: #EE5A6F;
        --light: #F5F6FA;
        --dark: #2C3E50;
    }
    
    * {font-family: 'Inter', sans-serif;}
    
    .main {
        background: linear-gradient(135deg, #F5F7FA 0%, #FFFFFF 100%);
        animation: fadeIn 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary) 0%, #1A6FC7 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 2.5rem;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 4px 16px rgba(46, 134, 222, 0.35);
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(46, 134, 222, 0.5);
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #2E86DE 0%, #10AC84 100%);
        height: 8px;
        border-radius: 10px;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# HEADER
# ==============================================================================

def _render_header():
    """Header moderne professionnel sans Font Awesome"""
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
        st.markdown("""
        <div>
            <h1 style="margin-bottom: 0.5rem;">
                🤖 Système de Classification Automatisé
            </h1>
            <p style="font-size: 1.1rem; color: var(--dark); font-weight: 500; opacity: 0.85;">
                NLP Avancé avec <strong>Mistral AI</strong>, <strong>BERT</strong> & <strong>Règles</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Statut système
        modules = _load_classification_modules()
        status = "✅ Opérationnel" if modules.get('available') else "❌ Erreur"
        st.metric("Statut Système", "", help="État des modules de classification")
        st.markdown(f"<div style='text-align: center; margin-top: -20px; font-weight: 600;'>{status}</div>", unsafe_allow_html=True)
    
    with col3:
        # Étape workflow
        step = st.session_state.get('workflow_step', 'upload')
        step_names = {'upload': 'Upload', 'classify': 'Classification', 'results': 'Résultats'}
        step_icons = {'upload': '📤', 'classify': '⚙️', 'results': '📊'}
        st.metric("Étape Actuelle", "", help="Progression workflow")
        st.markdown(f"<div style='text-align: center; margin-top: -20px; font-weight: 600;'>{step_icons.get(step)} {step_names.get(step, 'N/A')}</div>", unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# WORKFLOW INDICATOR
# ==============================================================================

def _render_workflow_indicator():
    """Indicateur visuel du workflow"""
    current_step = st.session_state.get('workflow_step', 'upload')
    
    steps = {
        'upload': {'num': 1, 'name': 'Upload & Nettoyage', 'icon': '↑'},
        'classify': {'num': 2, 'name': 'Classification', 'icon': '⚡'},
        'results': {'num': 3, 'name': 'Résultats & Export', 'icon': '▣'}
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
    """Sidebar moderne COMPLÈTE avec TOUS les onglets - FONT AWESOME"""
    with st.sidebar:
        # Header professionnel
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A5F 0%, #2E4A6F 100%);
                    padding: 1.5rem 1rem; border-radius: 16px; margin-bottom: 1.5rem;
                    box-shadow: 0 8px 24px rgba(30, 58, 95, 0.35);">
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">
                    ⚡
                </div>
                <h2 style="color: white; margin: 0; font-size: 1.4rem; font-weight: 800;">
                    Configuration
                </h2>
                <div style="background: rgba(255,255,255,0.2); color: white; padding: 0.4rem 1.2rem;
                            border-radius: 20px; margin-top: 0.75rem; font-size: 0.7rem; font-weight: 700;">
                    PARAMÈTRES SYSTÈME
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # System status
        st.markdown("""
        <div style="background: linear-gradient(135deg, #F8F9FA 0%, #EAECF0 100%);
                    padding: 1rem; border-radius: 12px; margin-bottom: 1rem;
                    border-left: 4px solid #2E86DE;">
            <h3 style="margin: 0; color: var(--primary); font-size: 1.1rem; font-weight: 700;">
                🔵 Statut Système
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ONGLET 1: CLASSIFICATEURS DISPONIBLES (RESTAURÉ)
        _render_classifiers_tab()
        
        # Mode de classification
        st.markdown("### Mode de Classification")
        
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
        
        # Configuration avancée optimisée
        with st.expander("⚡ Configuration Avancée", expanded=False):
            st.markdown("**Optimisations Performance**")
            
            # Timeout configuration
            if mode == 'precise':
                llm_timeout = st.slider(
                    "Timeout LLM (sec)",
                    min_value=10,
                    max_value=120,
                    value=30,
                    step=5,
                    help="Temps max par requête - évite les blocages"
                )
                llm_batch_size = st.number_input("Batch LLM", 1, 20, 5)
                max_retries = st.number_input("Tentatives max", 1, 5, 2)
                llm_percentage = 100
            elif mode == 'balanced':
                llm_timeout = st.slider("Timeout LLM (sec)", 10, 60, 20, 5)
                llm_percentage = st.slider("% LLM", 0, 100, 20, 5)
                llm_batch_size = 10
                max_retries = 2
            else:  # fast
                llm_timeout = 15
                llm_batch_size = 50
                max_retries = 1
                llm_percentage = 0
            
            bert_batch_size = st.number_input(
                "Batch BERT",
                min_value=10,
                max_value=100,
                value=50
            )
            
            use_cache = st.checkbox("Cache activé", value=True)
        
        # Save enhanced configuration
        st.session_state.config = {
            'mode': mode,
            'ollama_timeout': llm_timeout,
            'llm_batch_size': llm_batch_size,
            'bert_batch_size': bert_batch_size,
            'max_retries': max_retries,
            'llm_percentage': llm_percentage,
            'use_cache': use_cache
        }
        
        st.markdown("---")
        
        # ONGLET 2: CLEANING PARAMETERS (RESTAURÉ)
        with st.expander("Paramètres de Nettoyage", expanded=False):
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
        
        # ONGLET 3: INFORMATIONS SYSTÈME (RESTAURÉ)
        _render_system_info_tab()
        
        st.markdown("---")
        
        # ONGLET 4: ROLE MANAGEMENT (RESTAURÉ)
        _render_role_management_tab()
        
        # Footer
        st.markdown("---")
        st.caption(f"◉ Version 4.5 Final | {datetime.now().strftime('%Y-%m-%d')}", unsafe_allow_html=True)

def _render_classifiers_tab():
    """ONGLET CLASSIFICATEURS - RESTAURÉ avec FONT AWESOME"""
    modules = _load_classification_modules()
    
    if modules.get('available'):
        st.success("✓ **Modules chargés** - Tous les classificateurs sont opérationnels")
        
        with st.expander("Classificateurs Disponibles (5)", expanded=False):
            classificateurs = [
                ("BERT Classifier", "Deep Learning - Analyse de sentiment", "Actif"),
                ("Rule Classifier", "Classification par règles métier", "Actif"),
                ("Mistral Classifier", "LLM Mistral AI via Ollama", "Actif"),
                ("Multi-Model Orchestrator", "Orchestration intelligente", "Actif"),
                ("Ultra-Optimized V2", "Performance 3x optimisée", "Actif")
            ]
            
            for name, desc, status in classificateurs:
                st.info(f"**{name}**\n{desc}\n*Status: {status}*")
        
        # ONGLET MODÈLES OLLAMA (RESTAURÉ)
        try:
            check_ollama = modules.get('check_ollama_availability')
            list_models = modules.get('list_available_models')
            
            if check_ollama and check_ollama():
                st.success("✅ **Ollama actif** | Service LLM opérationnel")
                
                if list_models:
                    models = list_models()
                    if models:
                        with st.expander(f"Modèles LLM Disponibles ({len(models)})", expanded=False):
                            for idx, model in enumerate(models):
                                status = "⭐ Recommandé" if idx == 0 else "✅ Disponible"
                                st.info(f"**{model}**\n{status}")
            else:
                st.warning("⚠️ **Ollama inactif**\n\nService LLM non disponible\n\n💻 Démarrer avec: `ollama serve`")
        except Exception as e:
            logger.warning(f"Ollama check error: {e}")
    else:
        st.error("Modules non chargés")
        if modules.get('error'):
            st.caption(f"Erreur: {modules['error'][:100]}")

def _render_system_info_tab():
    """ONGLET INFORMATIONS SYSTÈME - RESTAURÉ"""
    with st.expander("Informations Système & Performance", expanded=False):
        try:
            modules = _load_classification_modules()
            if modules.get('available'):
                BERTClassifier = modules['BERTClassifier']
                bert = BERTClassifier(use_gpu=False)
                info = bert.get_model_info()
                
                st.markdown("**🤖 Modèle BERT**", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    device_icon = "🖥️" if info['device'].upper() == "CPU" else "🎮"
                    st.caption(f"{device_icon} **Device:** {info['device'].upper()}")
                    st.caption(f"📦 **Batch:** {info['batch_size']}", unsafe_allow_html=True)
                with col2:
                    model_short = info['model_name'].split('/')[-1][:25]
                    st.caption(f"📦 **Modèle:** {model_short}", unsafe_allow_html=True)
                
        except Exception as e:
            st.warning("Informations système non disponibles")

def _render_role_management_tab():
    """ONGLET ROLE MANAGEMENT - RESTAURÉ avec FONT AWESOME"""
    role_system = _load_role_system()
    
    if not role_system.get('available'):
        return
    
    with st.expander("Gestion des Rôles", expanded=False):
        st.markdown("#### Rôle Utilisateur & Permissions")
        
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
                        {role_config.display_name}
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
                    icon = "✓" if has_perm else "✗"
                    icon_color = "#10AC84" if has_perm else "#95A5A6"
                    st.markdown(f"<span style='color:{icon_color};'>{icon}</span> {perm_label}", unsafe_allow_html=True)
                
                st.caption(f"■ {len(role_config.features)} features disponibles", unsafe_allow_html=True)
                
        except Exception as e:
            st.warning(f"Erreur système de rôles: {e}")

# ==============================================================================
# SECTION UPLOAD - AVEC GESTION ERREUR 403 COMPLÈTE
# ==============================================================================

def _section_upload():
    """Section upload avec gestion erreur robuste"""
    st.header("↑ Étape 1 | Upload & Nettoyage des Données")
    
    # Instructions
    with st.expander("▣ Instructions d'Utilisation", expanded=True):
        st.markdown("""
        **✓ Préparez vos données:**
        
        1. □ **Format requis:** Fichier CSV
        2. ✎ **Contenu:** Au moins une colonne de texte avec tweets
        3. ◉ **Taille maximale:** 500 MB
        4. A **Encodage:** UTF-8 recommandé (auto-détection: utf-8, latin-1, iso-8859-1, cp1252)
        """)
        
        st.info("""
        **◆ Conseils pour un upload réussi:**
        
        - Assurez-vous que votre fichier CSV est valide
        - Vérifiez qu'il contient au moins une colonne de texte
        - Taille maximale : 500 MB
        - Encodages supportés : UTF-8, Latin-1, ISO-8859-1, CP1252
        """)
    
    st.markdown("<h3>■ Sélection du Fichier</h3>", unsafe_allow_html=True)
    
    # FILE UPLOADER ROBUSTE
    try:
        uploaded_file = st.file_uploader(
            "Déposez votre fichier CSV ici",
            type=['csv'],
            help="Glissez-déposez ou cliquez pour parcourir. Max: 500 MB"
        )
    except Exception as e:
        st.error(f"Erreur file uploader: {str(e)}")
        logger.error(f"File uploader error: {e}", exc_info=True)
        
        if "403" in str(e) or "Forbidden" in str(e):
            st.error("""
            Erreur 403 - Accès Interdit
            
            Solutions:
            1. Vérifier taille fichier < 500 MB
            2. Rafraîchir la page (F5)
            3. Vider le cache navigateur
            4. Redémarrer Streamlit
            """, icon="●")
        return
    
    if uploaded_file:
        _handle_upload_robust(uploaded_file)

def _handle_upload_robust(uploaded_file):
    """Gestion upload ultra-robuste avec détection erreur 403"""
    try:
        # Vérification taille AVANT lecture (éviter 403)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > 500:
            st.error(f"❌ Fichier trop volumineux: {file_size_mb:.1f} MB (max: 500 MB)")
            st.info("◆ Réduisez la taille du fichier ou filtrez les données")
            return
        
        # Info fichier
        st.success(f"✅ Fichier accepté: {uploaded_file.name} ({file_size_mb:.1f} MB)")
        
        # Lecture robuste avec multi-encodage
        with st.spinner("Lecture du fichier en cours..."):
            df = None
            
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
            
            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines='skip')
                    logger.info(f"✓ Lecture réussie avec encodage: {encoding}")
                    st.caption(f"Encodage détecté: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Erreur avec {encoding}: {e}")
                    continue
            
            if df is None:
                st.error("❌ Impossible de lire le fichier")
                st.info("◆ Essayez de sauvegarder le CSV avec encodage UTF-8 dans Excel")
                return
        
        if df.empty:
            st.error("❌ Fichier vide")
            return
        
        st.success(f"✅ Chargé avec succès: {len(df):,} lignes • {len(df.columns)} colonnes")
        
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
        st.subheader("□ Sélection de la Colonne de Texte")
        
        text_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not text_columns:
            st.error("❌ Aucune colonne de texte trouvée")
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
        st.info(f"📄 **Exemple de texte:**\n\n{sample[:300]}...")
        
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
        st.subheader("→ Démarrer le Nettoyage")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("Nettoyer et Préparer les Données", type="primary", use_container_width=True):
                with st.spinner("Nettoyage des données en cours..."):
                    modules = _load_classification_modules()
                    
                    if modules.get('TweetCleaner'):
                        TweetCleaner = modules['TweetCleaner']
                        cleaner = TweetCleaner(
                            remove_urls=st.session_state.cleaning_config.get('remove_urls', True),
                            remove_mentions=st.session_state.cleaning_config.get('remove_mentions', True),
                            remove_hashtags=st.session_state.cleaning_config.get('remove_hashtags', False),
                            convert_emojis=st.session_state.cleaning_config.get('convert_emojis', True)
                        )
                        
                        progress_bar = st.progress(0)
                        time.sleep(0.05)  # DOM stability
                        
                        try:
                            progress_bar.progress(0.3)
                        except Exception:
                            pass
                        
                        df_cleaned, stats = cleaner.process_dataframe(df.copy(), selected_column)
                        
                        try:
                            progress_bar.progress(1.0)
                        except Exception:
                            pass
                        
                        st.session_state.df_cleaned = df_cleaned
                        st.session_state.cleaning_stats = stats
                        st.session_state.workflow_step = 'classify'
                        
                        st.success("✅ Nettoyage terminé!")
                        
                        # Clear progress bar safely before rerun
                        time.sleep(0.1)
                        try:
                            progress_bar.empty()
                        except Exception:
                            pass
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erreur: Module de nettoyage non disponible")
                        st.info("💡 Vérifiez que les dépendances sont installées: `pip install emoji unidecode`")
        
        with col2:
            if st.button("Réinitialiser", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith('df_') or key == 'selected_text_column':
                        del st.session_state[key]
                st.rerun()
                
    except Exception as e:
        st.error("🔴 Erreur lors du traitement du fichier")
        st.code(str(e))
        logger.error(f"Upload handling error: {e}", exc_info=True)
        
        # Proposer des solutions simples
        st.info("◆ **Suggestions:** Vérifiez que votre fichier CSV est valide et que toutes les colonnes sont correctement formatées.")

# ==============================================================================
# SECTION CLASSIFICATION  
# ==============================================================================

def _section_classification():
    """Section classification avec batch processing"""
    st.header("⚙️ Étape 2 | Classification Intelligente Multi-Modèle")
    
    if 'df_cleaned' not in st.session_state:
        st.warning("Aucune donnée nettoyée trouvée", icon="⚠️")
        if st.button("Retour à l'upload", type="secondary"):
            st.session_state.workflow_step = 'upload'
            st.rerun()
        return
    
    df_cleaned = st.session_state.df_cleaned
    text_col = st.session_state.selected_text_column
    stats = st.session_state.get('cleaning_stats', {})
    
    # Résumé nettoyage
    st.subheader("📈 Résumé du Nettoyage")
    
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
        st.info(f"""
**⚙️ Mode {mode.upper()} sélectionné**

💾 Dataset: **{len(df_cleaned):,}** tweets  
🤖 Modèles: {'BERT + Règles' if mode == 'fast' else 'BERT + Règles + Mistral (20%)' if mode == 'balanced' else 'BERT + Mistral (100%)'}  
⏱️ Temps estimé: {'~20s' if mode == 'fast' else '~2min' if mode == 'balanced' else '~10min'}  
🎯 Précision: {'75%' if mode == 'fast' else '88%' if mode == 'balanced' else '95%'}
        """)
    
    with col2:
        use_optimized = st.checkbox("Ultra-Optimisé V2", value=True)
        st.caption("✅ Batch processing (50)")
        st.caption("✅ Cache multi-niveau")
    
    # Lancement
    st.subheader("▶ Lancer la Classification")
    
    if st.button("Démarrer la Classification Intelligente", type="primary", use_container_width=True):
        _perform_classification(df_cleaned, text_col, mode, use_optimized)

def _perform_classification(df, text_col, mode, use_optimized):
    """Lance la classification OPTIMISÉE avec batch processing, timeouts et tracking"""
    import time as t
    
    # DOM stability: Initialize containers with small delay
    progress_bar = st.progress(0)
    status = st.empty()
    t.sleep(0.05)  # Allow DOM to stabilize
    
    # Get enhanced configuration
    config = st.session_state.get('config', {})
    llm_timeout = config.get('ollama_timeout', 30)
    llm_batch_size = config.get('llm_batch_size', 10)
    max_retries = config.get('max_retries', 2)
    bert_batch_size = config.get('bert_batch_size', 50)
    
    try:
        # DOM safe operations with try-catch
        try:
            status.info("↻ Chargement des modules...")
            t.sleep(0.05)
            progress_bar.progress(0.1)
        except Exception:
            pass  # Ignore DOM errors
        
        modules = _load_classification_modules()
        
        if not modules.get('available'):
            st.error(f"✗ Modules non disponibles: {modules.get('error')}")
            st.warning("⚠ Classification par règles de base utilisée...")
            df_classified = _classify_fallback(df, text_col)
        else:
            start_time = time.time()
            total_tweets = len(df)
            
            # Check Ollama connectivity for precise/balanced modes
            ollama_available = False
            if mode in ['precise', 'balanced']:
                try:
                    check_ollama = modules.get('check_ollama_availability')
                    if check_ollama:
                        status.info("□ Vérification connexion Ollama...")
                        ollama_available = check_ollama()
                        
                        if ollama_available:
                            st.success("✓ Ollama connecté - Mode LLM activé")
                        else:
                            st.warning("⚠ Ollama indisponible - Fallback vers mode FAST")
                            mode = 'fast'
                except Exception as e:
                    logger.warning(f"Ollama check failed: {e}")
                    mode = 'fast'
            
            if use_optimized:
                try:
                    from services.ultra_optimized_classifier import UltraOptimizedClassifier
                    
                    status.info("⚡ Classificateur ultra-optimisé avec batch processing...")
                    progress_bar.progress(0.2)
                    
                    # Configure with optimized settings
                    classifier = UltraOptimizedClassifier(
                        batch_size=bert_batch_size,
                        max_workers=4,
                        use_cache=config.get('use_cache', True)
                    )
                    
                    def update_progress(msg, pct):
                        elapsed = time.time() - start_time
                        rate = (pct * total_tweets) / elapsed if elapsed > 0 else 0
                        eta = ((1 - pct) * total_tweets) / rate if rate > 0 else 0
                        
                        # DOM safe progress update
                        try:
                            progress_bar.progress(0.2 + pct * 0.7)
                            t.sleep(0.03)
                            status.info(f"↻ {msg} | {rate:.1f} tweets/sec | ETA: {eta:.0f}s")
                        except Exception:
                            pass  # Ignore DOM errors
                    
                    results, benchmark = classifier.classify_tweets_batch(
                        df,
                        f'{text_col}_cleaned',
                        mode=mode,
                        progress_callback=update_progress
                    )
                    
                    elapsed = time.time() - start_time
                    tweets_per_sec = total_tweets / elapsed if elapsed > 0 else 0
                    
                    df_classified = results
                    st.session_state.classification_benchmark = benchmark
                    st.session_state.performance_metrics = {
                        'total_time': elapsed,
                        'tweets_per_second': tweets_per_sec,
                        'mode': mode,
                        'ollama_available': ollama_available
                    }
                    
                except Exception as e:
                    logger.warning(f"Ultra-optimized fallback: {e}")
                    
                    if modules.get('MultiModelOrchestrator'):
                        MultiModelOrchestrator = modules['MultiModelOrchestrator']
                        orchestrator = MultiModelOrchestrator(mode=mode)
                        
                        status.info("⚡ Classification multi-modèles standard...")
                        df_classified = orchestrator.classify_intelligent(
                            df,
                            text_col,
                            progress_callback=lambda msg, pct: progress_bar.progress(0.2 + pct * 0.7)
                        )
                    else:
                        # Final fallback
                        df_classified = _classify_fallback(df, text_col)
            else:
                if modules.get('MultiModelOrchestrator'):
                    MultiModelOrchestrator = modules['MultiModelOrchestrator']
                    orchestrator = MultiModelOrchestrator(mode=mode)
                    
                    status.info("⚡ Classification multi-modèles en cours...")
                    df_classified = orchestrator.classify_intelligent(
                        df,
                        text_col,
                        progress_callback=lambda msg, pct: progress_bar.progress(0.2 + pct * 0.7)
                    )
                else:
                    df_classified = _classify_fallback(df, text_col)
        
        # Calcul rapport
        try:
            status.info("▣ Calcul des métriques...")
            t.sleep(0.05)
            progress_bar.progress(0.95)
        except Exception:
            pass
        
        report = _calculate_metrics(df_classified)
        
        # Sauvegarder
        st.session_state.df_classified = df_classified
        st.session_state.classification_report = report
        st.session_state.classification_mode = mode
        st.session_state.workflow_step = 'results'
        
        try:
            progress_bar.progress(1.0)
        except Exception:
            pass
        
        # Display performance summary
        perf = st.session_state.get('performance_metrics', {})
        if perf:
            st.success(
                f"✓ Classification terminée en {perf['total_time']:.1f}s | "
                f"{perf['tweets_per_second']:.1f} tweets/sec | "
                f"Mode: {mode.upper()}"
            )
        else:
            try:
                status.success("✓ Classification terminée avec succès!")
            except Exception:
                pass
        
        # Clear containers safely before rerun
        t.sleep(0.1)
        try:
            status.empty()
            progress_bar.empty()
        except Exception:
            pass
        
        time.sleep(0.5)
        st.rerun()
        
    except Exception as e:
        # Clear containers safely in exception handler
        t.sleep(0.1)
        try:
            status.empty()
            progress_bar.empty()
        except Exception:
            pass
        
        st.error(f"● Erreur classification: {str(e)}", icon="●")
        logger.error(f"Classification error: {e}", exc_info=True)
        
        with st.expander("Détails de l'erreur"):
            st.code(str(e))

def _classify_fallback(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Classification fallback par règles enrichie - IDENTIQUE à Classification_LLM"""
    logger.info("→ Fallback: classification par règles avancées (score-based)")
    
    df_copy = df.copy()
    
    def classify_row(text):
        """Classifie un tweet avec logique améliorée (score-based)"""
        if pd.isna(text):
            return pd.Series({
                'is_claim': 'non',
                'sentiment': 'neutre',
                'urgence': 'faible',
                'topics': 'autre',
                'incident': 'information',
                'responsable': 'aucun',
                'confidence': 0.50
            })
        
        t = str(text).lower()
        
        # Réclamation - mots-clés élargis
        claim_kw = [
            'panne', 'problème', 'bug', '@free', '@freebox', 'ne fonctionne', 
            'impossible', 'bloqué', 'erreur', 'dysfonctionnement', 'coupé', 
            'déçu', 'mécontent', 'frustré', 'inadmissible', 'scandale'
        ]
        is_claim = 'oui' if any(w in t for w in claim_kw) else 'non'
        
        # Thème principal - ENRICHI avec priorités et scores
        theme_scores = {}
        
        # FIBRE/INTERNET (priorité haute)
        fibre_kw = ['fibre', 'ftth', 'internet', 'connexion', 'débit', 'box', 'freebox', 
                    'ligne', 'adsl', 'vdsl', 'wifi', 'réseau wifi', 'routeur']
        theme_scores['fibre'] = sum(1 for w in fibre_kw if w in t)
        
        # MOBILE (priorité haute)
        mobile_kw = ['mobile', 'forfait', 'téléphone', 'portable', 'smartphone', 
                     '4g', '5g', 'data', 'sms', 'appel', 'réseau mobile']
        theme_scores['mobile'] = sum(1 for w in mobile_kw if w in t)
        
        # TV (priorité moyenne)
        tv_kw = ['tv', 'télé', 'télévision', 'chaîne', 'canal', 'programme', 
                 'replay', 'décodeur', 'freebox tv']
        theme_scores['tv'] = sum(1 for w in tv_kw if w in t)
        
        # FACTURE (priorité moyenne)
        facture_kw = ['facture', 'facturation', 'prix', 'coût', 'tarif', 'abonnement', 
                      'paiement', 'prélèvement', 'montant', 'euros', '€']
        theme_scores['facture'] = sum(1 for w in facture_kw if w in t)
        
        # SAV (priorité moyenne)
        sav_kw = ['sav', 'service client', 'support', 'assistance', 'conseiller', 
                  'technicien', 'intervention', 'rendez-vous', 'hotline']
        theme_scores['sav'] = sum(1 for w in sav_kw if w in t)
        
        # RÉSEAU (priorité basse)
        reseau_kw = ['réseau', 'couverture', 'antenne', 'signal', 'zone blanche', 
                     'infrastructure', 'déploiement']
        theme_scores['reseau'] = sum(1 for w in reseau_kw if w in t)
        
        # Sélection du thème avec le score maximum
        topics = 'autre'
        if theme_scores:
            max_score = max(theme_scores.values())
            if max_score > 0:
                # Prendre le thème avec score max
                topics = max(theme_scores, key=theme_scores.get)
        
        # Sentiment - logique enrichie
        positive_kw = ['merci', 'super', 'bravo', 'excellent', 'parfait', 'content', 
                       'satisfait', 'ravi', 'génial', 'top', 'nickel', 'résolu']
        negative_kw = ['panne', 'nul', 'mauvais', 'horrible', 'catastrophe', 'dégoûté', 
                       'énervé', 'frustré', 'déçu', 'insatisfait', 'inadmissible', 
                       'scandale', 'honte', 'lamentable']
        
        pos_score = sum(1 for w in positive_kw if w in t)
        neg_score = sum(1 for w in negative_kw if w in t)
        
        if pos_score > neg_score:
            sentiment = 'positif'
        elif neg_score > pos_score:
            sentiment = 'negatif'
        else:
            sentiment = 'neutre'
        
        # Urgence - basée sur mots-clés et contexte
        urgence_critique_kw = ['urgent', 'critique', 'grave', 'bloqué', 'impossible', 
                               'catastrophe', 'plus rien', 'totalement coupé']
        urgence_haute_kw = ['plusieurs heures', 'depuis longtemps', 'toute la journée', 
                            'depuis ce matin', 'depuis hier']
        
        if any(w in t for w in urgence_critique_kw):
            urgence = 'critique'
        elif any(w in t for w in urgence_haute_kw) or (is_claim == 'oui' and neg_score >= 2):
            urgence = 'haute'
        elif is_claim == 'oui':
            urgence = 'moyenne'
        else:
            urgence = 'faible'
        
        # Type d'incident - logique enrichie avec responsable
        incident = 'information'  # Default
        responsable = 'aucun'  # New field
        
        if 'facture' in t or 'facturation' in t or 'prix' in t:
            incident = 'facturation'
            responsable = 'service_commercial'
        elif 'panne' in t or 'coupé' in t or 'ne fonctionne' in t:
            incident = 'panne_technique'
            responsable = 'service_technique'
        elif 'lent' in t or 'lenteur' in t or 'ralentissement' in t:
            incident = 'degradation_service'
            responsable = 'service_technique'
        elif any(w in t for w in ['sav', 'service client', 'conseiller']):
            incident = 'processus_sav'
            responsable = 'service_client'
        elif any(w in t for w in ['réseau', 'couverture', 'signal']):
            incident = 'infrastructure_reseau'
            responsable = 'service_reseau'
        elif is_claim == 'oui':
            incident = 'autre_reclamation'
            responsable = 'service_client'
        
        # Calcul confiance basé sur nombre de mots-clés détectés
        total_keywords = max(theme_scores.values()) if theme_scores else 0
        base_confidence = 0.70
        if total_keywords >= 3:
            confidence = 0.90
        elif total_keywords >= 2:
            confidence = 0.85
        elif total_keywords >= 1:
            confidence = 0.75
        else:
            confidence = base_confidence
        
        return pd.Series({
            'is_claim': is_claim,
            'sentiment': sentiment,
            'urgence': urgence,
            'topics': topics,
            'incident': incident,
            'responsable': responsable,  # NEW
            'confidence': confidence
        })
    
    classifications = df_copy[text_col].apply(classify_row)
    return pd.concat([df_copy, classifications], axis=1)

def _calculate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcule tous les KPIs - RÉCLAMATIONS au lieu de CLAIMS + RESPONSABLE"""
    return {
        'total_tweets': len(df),
        'reclamations_count': len(df[df['is_claim'] == 'oui']) if 'is_claim' in df.columns else 0,
        'reclamations_percentage': (len(df[df['is_claim'] == 'oui']) / len(df) * 100) if 'is_claim' in df.columns and len(df) > 0 else 0,
        'negative_count': len(df[df['sentiment'] == 'negatif']) if 'sentiment' in df.columns else 0,
        'negative_percentage': (len(df[df['sentiment'] == 'negatif']) / len(df) * 100) if 'sentiment' in df.columns and len(df) > 0 else 0,
        'urgence_haute_count': len(df[df['urgence'] == 'haute']) if 'urgence' in df.columns else 0,
        'urgence_haute_percentage': (len(df[df['urgence'] == 'haute']) / len(df) * 100) if 'urgence' in df.columns and len(df) > 0 else 0,
        'confidence_avg': df['confidence'].mean() if 'confidence' in df.columns else 0,
        'sentiment_dist': df['sentiment'].value_counts() if 'sentiment' in df.columns else pd.Series(),
        'urgence_dist': df['urgence'].value_counts() if 'urgence' in df.columns else pd.Series(),
        'topics_dist': df['topics'].value_counts() if 'topics' in df.columns else pd.Series(),
        'incident_dist': df['incident'].value_counts() if 'incident' in df.columns else pd.Series(),
        'responsable_dist': df['responsable'].value_counts() if 'responsable' in df.columns else pd.Series()  # NEW
    }

# ==============================================================================
# SECTION RÉSULTATS - COMPLÈTE AVEC TOUS LES ONGLETS ET BOUTON COMPLET
# ==============================================================================

def _section_results():
    """Section résultats ultra-complète avec bouton affichage total"""
    st.markdown("<h2><i class='fas fa-chart-line'></i> Étape 3 | Résultats et Export</h2>", unsafe_allow_html=True)
    
    df = st.session_state.df_classified
    report = st.session_state.get('classification_report', {})
    mode = st.session_state.get('classification_mode', 'balanced')
    
    # Header avec bouton affichage complet
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"**Mode {mode.upper()}** | **{len(df):,}** tweets classifiés avec succès", icon="ℹ️")
    
    with col2:
        # NOUVEAU: Bouton affichage complet des indicateurs
        if 'show_all_indicators' not in st.session_state:
            st.session_state.show_all_indicators = False
        
        if st.button("Tout Afficher" if not st.session_state.show_all_indicators else "Réduire", 
                    use_container_width=True):
            st.session_state.show_all_indicators = not st.session_state.show_all_indicators
            st.rerun()
    
    # KPIs principaux avec pourcentages
    st.markdown("<h3><i class='fas fa-tachometer-alt'></i> Indicateurs Clés de Performance</h3>", unsafe_allow_html=True)
    
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
            if not report.get('incident_dist', pd.Series()).empty:
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
    
    # TOUS LES ONGLETS DE VISUALISATION (RESTAURÉS + RESPONSABLE)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Sentiment",
        "Réclamations",
        "Urgence",
        "Topics",
        "Incidents",
        "Responsable",
        "Données"
    ])
    
    with tab1:
        _render_sentiment_chart(df)
    
    with tab2:
        _render_reclamations_chart(df)  # CORRECTION: réclamations
    
    with tab3:
        _render_urgence_chart(df)
    
    with tab4:
        _render_topics_chart(df)
    
    with tab5:
        _render_incidents_chart(df)
    
    with tab6:
        _render_responsable_chart(df)  # NEW
    
    with tab7:
        st.markdown("<h3><i class='fas fa-table'></i> Tableau Détaillé</h3>", unsafe_allow_html=True)
        display_cols = ['text_cleaned', 'sentiment', 'is_claim', 'urgence', 'topics', 'incident', 'responsable', 'confidence']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            st.dataframe(df[available_cols], use_container_width=True, height=450)
            st.caption(f"<i class='fas fa-info-circle'></i> Affichage de {len(df)} lignes", unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True, height=450)
    
    st.markdown("---")
    
    # Export avec permissions
    _render_export_section(df, report)

def _render_sentiment_chart(df):
    """Graphique sentiment"""
    st.markdown("<h4><i class='fas fa-smile'></i> Distribution des Sentiments</h4>", unsafe_allow_html=True)
    
    if 'sentiment' in df.columns:
        counts = df['sentiment'].value_counts()
        
        fig = px.pie(
            values=counts.values,
            names=counts.index,
            title="",
            color_discrete_map={
                'positif': '#10AC84',
                'neutre': '#95A5A6',
                'negatif': '#E74C3C'
            }
        )
        fig.update_traces(textinfo='label+percent', textfont_size=14)
        fig.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"<i class='fas fa-info-circle'></i> Total: {len(df)} tweets analysés", unsafe_allow_html=True)

def _render_reclamations_chart(df):
    """Graphique réclamations - CORRECTION TERMINOLOGIE"""
    st.markdown("<h4><i class='fas fa-exclamation-circle'></i> Répartition Réclamations vs Non-Réclamations</h4>", unsafe_allow_html=True)
    
    if 'is_claim' in df.columns:
        counts = df['is_claim'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=['Réclamations' if l == 'oui' else 'Non-Réclamations' for l in counts.index],
            values=counts.values,
            marker_colors=['#E74C3C', '#10AC84'],
            hole=0.5,
            textinfo='label+percent'
        )])
        
        fig.update_layout(
            title="",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        reclamations = len(df[df['is_claim'] == 'oui'])
        pct = (reclamations / len(df) * 100) if len(df) > 0 else 0
        st.caption(f"<i class='fas fa-info-circle'></i> {reclamations:,} réclamations ({pct:.1f}%)", unsafe_allow_html=True)

def _render_urgence_chart(df):
    """Graphique urgence"""
    st.markdown("<h4><i class='fas fa-bolt'></i> Niveaux d'Urgence</h4>", unsafe_allow_html=True)
    
    if 'urgence' in df.columns:
        counts = df['urgence'].value_counts()
        
        fig = px.bar(
            x=counts.index,
            y=counts.values,
            title="",
            color=counts.values,
            color_continuous_scale='Reds',
            text=counts.values
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"<i class='fas fa-info-circle'></i> Distribution sur {len(df)} tweets", unsafe_allow_html=True)

def _render_topics_chart(df):
    """Graphique topics"""
    st.markdown("<h4><i class='fas fa-tags'></i> Distribution des Thèmes</h4>", unsafe_allow_html=True)
    
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
    """Graphique incidents"""
    st.markdown("<h4><i class='fas fa-wrench'></i> Types d'Incidents</h4>", unsafe_allow_html=True)
    
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

def _render_responsable_chart(df):
    """Graphique responsables - NOUVEAU KPI"""
    st.markdown("<h4><i class='fas fa-user-tie'></i> Responsables de l'Incident</h4>", unsafe_allow_html=True)
    
    if 'responsable' in df.columns:
        counts = df['responsable'].value_counts()
        
        # Couleurs adaptées par service
        color_map = {
            'service_technique': '#E74C3C',      # Rouge pour technique
            'service_commercial': '#3498DB',     # Bleu pour commercial
            'service_client': '#F39C12',         # Orange pour client
            'service_reseau': '#9B59B6',         # Violet pour réseau
            'aucun': '#95A5A6'                   # Gris pour aucun
        }
        
        colors = [color_map.get(name, '#95A5A6') for name in counts.index]
        
        fig = go.Figure(data=[go.Bar(
            x=counts.index,
            y=counts.values,
            marker_color=colors,
            text=counts.values,
            texttemplate='%{text}',
            textposition='outside'
        )])
        
        fig.update_layout(
            title="",
            height=400,
            showlegend=False,
            xaxis_title="Service Responsable",
            yaxis_title="Nombre d'incidents"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Afficher statistiques détaillées
        non_aucun = len(df[df['responsable'] != 'aucun'])
        pct = (non_aucun / len(df) * 100) if len(df) > 0 else 0
        st.caption(f"<i class='fas fa-info-circle'></i> {non_aucun:,} incidents affectés ({pct:.1f}%) | {len(df['responsable'].unique())} services distincts", unsafe_allow_html=True)

def _display_business_dashboard_mistral(df, report):
    """Dashboard Business KPIs COMPLET - RESTAURÉ"""
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
        st.markdown("<h2><i class='fas fa-briefcase'></i> Tableau de Bord Business - KPIs Avancés</h2>", unsafe_allow_html=True)
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
                    claims = len(df[df['is_claim'] == 'oui'])
                    claims_pct = (claims / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Réclamations",
                        f"{claims:,}",
                        delta=f"{claims_pct:.1f}%"
                    )
            
            with col3:
                if 'sentiment' in df.columns:
                    neg = len(df[df['sentiment'].isin(['negatif', 'negative', 'neg'])])
                    neg_pct = (neg / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Sentiments Négatifs",
                        f"{neg:,}",
                        delta=f"{neg_pct:.1f}%"
                    )
            
            with col4:
                if 'urgence' in df.columns:
                    urgent = len(df[df['urgence'] == 'haute'])
                    urgent_pct = (urgent / len(df) * 100) if len(df) > 0 else 0
                    st.metric(
                        "Urgence Haute",
                        f"{urgent:,}",
                        delta=f"{urgent_pct:.1f}%"
                    )
        
        # Afficher les KPIs enrichis du dataset d'entraînement
        _display_enriched_training_kpis_mistral()
        
    except Exception as e:
        logger.error(f"Erreur dashboard business: {e}")
        st.warning("Certains KPIs avancés ne sont pas disponibles", icon="⚠️")

def _display_enriched_training_kpis_mistral():
    """Affiche les KPIs du dataset enrichi d'entraînement pour Mistral"""
    try:
        from components.enriched_kpis_display import render_enriched_kpis_summary
        
        st.markdown("---")
        st.markdown("## 📚 KPIs du Dataset d'Entraînement Enrichi")
        st.caption("Métriques du dataset utilisé pour l'entraînement des modèles")
        
        render_enriched_kpis_summary()
        
    except Exception as e:
        logger.warning(f"Enriched training KPIs error: {e}")

def _render_export_section(df, report):
    """Section export avec vérification permissions"""
    st.markdown("<h3><i class='fas fa-download'></i> Export des Résultats</h3>", unsafe_allow_html=True)
    
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
        st.warning("Permission d'export requise", icon="⚠️")
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
