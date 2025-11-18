"""
Configuration Centralisée du Système de Classification Mistral - FreeMobilaChat
=============================================================================

Module de configuration global contenant tous les paramètres, constantes,
taxonomies et règles de détection pour le système de classification intelligent.

Développé dans le cadre d'un mémoire de master en Data Science et Intelligence Artificielle.
Ce module centralise la configuration pour faciliter la maintenance et les tests.
"""

# Imports pour la gestion des chemins et types
import os  # Accès aux variables d'environnement système
from pathlib import Path  # Manipulation multi-plateforme des chemins de fichiers
from typing import Dict, List, Any  # Annotations de types pour la sécurité du code

# Définition des chemins de base du projet (structure hiérarchique)
BASE_DIR = Path(__file__).parent  # Répertoire streamlit_app/ (racine de l'application)
SERVICES_DIR = (
    BASE_DIR / "services"
)  # Répertoire des modules de service (classificateurs, visualisations)
TESTS_DIR = BASE_DIR / "tests"  # Répertoire des tests unitaires et d'intégration
DATA_DIR = BASE_DIR.parent / "data"  # Répertoire des données (datasets, modèles entraînés)

# Configuration des modèles de langage (LLM) avec paramètres optimisés
LLM_CONFIG = {
    "ollama": {  # Configuration pour Ollama (modèles locaux open-source)
        "model": "llama2",  # Modèle par défaut (peut être substitué par mistral, codellama, etc.)
        "temperature": 0.3,  # Contrôle de la créativité (0.3 = prévisible, 1.0 = créatif)
        "max_tokens": 1000,  # Limitation de la longueur de réponse pour optimiser les performances
        "timeout": 30,  # Délai maximal d'attente en secondes avant abandon de la requête
    },
    "openai": {  # Configuration pour OpenAI GPT (API cloud payante)
        "model": "gpt-3.5-turbo",  # Modèle économique d'OpenAI avec bon rapport qualité/prix
        "temperature": 0.3,  # Température basse pour réponses cohérentes et reproductibles
        "max_tokens": 1000,  # Limitation économique des tokens générés
        "timeout": 30,  # Timeout pour éviter les blocages sur requêtes lentes
    },
    "fallback": {  # Configuration du mode de secours (classification par règles)
        "enabled": True,  # Activation du fallback automatique en cas d'échec LLM
        "confidence_threshold": 0.5,  # Seuil de confiance minimal pour accepter les résultats
    },
}

# Taxonomie de classification
TAXONOMY = {
    "is_reclamation": ["OUI", "NON"],
    "theme": ["FIBRE", "MOBILE", "TV", "FACTURE", "SAV", "RESEAU", "AUTRE"],
    "sentiment": ["NEGATIF", "NEUTRE", "POSITIF"],
    "urgence": ["FAIBLE", "MOYENNE", "ELEVEE", "CRITIQUE"],
    "type_incident": ["PANNE", "LENTEUR", "FACTURATION", "PROCESSUS_SAV", "INFO", "AUTRE"],
}

