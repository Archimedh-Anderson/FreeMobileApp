"""
Module de Calcul de KPIs et Visualisations Avancées - FreeMobilaChat
====================================================================

Module spécialisé dans le calcul dynamique d'indicateurs clés de performance (KPIs)
et la création de visualisations interactives pour l'analyse de sentiment client.

Fonctionnalités:
- Calculs 100% dynamiques (recalculés à chaque exécution, pas de cache)
- Optimisation vectorielle avec pandas/numpy pour hautes performances
- Support multi-formats (français/anglais, numérique/texte)
- Visualisations interactives avec Plotly
- Interface moderne avec design cards premium
"""

# Imports des bibliothèques de traitement et visualisation de données
import pandas as pd  # Manipulation de DataFrames et calculs vectorisés
import numpy as np  # Calculs mathématiques optimisés et agrégations
import plotly.express as px  # Graphiques interactifs haut niveau
import plotly.graph_objects as go  # Graphiques interactifs bas niveau (contrôle fin)
from plotly.subplots import make_subplots  # Création de tableaux de bord multi-graphiques
from typing import Dict, Any, List, Tuple  # Annotations de types pour clarté
import streamlit as st  # Interface utilisateur et composants de rendu
from datetime import datetime  # Gestion des horodatages pour traçabilité

# Palette de couleurs Free Mobile (identité visuelle de la marque)
COLORS = {
    'primary': '#CC0000',  # Rouge principal Free Mobile (couleur signature)
    'secondary': '#8B0000',  # Rouge foncé pour contraste
    'accent': '#FF6B6B',  # Rouge clair pour accents et highlights
    'success': '#28a745',  # Vert pour indicateurs positifs (satisfaction, succès)
    'warning': '#ffc107',  # Jaune/orange pour avertissements et alertes moyennes
    'danger': '#dc3545',  # Rouge vif pour alertes critiques et erreurs
    'info': '#17a2b8',  # Bleu pour informations neutres
    'positive': '#28a745',  # Vert pour sentiments positifs
    'neutral': '#6c757d',  # Gris pour sentiments neutres
    'negative': '#dc3545'  # Rouge pour sentiments négatifs
}

