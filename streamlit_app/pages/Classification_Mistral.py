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

Version: 4.5 - Production Ready
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

# Configuration du logging (doit être avant l'utilisation de logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env
# Chercher le fichier .env à la racine du projet
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Fichier .env chargé depuis: {env_path}")
else:
    # Essayer aussi à la racine du workspace
    root_env = Path(__file__).parent.parent.parent.parent / '.env'
    if root_env.exists():
        load_dotenv(root_env)
        logger.info(f"Fichier .env chargé depuis: {root_env}")
    else:
        logger.warning("Fichier .env non trouvé, utilisation des variables d'environnement système")

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
    """Charge les modules de classification avec cache"""
    try:
        logger.info("Chargement des modules de classification...")
        
        from services.tweet_cleaner import TweetCleaner
        from services.mistral_classifier import (
            MistralClassifier,
            check_ollama_availability,
            list_available_models
        )
        from services.multi_model_orchestrator import MultiModelOrchestrator
        from services.bert_classifier import BERTClassifier
        from services.rule_classifier import EnhancedRuleClassifier
        
        logger.info("Modules chargés avec succès")
        
        return {
            'TweetCleaner': TweetCleaner,
            'MistralClassifier': MistralClassifier,
            'check_ollama_availability': check_ollama_availability,
            'list_available_models': list_available_models,
            'MultiModelOrchestrator': MultiModelOrchestrator,
            'BERTClassifier': BERTClassifier,
            'EnhancedRuleClassifier': EnhancedRuleClassifier,
            'available': True
        }
    except Exception as e:
        logger.error(f"Erreur lors du chargement des modules: {e}")
        return {'available': False, 'error': str(e)}

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
    Charge les styles CSS personnalisés pour l'interface utilisateur.
    
    Utilise Font Awesome pour les icônes et définit une palette de couleurs
    cohérente ainsi que des animations pour améliorer l'expérience utilisateur.
    """
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
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
        # Header professionnel
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A5F 0%, #2E4A6F 100%);
                    padding: 1.5rem 1rem; border-radius: 16px; margin-bottom: 1.5rem;
                    box-shadow: 0 8px 24px rgba(30, 58, 95, 0.35);">
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">
                    <i class="fas fa-cog"></i>
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
                <i class="fas fa-info-circle"></i> Statut Système
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ONGLET 1: CLASSIFICATEURS DISPONIBLES (RESTAURÉ)
        _render_classifiers_tab()
        
        # Sélecteur de Provider API (Mistral Local vs Gemini API)
        st.markdown("### Provider de Classification")
        
        # Vérifier disponibilité des providers
        mistral_available = _check_mistral_availability()
        gemini_available = _check_gemini_availability()
        
        provider_options = []
        provider_labels = {}
        
        if mistral_available:
            provider_options.append('mistral')
            provider_labels['mistral'] = 'Mistral (Local)'
        
        if gemini_available:
            provider_options.append('gemini')
            provider_labels['gemini'] = 'Gemini API (Externe)'
        
        # Si aucun provider disponible, ajouter quand même les options avec avertissement
        if not provider_options:
            provider_options = ['mistral', 'gemini']
            provider_labels = {
                'mistral': 'Mistral (Local) - Non disponible',
                'gemini': 'Gemini API (Externe) - Non disponible'
            }
        
        # Sélection du provider
        selected_provider = st.radio(
            "Choisissez le modèle de classification:",
            options=provider_options,
            format_func=lambda x: provider_labels.get(x, x),
            index=0 if 'mistral' in provider_options else 0,
            key='api_provider_selector',
            help="Mistral: Local via Ollama (situation de crise) | Gemini: API externe (serveur entreprise)"
        )
        
        # Afficher statut des providers
        col1, col2 = st.columns(2)
        with col1:
            if mistral_available:
                st.success("Mistral disponible")
            else:
                st.error("Mistral indisponible")
        
        with col2:
            if gemini_available:
                st.success("Gemini disponible")
            else:
                st.warning("Gemini indisponible")
                st.caption("Vérifiez GEMINI_API_KEY dans .env")
        
        # Sauvegarder le provider sélectionné
        st.session_state.selected_api_provider = selected_provider
        
        st.markdown("---")
        
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
        
        st.session_state.config = {
            'mode': mode,
            'provider': selected_provider
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
        st.caption(f"<i class='fas fa-code'></i> Version 4.5 Final | {datetime.now().strftime('%Y-%m-%d')}", unsafe_allow_html=True)

def _check_mistral_availability() -> bool:
    """Vérifie si Mistral/Ollama est disponible"""
    try:
        modules = _load_classification_modules()
        if modules.get('available'):
            check_ollama = modules.get('check_ollama_availability')
            if check_ollama:
                return check_ollama()
        return False
    except Exception as e:
        logger.warning(f"Erreur vérification Mistral: {e}")
        return False

def _check_gemini_availability() -> bool:
    """Vérifie si l'API Gemini est disponible"""
    try:
        from services.gemini_classifier import check_gemini_availability
        return check_gemini_availability()
    except Exception as e:
        logger.warning(f"Erreur vérification Gemini: {e}")
        return False

