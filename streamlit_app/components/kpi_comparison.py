"""
Composant de Comparaison KPI - FreeMobilaChat
==============================================

Affiche côte à côte les KPIs du dataset d'entraînement (référence historique)
et les KPIs business actuels (analyse en temps réel) pour permettre une 
comparaison visuelle et chiffrée.

Fonctionnalités:
- Comparaison taux de réclamations (historique vs actuel)
- Compteurs "Oui" pour réclamations (nombre et pourcentage)
- Graphiques comparatifs (barres horizontales)
- Interprétation dynamique (amélioration/dégradation)
- Design moderne avec couleurs conditionnelles

Auteur: FreeMobilaChat Team
Date: 2025-11-12
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Couleurs Free Mobile
COLORS = {
    'primary': '#CC0000',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'neutral': '#6c757d'
}


def render_kpi_comparison_header():
    """Affiche l'en-tête de la section comparaison KPI - Version simplifiée"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1a202c; 
                   font-size: 2rem; 
                   margin: 0 0 0.5rem 0; 
                   font-weight: 700;">
            📊 Comparaison KPI
        </h1>
        <p style="color: #718096; 
                 font-size: 1rem; 
                 margin: 0;">
            Référence Historique vs Analyse Actuelle
        </p>
    </div>
    """, unsafe_allow_html=True)


def calculate_business_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs business à partir du DataFrame uploadé.
    
    Args:
        df: DataFrame avec les données actuelles
        
    Returns:
        Dictionnaire avec les KPIs calculés
    """
    if df is None or len(df) == 0:
        return {
            'total_tweets': 0,
            'reclamations_count': 0,
            'reclamations_rate': 0.0
        }
    
    total_tweets = len(df)
    
    # Détecter la colonne de réclamations avec logging pour debug
    reclamations_count = 0
    
    logger.info(f"\n=== DEBUG KPI CALCULATION ===")
    logger.info(f"Total tweets: {total_tweets}")
    logger.info(f"Columns available: {list(df.columns)}")
    
    if 'réclamations' in df.columns:
        # Colonne enrichie
        logger.info(f"Using 'réclamations' column")
        logger.info(f"Sample values: {df['réclamations'].head().tolist()}")
        reclamations_count = int((df['réclamations'].astype(str).str.lower() == 'oui').sum())
        logger.info(f"Reclamations count (enriched): {reclamations_count}")
    elif 'is_claim' in df.columns:
        # Colonne legacy - priorité pour Mistral qui utilise is_claim = 'oui'
        logger.info(f"Using 'is_claim' column")
        logger.info(f"Sample values: {df['is_claim'].head().tolist()}")
        logger.info(f"Value types: {df['is_claim'].dtype}")
        
        # Convertir en string pour comparaison uniforme
        is_claim_str = df['is_claim'].astype(str).str.lower().str.strip()
        reclamations_mask = is_claim_str.isin(['1', 'oui', 'yes', 'true'])
        reclamations_count = int(reclamations_mask.sum())
        
        logger.info(f"Reclamations count (is_claim): {reclamations_count}")
        logger.info(f"Sample matches: {df[reclamations_mask]['is_claim'].head().tolist()}")
    elif 'category' in df.columns:
        # Détection par catégorie
        logger.info(f"Using 'category' column")
        reclamations_count = int(df['category'].astype(str).str.contains('réclamation|claim|complaint', case=False, na=False).sum())
        logger.info(f"Reclamations count (category): {reclamations_count}")
    else:
        logger.warning("No reclamations column found!")
    
    reclamations_rate = (reclamations_count / total_tweets * 100) if total_tweets > 0 else 0.0
    
    logger.info(f"Final rate: {reclamations_rate:.2f}%")
    logger.info(f"=== END DEBUG ===")
    
    return {
        'total_tweets': total_tweets,
        'reclamations_count': reclamations_count,
        'reclamations_rate': reclamations_rate
    }


