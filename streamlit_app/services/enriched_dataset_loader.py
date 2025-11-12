"""
Service de Chargement du Dataset Enrichi - FreeMobilaChat
==========================================================

Module responsable du chargement et de la gestion du dataset enrichi avec KPIs avancés.
Fournit des métriques supplémentaires pour l'analyse thématique et de réclamations.

Fonctionnalités:
- Chargement du dataset enrichi (train_dataset_enriched.csv)
- Accès aux statistiques KPI pré-calculées (train_dataset_enriched_kpi_stats.json)
- Intégration transparente avec les classificateurs existants
- Cache intelligent pour optimiser les performances
- Backward compatibility totale avec le dataset original

Auteur: FreeMobilaChat Team
Date: 2025-11-12
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class EnrichedDatasetMetrics:
    """Métriques du dataset enrichi avec KPIs avancés"""
    total_tweets: int
    themes_distribution: Dict[str, Dict[str, float]]  # {theme: {count, percentage, avg_confidence}}
    incidents_distribution: Dict[str, Dict[str, float]]  # {incident: {count, percentage, avg_confidence}}
    reclamations_distribution: Dict[str, Dict[str, float]]  # {Oui/Non: {count, percentage}}
    responsables_distribution: Dict[str, Dict[str, float]]  # {service: {count, percentage}}
    date_traitement: str
    
    def get_top_theme(self) -> Tuple[str, float]:
        """Retourne le thème principal et son pourcentage"""
        if not self.themes_distribution:
            return ("autre", 0.0)
        
        top_theme = max(
            self.themes_distribution.items(),
            key=lambda x: x[1].get('count', 0)
        )
        return top_theme[0], top_theme[1].get('percentage', 0.0)
    
    def get_top_incident(self) -> Tuple[str, float]:
        """Retourne l'incident principal et son pourcentage"""
        if not self.incidents_distribution:
            return ("aucun", 0.0)
        
        top_incident = max(
            self.incidents_distribution.items(),
            key=lambda x: x[1].get('count', 0)
        )
        return top_incident[0], top_incident[1].get('percentage', 0.0)
    
    def get_reclamation_rate(self) -> float:
        """Retourne le taux de réclamations en pourcentage"""
        oui_stats = self.reclamations_distribution.get('Oui', {})
        return oui_stats.get('percentage', 0.0)
    
    def get_theme_confidence(self, theme: str) -> float:
        """Retourne la confiance moyenne pour un thème donné"""
        theme_stats = self.themes_distribution.get(theme, {})
        return theme_stats.get('avg_confidence', 0.0)