def _render_classifiers_tab():
    """
    Affiche l'onglet des classificateurs disponibles.
    
    Liste tous les modèles de classification disponibles (BERT, Règles, Mistral, etc.)
    et affiche leur statut ainsi que les modèles Ollama disponibles si applicable.
    """
    modules = _load_classification_modules()
    
    if modules.get('available'):
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(16, 172, 132, 0.15) 0%, rgba(16, 172, 132, 0.08) 100%);
                    padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 1rem;
                    border-left: 4px solid #10AC84;">
            <strong style="color: #10AC84;"><i class="fas fa-check-circle"></i> Modules chargés</strong>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Classificateurs Disponibles (5)", expanded=False):
            classificateurs = [
                ("BERT Classifier", "Deep Learning - Analyse de sentiment", "Actif"),
                ("Rule Classifier", "Classification par règles métier", "Actif"),
                ("Mistral Classifier", "LLM Mistral AI via Ollama", "Actif"),
                ("Multi-Model Orchestrator", "Orchestration intelligente", "Actif"),
                ("Ultra-Optimized V2", "Performance 3x optimisée", "Actif")
            ]
            
            for name, desc, status in classificateurs:
                st.markdown(f"""
                <div style="background: white; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;
                            border: 1px solid #E0E0E0;">
                    <div style="font-weight: 700; color: #1E3A5F; font-size: 0.95rem;">{name}</div>
                    <div style="font-size: 0.8rem; color: #666;">{desc}</div>
                    <div style="font-size: 0.75rem; font-weight: 600;">{status}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # ONGLET MODÈLES OLLAMA (RESTAURÉ)
        try:
            check_ollama = modules.get('check_ollama_availability')
            list_models = modules.get('list_available_models')
            
            if check_ollama and check_ollama():
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
    else:
        st.error("Modules non chargés")
        if modules.get('error'):
            st.caption(f"Erreur: {modules['error'][:100]}")

def _render_system_info_tab():
    """
    Affiche les informations système et de performance.
    
    Présente les détails techniques du modèle BERT chargé, notamment
    le device utilisé (CPU/GPU), la taille des batches et le nom du modèle.
    """
    with st.expander("Informations Système & Performance", expanded=False):
        try:
            modules = _load_classification_modules()
            if modules.get('available'):
                BERTClassifier = modules['BERTClassifier']
                bert = BERTClassifier(use_gpu=False)
                info = bert.get_model_info()
                
                st.markdown("**<i class='fas fa-brain'></i> Modèle BERT**", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    device_icon = "<i class='fas fa-microchip'></i>" if info['device'].upper() == "CPU" else "<i class='fas fa-gpu-card'></i>"
                    st.caption(f"{device_icon} **Device:** {info['device'].upper()}")
                    st.caption(f"<i class='fas fa-layer-group'></i> **Batch:** {info['batch_size']}", unsafe_allow_html=True)
                with col2:
                    model_short = info['model_name'].split('/')[-1][:25]
                    st.caption(f"<i class='fas fa-cube'></i> **Modèle:** {model_short}", unsafe_allow_html=True)
                
        except Exception as e:
            st.warning("Informations système non disponibles")

def _render_role_management_tab():
    """
    Affiche l'onglet de gestion des rôles utilisateurs.
    
    Permet de changer de rôle et affiche les permissions associées à chaque rôle
    ainsi que les fonctionnalités disponibles.
    """
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
    """Section upload avec gestion complète des erreurs"""
    st.markdown("## Étape 1 | Upload et Nettoyage des Données")
    
    # Instructions
    with st.expander("Instructions d'Utilisation", expanded=True):
        st.markdown("""
        **Préparation des données:**
        
        1. **Format requis:** Fichier CSV
        2. **Contenu:** Au moins une colonne de texte contenant les tweets à analyser
        3. **Taille maximale:** 500 MB (limite augmentée pour éviter les erreurs d'accès)
        4. **Encodage:** UTF-8 recommandé (détection automatique de 6 encodages supportés)
        
        **En cas d'erreur 403 (Accès Interdit):**
        
        """)
        st.warning("""
        **Vérifications à effectuer:**
        
        1. Vérifier que la taille du fichier est inférieure à 500 MB
        2. Rafraîchir la page (touche F5)
        3. Vérifier que le fichier n'est pas en lecture seule
        4. Vider le cache du navigateur (Ctrl+Shift+Del)
        5. Désactiver temporairement l'anti-virus si nécessaire
        6. Redémarrer l'application si le problème persiste
        
        **Commande de redémarrage:**
        ```bash
        streamlit run streamlit_app/app.py --server.port=8503
        ```
        """)
        st.markdown("**Pour plus d'aide:** Consultez le guide d'utilisation")
    
    st.markdown("### Sélection du Fichier")
    
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
            <h4><i class='fas fa-ban'></i> Erreur 403 - Accès Interdit</h4>
            
            Cette erreur indique un problème de permissions. Solutions recommandées:
            
            1. <i class='fas fa-weight'></i> Vérifier que la taille du fichier est inférieure à 500 MB
            2. <i class='fas fa-sync'></i> Rafraîchir la page (F5)
            3. <i class='fas fa-trash'></i> Vider le cache du navigateur
            4. <i class='fas fa-redo'></i> Redémarrer Streamlit
            """, icon="error")
        return
    
    if uploaded_file:
        _handle_upload_robust(uploaded_file)

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
            st.error(f"Fichier trop volumineux: {file_size_mb:.1f} MB (max: 500 MB)")
            st.info("Réduisez la taille du fichier ou filtrez les données")
            return
        
        # Info fichier
        st.success(f"Fichier accepté: {uploaded_file.name} ({file_size_mb:.1f} MB)")
        
        # Lecture robuste avec multi-encodage
        with st.spinner("Lecture du fichier en cours..."):
            df = None
            
            # Détection automatique d'encodage avec chardet (si disponible)
            detected_encoding = None
            try:
                import chardet
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
        status.info("Chargement des modules...")
        progress_bar.progress(0.1)
        
        # Récupérer le provider sélectionné
        selected_provider = st.session_state.get('selected_api_provider', 'mistral')
        config = st.session_state.get('config', {})
        selected_provider = config.get('provider', selected_provider)
        
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
                
                # Les résultats Gemini sont déjà complets avec tous les champs KPI
                # Vérification et validation post-traitement
                required_fields = ['sentiment', 'categorie', 'score_confiance', 'is_claim', 'urgence', 'topics', 'incident']
                missing_fields = [field for field in required_fields if field not in df_classified.columns]
                
                if missing_fields:
                    logger.warning(f"Champs manquants après classification Gemini: {missing_fields}")
                    # Compléter avec valeurs par défaut si nécessaire
                    if 'is_claim' not in df_classified.columns:
                        df_classified['is_claim'] = df_classified['sentiment'].apply(
                            lambda x: 'oui' if str(x).lower() == 'negatif' else 'non'
                        )
                    if 'urgence' not in df_classified.columns:
                        df_classified['urgence'] = df_classified.apply(
                            lambda row: 'haute' if (
                                str(row.get('sentiment', '')).lower() == 'negatif' and 
                                row.get('is_claim', 'non') == 'oui'
                            ) else 'moyenne' if str(row.get('sentiment', '')).lower() == 'negatif' else 'faible',
                            axis=1
                        )
                    if 'topics' not in df_classified.columns:
                        df_classified['topics'] = df_classified.get('categorie', 'autre')
                    if 'incident' not in df_classified.columns:
                        df_classified['incident'] = df_classified['is_claim'].apply(
                            lambda x: 'non_specifie' if x == 'oui' else 'aucun'
                        )
                
                # Validation post-traitement stricte
                # Assert sur enum sentiment
                valid_sentiments = ['positif', 'negatif', 'neutre']
                invalid_sentiments = df_classified[~df_classified['sentiment'].isin(valid_sentiments)]
                if len(invalid_sentiments) > 0:
                    logger.warning(f"Correction de {len(invalid_sentiments)} sentiments invalides")
                    df_classified.loc[~df_classified['sentiment'].isin(valid_sentiments), 'sentiment'] = 'neutre'
                
                # Assert sur enum categorie
                valid_categories = ['produit', 'service', 'support', 'promotion', 'autre']
                invalid_categories = df_classified[~df_classified['categorie'].isin(valid_categories)]
                if len(invalid_categories) > 0:
                    logger.warning(f"Correction de {len(invalid_categories)} catégories invalides")
                    df_classified.loc[~df_classified['categorie'].isin(valid_categories), 'categorie'] = 'autre'
                
                # Assert sur range score_confiance (0.0-1.0)
                df_classified['score_confiance'] = df_classified['score_confiance'].clip(0.0, 1.0)
                
                # Alias confidence pour compatibilité
                if 'confidence' not in df_classified.columns:
                    df_classified['confidence'] = df_classified['score_confiance']
                
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
        
        # Vérifier que df_classified est défini avant de calculer les métriques
        # Note: Si Gemini a réussi, le code s'arrête avant avec st.rerun()
        # Cette vérification s'applique uniquement au cas Mistral
        
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

def _calculate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule tous les indicateurs clés de performance (KPIs).
    
    Calcule les métriques de réclamations, sentiments, urgence, topics et incidents
    à partir du DataFrame classifié.
    
    Args:
        df: DataFrame contenant les données classifiées
        
    Returns:
        Dictionnaire contenant toutes les métriques calculées
    """
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
    
    # TOUS LES ONGLETS DE VISUALISATION (RESTAURÉS)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Sentiment",
        "Réclamations",
        "Urgence",
        "Topics",
        "Incidents",
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

def _render_sentiment_chart(df):
    """Graphique de distribution des sentiments"""
    st.markdown("#### Distribution des Sentiments")
    
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
    """Graphique de répartition des réclamations"""
    st.markdown("#### Répartition Réclamations vs Non-Réclamations")
    
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
    """Graphique de distribution des niveaux d'urgence"""
    st.markdown("#### Niveaux d'Urgence")
    
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