def get_training_kpis() -> Optional[Dict[str, Any]]:
    """
    Récupère les KPIs du dataset d'entraînement enrichi.
    
    Returns:
        Dictionnaire avec les KPIs d'entraînement ou None
    """
    try:
        from services.enriched_dataset_loader import get_enriched_dataset_loader
        
        loader = get_enriched_dataset_loader()
        
        if not loader.is_enriched():
            return None
        
        metrics = loader.get_kpi_stats()
        
        if metrics is None:
            return None
        
        # Extraire les informations de réclamations
        reclamations_dist = metrics.reclamations_distribution
        oui_stats = reclamations_dist.get('Oui', {})
        
        return {
            'total_tweets': metrics.total_tweets,
            'reclamations_count': oui_stats.get('count', 0),
            'reclamations_rate': oui_stats.get('percentage', 0.0)
        }
        
    except Exception as e:
        logger.warning(f"Erreur lors du chargement des KPIs d'entraînement: {e}")
        return None


def render_comparison_metrics(training_kpis: Dict[str, Any], business_kpis: Dict[str, Any]):
    """
    Affiche les métriques de comparaison en cartes simplifiées et lisibles.
    
    Args:
        training_kpis: KPIs du dataset d'entraînement
        business_kpis: KPIs du fichier actuel
    """
    col1, col2, col3 = st.columns(3, gap="medium")
    
    # Calcul de la différence
    diff_rate = business_kpis['reclamations_rate'] - training_kpis['reclamations_rate']
    diff_count = business_kpis['reclamations_count'] - training_kpis['reclamations_count']
    
    # Carte 1: Taux Historique - Version simplifiée
    with col1:
        st.markdown(f"""
        <div style="background: #f7fafc; 
                    padding: 2rem 1.5rem; 
                    border-radius: 8px; 
                    border-left: 4px solid #667eea;
                    text-align: center;">
            <div style="color: #667eea; 
                        font-size: 0.75rem; 
                        font-weight: 600; 
                        text-transform: uppercase; 
                        letter-spacing: 1.5px; 
                        margin-bottom: 1rem;">
                📚 RÉFÉRENCE HISTORIQUE
            </div>
            <div style="color: #1a202c; 
                        font-size: 3.5rem; 
                        font-weight: 700; 
                        line-height: 1;
                        margin-bottom: 1rem;">
                {training_kpis['reclamations_rate']:.1f}<span style="font-size: 2rem; color: #4a5568;">%</span>
            </div>
            <div style="color: #4a5568; 
                        font-size: 0.9rem;">
                {training_kpis['reclamations_count']:,} réclamations<br>
                sur {training_kpis['total_tweets']:,} tweets
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Carte 2: Taux Actuel - Version simplifiée avec couleur conditionnelle
    with col2:
        # Couleur conditionnelle
        if diff_rate < 0:
            border_color = "#28a745"  # Vert (amélioration)
            bg_color = "#f0fdf4"
        elif diff_rate > 0:
            border_color = "#dc3545"  # Rouge (dégradation)
            bg_color = "#fef2f2"
        else:
            border_color = "#17a2b8"  # Bleu (stable)
            bg_color = "#f0f9ff"
        
        st.markdown(f"""
        <div style="background: {bg_color}; 
                    padding: 2rem 1.5rem; 
                    border-radius: 8px; 
                    border-left: 4px solid {border_color};
                    text-align: center;">
            <div style="color: {border_color}; 
                        font-size: 0.75rem; 
                        font-weight: 600; 
                        text-transform: uppercase; 
                        letter-spacing: 1.5px; 
                        margin-bottom: 1rem;">
                🔴 ANALYSE ACTUELLE
            </div>
            <div style="color: #1a202c; 
                        font-size: 3.5rem; 
                        font-weight: 700; 
                        line-height: 1;
                        margin-bottom: 1rem;">
                {business_kpis['reclamations_rate']:.1f}<span style="font-size: 2rem; color: #4a5568;">%</span>
            </div>
            <div style="color: #4a5568; 
                        font-size: 0.9rem;">
                {business_kpis['reclamations_count']:,} réclamations<br>
                sur {business_kpis['total_tweets']:,} tweets
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Carte 3: Différence - Version simplifiée
    with col3:
        delta_symbol = "↑" if diff_rate > 0 else "↓" if diff_rate < 0 else "→"
        delta_color = COLORS['danger'] if diff_rate > 0 else COLORS['success'] if diff_rate < 0 else COLORS['neutral']
        delta_text = f"{abs(diff_rate):.1f}%"
        delta_direction = "+" if diff_rate > 0 else "-" if diff_rate < 0 else ""
        
        st.markdown(f"""
        <div style="background: white; 
                    padding: 2rem 1.5rem; 
                    border-radius: 8px; 
                    border: 2px solid {delta_color};
                    text-align: center;">
            <div style="color: #4a5568; 
                        font-size: 0.75rem; 
                        font-weight: 600; 
                        text-transform: uppercase; 
                        letter-spacing: 1.5px; 
                        margin-bottom: 1rem;">
                {delta_symbol} DIFFÉRENCE
            </div>
            <div style="color: {delta_color}; 
                        font-size: 3.5rem; 
                        font-weight: 700; 
                        line-height: 1;
                        margin-bottom: 1rem;">
                {delta_direction}{delta_text}
            </div>
            <div style="color: #718096; 
                        font-size: 0.9rem;">
                {delta_direction}{diff_count:,} réclamations<br>
                de différence
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_comparison_bar_chart(training_kpis: Dict[str, Any], business_kpis: Dict[str, Any]) -> go.Figure:
    """
    Crée un graphique en barres horizontales pour comparer les taux de réclamations.
    
    Args:
        training_kpis: KPIs du dataset d'entraînement
        business_kpis: KPIs du fichier actuel
        
    Returns:
        Figure Plotly
    """
    categories = ['Référence Historique', 'Analyse Actuelle']
    values = [training_kpis['reclamations_rate'], business_kpis['reclamations_rate']]
    counts = [training_kpis['reclamations_count'], business_kpis['reclamations_count']]
    
    colors = ['#667eea', '#28a745' if business_kpis['reclamations_rate'] < training_kpis['reclamations_rate'] else '#dc3545']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='white', width=2)
        ),
        text=[f"{val:.1f}% ({count:,} tweets)" for val, count in zip(values, counts)],
        textposition='outside',
        textfont=dict(size=14, color='#1a202c', family='Arial, sans-serif'),
        hovertemplate="<b>%{y}</b><br>" +
                     "Taux: %{x:.1f}%<br>" +
                     "Count: %{customdata:,}<br>" +
                     "<extra></extra>",
        customdata=counts
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Comparaison du Taux de Réclamations</b>",
            font=dict(size=20, family="Arial, sans-serif", color="#1a202c"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Taux de Réclamations (%)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            range=[0, max(values) * 1.3]
        ),
        yaxis=dict(
            title="",
            showgrid=False
        ),
        height=300,
        template="plotly_white",
        margin=dict(l=20, r=100, t=60, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_count_comparison_chart(training_kpis: Dict[str, Any], business_kpis: Dict[str, Any]) -> go.Figure:
    """
    Crée un graphique empilé pour comparer les compteurs "Oui" vs "Non".
    
    Args:
        training_kpis: KPIs du dataset d'entraînement
        business_kpis: KPIs du fichier actuel
        
    Returns:
        Figure Plotly
    """
    categories = ['Référence Historique', 'Analyse Actuelle']
    
    oui_counts = [training_kpis['reclamations_count'], business_kpis['reclamations_count']]
    non_counts = [
        training_kpis['total_tweets'] - training_kpis['reclamations_count'],
        business_kpis['total_tweets'] - business_kpis['reclamations_count']
    ]
    
    fig = go.Figure()
    
    # Barres "Oui" (réclamations)
    fig.add_trace(go.Bar(
        name='Réclamations (Oui)',
        y=categories,
        x=oui_counts,
        orientation='h',
        marker=dict(color='#dc3545'),
        text=[f"{count:,}" for count in oui_counts],
        textposition='inside',
        textfont=dict(color='white', size=13),
        hovertemplate="<b>Réclamations</b><br>" +
                     "Count: %{x:,}<br>" +
                     "<extra></extra>"
    ))
    
    # Barres "Non" (pas de réclamations)
    fig.add_trace(go.Bar(
        name='Pas de Réclamations (Non)',
        y=categories,
        x=non_counts,
        orientation='h',
        marker=dict(color='#28a745'),
        text=[f"{count:,}" for count in non_counts],
        textposition='inside',
        textfont=dict(color='white', size=13),
        hovertemplate="<b>Pas de Réclamations</b><br>" +
                     "Count: %{x:,}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Distribution Oui/Non - Réclamations</b>",
            font=dict(size=20, family="Arial, sans-serif", color="#1a202c"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Nombre de Tweets",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title="",
            showgrid=False
        ),
        barmode='stack',
        height=300,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def render_interpretation(training_kpis: Dict[str, Any], business_kpis: Dict[str, Any]):
    """
    Affiche l'interprétation dynamique de la comparaison.
    
    Args:
        training_kpis: KPIs du dataset d'entraînement
        business_kpis: KPIs du fichier actuel
    """
    diff_rate = business_kpis['reclamations_rate'] - training_kpis['reclamations_rate']
    
    st.markdown("### 💡 Interprétation")
    
    if diff_rate < -5:  # Amélioration significative
        st.success(f"""
        ✅ **Amélioration Significative du Service**
        
        Le taux de réclamations actuel ({business_kpis['reclamations_rate']:.1f}%) est **nettement inférieur** 
        à la référence historique ({training_kpis['reclamations_rate']:.1f}%).
        
        **Différence**: {abs(diff_rate):.1f} points de pourcentage ⬇️
        
        **Analogie**: En novembre dernier, il a plu {training_kpis['reclamations_rate']:.1f}% des jours. 
        Ce novembre, il a plu seulement {business_kpis['reclamations_rate']:.1f}% des jours jusqu'à présent.
        
        → Les deux valeurs sont correctes, mais reflètent des périodes et contextes différents.
        """)
    elif diff_rate < 0:  # Légère amélioration
        st.info(f"""
        ℹ️ **Légère Amélioration**
        
        Le taux de réclamations actuel ({business_kpis['reclamations_rate']:.1f}%) est **légèrement inférieur** 
        à la référence historique ({training_kpis['reclamations_rate']:.1f}%).
        
        **Différence**: {abs(diff_rate):.1f} points de pourcentage ⬇️
        
        → Tendance positive mais à surveiller sur le long terme.
        """)
    elif diff_rate > 5:  # Dégradation significative
        st.error(f"""
        ⚠️ **Hausse Significative des Réclamations - Analyse Requise**
        
        Le taux de réclamations actuel ({business_kpis['reclamations_rate']:.1f}%) est **nettement supérieur** 
        à la référence historique ({training_kpis['reclamations_rate']:.1f}%).
        
        **Différence**: +{diff_rate:.1f} points de pourcentage ⬆️
        
        **Actions recommandées**:
        - Investiguer les causes de l'augmentation
        - Analyser les thèmes principaux de réclamations
        - Vérifier la qualité du service
        - Examiner les incidents récents
        """)
    elif diff_rate > 0:  # Légère dégradation
        st.warning(f"""
        ⚠️ **Légère Hausse des Réclamations**
        
        Le taux de réclamations actuel ({business_kpis['reclamations_rate']:.1f}%) est **légèrement supérieur** 
        à la référence historique ({training_kpis['reclamations_rate']:.1f}%).
        
        **Différence**: +{diff_rate:.1f} points de pourcentage ⬆️
        
        → À surveiller mais pas d'alerte critique.
        """)
    else:  # Stable
        st.info(f"""
        ➡️ **Taux Stable**
        
        Le taux de réclamations actuel ({business_kpis['reclamations_rate']:.1f}%) est **identique** 
        à la référence historique ({training_kpis['reclamations_rate']:.1f}%).
        
        → Situation stable, pas de changement notable.
        """)


def render_kpi_comparison_tab(current_dataframe: pd.DataFrame):
    """
    Fonction principale pour afficher l'onglet de comparaison KPI.
    
    Args:
        current_dataframe: DataFrame du fichier actuellement uploadé
    """
    # En-tête
    render_kpi_comparison_header()
    
    # DEBUG: Log le dataframe reçu
    logger.info(f"\n{'='*60}")
    logger.info("RENDER KPI COMPARISON TAB - DEBUG")
    logger.info(f"Dataframe shape: {current_dataframe.shape if current_dataframe is not None else 'None'}")
    if current_dataframe is not None:
        logger.info(f"Columns: {list(current_dataframe.columns)}")
        logger.info(f"First 3 rows sample:")
        logger.info(current_dataframe.head(3).to_string())
    logger.info(f"{'='*60}\n")
    
    # Récupérer les KPIs
    training_kpis = get_training_kpis()
    
    if training_kpis is None:
        st.warning("""
        ⚠️ **Dataset d'entraînement non disponible**
        
        La comparaison KPI nécessite le dataset d'entraînement enrichi 
        (`train_dataset_enriched.csv`) pour fonctionner.
        
        Veuillez vous assurer que le fichier existe dans `data/training/`.
        """)
        return
    
    if current_dataframe is None or len(current_dataframe) == 0:
        st.info("""
        ℹ️ **Aucune donnée actuelle à comparer**
        
        Veuillez uploader un fichier de tweets pour effectuer la comparaison.
        """)
        return
    
    # Calculer les KPIs business
    business_kpis = calculate_business_kpis(current_dataframe)
    
    # Afficher les métriques comparatives
    render_comparison_metrics(training_kpis, business_kpis)
    
    st.markdown("---")
    
    # Graphiques comparatifs
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("#### 📊 Taux de Réclamations")
        fig_rate = create_comparison_bar_chart(training_kpis, business_kpis)
        st.plotly_chart(fig_rate, use_container_width=True, key='comparison_rate_chart')
    
    with col2:
        st.markdown("#### 📈 Compteur Oui/Non")
        fig_count = create_count_comparison_chart(training_kpis, business_kpis)
        st.plotly_chart(fig_count, use_container_width=True, key='comparison_count_chart')
    
    st.markdown("---")
    
    # Interprétation dynamique
    render_interpretation(training_kpis, business_kpis)
    
    # Section explicative
    with st.expander("📖 Comprendre les Différences"):
        st.markdown("""
        ### Pourquoi les deux valeurs diffèrent-elles ?
        
        **C'est tout à fait normal et attendu !** Voici pourquoi :
        
        #### 1️⃣ **Datasets Différents**
        - **Référence Historique** : Dataset utilisé pour l'entraînement du modèle (3,500 tweets)
        - **Analyse Actuelle** : Fichier que vous avez uploadé (volume variable)
        
        #### 2️⃣ **Périodes Différentes**
        - Le dataset d'entraînement reflète une période spécifique du passé
        - Vos données actuelles reflètent la situation présente ou récente
        
        #### 3️⃣ **Contextes Différents**
        - Les conditions de service peuvent avoir évolué
        - La qualité du service peut s'être améliorée ou dégradée
        - Les types de tweets peuvent varier selon les campagnes marketing
        
        #### 4️⃣ **Interprétation**
        - Si actuel **< historique** → ✅ Amélioration de la satisfaction client
        - Si actuel **> historique** → ⚠️ Augmentation des problèmes à investiguer
        - Si actuel **≈ historique** → ➡️ Situation stable
        
        ### 📚 Analogie Simple
        
        > **Référence Historique (44,5%)** : "L'année dernière en novembre, il a plu 44,5% des jours."
        > 
        > **Analyse Actuelle (28,5%)** : "Ce novembre, il a plu 28,5% des jours jusqu'à présent."
        
        → Les deux valeurs sont **correctes**, mais elles mesurent des **périodes différentes**.
        
        C'est exactement la même logique pour vos KPIs ! 🎯
        """)