# Patterns de détection pour le mode fallback
DETECTION_PATTERNS = {
    "reclamation_keywords": [
        "problème",
        "panne",
        "coupé",
        "lent",
        "bug",
        "erreur",
        "dysfonctionnement",
        "insatisfait",
        "mécontent",
        "déçu",
        "frustré",
        "énervé",
        "colère",
        "réclamation",
        "plainte",
        "insatisfaction",
        "défaillance",
    ],
    "theme_fibre": [
        "fibre",
        "internet",
        "débit",
        "connexion",
        "wifi",
        "box",
        "freebox",
        "ligne",
        "adsl",
        "vdsl",
        "fibre optique",
    ],
    "theme_mobile": [
        "mobile",
        "téléphone",
        "portable",
        "smartphone",
        "forfait",
        "data",
        "sms",
        "appel",
        "réseau mobile",
        "4g",
        "5g",
    ],
    "theme_tv": [
        "télévision",
        "tv",
        "chaîne",
        "canal",
        "programme",
        "replay",
        "streaming",
        "netflix",
        "prime",
        "disney",
    ],
    "theme_facture": [
        "facture",
        "facturation",
        "prix",
        "coût",
        "tarif",
        "abonnement",
        "paiement",
        "prélèvement",
        "montant",
    ],
    "theme_sav": [
        "sav",
        "service client",
        "support",
        "assistance",
        "aide",
        "technicien",
        "intervention",
        "rendez-vous",
    ],
    "theme_reseau": [
        "réseau",
        "infrastructure",
        "antenne",
        "couverture",
        "signal",
        "zone blanche",
        "déploiement",
    ],
    "sentiment_negatif": [
        "nul",
        "horrible",
        "catastrophe",
        "dégoûté",
        "énervé",
        "frustré",
        "déçu",
        "insatisfait",
        "mécontent",
        "colère",
        "rage",
    ],
    "sentiment_positif": [
        "super",
        "excellent",
        "génial",
        "parfait",
        "content",
        "satisfait",
        "ravi",
        "heureux",
        "merci",
        "bravo",
        "félicitations",
    ],
    "urgence_critique": [
        "urgence",
        "critique",
        "grave",
        "bloqué",
        "impossible",
        "catastrophe",
        "plus rien ne fonctionne",
        "totalement coupé",
    ],
    "urgence_elevee": [
        "depuis longtemps",
        "plusieurs heures",
        "toute la journée",
        "depuis ce matin",
        "depuis hier",
        "urgent",
    ],
    "type_panne": [
        "panne",
        "coupé",
        "ne fonctionne plus",
        "plus de service",
        "dysfonctionnement",
        "arrêt",
    ],
    "type_lenteur": ["lent", "lenteur", "débit faible", "ralentissement", "performance"],
    "type_facturation": ["facture", "facturation", "prix", "coût", "tarif", "montant"],
    "type_processus_sav": ["sav", "service client", "support", "assistance", "technicien"],
}

# Configuration des types de données
DATA_TYPES = {
    "SOCIAL_MEDIA": {
        "keywords": ["tweet", "text", "message", "post"],
        "kpis": ["engagement", "sentiment", "reach"],
    },
    "ECOMMERCE": {
        "keywords": ["product", "price", "order", "customer"],
        "kpis": ["revenue", "conversion", "cart_abandonment"],
    },
    "FINANCIAL": {
        "keywords": ["amount", "balance", "transaction", "revenue"],
        "kpis": ["profit", "loss", "roi", "volatility"],
    },
    "IOT_SENSORS": {
        "keywords": ["sensor", "measurement", "value", "reading"],
        "kpis": ["data_quality", "sampling_rate", "anomalies"],
    },
    "TEMPORAL": {
        "keywords": ["date", "time", "timestamp", "hour"],
        "kpis": ["trends", "seasonality", "patterns"],
    },
}

# Configuration des métriques de performance
PERFORMANCE_METRICS = {
    "accuracy_threshold": 0.85,
    "confidence_threshold": 0.7,
    "processing_speed_threshold": 100,  # tweets/seconde
    "memory_limit_mb": 1000,
    "timeout_seconds": 30,
}

# Configuration des tests
TEST_CONFIG = {
    "test_tweets": [
        "@Free Internet coupé depuis ce matin à Marseille, aidez-moi !",
        "📢 Free annonce le déploiement de la fibre dans 200 nouvelles communes !",
        "@Free J'attends depuis 2 semaines une réponse du SAV pour ma box, toujours rien !",
        "Merci @Free pour le service client rapide et efficace !",
        "La 4G de Free fonctionne parfaitement dans ma région",
    ],
    "benchmark_volumes": [10, 50, 100, 500],
    "expected_accuracy": 0.85,
    "expected_confidence": 0.8,
}