def compute_business_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs business de manière 100% DYNAMIQUE avec optimisations de performance
    
    GARANTIE DE DYNAMISME:
    - Pas de cache entre les appels
    - Pas de variables globales
    - Calculs basés uniquement sur df
    - Chaque fichier uploadé = nouveaux KPIs
    
    OPTIMISATIONS DE PERFORMANCE:
    - Calculs vectorisés avec pandas/numpy
    - Évite les boucles explicites
    - Réutilise les calculs intermédiaires
    - Minimise les conversions de types
    
    Args:
        df: DataFrame avec les tweets analysés (données du fichier actuel)
        
    Returns:
        Dictionnaire avec les KPIs business recalculés dynamiquement
    """
    kpis = {}
    total_tweets = len(df)
    
    # Éviter les divisions par zéro
    if total_tweets == 0:
        return kpis
    
    # 1. Claim Rate (Taux de réclamations) - OPTIMISÉ ET ROBUSTE
    claims_count = 0
    
    # Vérifier multiple colonnes possibles
    if 'is_claim' in df.columns:
        # Conversion vectorisée - supporter 'oui'/'non' et 1/0
        claims_array = df['is_claim'].astype(str).str.lower()
        claims_count = int(claims_array.isin(['oui', 'yes', '1', 'true']).sum())
    elif 'category' in df.columns:
        # Vectorisation avec str.contains
        claims_mask = df['category'].astype(str).str.contains('réclamation|claim|complaint', case=False, na=False)
        claims_count = int(claims_mask.sum())
    elif 'incident' in df.columns:
        # Support pour colonne 'incident'
        claims_mask = df['incident'].astype(str).str.contains('réclamation|claim|complaint', case=False, na=False)
        claims_count = int(claims_mask.sum())
    
    kpis['claim_rate'] = {
        'value': (claims_count / total_tweets * 100) if total_tweets > 0 else 0.0,
        'count': claims_count,
        'total': total_tweets
    }
    
    # 2. Thematic Distribution (Distribution thématique) - OPTIMISÉ
    # Prioriser les colonnes enrichies du nouveau dataset
    if 'Thème principal' in df.columns:
        theme_dist = df['Thème principal'].value_counts()
        kpis['thematic_distribution'] = {
            'categories': theme_dist.to_dict(),
            'top_category': theme_dist.index[0] if len(theme_dist) > 0 else 'N/A',
            'count': len(theme_dist)
        }
        # Ajouter la confiance moyenne si disponible
        if 'theme_confidence' in df.columns:
            kpis['thematic_distribution']['avg_confidence'] = float(df['theme_confidence'].mean())
    elif 'category' in df.columns:
        theme_dist = df['category'].value_counts()
        kpis['thematic_distribution'] = {
            'categories': theme_dist.to_dict(),
            'top_category': theme_dist.index[0] if len(theme_dist) > 0 else 'N/A',
            'count': len(theme_dist)
        }
    elif 'incident' in df.columns:
        theme_dist = df['incident'].value_counts()
        kpis['thematic_distribution'] = {
            'categories': theme_dist.to_dict(),
            'top_category': theme_dist.index[0] if len(theme_dist) > 0 else 'N/A',
            'count': len(theme_dist)
        }
    elif 'theme' in df.columns:
        theme_dist = df['theme'].value_counts()
        kpis['thematic_distribution'] = {
            'categories': theme_dist.to_dict(),
            'top_category': theme_dist.index[0] if len(theme_dist) > 0 else 'N/A',
            'count': len(theme_dist)
        }
    
    # 3. Customer Satisfaction Index (Indice de satisfaction) - OPTIMISÉ ET ROBUSTE
    if 'sentiment' in df.columns:
        # Normaliser les sentiments pour supporter différents formats
        sentiment_normalized = df['sentiment'].astype(str).str.lower().str.strip()
        
        # Détecter tous les formats possibles
        positive_mask = sentiment_normalized.isin(['positive', 'positif', 'pos', '1', 'good', 'happy'])
        neutral_mask = sentiment_normalized.isin(['neutral', 'neutre', 'neu', '0', 'ok'])
        negative_mask = sentiment_normalized.isin(['negative', 'négatif', 'negatif', 'neg', '-1', 'bad', 'angry'])
        
        positive = int(positive_mask.sum())
        neutral = int(neutral_mask.sum())
        negative = int(negative_mask.sum())
        
        # Calcul de l'indice de satisfaction (scale 0-100)
        # Formule: ((positif - négatif) / total) * 50 + 50
        satisfaction_index = ((positive - negative) / total_tweets * 50 + 50) if total_tweets > 0 else 50.0
        
        kpis['satisfaction_index'] = {
            'value': satisfaction_index,
            'positive_count': positive,
            'neutral_count': neutral,
            'negative_count': negative,
            'positive_pct': (positive / total_tweets * 100) if total_tweets > 0 else 0.0,
            'neutral_pct': (neutral / total_tweets * 100) if total_tweets > 0 else 0.0,
            'negative_pct': (negative / total_tweets * 100) if total_tweets > 0 else 0.0
        }
    
    # 4. Urgency Rate (Taux d'urgence) - OPTIMISÉ ET ROBUSTE
    critical = 0
    high = 0
    
    if 'priority' in df.columns:
        priority_normalized = df['priority'].astype(str).str.lower().fillna('')
        critical_mask = priority_normalized.str.contains('critique|critical|urgent|très haute', regex=True, na=False)
        high_mask = priority_normalized.str.contains('haute|high|élevée', regex=True, na=False) & ~critical_mask
        critical = int(critical_mask.sum())
        high = int(high_mask.sum())
    elif 'urgence' in df.columns:
        urgence_normalized = df['urgence'].astype(str).str.lower().fillna('')
        critical_mask = urgence_normalized.str.contains('critique|critical|urgent|très haute', regex=True, na=False)
        high_mask = urgence_normalized.str.contains('haute|high|élevée', regex=True, na=False) & ~critical_mask
        critical = int(critical_mask.sum())
        high = int(high_mask.sum())
    elif 'is_urgent' in df.columns:
        urgent_array = df['is_urgent'].astype(str).str.lower()
        critical = int(urgent_array.isin(['oui', 'yes', '1', 'true']).sum())
        high = 0
    
    urgent_total = critical + high
    kpis['urgency_rate'] = {
        'critical_count': critical,
        'high_count': high,
        'urgent_total': urgent_total,
        'urgency_pct': (urgent_total / total_tweets * 100) if total_tweets > 0 else 0.0
    }
    
    # 5. Average Confidence Score (Score de confiance moyen) - OPTIMISÉ
    if 'confidence' in df.columns:
        confidence_numeric = pd.to_numeric(df['confidence'], errors='coerce')
        confidence_clean = confidence_numeric.dropna()
        
        if len(confidence_clean) > 0:
            kpis['confidence_score'] = {
                'average': float(confidence_clean.mean()),
                'min': float(confidence_clean.min()),
                'max': float(confidence_clean.max()),
                'std': float(confidence_clean.std()) if len(confidence_clean) > 1 else 0.0
            }
        else:
            kpis['confidence_score'] = {'average': 0, 'min': 0, 'max': 0, 'std': 0}
    elif 'sentiment_score' in df.columns:
        sentiment_numeric = pd.to_numeric(df['sentiment_score'], errors='coerce').dropna()
        
        if len(sentiment_numeric) > 0:
            kpis['confidence_score'] = {
                'average': float(abs(sentiment_numeric.mean())),
                'min': float(sentiment_numeric.min()),
                'max': float(sentiment_numeric.max()),
                'std': float(sentiment_numeric.std()) if len(sentiment_numeric) > 1 else 0.0
            }
        else:
            kpis['confidence_score'] = {'average': 0, 'min': 0, 'max': 0, 'std': 0}
    
    # 6. Incident Distribution (Distribution des incidents) - NOUVEAU POUR DATASET ENRICHI
    if 'Incident principal' in df.columns:
        incident_dist = df['Incident principal'].value_counts()
        kpis['incident_distribution'] = {
            'categories': incident_dist.to_dict(),
            'top_incident': incident_dist.index[0] if len(incident_dist) > 0 else 'aucun',
            'top_incident_count': int(incident_dist.iloc[0]) if len(incident_dist) > 0 else 0,
            'top_incident_pct': (incident_dist.iloc[0] / total_tweets * 100) if len(incident_dist) > 0 else 0.0,
            'count': len(incident_dist)
        }
        # Ajouter la confiance moyenne si disponible
        if 'incident_confidence' in df.columns:
            kpis['incident_distribution']['avg_confidence'] = float(df['incident_confidence'].mean())
        
        # Ajouter la distribution des responsables si disponible
        if 'incident_responsable' in df.columns:
            responsable_dist = df['incident_responsable'].value_counts()
            kpis['responsable_distribution'] = {
                'categories': responsable_dist.to_dict(),
                'top_responsable': responsable_dist.index[0] if len(responsable_dist) > 0 else 'N/A',
                'count': len(responsable_dist)
            }
    
    # 7. Réclamations améliorées avec confiance - NOUVEAU POUR DATASET ENRICHI
    if 'réclamations' in df.columns:
        reclamations_dist = df['réclamations'].value_counts()
        oui_count = int(reclamations_dist.get('Oui', reclamations_dist.get('oui', 0)))
        non_count = int(reclamations_dist.get('Non', reclamations_dist.get('non', 0)))
        
        kpis['reclamations_enriched'] = {
            'oui_count': oui_count,
            'non_count': non_count,
            'oui_pct': (oui_count / total_tweets * 100) if total_tweets > 0 else 0.0,
            'non_pct': (non_count / total_tweets * 100) if total_tweets > 0 else 0.0
        }
        
        # Ajouter la confiance moyenne si disponible
        if 'reclamation_confidence' in df.columns:
            kpis['reclamations_enriched']['avg_confidence'] = float(df['reclamation_confidence'].mean())
    
    return kpis


def render_business_kpis(kpis: Dict[str, Any]):
    """
    Affiche les KPIs business dans une interface moderne et professionnelle OPTIMISÉE
    
    AMÉLIORATIONS:
    - Design moderne avec cards premium
    - Emojis Unicode natifs (pas de Font Awesome)
    - Indicateurs visuels de performance (couleurs intelligentes)
    - Layout responsive et épuré
    - Typographie améliorée pour la lisibilité
    - Calculs 100% dynamiques
    
    Args:
        kpis: Dictionnaire des KPIs calculés par compute_business_kpis()
    """
    # Titre de section moderne avec design premium
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                padding: 2rem; 
                border-radius: 12px; 
                text-align: center; 
                margin: 1.5rem 0; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <h2 style="font-size: 1.9rem; font-weight: 800; color: #1a202c; margin: 0; letter-spacing: -0.5px;">
            📊 Tableau de Bord Business - KPIs Avancés
        </h2>
        <p style="color: #4a5568; font-size: 0.95rem; margin-top: 0.75rem; font-weight: 500;">
            🔄 Mise à jour en temps réel • Calculs dynamiques
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ligne de 5 KPIs avec cards modernes
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    
    # KPI 1: Taux de Réclamations - Design Moderne
    with col1:
        if 'claim_rate' in kpis:
            claim_rate = kpis['claim_rate']['value']
            claim_count = kpis['claim_rate']['count']
            
            # Couleur dynamique basée sur le taux
            color = "#e53e3e" if claim_rate > 30 else "#ed8936" if claim_rate > 15 else "#48bb78"
            emoji = "⚠️" if claim_rate > 30 else "🟠" if claim_rate > 15 else "✅"
            
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
                    {claim_rate:.1f}<span style="font-size: 1.2rem; color: #718096;">%</span>
                </div>
                <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                    {claim_count} tweets
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Réclamations", "N/A")
    
    # KPI 2: Indice de Satisfaction - Design Premium
    with col2:
        if 'satisfaction_index' in kpis:
            satisfaction = kpis['satisfaction_index']['value']
            
            # Couleur et icône dynamiques
            if satisfaction > 60:
                color = "#48bb78"
                icon = "fa-smile"
                status = "Élevé"
            elif satisfaction > 40:
                color = "#4299e1"
                icon = "fa-meh"
                status = "Moyen"
            else:
                color = "#e53e3e"
                icon = "fa-frown"
                status = "Faible"
            
            st.markdown(f"""
            <div style="background: white; 
                        padding: 1.25rem; 
                        border-radius: 10px; 
                        border-left: 4px solid {color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        height: 140px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <i class="fas {icon}" style="color: {color}; font-size: 1.2rem; margin-right: 0.5rem;"></i>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">Satisfaction</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                    {satisfaction:.0f}<span style="font-size: 1.2rem; color: #718096;">/100</span>
                </div>
                <div style="font-size: 0.8rem; color: {color}; font-weight: 600;">
                    <i class="fas fa-circle" style="font-size: 0.5rem;"></i> {status}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Satisfaction", "N/A")
    
    # KPI 3: Taux d'Urgence - Design Critique
    with col3:
        if 'urgency_rate' in kpis:
            urgency = kpis['urgency_rate']['urgency_pct']
            urgent_total = kpis['urgency_rate']['urgent_total']
            
            # Couleur dynamique urgence
            color = "#e53e3e" if urgency > 20 else "#ed8936" if urgency > 10 else "#48bb78"
            
            st.markdown(f"""
            <div style="background: white; 
                        padding: 1.25rem; 
                        border-radius: 10px; 
                        border-left: 4px solid {color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        height: 140px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <i class="fas fa-bolt" style="color: {color}; font-size: 1.2rem; margin-right: 0.5rem;"></i>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">Urgence</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                    {urgency:.1f}<span style="font-size: 1.2rem; color: #718096;">%</span>
                </div>
                <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                    <i class="fas fa-fire" style="font-size: 0.7rem;"></i> {urgent_total} cas
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Urgence", "N/A")
    
    # KPI 4: Confiance Moyenne - Design Précision
    with col4:
        if 'confidence_score' in kpis:
            confidence = kpis['confidence_score']['average']
            max_conf = kpis['confidence_score']['max']
            
            # Couleur basée sur la confiance
            color = "#48bb78" if confidence > 0.8 else "#4299e1" if confidence > 0.6 else "#ed8936"
            
            st.markdown(f"""
            <div style="background: white; 
                        padding: 1.25rem; 
                        border-radius: 10px; 
                        border-left: 4px solid {color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        height: 140px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <i class="fas fa-shield-alt" style="color: {color}; font-size: 1.2rem; margin-right: 0.5rem;"></i>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">Confiance</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                    {confidence:.2f}
                </div>
                <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                    <i class="fas fa-arrow-up" style="font-size: 0.7rem;"></i> Max: {max_conf:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Confiance", "N/A")
    
    # KPI 5: Thèmes Identifiés - Design Catégories
    with col5:
        if 'thematic_distribution' in kpis:
            theme_count = kpis['thematic_distribution']['count']
            top_theme = kpis['thematic_distribution']['top_category']
            
            # Tronquer proprement
            top_theme_display = top_theme[:12] + "..." if len(top_theme) > 12 else top_theme
            
            st.markdown(f"""
            <div style="background: white; 
                        padding: 1.25rem; 
                        border-radius: 10px; 
                        border-left: 4px solid #667eea;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        height: 140px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <i class="fas fa-tags" style="color: #667eea; font-size: 1.2rem; margin-right: 0.5rem;"></i>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">Thèmes</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                    {theme_count}
                </div>
                <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                    <i class="fas fa-star" style="font-size: 0.7rem; color: #ffd700;"></i> {top_theme_display}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Thèmes", "N/A")


def create_sentiment_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Crée un graphique moderne de distribution des sentiments OPTIMISÉ
    
    OPTIMISATIONS:
    - Calculs vectorisés
    - Design moderne avec gradients
    - Annotations intelligentes
    - Performance améliorée
    
    Args:
        df: DataFrame avec colonne 'sentiment'
        
    Returns:
        Figure Plotly optimisée
    """
    if 'sentiment' not in df.columns:
        return None
    
    # Calcul optimisé avec value_counts (déjà vectorisé)
    sentiment_counts = df['sentiment'].value_counts()
    
    if len(sentiment_counts) == 0:
        return None
    
    # Mapping couleurs optimisé avec dict.get()
    color_map = {
        'positive': COLORS['positive'],
        'positif': COLORS['positive'],
        'pos': COLORS['positive'],
        'neutral': COLORS['neutral'],
        'neutre': COLORS['neutral'],
        'neu': COLORS['neutral'],
        'negative': COLORS['negative'],
        'négatif': COLORS['negative'],
        'negatif': COLORS['negative'],
        'neg': COLORS['negative']
    }
    
    # List comprehension optimisée
    colors = [color_map.get(str(sent).lower(), COLORS['info']) for sent in sentiment_counts.index]
    
    # Création du graphique avec design moderne
    fig = go.Figure(data=[
        go.Pie(
            labels=[str(label).capitalize() for label in sentiment_counts.index],
            values=sentiment_counts.values,
            hole=0.45,  # Donut plus moderne
            marker=dict(
                colors=colors,
                line=dict(color='white', width=2)  # Séparation blanche
            ),
            textinfo='label+percent',
            textfont=dict(size=13, family="Arial, sans-serif", color="white"),
            textposition='inside',
            insidetextorientation='horizontal',
            hovertemplate="<b>%{label}</b><br>" +
                         "Tweets: %{value}<br>" +
                         "Pourcentage: %{percent}<br>" +
                         "<extra></extra>",
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
    ])
    
    # Layout moderne et épuré
    fig.update_layout(
        title=dict(
            text="<b>Distribution des Sentiments</b>",
            font=dict(size=18, family="Arial, sans-serif", color="#1a202c"),
            x=0.5,
            xanchor='center'
        ),
        height=420,
        template="plotly_white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1
        ),
        margin=dict(t=60, b=60, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_time_series_chart(df: pd.DataFrame, date_col: str = 'date') -> go.Figure:
    """
    Crée un graphique temporel multi-lignes
    
    Args:
        df: DataFrame avec colonne de date
        date_col: Nom de la colonne de date
        
    Returns:
        Figure Plotly
    """
    if date_col not in df.columns:
        # Essayer d'autres noms
        possible_names = ['created_at', 'timestamp', 'datetime', 'Date']
        for name in possible_names:
            if name in df.columns:
                date_col = name
                break
        else:
            return None
    
    # Convertir en datetime
    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])
        
        if len(df_copy) == 0:
            return None
        
        # Grouper par jour
        df_copy['date_only'] = df_copy[date_col].dt.date
        daily_counts = df_copy.groupby('date_only').size().reset_index(name='count')
        
        # Si on a la colonne sentiment, ajouter les courbes par sentiment
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_counts['date_only'],
            y=daily_counts['count'],
            mode='lines+markers',
            name='Volume Total',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=6)
        ))
        
        if 'sentiment' in df_copy.columns:
            for sentiment in df_copy['sentiment'].unique():
                if pd.notna(sentiment):
                    sentiment_data = df_copy[df_copy['sentiment'] == sentiment].groupby('date_only').size().reset_index(name='count')
                    
                    color = COLORS.get(sentiment.lower(), COLORS['info'])
                    
                    fig.add_trace(go.Scatter(
                        x=sentiment_data['date_only'],
                        y=sentiment_data['count'],
                        mode='lines',
                        name=f'Sentiment: {sentiment}',
                        line=dict(color=color, width=2),
                        opacity=0.7
                    ))
        
        fig.update_layout(
            title="<b>Évolution Temporelle du Volume de Tweets</b>",
            xaxis_title="Date",
            yaxis_title="Nombre de Tweets",
            title_font_size=18,
            height=450,
            template="plotly_white",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erreur lors de la création du graphique temporel: {e}")
        return None


def create_activity_heatmap(df: pd.DataFrame, date_col: str = 'date') -> go.Figure:
    """
    Crée une heatmap d'activité par heure et jour
    
    Args:
        df: DataFrame avec colonne de date
        date_col: Nom de la colonne de date
        
    Returns:
        Figure Plotly
    """
    if date_col not in df.columns:
        possible_names = ['created_at', 'timestamp', 'datetime', 'Date']
        for name in possible_names:
            if name in df.columns:
                date_col = name
                break
        else:
            return None
    
    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])
        
        if len(df_copy) == 0:
            return None
        
        # Extraire heure et jour de la semaine
        df_copy['hour'] = df_copy[date_col].dt.hour
        df_copy['day_of_week'] = df_copy[date_col].dt.day_name()
        
        # Créer une matrice heure x jour
        heatmap_data = df_copy.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        
        # Pivoter pour avoir le bon format
        heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # Ordonner les jours
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Reds',
            hovertemplate='Jour: %{y}<br>Heure: %{x}h<br>Tweets: %{z}<extra></extra>',
            colorbar=dict(title="Nombre de Tweets")
        ))
        
        fig.update_layout(
            title="<b>Heatmap d'Activité (Jour × Heure)</b>",
            xaxis_title="Heure de la journée",
            yaxis_title="Jour de la semaine",
            title_font_size=18,
            height=400,
            template="plotly_white"
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erreur lors de la création de la heatmap: {e}")
        return None


def create_category_comparison_chart(df: pd.DataFrame, category_col: str = 'category') -> go.Figure:
    """
    Crée un graphique en barres verticales pour les top 10 thèmes
    Correspond exactement au screenshot fourni
    
    Args:
        df: DataFrame avec colonne de catégorie
        category_col: Nom de la colonne de catégorie
        
    Returns:
        Figure Plotly avec barres verticales gradientées
    """
    # Prioriser la colonne enrichie "Thème principal"
    actual_col = None
    if 'Thème principal' in df.columns:
        actual_col = 'Thème principal'
    elif category_col in df.columns:
        actual_col = category_col
    elif 'category' in df.columns:
        actual_col = 'category'
    elif 'incident' in df.columns:
        actual_col = 'incident'
    elif 'theme' in df.columns:
        actual_col = 'theme'
    elif 'topics' in df.columns:
        actual_col = 'topics'
    
    if actual_col is None:
        return None
    
    # Top 10 thèmes triés par fréquence décroissante
    category_counts = df[actual_col].value_counts().head(10)
    
    # Calculer les pourcentages
    total_tweets = len(df)
    percentages = (category_counts / total_tweets * 100).round(2)
    
    # Palette de couleurs gradient (rouge foncé -> clair comme le screenshot)
    # Du plus foncé au plus clair selon la fréquence
    colors = [
        '#8B0000',  # Dark red (le plus fréquent)
        '#CD5C5C',  # Indian red
        '#F08080',  # Light coral
        '#FFB6C1',  # Light pink
        '#FFC0CB',  # Pink
        '#FFD1DC',  # Pale pink
        '#FFE4E1',  # Misty rose
        '#FFF0F5',  # Lavender blush
        '#FFF5EE',  # Seashell
        '#FFFAF0'   # Floral white (le moins fréquent)
    ]
    
    # Utiliser seulement le nombre de couleurs nécessaire
    color_list = colors[:len(category_counts)]
    
    # Créer les labels avec pourcentages
    text_labels = [f"{count}<br>({pct}%)" for count, pct in zip(category_counts.values, percentages)]
    
    fig = go.Figure(data=[
        go.Bar(
            x=category_counts.index,
            y=category_counts.values,
            marker=dict(
                color=color_list,
                line=dict(color='white', width=1)
            ),
            text=text_labels,
            textposition='outside',
            textfont=dict(size=11, color='#1a202c', family='Arial'),
            hovertemplate="<b>%{x}</b><br>Nombre: %{y:,}<br>Pourcentage: %{customdata:.2f}%<extra></extra>",
            customdata=percentages,
            showlegend=False
        )
    ])
    
    # Ajouter une colorbar légende à droite
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            colorscale=[[0, '#8B0000'], [1, '#FFFAF0']],
            showscale=True,
            cmin=0,
            cmax=category_counts.max(),
            colorbar=dict(
                title="Nombre",
                titleside="right",
                tickmode="linear",
                tick0=0,
                dtick=500,
                thickness=15,
                len=0.7,
                x=1.15
            )
        ),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Titre descriptif
    if actual_col == 'Thème principal':
        title_text = "<b>Top 10 Thème principal</b>"
    else:
        title_text = f"<b>Top 10 {actual_col}</b>"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=16, family="Arial, sans-serif", color="#1a202c"),
            x=0,
            xanchor='left',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title="Thème principal",
            showgrid=False,
            titlefont=dict(size=12, color='#4a5568'),
            tickangle=-45,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title="Nombre de Tweets",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            titlefont=dict(size=12, color='#4a5568'),
            range=[0, category_counts.max() * 1.15]  # Extra space for labels
        ),
        height=450,
        template="plotly_white",
        margin=dict(l=60, r=150, t=80, b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest'
    )
    
    return fig


