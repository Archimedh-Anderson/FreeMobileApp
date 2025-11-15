"""
Composants de graphiques Plotly pour Streamlit
==============================================
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional


def render_sentiment_distribution(data: pd.DataFrame, sentiment_col: str = 'sentiment'):
    """Affiche la distribution des sentiments"""
    if sentiment_col not in data.columns:
        st.warning(f"Colonne '{sentiment_col}' non trouvée")
        return
    
    sentiment_counts = data[sentiment_col].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title="Distribution des Sentiments",
        color_discrete_map={
            'positif': '#28a745',
            'négatif': '#dc3545',
            'neutre': '#ffc107'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_urgency_distribution(data: pd.DataFrame, urgency_col: str = 'urgence'):
    """Affiche la distribution des urgences"""
    if urgency_col not in data.columns:
        st.warning(f"Colonne '{urgency_col}' non trouvée")
        return
    
    urgency_counts = data[urgency_col].value_counts()
    
    fig = px.bar(
        x=urgency_counts.index,
        y=urgency_counts.values,
        title="Distribution des Niveaux d'Urgence",
        labels={'x': 'Urgence', 'y': 'Nombre'},
        color=urgency_counts.values,
        color_continuous_scale='Reds'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_topics_chart(data: pd.DataFrame, topics_col: str = 'topics'):
    """Affiche les topics les plus fréquents"""
    if topics_col not in data.columns:
        st.warning(f"Colonne '{topics_col}' non trouvée")
        return
    
    # Extraire tous les topics
    all_topics = []
    for topics_str in data[topics_col].dropna():
        if isinstance(topics_str, str):
            topics = [t.strip() for t in topics_str.split(',')]
            all_topics.extend(topics)
    
    if not all_topics:
        st.info("Aucun topic trouvé")
        return
    
    topics_df = pd.DataFrame({'topic': all_topics})
    topics_counts = topics_df['topic'].value_counts().head(10)
    
    fig = px.bar(
        x=topics_counts.values,
        y=topics_counts.index,
        orientation='h',
        title="Top 10 Topics",
        labels={'x': 'Nombre', 'y': 'Topic'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_confidence_distribution(confidences: List[float]):
    """Affiche la distribution des scores de confiance"""
    if not confidences:
        st.warning("Aucune donnée de confiance disponible")
        return
    
    fig = px.histogram(
        x=confidences,
        nbins=20,
        title="Distribution des Scores de Confiance",
        labels={'x': 'Confiance', 'y': 'Fréquence'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_time_series(data: pd.DataFrame, date_col: str, value_col: str):
    """Affiche une série temporelle"""
    if date_col not in data.columns or value_col not in data.columns:
        st.warning("Colonnes requises non trouvées")
        return
    
    try:
        data[date_col] = pd.to_datetime(data[date_col])
        data_sorted = data.sort_values(date_col)
        
        fig = px.line(
            data_sorted,
            x=date_col,
            y=value_col,
            title=f"Évolution de {value_col}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la création du graphique: {str(e)}")


def render_confusion_matrix(cm: List[List[int]], labels: List[str]):
    """Affiche une matrice de confusion"""
    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=labels,
        y=labels,
        colorscale='Blues',
        text=cm,
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="Matrice de Confusion",
        xaxis_title="Prédit",
        yaxis_title="Réel"
    )
    
    st.plotly_chart(fig, use_container_width=True)




