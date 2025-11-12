"""
Composants de Visualisation pour KPIs Enrichis - FreeMobilaChat
================================================================

Module de visualisation spécialisé pour afficher les nouveaux KPIs du dataset enrichi:
- Thème principal avec distribution et confiance
- Incident principal avec responsables
- Réclamations améliorées avec métriques détaillées

Intégration transparente avec les dashboards existants.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional
import logging

from services.enriched_dataset_loader import EnrichedDatasetMetrics, get_enriched_dataset_loader

logger = logging.getLogger(__name__)


def render_enriched_kpis_header():
    """Affiche le header pour les KPIs enrichis"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                padding: 2rem; 
                border-radius: 12px; 
                text-align: center; 
                margin: 1.5rem 0; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <h2 style="font-size: 1.9rem; font-weight: 800; color: #1a202c; margin: 0; letter-spacing: -0.5px;">
            📊 KPIs Enrichis - Dataset d'Entraînement
        </h2>
        <p style="color: #4a5568; font-size: 0.95rem; margin-top: 0.75rem; font-weight: 500;">
            🔄 Métriques avancées avec thèmes, incidents et responsabilités
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_enriched_kpis_cards(metrics: EnrichedDatasetMetrics):
    """
    Affiche les cartes KPI pour les métriques enrichies.
    
    Args:
        metrics: Objet EnrichedDatasetMetrics avec les statistiques
    """
    if metrics is None:
        st.warning("⚠️ Métriques enrichies non disponibles")
        return
    
    # Ligne de 5 KPIs
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    
    # KPI 1: Total Tweets
    with col1:
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid #4299e1;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">📊</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">TOTAL TWEETS</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {metrics.total_tweets:,}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                Dataset enrichi
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI 2: Thème Principal
    with col2:
        top_theme, theme_pct = metrics.get_top_theme()
        theme_color = "#48bb78" if theme_pct > 30 else "#4299e1"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {theme_color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🎯</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">THÈME PRINCIPAL</span>
            </div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {top_theme.upper()}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                {theme_pct:.1f}% des tweets
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI 3: Incident Principal
    with col3:
        top_incident, incident_pct = metrics.get_top_incident()
        incident_color = "#ed8936" if incident_pct > 20 else "#805ad5"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {incident_color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">⚡</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">INCIDENT MAJEUR</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {top_incident.replace('_', ' ').title()}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                {incident_pct:.1f}% des cas
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI 4: Taux de Réclamations
    with col4:
        reclamation_rate = metrics.get_reclamation_rate()
        reclamation_color = "#e53e3e" if reclamation_rate > 50 else "#ed8936" if reclamation_rate > 30 else "#48bb78"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {reclamation_color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">⚠️</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">RÉCLAMATIONS</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {reclamation_rate:.1f}<span style="font-size: 1.2rem; color: #718096;">%</span>
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                Taux de plaintes
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI 5: Confiance Moyenne Thème
    with col5:
        if metrics.themes_distribution:
            avg_confidence = sum(
                theme['avg_confidence'] 
                for theme in metrics.themes_distribution.values()
            ) / len(metrics.themes_distribution)
        else:
            avg_confidence = 0.0
        
        conf_color = "#48bb78" if avg_confidence > 0.8 else "#4299e1" if avg_confidence > 0.6 else "#ed8936"
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 1.25rem; 
                    border-radius: 10px; 
                    border-left: 4px solid {conf_color};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    height: 140px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🎓</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px;">CONFIANCE</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1a202c; margin: 0.5rem 0;">
                {avg_confidence:.2f}
            </div>
            <div style="font-size: 0.8rem; color: #718096; font-weight: 500;">
                Score moyen
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_theme_distribution_chart(metrics: EnrichedDatasetMetrics):
    """Crée un graphique de distribution des thèmes principaux"""
    if not metrics or not metrics.themes_distribution:
        return None
    
    # Préparer les données
    themes_data = []
    for theme, stats in metrics.themes_distribution.items():
        themes_data.append({
            'Thème': theme.upper(),
            'Count': stats['count'],
            'Percentage': stats['percentage'],
            'Confiance': stats['avg_confidence']
        })
    
    df = pd.DataFrame(themes_data).sort_values('Count', ascending=False)
    
    # Créer le graphique
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['Thème'],
        y=df['Count'],
        text=df['Percentage'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        marker=dict(
            color=df['Confiance'],
            colorscale='Viridis',
            colorbar=dict(title="Confiance", len=0.5, y=0.5),
            line=dict(color='white', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>Count: %{y:,}<br>Confiance: %{marker.color:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribution des Thèmes Principaux",
        xaxis_title="Thème",
        yaxis_title="Nombre de Tweets",
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        font=dict(size=12),
        margin=dict(t=80, b=80, l=60, r=60)
    )
    
    return fig


def render_incident_responsibility_chart(metrics: EnrichedDatasetMetrics):
    """Crée un graphique de responsabilité par service"""
    if not metrics or not metrics.responsables_distribution:
        return None
    
    # Préparer les données
    resp_data = []
    for service, stats in metrics.responsables_distribution.items():
        resp_data.append({
            'Service': service.replace('service_', '').title(),
            'Count': stats['count'],
            'Percentage': stats['percentage']
        })
    
    df = pd.DataFrame(resp_data).sort_values('Count', ascending=True)
    
    # Créer le graphique horizontal
    fig = go.Figure()
    
    colors = ['#4299e1', '#48bb78', '#ed8936', '#805ad5']
    
    fig.add_trace(go.Bar(
        y=df['Service'],
        x=df['Count'],
        orientation='h',
        text=df['Percentage'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        marker=dict(
            color=colors[:len(df)],
            line=dict(color='white', width=1.5)
        ),
        hovertemplate='<b>%{y}</b><br>Tweets: %{x:,}<br>Part: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Répartition des Incidents par Service Responsable",
        xaxis_title="Nombre de Tweets",
        yaxis_title="Service",
        height=300,
        showlegend=False,
        plot_bgcolor='white',
        font=dict(size=12),
        margin=dict(t=80, b=60, l=120, r=100)
    )
    
    return fig


def render_enriched_visualizations(metrics: EnrichedDatasetMetrics):
    """
    Affiche toutes les visualisations pour les métriques enrichies.
    
    Args:
        metrics: EnrichedDatasetMetrics avec les statistiques
    """
    if metrics is None:
        st.info("📊 Visualisations enrichies non disponibles - dataset original utilisé")
        return
    
    st.markdown("---")
    st.markdown("### 📈 Visualisations des KPIs Enrichis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de distribution des thèmes
        fig_themes = render_theme_distribution_chart(metrics)
        if fig_themes:
            st.plotly_chart(fig_themes, use_container_width=True, key='enriched_themes_dist')
    
    with col2:
        # Graphique de responsabilité
        fig_resp = render_incident_responsibility_chart(metrics)
        if fig_resp:
            st.plotly_chart(fig_resp, use_container_width=True, key='enriched_resp_dist')


def render_enriched_kpis_summary():
    """
    Point d'entrée principal pour afficher le dashboard complet des KPIs enrichis.
    
    Cette fonction:
    1. Charge les métriques du dataset enrichi
    2. Affiche le header
    3. Affiche les cartes KPI
    4. Affiche les visualisations
    
    Usage dans une page Streamlit:
        from components.enriched_kpis_display import render_enriched_kpis_summary
        render_enriched_kpis_summary()
    """
    try:
        # Charger les métriques enrichies
        loader = get_enriched_dataset_loader()
        
        if not loader.is_enriched():
            st.info("ℹ️ Dataset enrichi non disponible. Utilisation du dataset original.")
            return
        
        metrics = loader.get_kpi_stats()
        
        if metrics is None:
            st.warning("⚠️ Impossible de charger les statistiques KPI enrichies")
            return
        
        # Afficher le dashboard complet
        render_enriched_kpis_header()
        render_enriched_kpis_cards(metrics)
        render_enriched_visualizations(metrics)
        
        # Informations supplémentaires en expander
        with st.expander("ℹ️ Informations sur le Dataset Enrichi", expanded=False):
            st.markdown(f"""
            **Date de traitement**: {metrics.date_traitement}
            
            **Total de tweets analysés**: {metrics.total_tweets:,}
            
            **Colonnes enrichies ajoutées**:
            - `Thème principal`: Classification thématique (9 catégories)
            - `theme_confidence`: Score de confiance du thème
            - `Incident principal`: Type d'incident détecté (6 types)
            - `incident_responsable`: Service responsable (4 services)
            - `incident_confidence`: Score de confiance de l'incident
            - `reclamation_confidence`: Score de confiance de la réclamation
            
            **Approche de classification**:
            - Score-based keyword matching (pas de first-match)
            - Confidence scoring basé sur le nombre de keywords
            - Mapping automatique service ↔ incident
            """)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des KPIs enrichis: {e}")
        st.error(f"❌ Erreur lors du chargement des KPIs enrichis: {str(e)}")