def create_incident_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Crée un graphique horizontal de distribution des incidents
    Correspond exactement au screenshot avec couleurs sémantiques
    
    Args:
        df: DataFrame avec colonne 'Incident principal' ou 'incident'
        
    Returns:
        Figure Plotly avec barres horizontales colorées par sévérité
    """
    # Vérifier les colonnes disponibles
    incident_col = None
    if 'Incident principal' in df.columns:
        incident_col = 'Incident principal'
    elif 'incident' in df.columns:
        incident_col = 'incident'
    elif 'category' in df.columns:
        incident_col = 'category'
    
    if incident_col is None:
        return None
    
    # Obtenir tous les incidents (pas de limite)
    incident_counts = df[incident_col].value_counts()
    
    # Calculer les pourcentages
    total_tweets = len(df)
    percentages = (incident_counts / total_tweets * 100).round(2)
    
    # Mapping exact des couleurs selon le screenshot
    color_map = {
        'aucun': '#28a745',              # Vert clair (pas d'incident)
        'information': '#17a2b8',         # Cyan/Turquoise
        'technique': '#dc3545',           # Rouge
        'incident_technique': '#dc3545',
        'incident_reseau': '#dc3545',     # Rouge
        'incident_réseau': '#dc3545',
        'processus_sav': '#dc3545',       # Rouge
        'facturation': '#dc3545',         # Rouge
        'incident_facturation': '#dc3545',
        'livraison': '#dc3545',           # Rouge
        'dysfonctionnement': '#dc3545',
        'connexion': '#dc3545',
        'probleme_connexion': '#dc3545'
    }
    
    # Assigner couleurs avec fallback
    colors = []
    for inc in incident_counts.index:
        inc_lower = str(inc).lower().strip()
        matched_color = '#6c757d'  # Gris par défaut
        
        # Correspondance exacte ou partielle
        if inc_lower in color_map:
            matched_color = color_map[inc_lower]
        else:
            # Recherche partielle
            for key, color in color_map.items():
                if key in inc_lower or inc_lower in key:
                    matched_color = color
                    break
        
        colors.append(matched_color)
    
    # Créer labels avec nombre et pourcentage
    text_labels = [f"{count} ({pct}%)" for count, pct in zip(incident_counts.values, percentages)]
    
    fig = go.Figure(data=[
        go.Bar(
            x=incident_counts.values,
            y=incident_counts.index,
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='white', width=1)
            ),
            text=text_labels,
            textposition='outside',
            textfont=dict(size=11, color='#1a202c', family='Arial'),
            hovertemplate="<b>%{y}</b><br>Nombre: %{x:,}<br>Pourcentage: %{customdata:.2f}%<extra></extra>",
            customdata=percentages,
            showlegend=False
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="<b>Distribution des Incidents Principaux</b>",
            font=dict(size=16, family="Arial, sans-serif", color="#1a202c"),
            x=0,
            xanchor='left',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title="Nombre de Tweets",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            titlefont=dict(size=12, color='#4a5568'),
            range=[0, incident_counts.max() * 1.2]  # Extra space for labels
        ),
        yaxis=dict(
            title="Type d'Incident",
            showgrid=False,
            categoryorder='total ascending',
            titlefont=dict(size=12, color='#4a5568'),
            tickfont=dict(size=10)
        ),
        height=450,
        template="plotly_white",
        margin=dict(l=150, r=120, t=80, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        showlegend=False
    )
    
    return fig


def create_radar_chart(kpis: Dict[str, Any], df: pd.DataFrame) -> go.Figure:
    """
    Crée un radar chart pour les performances par domaine
    
    Args:
        kpis: Dictionnaire des KPIs
        df: DataFrame
        
    Returns:
        Figure Plotly
    """
    # Calculer des métriques par domaine si category existe
    if 'category' not in df.columns:
        return None
    
    categories = df['category'].value_counts().head(6).index.tolist()
    
    metrics = []
    for cat in categories:
        cat_df = df[df['category'] == cat]
        
        # Calculer un score de performance (0-100)
        satisfaction = 50
        if 'sentiment' in cat_df.columns:
            positive = (cat_df['sentiment'].str.contains('positive|positif', case=False, na=False)).sum()
            negative = (cat_df['sentiment'].str.contains('negative|négatif|negatif', case=False, na=False)).sum()
            total = len(cat_df)
            satisfaction = ((positive - negative) / total * 50 + 50) if total > 0 else 50
        
        metrics.append(satisfaction)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=metrics,
        theta=categories,
        fill='toself',
        fillcolor='rgba(204, 0, 0, 0.3)',
        line=dict(color=COLORS['primary'], width=2),
        name='Performance'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="<b>Performance par Catégorie</b>",
        title_font_size=18,
        height=450,
        template="plotly_white",
        showlegend=False
    )
    
    return fig


def create_urgency_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Crée un graphique de distribution d'urgence
    
    Args:
        df: DataFrame avec colonne 'priority' ou 'is_urgent'
        
    Returns:
        Figure Plotly
    """
    if 'priority' in df.columns:
        priority_counts = df['priority'].value_counts()
        
        # Mapper aux couleurs
        color_map = {
            'critique': COLORS['danger'],
            'critical': COLORS['danger'],
            'haute': COLORS['warning'],
            'high': COLORS['warning'],
            'élevée': COLORS['warning'],
            'moyenne': COLORS['info'],
            'medium': COLORS['info'],
            'basse': COLORS['success'],
            'low': COLORS['success']
        }
        
        colors = [color_map.get(p.lower(), COLORS['info']) for p in priority_counts.index]
        
        fig = go.Figure(data=[
            go.Bar(
                x=priority_counts.index,
                y=priority_counts.values,
                marker=dict(color=colors),
                text=priority_counts.values,
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
            )
        ])
        
        fig.update_layout(
            title="<b>Distribution des Niveaux d'Urgence</b>",
            xaxis_title="Niveau de Priorité",
            yaxis_title="Nombre de Tweets",
            title_font_size=18,
            height=400,
            template="plotly_white"
        )
        
        return fig
    
    elif 'is_urgent' in df.columns:
        urgent_counts = df['is_urgent'].value_counts()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['Urgent' if x else 'Non Urgent' for x in urgent_counts.index],
                values=urgent_counts.values,
                marker=dict(colors=[COLORS['danger'], COLORS['success']]),
                hole=0.3
            )
        ])
        
        fig.update_layout(
            title="<b>Distribution Urgent / Non Urgent</b>",
            title_font_size=18,
            height=400,
            template="plotly_white"
        )
        
        return fig
    
    return None