# Configuration de l'interface Streamlit
STREAMLIT_CONFIG = {
    "page_title": "FreeMobilaChat - Classification Mistral",
    "page_icon": ":brain:",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Configuration des couleurs
COLORS = {
    "primary": "#CC0000",
    "secondary": "#8B0000",
    "accent": "#FF6B6B",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8",
}

# Configuration des logs
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["file", "console"],
}

# Configuration des exports
EXPORT_CONFIG = {"csv_encoding": "utf-8", "json_indent": 2, "date_format": "%Y%m%d_%H%M%S"}

# Configuration des modèles
MODEL_CONFIG = {"batch_size": 100, "max_retries": 3, "retry_delay": 1, "cache_size": 1000}

# Configuration des visualisations
VISUALIZATION_CONFIG = {
    "default_width": 800,
    "default_height": 600,
    "color_scheme": "Set3",
    "animation_duration": 500,
}


def get_config() -> Dict[str, Any]:
    """Retourne la configuration complète"""
    return {
        "base_dir": str(BASE_DIR),
        "services_dir": str(SERVICES_DIR),
        "tests_dir": str(TESTS_DIR),
        "data_dir": str(DATA_DIR),
        "llm_config": LLM_CONFIG,
        "taxonomy": TAXONOMY,
        "patterns": DETECTION_PATTERNS,
        "data_types": DATA_TYPES,
        "performance": PERFORMANCE_METRICS,
        "tests": TEST_CONFIG,
        "streamlit": STREAMLIT_CONFIG,
        "colors": COLORS,
        "logging": LOGGING_CONFIG,
        "export": EXPORT_CONFIG,
        "model": MODEL_CONFIG,
        "visualization": VISUALIZATION_CONFIG,
    }


def get_llm_config(provider: str = "fallback") -> Dict[str, Any]:
    """Retourne la configuration LLM pour un fournisseur"""
    return LLM_CONFIG.get(provider, LLM_CONFIG["fallback"])


def get_patterns(category: str) -> List[str]:
    """Retourne les patterns pour une catégorie"""
    return DETECTION_PATTERNS.get(category, [])


def get_data_type_config(data_type: str) -> Dict[str, Any]:
    """Retourne la configuration pour un type de données"""
    return DATA_TYPES.get(data_type, {})


def is_development_mode() -> bool:
    """Vérifie si on est en mode développement"""
    return os.getenv("ENVIRONMENT", "development") == "development"


def get_debug_mode() -> bool:
    """Vérifie si le mode debug est activé"""
    return os.getenv("DEBUG", "false").lower() == "true"


def get_log_level() -> str:
    """Retourne le niveau de log configuré"""
    return os.getenv("LOG_LEVEL", "INFO")


def get_llm_provider() -> str:
    """Retourne le fournisseur LLM configuré"""
    return os.getenv("LLM_PROVIDER", "fallback")


def get_llm_model() -> str:
    """Retourne le modèle LLM configuré"""
    provider = get_llm_provider()
    return os.getenv("LLM_MODEL", LLM_CONFIG[provider]["model"])


# Configuration par défaut
DEFAULT_CONFIG = get_config()

# Export des configurations principales
__all__ = [
    "BASE_DIR",
    "SERVICES_DIR",
    "TESTS_DIR",
    "DATA_DIR",
    "LLM_CONFIG",
    "TAXONOMY",
    "DETECTION_PATTERNS",
    "DATA_TYPES",
    "PERFORMANCE_METRICS",
    "TEST_CONFIG",
    "STREAMLIT_CONFIG",
    "COLORS",
    "LOGGING_CONFIG",
    "EXPORT_CONFIG",
    "MODEL_CONFIG",
    "VISUALIZATION_CONFIG",
    "get_config",
    "get_llm_config",
    "get_patterns",
    "get_data_type_config",
    "is_development_mode",
    "get_debug_mode",
    "get_log_level",
    "get_llm_provider",
    "get_llm_model",
]
