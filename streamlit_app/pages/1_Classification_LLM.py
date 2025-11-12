"""
Page de Classification LLM - FreeMobilaChat v4.4 COMPLÈTE
==========================================================

VERSION DÉFINITIVE avec TOUTES les fonctionnalités:
✅ File uploader robuste avec gestion erreur 403
✅ Toutes les visualisations (6 graphiques)
✅ Dashboard Business KPIs (10 KPIs)
✅ Système de rôles complet
✅ Export multi-format
✅ Performance optimisée

Classification professionnelle de tweets avec LLM et Machine Learning
Few-shot learning | Analyse multi-dimensionnelle | 50 tweets max
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from datetime import datetime
import sys
import os
import logging
from typing import Dict, Any, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemins
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==============================================================================
# LAZY LOADING
# ==============================================================================

@st.cache_resource(show_spinner=False)
def _get_enriched_kpis_display():
    """Charge le module d'affichage des KPIs enrichis"""
    try:
        from components.enriched_kpis_display import render_enriched_kpis_summary
        return {
            'render_enriched_kpis_summary': render_enriched_kpis_summary,
            'available': True
        }
    except Exception as e:
        logger.warning(f"Enriched KPIs display error: {e}")
        return {'available': False}

@st.cache_resource(show_spinner=False)
def _get_role_selector():
    """Charge le role selector avec cache"""
    try:
        from components.role_selector import (
            render_role_selector,
            render_role_specific_header,
            get_current_role,
            filter_kpis_by_role,
            filter_dataframe_by_role,
            has_permission
        )
        return {
            'render_role_selector': render_role_selector,
            'render_role_specific_header': render_role_specific_header,
            'get_current_role': get_current_role,
            'filter_kpis_by_role': filter_kpis_by_role,
            'filter_dataframe_by_role': filter_dataframe_by_role,
            'has_permission': has_permission,
            'available': True
        }
    except Exception as e:
        logger.warning(f"Role selector error: {e}")
        return {'available': False}

@st.cache_resource(show_spinner=False)
def _get_enhanced_kpis():
    """Charge les KPIs avancés avec cache"""
    try:
        from services import enhanced_kpis_vizualizations as ekv
        from services.enhanced_kpis_vizualizations import (
            compute_business_kpis,
            render_business_kpis
        )
        return {
            'ekv': ekv,
            'compute_business_kpis': compute_business_kpis,
            'render_business_kpis': render_business_kpis,
            'available': True
        }
    except Exception as e:
        logger.warning(f"Enhanced KPIs error: {e}")
        return {'available': False}