def render_enhanced_visualizations(df: pd.DataFrame, kpis: Dict[str, Any]):
    """
    Rend les visualisations essentielles de maniere moderne et epuree
    
    Cette fonction affiche uniquement les 3 visualisations cles:
    - Distribution des sentiments (Pie Chart)
    - Evolution temporelle (Line Chart)  
    - Heatmap d'activite (Heatmap)
    
    NOUVEAU: Support pour les colonnes enrichies du dataset
    - Thème principal (avec pourcentages)
    - Incident principal (avec responsables)
    
    Les visualisations supprimees (Radar, Categories, Urgence) ont ete retirees
    pour une interface plus epuree et professionnelle.
    
    Args:
        df: DataFrame avec les donnees analysees
        kpis: KPIs calcules (utilise pour compatibilite)
    """
    # Separateur visuel avant la section visualisations
    st.markdown("---")
    
    # DEBUG: Log available columns
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"\n{'='*60}")
    logger.info("RENDER ENHANCED VISUALIZATIONS - DEBUG")
    logger.info(f"DataFrame columns: {list(df.columns)}")
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"{'='*60}\n")
    
    # Titre de section moderne sans emoji
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
        <h2 style="font-size: 1.8rem; font-weight: 700; color: #1a202c; margin: 0;">
            <i class="fas fa-chart-line" style="color: #CC0000; margin-right: 0.75rem;"></i>
            Visualisations Analytiques
        </h2>
        <p style="color: #718096; font-size: 1rem; margin-top: 0.5rem;">
            Graphiques interactifs pour analyser les tendances et patterns
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Vérifier les colonnes disponibles pour les visualisations
    # Support pour colonnes enrichies ET colonnes standard
    has_theme_data = (
        'Thème principal' in df.columns or 
        'topics' in df.columns or 
        'category' in df.columns or
        'theme' in df.columns
    )
    
    has_incident_data = (
        'Incident principal' in df.columns or 
        'incident' in df.columns or
        'category' in df.columns
    )
    
    # Afficher les graphiques si des données de thèmes OU incidents sont disponibles
    if has_theme_data or has_incident_data:
        col1, col2 = st.columns(2, gap="large")
        
        # Graphique des thèmes (gauche)
        with col1:
            st.markdown("#### <i class='fas fa-tags'></i> Distribution des Thèmes", unsafe_allow_html=True)
            
            # Déterminer la colonne à utiliser
            theme_col = None
            if 'Thème principal' in df.columns:
                theme_col = 'Thème principal'
            elif 'topics' in df.columns:
                theme_col = 'topics'
            elif 'theme' in df.columns:
                theme_col = 'theme'
            elif 'category' in df.columns:
                theme_col = 'category'
            
            if theme_col:
                fig_theme = create_category_comparison_chart(df, theme_col)
                if fig_theme:
                    st.plotly_chart(fig_theme, use_container_width=True, key='business_viz_theme_dist')
                else:
                    st.info(f"Aucune donnée disponible dans la colonne '{theme_col}'")
            else:
                st.info("Colonne de thèmes non détectée")
        
        # Graphique des incidents (droite)
        with col2:
            st.markdown("#### <i class='fas fa-exclamation-triangle'></i> Distribution des Incidents", unsafe_allow_html=True)
            
            # Déterminer la colonne à utiliser
            incident_col = None
            if 'Incident principal' in df.columns:
                incident_col = 'Incident principal'
            elif 'incident' in df.columns:
                incident_col = 'incident'
            elif 'category' in df.columns and not has_theme_data:
                incident_col = 'category'
            
            if incident_col:
                fig_incident = create_incident_distribution_chart(df)
                if fig_incident:
                    st.plotly_chart(fig_incident, use_container_width=True, key='business_viz_incident_dist')
                else:
                    st.info(f"Aucune donnée disponible dans la colonne '{incident_col}'")
            else:
                st.info("Colonne d'incidents non détectée")
    
    # Afficher le graphique de sentiment si disponible
    st.markdown("#### <i class='fas fa-chart-pie'></i> Distribution des Sentiments", unsafe_allow_html=True)
    
    # Creation et affichage du graphique de distribution des sentiments
    fig_sentiment = create_sentiment_distribution_chart(df)
    if fig_sentiment:
        st.plotly_chart(fig_sentiment, use_container_width=True, key='business_viz_sentiment_dist')
    else:
        # Message si la colonne sentiment n'existe pas
        st.info("Distribution des sentiments non disponible (colonne 'sentiment' manquante)")


