"""
Provider Manager - Gestion Centralisée des Providers de Classification
========================================================================

Module centralisé pour gérer la disponibilité et la configuration
de tous les providers de classification (Mistral Local/Ollama et Gemini API).

Développé dans le cadre d'un mémoire de master en Data Science et Intelligence Artificielle.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    logger.info(f"Fichier .env chargé depuis: {env_path}")
else:
    root_env = Path(__file__).parent.parent.parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=True)
        logger.info(f"Fichier .env chargé depuis: {root_env}")


@dataclass
class ProviderStatus:
    """
    État d'un provider de classification.

    Attributes:
        name: Nom du provider (ex: "Mistral Local (Ollama)")
        available: True si le provider est disponible et fonctionnel
        configured: True si le provider est configuré (mais peut ne pas être disponible)
        status_message: Message de statut (ex: "✅ Ollama disponible")
        error_message: Message d'erreur si non disponible (None si disponible)
        installation_command: Commande ou lien pour installer/configurer
        config_required: Dictionnaire avec les configurations requises
    """

    name: str
    available: bool
    configured: bool
    status_message: str
    error_message: Optional[str] = None
    installation_command: Optional[str] = None
    config_required: Optional[Dict] = None


class ProviderManager:
    """
    Gère tous les providers de classification avec vérification automatique.

    Cette classe centralise la vérification de disponibilité de tous les providers,
    permettant à l'application de s'adapter automatiquement selon les providers disponibles.
    """

    def __init__(self):
        """Initialise le gestionnaire de providers."""
        self.providers = {
            "mistral_local": self._check_mistral_local,
            "gemini_cloud": self._check_gemini_cloud,
        }
        self.cache = {}
        logger.info("ProviderManager initialisé")

    def check_ollama_connection(self) -> Tuple[bool, str]:
        """
        Vérifie si Ollama est en cours d'exécution et accessible.

        Returns:
            Tuple (bool, str): (True/False, message de statut)
        """
        try:
            import requests

            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)

            if response.status_code == 200:
                try:
                    data = response.json()
                    models = data.get("models", [])
                    model_count = len(models)
                    model_names = [m.get("name", "unknown") for m in models[:3]]

                    if model_count > 0:
                        return (
                            True,
                            f"✅ Ollama disponible ({model_count} modèle(s): {', '.join(model_names)}{'...' if model_count > 3 else ''})",
                        )
                    else:
                        return True, "✅ Ollama disponible (aucun modèle installé)"
                except Exception as e:
                    return True, f"✅ Ollama disponible (erreur parsing: {str(e)[:50]})"
            else:
                return False, f"❌ Ollama ne répond pas (code {response.status_code})"

        except ImportError:
            return False, "❌ Module requests non disponible (pip install requests)"
        except ConnectionError:
            return False, f"❌ Ollama non lancé ({ollama_url})"
        except Exception as e:
            error_msg = str(e)[:100]
            return False, f"❌ Erreur connexion Ollama: {error_msg}"

    def _check_mistral_local(self) -> ProviderStatus:
        """
        Vérifie la disponibilité de Mistral Local via Ollama.

        Returns:
            ProviderStatus avec les détails de disponibilité
        """
        # Vérifier si le module ollama est installé
        try:
            import ollama

            ollama_available = True
        except ImportError:
            return ProviderStatus(
                name="Mistral Local (Ollama)",
                available=False,
                configured=False,
                status_message="⚠️ Module ollama non installé",
                error_message="Le module Python 'ollama' n'est pas installé",
                installation_command="pip install ollama",
                config_required={"url": "http://localhost:11434", "model": "mistral"},
            )

        # Vérifier la connexion Ollama
        available, msg = self.check_ollama_connection()

        if available:
            # Vérifier si le modèle mistral est disponible
            try:
                import requests

                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                response = requests.get(f"{ollama_url}/api/tags", timeout=2)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    has_mistral = any(
                        "mistral" in m.get("name", "").lower() for m in models
                    )

                    if has_mistral:
                        return ProviderStatus(
                            name="Mistral Local (Ollama)",
                            available=True,
                            configured=True,
                            status_message=msg,
                            error_message=None,
                            installation_command=None,
                            config_required={"url": ollama_url, "model": "mistral"},
                        )
                    else:
                        return ProviderStatus(
                            name="Mistral Local (Ollama)",
                            available=False,
                            configured=True,
                            status_message="⚠️ Ollama disponible mais modèle mistral non installé",
                            error_message="Le modèle Mistral n'est pas installé dans Ollama",
                            installation_command="ollama pull mistral",
                            config_required={"url": ollama_url, "model": "mistral"},
                        )
            except Exception:
                pass  # On considère que c'est OK si on a réussi la première vérification

            return ProviderStatus(
                name="Mistral Local (Ollama)",
                available=True,
                configured=True,
                status_message=msg,
                error_message=None,
                installation_command=None,
                config_required={
                    "url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                    "model": "mistral",
                },
            )
        else:
            # Ollama n'est pas disponible
            return ProviderStatus(
                name="Mistral Local (Ollama)",
                available=False,
                configured=False,
                status_message=msg,
                error_message="Ollama n'est pas en cours d'exécution ou inaccessible",
                installation_command="https://ollama.ai - Téléchargez le client et lancez 'ollama serve'",
                config_required={"url": "http://localhost:11434", "model": "mistral"},
            )

    def _check_gemini_cloud(self) -> ProviderStatus:
        """
        Vérifie la disponibilité de Gemini API.

        Returns:
            ProviderStatus avec les détails de disponibilité
        """
        # Vérifier si le module est installé
        try:
            import google.generativeai as genai

            gemini_module_available = True
        except ImportError:
            return ProviderStatus(
                name="Gemini API (Google Cloud)",
                available=False,
                configured=False,
                status_message="⚠️ Module google-generativeai non installé",
                error_message="Le module Python 'google-generativeai' n'est pas installé",
                installation_command="pip install google-generativeai",
                config_required={"api_key": ""},
            )

        # Récupérer la clé API
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key or api_key.strip() == "":
            return ProviderStatus(
                name="Gemini API (Google Cloud)",
                available=False,
                configured=False,
                status_message="⚠️ Clé API non configurée",
                error_message="GEMINI_API_KEY non trouvée dans les variables d'environnement",
                installation_command="https://ai.google.dev/api - Obtenez votre clé API",
                config_required={"api_key": ""},
            )

        # Tester la clé API
        try:
            genai.configure(api_key=api_key)
            # Essayer de lister les modèles pour vérifier la clé
            try:
                models = list(genai.list_models())
                model_names = [m.name for m in models[:3]]

                return ProviderStatus(
                    name="Gemini API (Google Cloud)",
                    available=True,
                    configured=True,
                    status_message=f"✅ Gemini API configurée ({len(models)} modèle(s) disponibles)",
                    error_message=None,
                    installation_command=None,
                    config_required={
                        "api_key": api_key[:10] + "..." if len(api_key) > 10 else "***"
                    },
                )
            except Exception as list_error:
                # Si list_models échoue, on peut quand même considérer que la clé est valide
                # (certaines clés peuvent avoir des restrictions)
                return ProviderStatus(
                    name="Gemini API (Google Cloud)",
                    available=True,
                    configured=True,
                    status_message="✅ Gemini API configurée",
                    error_message=None,
                    installation_command=None,
                    config_required={
                        "api_key": api_key[:10] + "..." if len(api_key) > 10 else "***"
                    },
                )

        except Exception as e:
            error_msg = str(e)[:150]
            return ProviderStatus(
                name="Gemini API (Google Cloud)",
                available=False,
                configured=True,
                status_message="❌ Clé API invalide",
                error_message=f"Erreur de validation: {error_msg}",
                installation_command="https://ai.google.dev/api - Vérifiez votre clé API",
                config_required={"api_key": ""},
            )

    def get_all_statuses(self) -> Dict[str, ProviderStatus]:
        """
        Retourne le statut de tous les providers.

        Returns:
            Dictionnaire avec les statuts de tous les providers
        """
        return {
            provider_key: check_func()
            for provider_key, check_func in self.providers.items()
        }

    def get_available_providers(self) -> List[str]:
        """
        Retourne la liste des noms des providers disponibles.

        Returns:
            Liste des noms des providers disponibles
        """
        statuses = self.get_all_statuses()
        return [status.name for status in statuses.values() if status.available]

    def get_provider_status(self, provider_name: str) -> Optional[ProviderStatus]:
        """
        Retourne le statut d'un provider spécifique par son nom.

        Args:
            provider_name: Nom du provider (ex: "Mistral Local (Ollama)")

        Returns:
            ProviderStatus si trouvé, None sinon
        """
        statuses = self.get_all_statuses()
        for status in statuses.values():
            if status.name == provider_name:
                return status
        return None

    def is_any_provider_available(self) -> bool:
        """
        Vérifie s'il y a au moins un provider disponible.

        Returns:
            True si au moins un provider est disponible, False sinon
        """
        return len(self.get_available_providers()) > 0

    def get_default_provider(self) -> Optional[str]:
        """
        Retourne le nom du provider par défaut (le premier disponible).

        Returns:
            Nom du provider par défaut ou None si aucun disponible
        """
        available = self.get_available_providers()
        if available:
            return available[0]
        return None


# Instance globale pour utilisation dans l'application
provider_manager = ProviderManager()