class EnrichedDatasetLoader:
    """
    Chargeur centralisé pour le dataset enrichi et ses statistiques KPI.
    
    Ce service:
    1. Charge le dataset enrichi (train_dataset_enriched.csv)
    2. Charge les statistiques KPI pré-calculées (train_dataset_enriched_kpi_stats.json)
    3. Fournit des méthodes d'accès rapide aux métriques
    4. Gère le cache Streamlit pour optimiser les performances
    5. Maintient la compatibilité avec le dataset original
    """
    
    # Chemins par défaut (relatifs au root du projet)
    DEFAULT_ENRICHED_DATASET_PATH = "data/training/train_dataset_enriched.csv"
    DEFAULT_KPI_STATS_PATH = "data/training/train_dataset_enriched_kpi_stats.json"
    DEFAULT_ORIGINAL_DATASET_PATH = "data/training/train_dataset.csv"
    
    def __init__(
        self,
        enriched_dataset_path: Optional[str] = None,
        kpi_stats_path: Optional[str] = None,
        fallback_to_original: bool = True
    ):
        """
        Initialise le chargeur de dataset enrichi.
        
        Args:
            enriched_dataset_path: Chemin vers le dataset enrichi (optionnel)
            kpi_stats_path: Chemin vers les statistiques KPI (optionnel)
            fallback_to_original: Si True, charge le dataset original si l'enrichi n'existe pas
        """
        self.enriched_dataset_path = enriched_dataset_path or self.DEFAULT_ENRICHED_DATASET_PATH
        self.kpi_stats_path = kpi_stats_path or self.DEFAULT_KPI_STATS_PATH
        self.fallback_to_original = fallback_to_original
        
        self._dataset: Optional[pd.DataFrame] = None
        self._kpi_stats: Optional[EnrichedDatasetMetrics] = None
        self._is_enriched: bool = False
    
    @staticmethod
    @st.cache_data(show_spinner=False, ttl=3600)
    def _load_enriched_dataset_cached(file_path: str) -> Tuple[Optional[pd.DataFrame], bool]:
        """
        Charge le dataset enrichi avec cache Streamlit (1h TTL).
        
        Args:
            file_path: Chemin vers le fichier CSV enrichi
            
        Returns:
            Tuple (DataFrame, is_enriched_flag)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Dataset enrichi non trouvé: {file_path}")
                return None, False
            
            df = pd.read_csv(path, encoding='utf-8')
            
            # Vérifier les colonnes enrichies attendues
            enriched_columns = [
                'Thème principal', 'theme_confidence',
                'Incident principal', 'incident_responsable', 'incident_confidence',
                'reclamation_confidence'
            ]
            
            is_enriched = all(col in df.columns for col in enriched_columns)
            
            if is_enriched:
                logger.info(f"✅ Dataset enrichi chargé: {len(df):,} lignes avec {len(df.columns)} colonnes")
            else:
                logger.warning(f"⚠️ Dataset chargé mais colonnes enrichies manquantes")
            
            return df, is_enriched
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du dataset enrichi: {e}")
            return None, False
    
    @staticmethod
    @st.cache_data(show_spinner=False, ttl=3600)
    def _load_kpi_stats_cached(file_path: str) -> Optional[EnrichedDatasetMetrics]:
        """
        Charge les statistiques KPI avec cache Streamlit (1h TTL).
        
        Args:
            file_path: Chemin vers le fichier JSON des statistiques
            
        Returns:
            EnrichedDatasetMetrics ou None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Statistiques KPI non trouvées: {file_path}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                stats_dict = json.load(f)
            
            metrics = EnrichedDatasetMetrics(
                total_tweets=stats_dict.get('total_tweets', 0),
                themes_distribution=stats_dict.get('themes', {}),
                incidents_distribution=stats_dict.get('incidents', {}),
                reclamations_distribution=stats_dict.get('reclamations', {}),
                responsables_distribution=stats_dict.get('responsables', {}),
                date_traitement=stats_dict.get('date_traitement', 'Inconnue')
            )
            
            logger.info(f"✅ Statistiques KPI chargées: {metrics.total_tweets:,} tweets analysés")
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des statistiques KPI: {e}")
            return None
    
    def load(self) -> bool:
        """
        Charge le dataset enrichi et ses statistiques KPI.
        
        Returns:
            True si le chargement a réussi, False sinon
        """
        # Charger le dataset enrichi
        self._dataset, self._is_enriched = self._load_enriched_dataset_cached(
            self.enriched_dataset_path
        )
        
        # Si échec et fallback activé, charger le dataset original
        if self._dataset is None and self.fallback_to_original:
            logger.info("Tentative de chargement du dataset original...")
            try:
                self._dataset = pd.read_csv(
                    self.DEFAULT_ORIGINAL_DATASET_PATH,
                    encoding='utf-8'
                )
                self._is_enriched = False
                logger.info(f"✅ Dataset original chargé: {len(self._dataset):,} lignes")
            except Exception as e:
                logger.error(f"Impossible de charger le dataset original: {e}")
                return False
        
        # Charger les statistiques KPI si le dataset est enrichi
        if self._is_enriched:
            self._kpi_stats = self._load_kpi_stats_cached(self.kpi_stats_path)
        
        return self._dataset is not None
    
    def get_dataset(self) -> Optional[pd.DataFrame]:
        """Retourne le dataset chargé (enrichi ou original)"""
        if self._dataset is None:
            self.load()
        return self._dataset
    
    def get_kpi_stats(self) -> Optional[EnrichedDatasetMetrics]:
        """Retourne les statistiques KPI si disponibles"""
        if self._kpi_stats is None and self._is_enriched:
            self.load()
        return self._kpi_stats
    
    def is_enriched(self) -> bool:
        """Vérifie si le dataset enrichi est chargé"""
        if self._dataset is None:
            self.load()
        return self._is_enriched
    
    def get_enriched_columns(self) -> list:
        """Retourne la liste des colonnes enrichies disponibles"""
        if not self.is_enriched() or self._dataset is None:
            return []
        
        enriched_cols = [
            'Thème principal', 'theme_confidence',
            'Incident principal', 'incident_responsable', 'incident_confidence',
            'reclamation_confidence'
        ]
        
        return [col for col in enriched_cols if col in self._dataset.columns]
    
    def get_sample_data(self, n: int = 100) -> Optional[pd.DataFrame]:
        """
        Retourne un échantillon du dataset enrichi.
        
        Args:
            n: Nombre de lignes à retourner
            
        Returns:
            DataFrame échantillon ou None
        """
        dataset = self.get_dataset()
        if dataset is None:
            return None
        
        return dataset.sample(n=min(n, len(dataset)), random_state=42)
    
    def get_theme_summary(self) -> Dict[str, Any]:
        """Génère un résumé des thèmes principaux"""
        stats = self.get_kpi_stats()
        if stats is None:
            return {}
        
        summary = {
            'total_themes': len(stats.themes_distribution),
            'top_theme': stats.get_top_theme()[0],
            'top_theme_percentage': stats.get_top_theme()[1],
            'distribution': stats.themes_distribution
        }
        
        return summary
    
    def get_incident_summary(self) -> Dict[str, Any]:
        """Génère un résumé des incidents principaux"""
        stats = self.get_kpi_stats()
        if stats is None:
            return {}
        
        summary = {
            'total_incidents': len(stats.incidents_distribution),
            'top_incident': stats.get_top_incident()[0],
            'top_incident_percentage': stats.get_top_incident()[1],
            'distribution': stats.incidents_distribution
        }
        
        return summary
    
    def get_reclamation_summary(self) -> Dict[str, Any]:
        """Génère un résumé des réclamations"""
        stats = self.get_kpi_stats()
        if stats is None:
            return {}
        
        summary = {
            'reclamation_rate': stats.get_reclamation_rate(),
            'distribution': stats.reclamations_distribution
        }
        
        return summary


# Instance singleton pour usage global
_enriched_dataset_loader_instance: Optional[EnrichedDatasetLoader] = None


def get_enriched_dataset_loader() -> EnrichedDatasetLoader:
    """
    Retourne l'instance singleton du chargeur de dataset enrichi.
    
    Usage:
        loader = get_enriched_dataset_loader()
        dataset = loader.get_dataset()
        kpi_stats = loader.get_kpi_stats()
    """
    global _enriched_dataset_loader_instance
    
    if _enriched_dataset_loader_instance is None:
        _enriched_dataset_loader_instance = EnrichedDatasetLoader()
        _enriched_dataset_loader_instance.load()
    
    return _enriched_dataset_loader_instance