def render_complete_dashboard(df: pd.DataFrame):
    """
    Rend un dashboard complet avec KPIs business et visualisations essentielles
    
    Cette fonction orchestre l'affichage complet du dashboard en 3 etapes:
    1. Calcul des KPIs business a partir du DataFrame
    2. Affichage des 5 metriques cles
    3. Affichage des 3 visualisations essentielles
    4. Affichage des insights business
    
    Le dashboard est entierement dynamique et se recalcule a chaque nouveau
    fichier uploade. Il n'y a pas de cache entre les fichiers.
    
    Args:
        df: DataFrame avec les donnees analysees
            Doit contenir au minimum:
            - sentiment (positive/neutral/negative) pour satisfaction
            - category ou theme pour distribution thematique
            - priority ou is_urgent pour taux d'urgence
            - is_claim pour taux de reclamations
            - confidence pour score de confiance
            - date pour evolution temporelle et heatmap
    """
    # Etape 1: Calculer les KPIs business a partir des donnees actuelles
    # Cette fonction parcourt le DataFrame et extrait les metriques
    business_kpis = compute_business_kpis(df)
    
    # Etape 2: Afficher les 5 KPIs principaux en ligne
    # Chaque KPI est affiche avec st.metric() pour une interface Streamlit native
    render_business_kpis(business_kpis)
    
    # Etape 3: Afficher les 3 visualisations essentielles
    # Distribution sentiments, Evolution temporelle, Heatmap activite
    render_enhanced_visualizations(df, business_kpis)
    
    # Etape 4: Section insights business (synthese textuelle)
    st.markdown("---")
    
    # Titre de section moderne
    st.markdown("""
    <div style="text-align: center; margin: 1.5rem 0 1rem 0;">
        <h3 style="font-size: 1.5rem; font-weight: 700; color: #1a202c; margin: 0;">
            <i class="fas fa-lightbulb" style="color: #CC0000; margin-right: 0.75rem;"></i>
            Synthese Business
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Affichage des insights en 3 colonnes
    insights_col1, insights_col2, insights_col3 = st.columns(3)
    
    # Insight 1: Volume total analyse
    with insights_col1:
        st.info(f"**Volume Total**: {len(df):,} tweets analyses")
    
    # Insight 2: Niveau de satisfaction
    with insights_col2:
        if 'satisfaction_index' in business_kpis:
            # Extraction du score de satisfaction
            satisfaction = business_kpis['satisfaction_index']['value']
            
            # Determination du niveau et affichage avec couleur appropriee
            if satisfaction > 60:
                st.success(f"**Satisfaction**: Positive ({satisfaction:.0f}/100)")
            elif satisfaction > 40:
                st.warning(f"**Satisfaction**: Neutre ({satisfaction:.0f}/100)")
            else:
                st.error(f"**Satisfaction**: Negative ({satisfaction:.0f}/100)")
        else:
            st.info("**Satisfaction**: Donnees insuffisantes")
    
    # Insight 3: Niveau d'urgence
    with insights_col3:
        if 'urgency_rate' in business_kpis:
            # Extraction du taux d'urgence
            urgency = business_kpis['urgency_rate']['urgency_pct']
            
            # Determination du niveau et affichage avec couleur appropriee
            if urgency > 20:
                st.error(f"**Urgence**: Elevee ({urgency:.1f}%)")
            elif urgency > 10:
                st.warning(f"**Urgence**: Moderee ({urgency:.1f}%)")
            else:
                st.success(f"**Urgence**: Faible ({urgency:.1f}%)")
        else:
            st.info("**Urgence**: Donnees insuffisantes")

