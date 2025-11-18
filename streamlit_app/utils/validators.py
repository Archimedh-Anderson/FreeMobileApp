"""
Validateurs pour fichiers et données
Validation robuste avec messages d'erreur détaillés
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

# Import magic with fallback for Streamlit Cloud
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, MIME type validation disabled")

from ..config.settings import get_config

logger = logging.getLogger(__name__)


class FileValidator:
    """Validateur de fichiers avec vérifications complètes"""

    def __init__(self):
        self.config = get_config()
        self.required_columns = ["text"]  # Colonne minimale requise
        self.recommended_columns = [
            "text",
            "author",
            "date",
            "retweet_count",
            "favorite_count",
        ]

    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """Valide un fichier uploadé"""

        try:
            # Vérification de base
            if not uploaded_file:
                return {
                    "valid": False,
                    "error": "Aucun fichier fourni",
                    "suggestion": "Veuillez sélectionner un fichier à analyser",
                }

            # Vérification du nom
            if not uploaded_file.name:
                return {
                    "valid": False,
                    "error": "Nom de fichier manquant",
                    "suggestion": "Le fichier doit avoir un nom valide",
                }

            # Vérification de la taille
            if uploaded_file.size > self.config.max_file_size:
                return {
                    "valid": False,
                    "error": f"Fichier trop volumineux ({self._format_size(uploaded_file.size)})",
                    "suggestion": f"Taille maximale autorisée: {self._format_size(self.config.max_file_size)}",
                }

            if uploaded_file.size == 0:
                return {
                    "valid": False,
                    "error": "Fichier vide",
                    "suggestion": "Le fichier doit contenir des données",
                }

            # Vérification de l'extension
            file_extension = self._get_file_extension(uploaded_file.name)
            if file_extension not in self.config.supported_formats:
                return {
                    "valid": False,
                    "error": f"Format non supporté: {file_extension}",
                    "suggestion": f"Formats supportés: {', '.join(self.config.supported_formats)}",
                }

            # Vérification du type MIME (si disponible)
            if MAGIC_AVAILABLE:
                try:
                    file_content = uploaded_file.read(
                        1024
                    )  # Lire les premiers 1024 bytes
                    uploaded_file.seek(0)  # Reset position

                    mime_type = magic.from_buffer(file_content, mime=True)
                    expected_mimes = {
                        ".csv": ["text/csv", "text/plain", "application/csv"],
                        ".xlsx": [
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        ],
                        ".xls": ["application/vnd.ms-excel"],
                        ".json": ["application/json", "text/json"],
                        ".parquet": ["application/octet-stream"],
                    }

                    if file_extension in expected_mimes:
                        if mime_type not in expected_mimes[file_extension]:
                            logger.warning(
                                f"MIME type mismatch: expected {expected_mimes[file_extension]}, got {mime_type}"
                            )

                except Exception as e:
                    logger.warning(f"Impossible de vérifier le type MIME: {e}")
            else:
                logger.debug(
                    "python-magic not available, skipping MIME type validation"
                )

            return {
                "valid": True,
                "file_size": uploaded_file.size,
                "file_extension": file_extension,
                "warnings": self._get_file_warnings(uploaded_file),
            }

        except Exception as e:
            logger.error(f"Erreur lors de la validation du fichier: {str(e)}")
            return {
                "valid": False,
                "error": f"Erreur de validation: {str(e)}",
                "suggestion": "Vérifiez que le fichier n'est pas corrompu",
            }

    def validate_data_structure(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Valide la structure des données"""

        try:
            warnings = []
            suggestions = []

            # Vérification des colonnes requises
            missing_required = [
                col for col in self.required_columns if col not in data.columns
            ]
            if missing_required:
                return {
                    "valid": False,
                    "error": f"Colonnes requises manquantes: {', '.join(missing_required)}",
                    "suggestions": [
                        f"Ajoutez une colonne '{col}' avec le contenu des tweets"
                        for col in missing_required
                    ],
                }

            # Vérification des colonnes recommandées
            missing_recommended = [
                col for col in self.recommended_columns if col not in data.columns
            ]
            if missing_recommended:
                warnings.append(
                    f"Colonnes recommandées manquantes: {', '.join(missing_recommended)}"
                )
                suggestions.append(
                    "Ajoutez les colonnes 'author', 'date' pour une meilleure analyse"
                )

            # Vérification de la qualité des données
            if "text" in data.columns:
                # Vérification des valeurs nulles
                null_count = data["text"].isnull().sum()
                if null_count > 0:
                    warnings.append(f"{null_count} tweets avec texte vide")
                    suggestions.append("Supprimez les lignes avec des tweets vides")

                # Vérification de la longueur des textes
                if not data["text"].empty:
                    text_lengths = data["text"].str.len()
                    avg_length = text_lengths.mean()
                    min_length = text_lengths.min()
                    max_length = text_lengths.max()

                    if min_length < 5:
                        warnings.append(
                            "Textes très courts détectés (moins de 5 caractères)"
                        )

                    if max_length > 1000:
                        warnings.append(
                            "Textes très longs détectés (plus de 1000 caractères)"
                        )

                    if avg_length < 10:
                        warnings.append("Longueur moyenne des textes très faible")
                        suggestions.append(
                            "Vérifiez que les données contiennent du contenu textuel valide"
                        )

            # Vérification du nombre de lignes
            row_count = len(data)
            if row_count > 10000:
                warnings.append(f"Fichier volumineux ({row_count:,} lignes)")
                suggestions.append(
                    "Considérez limiter à 1000 tweets pour les premiers tests"
                )
            elif row_count < 10:
                warnings.append("Fichier très petit (moins de 10 tweets)")
                suggestions.append(
                    "Ajoutez plus de données pour une analyse significative"
                )

            # Vérification des doublons
            if "text" in data.columns:
                duplicate_count = data["text"].duplicated().sum()
                if duplicate_count > 0:
                    warnings.append(f"{duplicate_count} tweets en double détectés")
                    suggestions.append("Considérez supprimer les doublons")

            return {
                "valid": True,
                "warnings": warnings,
                "suggestions": suggestions,
                "row_count": row_count,
                "column_count": len(data.columns),
                "data_quality_score": self._calculate_quality_score(data),
            }

        except Exception as e:
            logger.error(f"Erreur lors de la validation des données: {str(e)}")
            return {
                "valid": False,
                "error": f"Erreur de validation des données: {str(e)}",
                "suggestions": ["Vérifiez que le fichier contient des données valides"],
            }

    def _get_file_extension(self, filename: str) -> str:
        """Extrait l'extension du fichier"""
        return Path(filename).suffix.lower()

    def _format_size(self, size_bytes: int) -> str:
        """Formate la taille en format lisible"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _get_file_warnings(self, uploaded_file) -> List[str]:
        """Génère des avertissements pour le fichier"""
        warnings = []

        # Taille du fichier
        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
            warnings.append("Fichier volumineux - le traitement peut prendre du temps")

        # Extension
        file_extension = self._get_file_extension(uploaded_file.name)
        if file_extension == ".xls":
            warnings.append(
                "Fichier .xls détecté - considérez utiliser .xlsx pour de meilleures performances"
            )

        return warnings

    def _calculate_quality_score(self, data: pd.DataFrame) -> float:
        """Calcule un score de qualité des données (0-100)"""
        score = 100.0

        # Pénalités
        if "text" in data.columns:
            # Valeurs nulles
            null_ratio = data["text"].isnull().sum() / len(data)
            score -= null_ratio * 30

            # Doublons
            duplicate_ratio = data["text"].duplicated().sum() / len(data)
            score -= duplicate_ratio * 20

            # Longueur des textes
            if not data["text"].empty:
                avg_length = data["text"].str.len().mean()
                if avg_length < 10:
                    score -= 20
                elif avg_length < 20:
                    score -= 10

        # Bonus pour colonnes recommandées
        recommended_count = sum(
            1 for col in self.recommended_columns if col in data.columns
        )
        score += recommended_count * 5

        return max(0, min(100, score))


class DataValidator:
    """Validateur de données avec règles métier"""

    @staticmethod
    def validate_tweet_text(text: str) -> Dict[str, Any]:
        """Valide le texte d'un tweet"""
        if not text or not isinstance(text, str):
            return {"valid": False, "error": "Texte invalide"}

        text = text.strip()

        if len(text) < 3:
            return {"valid": False, "error": "Texte trop court"}

        if len(text) > 1000:
            return {"valid": False, "error": "Texte trop long"}

        return {"valid": True, "text": text}

    @staticmethod
    def validate_analysis_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la configuration d'analyse"""
        errors = []

        # Vérification des paramètres obligatoires
        required_params = ["llm_provider", "max_tweets", "batch_size", "user_role"]
        for param in required_params:
            if param not in config:
                errors.append(f"Paramètre manquant: {param}")

        # Vérification des valeurs
        if "max_tweets" in config:
            max_tweets = config["max_tweets"]
            if not isinstance(max_tweets, int) or max_tweets < 1 or max_tweets > 10000:
                errors.append("max_tweets doit être un entier entre 1 et 10000")

        if "batch_size" in config:
            batch_size = config["batch_size"]
            if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 50:
                errors.append("batch_size doit être un entier entre 1 et 50")

        if "llm_provider" in config:
            valid_providers = ["ollama", "mistral", "openai", "anthropic"]
            if config["llm_provider"] not in valid_providers:
                errors.append(
                    f"llm_provider doit être l'un de: {', '.join(valid_providers)}"
                )

        return {"valid": len(errors) == 0, "errors": errors}