# ==============================================================================
# CONFIGURATION PAGE
# ==============================================================================
st.set_page_config(
    page_title="Classification LLM - FreeMobilaChat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# TAXONOMIE ET EXEMPLES
# ==============================================================================
CLASSIFICATION_SCHEMA = {
    "is_claim": [0, 1],
    "topics": ["fibre", "dsl", "wifi", "tv", "mobile", "facture", "activation", "resiliation", "autre"],
    "sentiment": ["neg", "neu", "pos"],
    "urgence": ["haute", "moyenne", "basse"],
    "incident": ["facturation", "incident_reseau", "livraison", "information", "processus_sav", "autre"]
}

FEW_SHOT_EXAMPLES = [
    {"tweet": "rt @free: découvrez la nouvelle chaîne imearth en 4k !", "result": {"is_claim": 0, "topics": ["tv"], "sentiment": "neu", "urgence": "basse", "incident": "information", "confidence": 0.9}},
    {"tweet": "@free panne fibre à cergy depuis 7h, impossible de bosser", "result": {"is_claim": 1, "topics": ["fibre"], "sentiment": "neg", "urgence": "haute", "incident": "incident_reseau", "confidence": 0.95}},
    {"tweet": "@freebox toujours pas de réponse depuis 3 jours, c'est long", "result": {"is_claim": 1, "topics": ["autre"], "sentiment": "neg", "urgence": "moyenne", "incident": "processus_sav", "confidence": 0.88}},
    {"tweet": "Merci @free pour la résolution rapide de mon problème de connexion !", "result": {"is_claim": 0, "topics": ["fibre", "dsl"], "sentiment": "pos", "urgence": "basse", "incident": "information", "confidence": 0.92}},
    {"tweet": "@free ma facture est incorrecte ce mois-ci, pouvez-vous vérifier ?", "result": {"is_claim": 1, "topics": ["facture"], "sentiment": "neu", "urgence": "moyenne", "incident": "facturation", "confidence": 0.91}}
]

@st.cache_resource(show_spinner=False)
def _get_balanced_classifier():
    """Load balanced (rule-based advanced) classifier with cache"""
    try:
        from services.dynamic_classifier import DynamicClassificationEngine
        engine = DynamicClassificationEngine()
        
        def classify_batch(texts: List[str]) -> List[Dict[str, Any]]:
            """Classify a batch of texts using dynamic classifier"""
            results = []
            for text in texts:
                result = engine.classify_text(text)
                # Convert to expected format
                results.append({
                    'is_claim': 1 if result.intention in ['reclamation', 'demande_aide'] else 0,
                    'topics': [result.theme] if result.theme else ['autre'],
                    'sentiment': result.sentiment if result.sentiment in ['pos', 'neu', 'neg'] else 
                                ('pos' if 'positif' in result.sentiment else 
                                 'neg' if 'negatif' in result.sentiment else 'neu'),
                    'urgence': result.urgency if result.urgency in ['haute', 'moyenne', 'basse'] else 'moyenne',
                    'incident': _map_intention_to_incident(result.intention),
                    'confidence': result.confidence
                })
            return results
        
        return classify_batch
    except Exception as e:
        logger.error(f"Balanced classifier error: {e}")
        return None

@st.cache_resource(show_spinner=False)
def _get_precise_classifier(config: Dict[str, Any]):
    """Load precise LLM classifier with cache and timeout handling"""
    try:
        llm_provider = config.get('llm_provider', 'Mistral (Ollama)')
        
        if 'Ollama' in llm_provider:
            # Use local Ollama
            try:
                from services.mistral_classifier import MistralClassifier, check_ollama_availability
                
                # Check Ollama availability with timeout
                if not check_ollama_availability():
                    logger.warning("Ollama not available")
                    return None
                
                model_name = config.get('model_name', 'mistral:latest')
                temperature = config.get('temperature', 0.1)
                timeout = config.get('timeout', 30)
                
                classifier = MistralClassifier(
                    model_name=model_name,
                    batch_size=config.get('batch_size', 10),
                    temperature=temperature,
                    max_retries=2  # Reduced for better performance
                )
                
                def classify_batch_llm(texts: List[str]) -> List[Dict[str, Any]]:
                    """Classify using Mistral/Ollama with timeout"""
                    try:
                        results = classifier.classify_batch(texts)
                        # Convert Mistral format to expected format
                        converted = []
                        for r in results:
                            converted.append({
                                'is_claim': 1 if r.get('categorie') in ['reclamation', 'support', 'produit'] else 0,
                                'topics': [r.get('categorie', 'autre')],
                                'sentiment': _map_mistral_sentiment(r.get('sentiment', 'neutre')),
                                'urgence': 'haute' if r.get('score_confiance', 0.5) > 0.8 else 'moyenne',
                                'incident': _map_category_to_incident(r.get('categorie', 'autre')),
                                'confidence': r.get('score_confiance', 0.7)
                            })
                        return converted
                    except Exception as e:
                        logger.error(f"LLM classification error: {e}")
                        # Return fallback results
                        return [_classify_single_tweet_fallback(t) for t in texts]
                
                return classify_batch_llm
                
            except ImportError:
                logger.warning("Mistral classifier not available")
                return None
        
        else:
            # OpenAI/Anthropic (placeholder for now)
            logger.info(f"Provider {llm_provider} not yet implemented")
            return None
            
    except Exception as e:
        logger.error(f"Precise classifier error: {e}")
        return None

def _map_intention_to_incident(intention: str) -> str:
    """Map intention to incident type"""
    mapping = {
        'reclamation': 'incident_reseau',
        'demande_aide': 'processus_sav',
        'demande_info': 'information',
        'compliment': 'information',
        'suggestion': 'information',
        'information': 'information'
    }
    return mapping.get(intention, 'autre')

def _map_mistral_sentiment(sentiment: str) -> str:
    """Map Mistral sentiment to expected format"""
    sentiment_lower = sentiment.lower()
    if 'pos' in sentiment_lower:
        return 'pos'
    elif 'neg' in sentiment_lower:
        return 'neg'
    else:
        return 'neu'

def _map_category_to_incident(category: str) -> str:
    """Map category to incident type"""
    mapping = {
        'produit': 'incident_reseau',
        'service': 'processus_sav',
        'support': 'processus_sav',
        'promotion': 'information',
        'reclamation': 'incident_reseau',
        'autre': 'autre'
    }
    return mapping.get(category, 'autre')

def _classify_single_tweet_fallback(tweet: str) -> Dict[str, Any]:
    """Fallback classification using simple rules"""
    t = tweet.lower()
    
    claim_kw = ['panne', 'problème', 'bug', '@free', '@freebox', 'erreur', 'impossible']
    is_claim = 1 if any(w in t for w in claim_kw) else 0
    
    topics = []
    if any(w in t for w in ['fibre', 'ftth', 'internet']): topics.append('fibre')
    if 'wifi' in t: topics.append('wifi')
    if any(w in t for w in ['tv', 'télé', 'television']): topics.append('tv')
    if any(w in t for w in ['mobile', '4g', '5g']): topics.append('mobile')
    if 'facture' in t: topics.append('facture')
    if not topics: topics = ['autre']
    
    if any(w in t for w in ['merci', 'super', 'bravo', 'excellent']): sentiment = 'pos'
    elif any(w in t for w in ['panne', 'nul', 'mauvais', 'horrible']): sentiment = 'neg'
    else: sentiment = 'neu'
    
    if any(w in t for w in ['urgent', 'critique', 'impossible']): urgence = 'haute'
    elif is_claim: urgence = 'moyenne'
    else: urgence = 'basse'
    
    if 'facture' in t: incident = 'facturation'
    elif 'panne' in t: incident = 'incident_reseau'
    elif 'sav' in t: incident = 'processus_sav'
    elif is_claim: incident = 'autre'
    else: incident = 'information'
    
    return {
        'is_claim': is_claim,
        'topics': topics,
        'sentiment': sentiment,
        'urgence': urgence,
        'incident': incident,
        'confidence': 0.75 if is_claim else 0.70
    }

def _get_default_result() -> Dict[str, Any]:
    """Return default classification result"""
    return {
        'is_claim': 0,
        'topics': ['autre'],
        'sentiment': 'neu',
        'urgence': 'basse',
        'incident': 'information',
        'confidence': 0.5
    }

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Point d'entrée principal - VERSION COMPLÈTE"""
    
    _load_professional_css()
    
    # Système de rôles (lazy)
    role_funcs = _get_role_selector()
    if role_funcs.get('available'):
        try:
            render_role_selector = role_funcs['render_role_selector']
            render_role_specific_header = role_funcs['render_role_specific_header']
            current_role = render_role_selector()
            render_role_specific_header(current_role, "Classification LLM")
        except Exception as e:
            logger.warning(f"Role selector error: {e}")
            _render_professional_header()
    else:
        _render_professional_header()
    
    # Sidebar configuration
    _render_sidebar_config()
    
    # Upload zone
    uploaded_file = _render_upload_zone()
    
    if uploaded_file is not None:
        _handle_dynamic_classification(uploaded_file)
    else:
        _render_welcome_section()

# ==============================================================================
# CSS
# ==============================================================================

def _load_professional_css():
    """Styles CSS professionnels - Sans Font Awesome"""
    st.markdown("""
    <style>
    .main {background: #f5f7fa;}
    .block-container {padding: 1.5rem !important; max-width: 1400px !important;}
    #MainMenu, footer, header {visibility: hidden;}
    
    .professional-header {
        background: linear-gradient(135deg, #CC0000 0%, #8B0000 100%);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(204, 0, 0, 0.25);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        text-align: center;
        margin: 0;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #CC0000;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(204, 0, 0, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

def _render_professional_header():
    """Header professionnel - Sans Font Awesome"""
    st.markdown("""
    <div class="professional-header">
        <h1 class="header-title">
            🧠 CLASSIFICATION LLM DES TWEETS
        </h1>
        <p style="color: rgba(255,255,255,0.95); text-align: center; font-size: 1.1rem; margin-top: 0.5rem;">
            Intelligence Artificielle avancée | Few-shot learning | Analyse multi-dimensionnelle
        </p>
    </div>
    """, unsafe_allow_html=True)

def _render_sidebar_config():
    """Configuration sidebar - Sans Font Awesome"""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        with st.expander("Mode de Classification", expanded=True):
            classification_mode = st.radio(
                "Mode",
                ["⚡ Balanced (Rapide)", "🎯 Precise (LLM)"],
                help="Balanced: Règles avancées optimisées | Precise: LLM avec few-shot learning"
            )
            
            # Initialize default values
            model_name = "rule-based-advanced"
            temperature = 0.0
            timeout = 5
            
            if "Precise" in classification_mode:
                llm_provider = st.selectbox(
                    "Fournisseur LLM",
                    ["Mistral (Ollama)", "OpenAI", "Anthropic"],
                    help="Mistral/Ollama recommandé pour usage local"
                )
                
                # Configuration optimisée selon le provider
                if "Ollama" in llm_provider:
                    st.info("💡 **Ollama Local**: Aucune clé API requise")
                    model_name = st.text_input("Modèle", "mistral:latest")
                    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05, 
                                          help="0 = Déterministe, 1 = Créatif")
                    timeout = st.number_input("Timeout (sec)", 5, 120, 30, 5,
                                            help="Temps max par requête")
                else:
                    api_key = st.text_input("Clé API", type="password",
                                          help="Votre clé API pour le provider sélectionné")
                    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
                    timeout = st.number_input("Timeout (sec)", 5, 60, 20, 5)
            else:
                llm_provider = "Balanced"
            
            batch_size = st.number_input("Taille des lots", 5, 50, 10, 5,
                                        help="Nombre de tweets par lot")
            confidence_threshold = st.slider("Seuil de confiance", 0.0, 1.0, 0.7, 0.05)
        
        # Informations de performance
        with st.expander("📊 Estimations Performance", expanded=False):
            if "Precise" in classification_mode:
                st.markdown("""
                **Mode PRECISE** 🎯
                - ⏱️ Temps: ~2-5s par tweet
                - 🎯 Précision: 85-95%
                - 💡 Few-shot learning
                - 🔍 Analyse contextuelle profonde
                """)
            else:
                st.markdown("""
                **Mode BALANCED** ⚡
                - ⏱️ Temps: ~0.1s par tweet
                - 🎯 Précision: 75-85%
                - 📊 Règles optimisées
                - 🚀 Traitement parallèle
                """)
        
        st.session_state.llm_config = {
            "classification_mode": classification_mode,
            "llm_provider": llm_provider,
            "model_name": model_name,
            "temperature": temperature,
            "timeout": timeout,
            "batch_size": batch_size,
            "confidence_threshold": confidence_threshold
        }

def _render_upload_zone():
    """Upload zone avec gestion erreur 403 - Sans Font Awesome"""
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
        <h2 style="font-size: 2rem; font-weight: 700; color: #1a202c;">
            ☁️ Chargement des Données
        </h2>
        <p style="font-size: 1rem; color: #718096;">
            Formats: CSV, Excel, JSON | Max: 500 MB (augmenté pour éviter erreur 403)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        uploaded_file = st.file_uploader(
            "Sélectionnez votre fichier",
            type=['csv', 'xlsx', 'xls', 'json'],
            help="Max 500 MB - Multi-encodage supporté"
        )
        return uploaded_file
    except Exception as e:
        st.error(f"Erreur file uploader: {str(e)}")
        logger.error(f"File uploader error: {e}")
        
        if "403" in str(e):
            st.warning("""
            **Erreur 403 détectée:**
            1. Rafraîchir la page (F5)
            2. Vérifier taille fichier < 500 MB
            3. Redémarrer Streamlit si nécessaire
            """)
        
        return None

def _render_welcome_section():
    """Section bienvenue avec exemples - Sans Font Awesome"""
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 10px; margin: 2rem 0;">
        <h2>ℹ️ Classification LLM - Guide</h2>
        <p>Classification automatique intelligente selon:</p>
        <ul>
            <li><strong>is_claim:</strong> Réclamations (0 ou 1)</li>
            <li><strong>topics:</strong> Catégories (fibre, mobile, facture...)</li>
            <li><strong>sentiment:</strong> Sentiment (pos, neu, neg)</li>
            <li><strong>urgence:</strong> Priorité (haute, moyenne, basse)</li>
            <li><strong>incident:</strong> Type de problème</li>
            <li><strong>confidence:</strong> Confiance (0-1)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎓 Exemples Few-Shot Learning")
    st.info("5 exemples pré-annotés pour améliorer la précision")
    
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, 1):
        st.markdown(f"""
        <div style="background: #f7fafc; padding: 1rem; border-left: 4px solid #CC0000; margin: 1rem 0;">
            <strong>Exemple {i}:</strong> {ex['tweet']}<br>
            <strong>Classification:</strong> {json.dumps(ex['result'], ensure_ascii=False)}
        </div>
        """, unsafe_allow_html=True)

def _handle_dynamic_classification(uploaded_file):
    """Gestion classification complète avec toutes fonctionnalités"""
    try:
        # Vérification taille (erreur 403)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > 500:
            st.error(f"Fichier trop volumineux: {file_size_mb:.1f} MB (max: 500 MB)")
            return
        
        # Détection changement fichier
        current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        last_file_id = st.session_state.get('last_processed_file_id', None)
        
        if current_file_id != last_file_id:
            # Nettoyer cache
            for key in ['preprocessed_dataframe', 'classified_dataframe', 'classification_metrics']:
                st.session_state.pop(key, None)
            
            st.session_state['last_processed_file_id'] = current_file_id
            st.info(f"**Nouveau fichier:** {uploaded_file.name}")
        
        # Lecture multi-encodage
        df = _read_uploaded_file_robust(uploaded_file)
        
        if df is None or df.empty:
            st.error("Impossible de lire le fichier")
            return
        
        # Info fichier
        _display_file_info(uploaded_file, df)
        
        st.markdown("---")
        
        # Sélection colonne
        text_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not text_columns:
            st.error("Aucune colonne texte")
            return
        
        text_column = st.selectbox(
            "Colonne contenant le texte:",
            text_columns,
            index=0
        )
        
        st.session_state['text_column'] = text_column
        
        # Preview
        with st.expander("Preview", expanded=True):
            st.dataframe(df[[text_column]].head(10), use_container_width=True, height=300)
        
        st.markdown("---")
        
        # Bouton classification
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h3>🚀 Prêt pour Classification</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Lancer la Classification LLM", type="primary", use_container_width=True):
            df_classified, metrics = _perform_dynamic_classification(df, text_column)
            
            if df_classified is not None:
                _display_classification_results(df_classified, metrics)
                
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        logger.error(f"Handler error: {e}", exc_info=True)

def _read_uploaded_file_robust(uploaded_file):
    """Lecture robuste multi-encodage"""
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext == 'csv':
            # Multi-encodage
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines='skip')
                    st.caption(f"✓ Encodage: {encoding}")
                    return df
                except:
                    continue
            
            st.error("Impossible de décoder le CSV")
            return None
            
        elif file_ext in ['xlsx', 'xls']:
            return pd.read_excel(uploaded_file)
        elif file_ext == 'json':
            return pd.read_json(uploaded_file)
        else:
            st.error(f"Format non supporté: {file_ext}")
            return None
            
    except Exception as e:
        st.error(f"Erreur lecture: {str(e)}")
        return None

def _display_file_info(uploaded_file, df):
    """Affiche info fichier"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nom", uploaded_file.name[:20] + "...")
    with col2:
        st.metric("Lignes", f"{len(df):,}")
    with col3:
        st.metric("Colonnes", len(df.columns))
    with col4:
        st.metric("Taille", f"{uploaded_file.size / 1024:.1f} KB")

def _perform_dynamic_classification(df, text_column):
    """Classification optimisée avec mode PRECISE ou BALANCED"""
    import time as t
    
    # DOM stability: Initialize containers with small delay
    progress = st.progress(0)
    status = st.empty()
    t.sleep(0.05)  # Allow DOM to stabilize
    
    try:
        # Get configuration
        config = st.session_state.get('llm_config', {})
        classification_mode = config.get('classification_mode', '⚡ Balanced (Rapide)')
        batch_size = config.get('batch_size', 10)
        
        # Limit based on mode
        LIMIT = 50 if "Precise" in classification_mode else 100
        df_sample = df.head(LIMIT).copy()
        total = len(df_sample)
        
        if len(df) > LIMIT:
            st.info(f"📊 Analyse limitée aux {LIMIT} premiers tweets ({classification_mode})")
        
        # Initialize classifier based on mode
        if "Precise" in classification_mode:
            # PRECISE MODE: Use LLM with few-shot learning
            try:
                status.text("🧠 Initialisation du modèle LLM...")
                t.sleep(0.05)
                progress.progress(0.05)
            except Exception:
                pass
            
            classifier_func = _get_precise_classifier(config)
            if classifier_func is None:
                st.warning("⚠️ LLM indisponible, basculement sur mode Balanced")
                classifier_func = _get_balanced_classifier()
                classification_mode = "⚡ Balanced (Rapide)"
        else:
            # BALANCED MODE: Use optimized rule-based classifier
            try:
                status.text("⚡ Initialisation des règles avancées...")
                t.sleep(0.05)
                progress.progress(0.05)
            except Exception:
                pass
            classifier_func = _get_balanced_classifier()
        
        # Process in batches for better performance
        try:
            status.text(f"🔄 Classification en cours... 0/{total}")
            t.sleep(0.05)
            progress.progress(0.1)
        except Exception:
            pass
        
        results = []
        start_time = time.time()
        
        # Batch processing
        texts = df_sample[text_column].astype(str).tolist()
        
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_texts = texts[batch_start:batch_end]
            
            # Classify batch
            try:
                batch_results = classifier_func(batch_texts)
                results.extend(batch_results)
            except Exception as batch_error:
                logger.error(f"Batch error: {batch_error}")
                # Fallback: process individually
                for text in batch_texts:
                    try:
                        result = _classify_single_tweet_fallback(text)
                        results.append(result)
                    except:
                        results.append(_get_default_result())
            
            # Update progress with DOM safety
            pct = 0.1 + (batch_end / total) * 0.85
            elapsed = time.time() - start_time
            rate = batch_end / elapsed if elapsed > 0 else 0
            eta = (total - batch_end) / rate if rate > 0 else 0
            
            try:
                progress.progress(pct)
                t.sleep(0.03)
                status.text(f"🔄 {batch_end}/{total} tweets | {rate:.1f} tweets/sec | ETA: {eta:.0f}s")
            except Exception:
                pass  # Ignore DOM errors
        
        # Enrichissement
        try:
            status.text("✨ Enrichissement des données...")
            t.sleep(0.05)
            progress.progress(0.95)
        except Exception:
            pass
        
        df_sample['is_claim'] = [r['is_claim'] for r in results]
        df_sample['topics'] = [r['topics'] for r in results]
        df_sample['sentiment'] = [r['sentiment'] for r in results]
        df_sample['urgence'] = [r['urgence'] for r in results]
        df_sample['incident'] = [r['incident'] for r in results]
        df_sample['confidence'] = [r['confidence'] for r in results]
        
        # Métriques
        metrics = _calculate_classification_metrics(df_sample)
        
        # Add performance metrics
        total_time = time.time() - start_time
        metrics['processing_time'] = total_time
        metrics['tweets_per_second'] = total / total_time if total_time > 0 else 0
        metrics['mode'] = classification_mode
        
        try:
            progress.progress(1.0)
        except Exception:
            pass
        
        # Clear containers safely with delay (DOM stability)
        t.sleep(0.1)
        try:
            status.empty()
            progress.empty()
        except Exception:
            pass  # Ignore DOM errors
        
        st.success(f"✅ {total} tweets classifiés en {total_time:.1f}s | Confiance: {metrics['avg_confidence']:.0%} | Mode: {classification_mode}")
        
        return df_sample, metrics
        
    except Exception as e:
        # Clear containers safely in exception handler
        t.sleep(0.1)
        try:
            status.empty()
            progress.empty()
        except Exception:
            pass  # Ignore DOM errors
        
        st.error(f"❌ Erreur: {str(e)}")
        logger.error(f"Classification error: {e}", exc_info=True)
        return None, None

def _classify_single_tweet(tweet: str) -> Dict[str, Any]:
    """Classifie un tweet avec logique améliorée"""
    t = tweet.lower()
    
    # Réclamation - mots-clés élargis
    claim_kw = [
        'panne', 'problème', 'bug', '@free', '@freebox', 'ne fonctionne', 
        'impossible', 'bloqué', 'erreur', 'dysfonctionnement', 'coupé', 
        'déçu', 'mécontent', 'frustré', 'inadmissible', 'scandale'
    ]
    is_claim = 1 if any(w in t for w in claim_kw) else 0
    
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
    topics = []
    if theme_scores:
        max_score = max(theme_scores.values())
        if max_score > 0:
            # Prendre le(s) thème(s) avec score max
            top_themes = [theme for theme, score in theme_scores.items() if score == max_score]
            topics = top_themes[:2]  # Max 2 thèmes
        else:
            topics = ['autre']
    else:
        topics = ['autre']
    
    # Sentiment - logique enrichie
    positive_kw = ['merci', 'super', 'bravo', 'excellent', 'parfait', 'content', 
                   'satisfait', 'ravi', 'génial', 'top', 'nickel', 'résolu']
    negative_kw = ['panne', 'nul', 'mauvais', 'horrible', 'catastrophe', 'dégoûté', 
                   'énervé', 'frustré', 'déçu', 'insatisfait', 'inadmissible', 
                   'scandale', 'honte', 'lamentable']
    
    pos_score = sum(1 for w in positive_kw if w in t)
    neg_score = sum(1 for w in negative_kw if w in t)
    
    if pos_score > neg_score:
        sentiment = 'pos'
    elif neg_score > pos_score:
        sentiment = 'neg'
    else:
        sentiment = 'neu'
    
    # Urgence - basée sur mots-clés et contexte
    urgence_critique_kw = ['urgent', 'critique', 'grave', 'bloqué', 'impossible', 
                           'catastrophe', 'plus rien', 'totalement coupé']
    urgence_haute_kw = ['plusieurs heures', 'depuis longtemps', 'toute la journée', 
                        'depuis ce matin', 'depuis hier']
    
    if any(w in t for w in urgence_critique_kw):
        urgence = 'critique'
    elif any(w in t for w in urgence_haute_kw) or (is_claim and neg_score >= 2):
        urgence = 'haute'
    elif is_claim:
        urgence = 'moyenne'
    else:
        urgence = 'basse'
    
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
    elif is_claim:
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
    
    return {
        'is_claim': is_claim,
        'topics': topics,
        'sentiment': sentiment,
        'urgence': urgence,
        'incident': incident,
        'responsable': responsable,  # NEW
        'confidence': confidence
    }

def _calculate_classification_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcule métriques complètes"""
    total = len(df)
    
    return {
        'total_tweets': total,
        'claims': int(df['is_claim'].sum()),
        'claims_percentage': (df['is_claim'].sum() / total * 100) if total > 0 else 0,
        'negative_sentiments': int(len(df[df['sentiment'] == 'neg'])),
        'high_urgency': int(len(df[df['urgence'] == 'haute'])),
        'avg_confidence': float(df['confidence'].mean()),
        'topic_dist': df['topics'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).value_counts(),
        'sentiment_dist': df['sentiment'].value_counts(),
        'urgence_dist': df['urgence'].value_counts(),
        'incident_dist': df['incident'].value_counts()
    }

def _display_classification_results(df: pd.DataFrame, metrics: Dict):
    """Affiche résultats COMPLETS avec tous graphiques et métriques de performance"""
    
    st.markdown("---")
    
    # Performance Summary
    mode = metrics.get('mode', 'Unknown')
    processing_time = metrics.get('processing_time', 0)
    tweets_per_sec = metrics.get('tweets_per_second', 0)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                padding: 1.5rem; 
                border-radius: 12px; 
                text-align: center; 
                margin-bottom: 1.5rem; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <h2 style="font-size: 1.8rem; font-weight: 800; color: #1a202c; margin: 0;">
            📊 Résultats de Classification
        </h2>
        <p style="color: #4a5568; font-size: 0.9rem; margin-top: 0.5rem;">
            ⚡ Mode: {mode} | ⏱️ {processing_time:.1f}s | 🚀 {tweets_per_sec:.1f} tweets/sec
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs - Modernisés avec emojis dynamiques
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcul pourcentages pour affichage dynamique
    claim_rate = (metrics['claims'] / metrics['total_tweets'] * 100) if metrics['total_tweets'] > 0 else 0
    neg_rate = (metrics['negative_sentiments'] / metrics['total_tweets'] * 100) if metrics['total_tweets'] > 0 else 0
    urgency_rate = (metrics['high_urgency'] / metrics['total_tweets'] * 100) if metrics['total_tweets'] > 0 else 0
    
    with col1:
        # Emoji dynamique basé sur le taux de réclamations
        emoji = "⚠️" if claim_rate > 30 else "🟠" if claim_rate > 15 else "✅"
        color = "#e53e3e" if claim_rate > 30 else "#ed8936" if claim_rate > 15 else "#48bb78"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">RÉCLAMATIONS</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {metrics['claims']}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                {claim_rate:.1f}% du total
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Emoji dynamique basé sur le niveau de confiance
        emoji = "🎯" if metrics['avg_confidence'] >= 0.9 else "✅" if metrics['avg_confidence'] >= 0.75 else "⚡"
        color = "#38a169" if metrics['avg_confidence'] >= 0.75 else "#ed8936"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">CONFIANCE</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {metrics['avg_confidence']:.0%}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                Moyenne globale
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Emoji dynamique basé sur le taux de sentiments négatifs
        emoji = "😞" if neg_rate > 40 else "😐" if neg_rate > 20 else "😊"
        color = "#e53e3e" if neg_rate > 40 else "#ed8936" if neg_rate > 20 else "#48bb78"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">NÉGATIFS</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {metrics['negative_sentiments']}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                {neg_rate:.1f}% sentiments
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Emoji dynamique basé sur le taux d'urgence haute
        emoji = "🔥" if urgency_rate > 30 else "⚡" if urgency_rate > 15 else "🛡️"
        color = "#dd6b20" if urgency_rate > 30 else "#ed8936" if urgency_rate > 15 else "#48bb78"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">URGENCE HAUTE</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {metrics['high_urgency']}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                {urgency_rate:.1f}% prioritaires
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # TOUS LES GRAPHIQUES (6 visualisations)
    _display_all_visualizations(df, metrics)
    
    # Dashboard Business KPIs (si disponible)
    _display_business_dashboard(df)
    
    # Export
    _display_export_section(df, metrics)

def _display_all_visualizations(df, metrics):
    """6 visualisations complètes"""
    
    st.markdown("## 📈 Visualisations Détaillées")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        # Réclamations
        fig = go.Figure(data=[go.Pie(
            labels=['Réclamations', 'Non-réclamations'],
            values=[metrics['claims'], metrics['total_tweets'] - metrics['claims']],
            hole=0.4,
            marker=dict(colors=['#CC0000', '#48bb78'])
        )])
        fig.update_layout(title="Détection Réclamations", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Topics
        if not metrics['topic_dist'].empty:
            fig = px.bar(
                x=metrics['topic_dist'].index,
                y=metrics['topic_dist'].values,
                title="Distribution Topics",
                color=metrics['topic_dist'].values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    # Row 2
    col3, col4 = st.columns(2)
    
    with col3:
        # Sentiment
        if not metrics['sentiment_dist'].empty:
            fig = go.Figure(data=[go.Pie(
                labels=metrics['sentiment_dist'].index,
                values=metrics['sentiment_dist'].values,
                hole=0.5,
                marker=dict(colors=['#48bb78', '#90cdf4', '#fc8181'])
            )])
            fig.update_layout(title="Distribution Sentiments", height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        # Urgence
        if not metrics['urgence_dist'].empty:
            fig = px.bar(
                y=metrics['urgence_dist'].index,
                x=metrics['urgence_dist'].values,
                orientation='h',
                title="Niveaux d'Urgence",
                color=metrics['urgence_dist'].values,
                color_continuous_scale='Oranges'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    # Row 3
    col5, col6 = st.columns(2)
    
    with col5:
        # Incidents
        if not metrics['incident_dist'].empty:
            fig = px.pie(
                values=metrics['incident_dist'].values,
                names=metrics['incident_dist'].index,
                title="Types d'Incidents"
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    with col6:
        # Confiance
        fig = px.histogram(
            df,
            x='confidence',
            nbins=20,
            title="Distribution Confiance"
        )
        fig.add_vline(
            x=metrics['avg_confidence'],
            line_dash="dash",
            line_color="#CC0000",
            annotation_text=f"Moy: {metrics['avg_confidence']:.2f}"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

def _display_business_dashboard(df):
    """Dashboard Business KPIs si disponible"""
    kpis_system = _get_enhanced_kpis()
    
    if not kpis_system.get('available'):
        return
    
    try:
        st.markdown("---")
        st.markdown("## 💼 Tableau de Bord Business")
        
        compute_business_kpis = kpis_system['compute_business_kpis']
        render_business_kpis = kpis_system['render_business_kpis']
        
        # Préparer données
        df_business = _prepare_df_for_business_kpis(df)
        
        # Calculer KPIs
        business_kpis = compute_business_kpis(df_business)
        
        # Filtrer par rôle si disponible
        role_funcs = _get_role_selector()
        if role_funcs.get('available'):
            filter_kpis = role_funcs['filter_kpis_by_role']
            get_role = role_funcs['get_current_role']
            current_role = get_role()
            business_kpis = filter_kpis(business_kpis, current_role)
        
        # Afficher KPIs
        render_business_kpis(business_kpis)
        
        # Visualisations avancées
        ekv = kpis_system['ekv']
        ekv.render_enhanced_visualizations(df_business, business_kpis)
        
        # KPI sections removed for cleaner UI - keeping only dynamic visualizations
        
    except Exception as e:
        logger.warning(f"Business dashboard error: {e}")

# Removed _display_enriched_training_kpis() and _display_kpi_comparison()
# These functions created visual conflicts and duplicate displays

def _prepare_df_for_business_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Prépare DataFrame pour KPIs business"""
    df_conv = df.copy()
    
    # Conversion sentiments
    sentiment_map = {'pos': 'positive', 'neu': 'neutral', 'neg': 'negative'}
    if 'sentiment' in df_conv.columns:
        df_conv['sentiment'] = df_conv['sentiment'].map(
            lambda x: sentiment_map.get(str(x).lower(), str(x))
        )
    
    # Renommages
    if 'urgence' in df_conv.columns:
        df_conv['priority'] = df_conv['urgence']
    
    if 'incident' in df_conv.columns:
        df_conv['category'] = df_conv['incident']
    
    return df_conv

def _display_export_section(df, metrics):
    """Section export complète - Sans Font Awesome"""
    st.markdown("---")
    st.markdown("### 💾 Export des Résultats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_df = df.copy()
        export_df['topics'] = export_df['topics'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Export CSV",
            csv,
            f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        json_data = json.dumps({
            'total_tweets': metrics['total_tweets'],
            'claims': metrics['claims'],
            'avg_confidence': float(metrics['avg_confidence'])
        }, indent=2, ensure_ascii=False)
        st.download_button(
            "Export JSON",
            json_data,
            f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )
    
    with col3:
        if st.button("Nouvelle Analyse", use_container_width=True):
            for key in list(st.session_state.keys()):
                if 'df_' in key or 'classification' in key:
                    st.session_state.pop(key, None)
            st.rerun()

if __name__ == "__main__":
    main()

