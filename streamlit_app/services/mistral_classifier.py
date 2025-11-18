"""
Module de Classification Mistral - FreeMobilaChat
=================================================

Classification de tweets avec Mistral via Ollama (local).
Conforme aux spécifications techniques du projet.

Fonctionnalités:
- Classification par lots (batch processing)
- Retry logic (3 tentatives)
- Progress bar Streamlit
- Format JSON structuré
"""

# Imports des bibliothèques tierces pour la manipulation de données
from typing import List, Dict, Optional, Any  # Typage statique pour la validation
import pandas as pd  # Manipulation de DataFrame pour le traitement par lot
import json  # Parsing des réponses JSON du modèle Mistral
import re  # Expressions régulières pour l'extraction de données structurées
import time  # Gestion des délais entre les tentatives
import logging  # Journalisation des opérations et erreurs
import streamlit as st  # Interface utilisateur et barre de progression
import os  # Accès aux variables d'environnement

# Configuration du logger pour le suivi des opérations
logger = logging.getLogger(__name__)

# Configuration des paramètres de traitement par lot (conformes aux spécifications)
BATCH_SIZE = 50  # Nombre de tweets traités simultanément pour optimiser la performance
MAX_RETRIES = 3  # Nombre maximal de tentatives en cas d'échec de classification
RETRY_DELAY = 2  # Délai en secondes entre chaque tentative pour éviter la surcharge

SENTIMENT_OPTIONS = ["positif", "negatif", "neutre"]
CATEGORY_OPTIONS = ["produit", "service", "support", "promotion", "autre"]
URGENCE_OPTIONS = ["haute", "moyenne", "faible"]
CLAIM_OPTIONS = ["oui", "non"]
INCIDENT_OPTIONS = [
    "panne_connexion",
    "bug_freebox",
    "probleme_facturation",
    "probleme_mobile",
    "retard_activation",
    "debit_insuffisant",
    "information",
    "aucun",
    "non_specifie",
]
TOPIC_OPTIONS = [
    "fibre",
    "mobile",
    "reseau",
    "freebox",
    "wifi",
    "facture",
    "service_client",
    "support_technique",
    "promotion",
    "autre",
]

# Import conditionnel d'Ollama avec gestion d'erreur gracieuse
try:
    import ollama  # Bibliothèque cliente pour communiquer avec le serveur Ollama local

    OLLAMA_AVAILABLE = True  # Indicateur de disponibilité du module
except ImportError:
    OLLAMA_AVAILABLE = False  # Désactivation si le module n'est pas installé
    logger.warning(
        "Module ollama non disponible. Installation requise: pip install ollama"
    )


class MistralClassifier:
    """
    Classificateur de tweets utilisant le modèle Mistral via Ollama

    Cette classe implémente un système de classification par lots avec gestion
    robuste des erreurs, mécanisme de retry automatique et système de fallback.
    """

    def __init__(
        self,
        model_name: str = "mistral",
        batch_size: int = BATCH_SIZE,
        temperature: float = 0.1,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialise le classificateur Mistral avec les paramètres de configuration

        Args:
            model_name: Nom du modèle Ollama à utiliser (mistral, llama2, etc.)
            batch_size: Taille des lots pour le traitement par batch
            temperature: Paramètre de créativité du modèle (0.0 = déterministe, 1.0 = créatif)
            max_retries: Nombre maximal de tentatives en cas d'échec de requête
        """
        # Stockage des paramètres de configuration dans les attributs d'instance
        self.model_name = model_name  # Identification du modèle LLM à utiliser
        self.batch_size = batch_size  # Définition de la taille des lots de traitement
        self.temperature = (
            temperature  # Contrôle de la variabilité des réponses du modèle
        )
        self.max_retries = (
            max_retries  # Configuration de la résilience face aux erreurs
        )

        # Configuration des options Ollama pour le contrôle fin du modèle
        self.ollama_options = {
            "temperature": temperature,  # Reproductibilité des résultats avec valeur basse
            "num_predict": 2000,  # Limitation du nombre de tokens générés pour éviter les réponses trop longues
            "top_p": 0.9,  # Échantillonnage nucléaire pour équilibrer créativité et cohérence
        }

        # Vérification de la disponibilité et de la connexion au serveur Ollama
        self._check_ollama_connection()

        # Journalisation de l'initialisation réussie avec les paramètres
        logger.info(
            f"MistralClassifier initialisé: model={model_name}, batch_size={batch_size}"
        )

    def _check_ollama_connection(self) -> bool:
        """
        Vérifie la disponibilité et l'état de la connexion au serveur Ollama local

        Cette méthode effectue un test de connectivité pour s'assurer que le serveur
        Ollama est accessible avant de tenter des opérations de classification.

        Returns:
            True si Ollama est installé, démarré et accessible, False sinon
        """
        # Vérification de la disponibilité du module Python ollama
        if not OLLAMA_AVAILABLE:
            logger.warning(
                "Module ollama non installé. Installation: pip install ollama"
            )
            return False

        try:
            # Tentative de connexion au serveur en listant les modèles disponibles
            # Utiliser un timeout implicite via requests sous-jacent
            import requests
            from requests.exceptions import RequestException, Timeout

            # Vérifier que le serveur répond rapidement
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            try:
                response = requests.get(f"{base_url}/api/tags", timeout=3)
                if response.status_code == 200:
                    logger.info("Connexion Ollama OK")
                    # Vérifier que le modèle demandé est disponible
                    models_data = response.json()
                    available_models = [
                        m.get("name", "") for m in models_data.get("models", [])
                    ]
                    if self.model_name not in available_models and not any(
                        self.model_name in m for m in available_models
                    ):
                        logger.warning(
                            f"Modèle {self.model_name} non trouvé. Modèles disponibles: {', '.join(available_models[:3])}"
                        )
                    return True
                else:
                    logger.error(f"Ollama répond avec code {response.status_code}")
                    return False
            except Timeout:
                logger.error(
                    "Timeout lors de la connexion à Ollama (serveur non démarré?)"
                )
                return False
            except RequestException as e:
                logger.error(f"Erreur connexion Ollama: {e}")
                return False
        except ImportError:
            # Fallback si requests n'est pas disponible, utiliser ollama.list() directement
            try:
                ollama.list()
                logger.info("Connexion Ollama OK")
                return True
            except Exception as e:
                logger.error(f"Erreur connexion Ollama: {e}")
                return False
        except Exception as e:
            # Capture de toute erreur de connexion (serveur non démarré, timeout, etc.)
            logger.error(f"Erreur connexion Ollama: {e}")
            return False

    def build_classification_prompt(self, tweets: List[str]) -> str:
        """
        Construit le prompt d'instruction pour le modèle Mistral avec few-shot learning

        Cette méthode génère un prompt structuré qui guide le modèle LLM pour classifier
        les tweets selon des critères spécifiques à Free Mobile (sentiment, catégorie, confiance).

        Format de sortie JSON attendu:
        {
            "results": [
                {
                    "index": 0,
                    "sentiment": "positif|negatif|neutre",
                    "categorie": "produit|service|support|promotion|autre",
                    "score_confiance": 0.85
                }
            ]
        }

        Args:
            tweets: Liste des tweets à classifier (limitée par batch_size)

        Returns:
            Chaîne de caractères contenant le prompt complet formaté pour Mistral
        """
        # Construction de la liste numérotée des tweets pour référence dans les résultats
        tweets_text = ""  # Initialisation de la chaîne vide
        for i, tweet in enumerate(tweets):  # Itération avec index pour chaque tweet
            tweets_text += (
                f"{i}: {tweet}\n"  # Formatage index: contenu avec saut de ligne
            )

        # Construction du prompt avec instructions détaillées et taxonomie spécifique
        prompt = f"""Tu es un expert en analyse de tweets pour Free Mobile (opérateur télécoms français).

OBJECTIF: Classifier {len(tweets)} tweets et retourner TOUS les KPI suivants:
- sentiment ∈ {SENTIMENT_OPTIONS}
- categorie ∈ {CATEGORY_OPTIONS}
- is_claim ∈ {CLAIM_OPTIONS}
- urgence ∈ {URGENCE_OPTIONS}
- score_confiance entre 0.0 et 1.0 (2 décimales max)
- topics ∈ {TOPIC_OPTIONS}
- incident ∈ {INCIDENT_OPTIONS}

RAPPELS MÉTIERS:
- is_claim = "oui" dès qu'un problème, panne, bug, facturation ou mécontentement est mentionné.
- urgence = "haute" si panne totale, vocabulaire critique ("bloqué", "urgent", "impossible").
- incident doit décrire le problème (panne_connexion, probleme_facturation, etc.). Utilise "non_specifie" uniquement si tu ne peux pas déterminer.

CONTRAINTE: Chaque tweet DOIT avoir exactement un objet JSON complet avec toutes les clés ci-dessus.

TWEETS À CLASSIFIER:
{tweets_text}

FORMAT STRICT (aucun texte avant/après):
{{
    "results": [
        {{
            "index": 0,
            "sentiment": "negatif",
            "categorie": "support",
            "score_confiance": 0.94,
            "is_claim": "oui",
            "urgence": "haute",
            "topics": "reseau",
            "incident": "panne_connexion"
        }}
    ]
}}
"""

        return prompt  # Retour du prompt complet prêt pour l'envoi au LLM

    def classify_batch(self, tweets: List[str], retry: int = 0) -> List[Dict]:
        """
        Classifie un lot de tweets avec mécanisme de retry automatisé en cas d'échec

        Cette méthode implémente une stratégie de résilience avec tentatives multiples
        et fallback vers classification par règles si toutes les tentatives échouent.

        Args:
            tweets: Liste des tweets à classifier (généralement batch_size éléments)
            retry: Numéro de la tentative actuelle (0 = première tentative)

        Returns:
            Liste de dictionnaires contenant les résultats de classification:
            [{'index': 0, 'sentiment': 'positif', 'categorie': 'produit', 'score_confiance': 0.9}, ...]
        """
        # Vérification préalable de la disponibilité d'Ollama
        if not OLLAMA_AVAILABLE:
            logger.warning("Ollama non disponible, utilisation du fallback")
            return self._classify_batch_fallback(
                tweets
            )  # Basculement immédiat vers classification par règles

        try:
            # Construction du prompt d'instruction pour le modèle LLM
            prompt = self.build_classification_prompt(tweets)

            # Journalisation de la tentative en cours pour traçabilité
            logger.info(
                f"Appel Ollama pour {len(tweets)} tweets (tentative {retry + 1}/{self.max_retries})"
            )

            # Envoi de la requête au modèle Mistral via l'API Ollama
            response = ollama.generate(
                model=self.model_name,  # Sélection du modèle (mistral, llama2, etc.)
                prompt=prompt,  # Prompt construit avec taxonomie et exemples
                options=self.ollama_options,  # Paramètres de génération (température, tokens, etc.)
            )

            # Extraction du texte de réponse depuis la structure de données Ollama
            response_text = response.get("response", "")

            # Parsing et validation du JSON retourné par le modèle
            results = self._parse_ollama_response(response_text, len(tweets))

            # Validation de la présence et de la cohérence des résultats
            if results:
                logger.info(f"Classification réussie de {len(results)} tweets")
                return self._apply_quality_guards(tweets, results)
            else:
                # Lève une exception pour déclencher le mécanisme de retry
                raise ValueError("Réponse JSON invalide ou vide")

        except Exception as e:
            # Capture de toute erreur (timeout, JSON invalide, erreur serveur, etc.)
            logger.error(f"Erreur classification (tentative {retry + 1}): {e}")

            # Mécanisme de retry avec backoff exponentiel
            if retry < self.max_retries - 1:  # Vérification qu'il reste des tentatives
                logger.info(f"Nouvelle tentative dans {RETRY_DELAY}s...")
                time.sleep(
                    RETRY_DELAY
                )  # Pause avant retry pour éviter la surcharge serveur
                return self.classify_batch(
                    tweets, retry + 1
                )  # Appel récursif avec incrémentation du compteur
            else:
                # Épuisement des tentatives, basculement vers fallback
                logger.error(f"Échec après {self.max_retries} tentatives, fallback")
                return self._classify_batch_fallback(
                    tweets
                )  # Classification par règles comme solution de secours

    def _parse_ollama_response(
        self, response_text: str, expected_count: int
    ) -> List[Dict]:
        """
        Parse la réponse JSON d'Ollama

        Args:
            response_text: Texte de réponse brut
            expected_count: Nombre de résultats attendus

        Returns:
            Liste de classifications ou None si erreur
        """
        try:
            # Extraire le JSON (parfois Ollama ajoute du texte avant/après)
            json_match = re.search(r'\{.*"results".*\}', response_text, re.DOTALL)

            if json_match:
                json_text = json_match.group(0)
                data = json.loads(json_text)

                if "results" in data and isinstance(data["results"], list):
                    results = [self._validate_result(r) for r in data["results"]]

                    if len(results) == expected_count:
                        return results
                    else:
                        logger.warning(
                            f"Nombre de résultats incorrect: {len(results)} vs {expected_count}"
                        )
                        while len(results) < expected_count:
                            results.append(
                                self._validate_result({"index": len(results)})
                            )
                        return results[:expected_count]

            return None

        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return None

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise les champs renvoyés par Mistral pour alignement KPI."""
        sentiment = str(result.get("sentiment", "neutre")).lower().strip()
        if sentiment not in SENTIMENT_OPTIONS:
            sentiment = "neutre"

        categorie = str(result.get("categorie", "autre")).lower().strip()
        if categorie not in CATEGORY_OPTIONS:
            categorie = "autre"

        score = float(result.get("score_confiance", result.get("confidence", 0.6)))
        score = max(0.4, min(0.99, score))

        is_claim = (
            str(result.get("is_claim", "oui" if sentiment == "negatif" else "non"))
            .lower()
            .strip()
        )
        if is_claim not in CLAIM_OPTIONS:
            is_claim = "oui" if sentiment == "negatif" else "non"

        urgence = str(result.get("urgence", "faible")).lower().strip()
        if urgence not in URGENCE_OPTIONS:
            urgence = "moyenne" if is_claim == "oui" else "faible"

        topics = str(result.get("topics", categorie)).lower().strip()
        if topics not in TOPIC_OPTIONS:
            topics = categorie if categorie in TOPIC_OPTIONS else "autre"

        incident = (
            str(
                result.get("incident", "aucun" if is_claim == "non" else "non_specifie")
            )
            .lower()
            .strip()
        )
        if incident not in INCIDENT_OPTIONS:
            incident = "aucun" if is_claim == "non" else "non_specifie"

        return {
            "index": int(result.get("index", 0)),
            "sentiment": sentiment,
            "categorie": categorie,
            "score_confiance": round(score, 2),
            "is_claim": is_claim,
            "urgence": urgence,
            "topics": topics,
            "incident": incident,
        }

    def _classify_batch_fallback(self, tweets: List[str]) -> List[Dict]:
        """
        Classification fallback par règles si Ollama échoue

        Args:
            tweets: Liste de tweets

        Returns:
            Liste de classifications basiques
        """
        logger.info("Utilisation du classificateur fallback")

        results = []
        for i, tweet in enumerate(tweets):
            tweet_lower = tweet.lower()

            # Détection sentiment basique
            if any(
                w in tweet_lower
                for w in ["merci", "super", "génial", "excellent", "bravo"]
            ):
                sentiment = "positif"
            elif any(
                w in tweet_lower for w in ["panne", "nul", "bug", "problème", "mauvais"]
            ):
                sentiment = "negatif"
            else:
                sentiment = "neutre"

            # Détection catégorie basique
            if any(
                w in tweet_lower
                for w in ["fibre", "mobile", "box", "débit", "4g", "5g"]
            ):
                categorie = "produit"
            elif any(
                w in tweet_lower for w in ["sav", "service", "support", "assistance"]
            ):
                categorie = "service"
            elif any(
                w in tweet_lower
                for w in ["aide", "dépannage", "installation", "technicien"]
            ):
                categorie = "support"
            elif any(w in tweet_lower for w in ["offre", "promo", "prix", "réduction"]):
                categorie = "promotion"
            else:
                categorie = "autre"

            # Confiance basée sur la clarté
            confidence = 0.75 if sentiment != "neutre" or categorie != "autre" else 0.50

            is_claim = (
                "oui" if sentiment == "negatif" or "panne" in tweet_lower else "non"
            )
            if (
                "urgent" in tweet_lower
                or "impossible" in tweet_lower
                or "bloque" in tweet_lower
            ):
                urgence = "haute"
            elif is_claim == "oui":
                urgence = "moyenne"
            else:
                urgence = "faible"

            if "connexion" in tweet_lower or "reseau" in tweet_lower:
                incident = "panne_connexion"
            elif "facture" in tweet_lower or "paiement" in tweet_lower:
                incident = "probleme_facturation"
            elif "freebox" in tweet_lower:
                incident = "bug_freebox"
            else:
                incident = "aucun" if is_claim == "non" else "non_specifie"

            results.append(
                {
                    "index": i,
                    "sentiment": sentiment,
                    "categorie": categorie,
                    "score_confiance": confidence,
                    "is_claim": is_claim,
                    "urgence": urgence,
                    "topics": categorie if categorie != "autre" else "autre",
                    "incident": incident,
                }
            )

        return results

    def _apply_quality_guards(
        self, tweets: List[str], results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Heuristiques supplémentaires similaires au classificateur Gemini."""
        keywords_claim = [
            "panne",
            "bug",
            "incident",
            "bloqué",
            "bloque",
            "erreur",
            "facture",
            "dysfonctionnement",
            "plainte",
            "réclamation",
            "reclamation",
            "sav",
            "support",
            "service client",
            "retard",
            "activation",
            "installation",
            "ticket",
            "remboursement",
        ]
        urgent_tokens = [
            "urgent",
            "criti",
            "impossible",
            "panne totale",
            "depuis plusieurs jours",
            "bloqué",
            "bloque",
            "vite",
            "heures",
        ]
        facture_tokens = [
            "facture",
            "facturation",
            "paiement",
            "prelevement",
            "prélèvement",
            "remboursement",
        ]
        mobile_tokens = ["4g", "5g", "mobile", "smartphone", "reseau", "réseau"]
        service_tokens = ["sav", "service client", "support", "hotline", "assistance"]

        for idx, result in enumerate(results):
            text = tweets[idx].lower()
            if result.get("sentiment") == "negatif":
                result["is_claim"] = "oui"
                if result.get("urgence") == "faible":
                    result["urgence"] = "moyenne"
            if any(token in text for token in keywords_claim):
                result["is_claim"] = "oui"
                if result["urgence"] == "faible":
                    result["urgence"] = "moyenne"
            if any(token in text for token in urgent_tokens):
                result["urgence"] = "haute"
                result["is_claim"] = "oui"
            if any(tok in text for tok in facture_tokens):
                result["topics"] = "facture"
                result["incident"] = "probleme_facturation"
            if (
                any(tok in text for tok in mobile_tokens)
                or "connexion" in text
                or "wifi" in text
            ):
                result["topics"] = "reseau"
                if result["incident"] in ["aucun", "non_specifie"]:
                    result["incident"] = "panne_connexion"
            if any(tok in text for tok in service_tokens):
                result["topics"] = "service_client"
            if (
                result["incident"] == "aucun"
                and result["is_claim"] == "oui"
                and ("freebox" in text or "box" in text)
            ):
                result["incident"] = "bug_freebox"
            result["score_confiance"] = max(0.4, min(0.99, result["score_confiance"]))
        return results

    def classify_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str = "text_cleaned",
        show_progress: bool = True,
    ) -> pd.DataFrame:
        """
        Classifie tous les tweets du DataFrame par lots avec progress bar

        Conforme aux specs: batch processing avec progress bar Streamlit

        Args:
            df: DataFrame avec tweets nettoyés
            text_column: Colonne à classifier
            show_progress: Afficher la progress bar Streamlit

        Returns:
            DataFrame enrichi avec sentiment, categorie, score_confiance
        """
        logger.info(f"Classification de {len(df)} tweets par lots de {self.batch_size}")

        if text_column not in df.columns:
            logger.error(f"Colonne '{text_column}' non trouvée")
            return df

        # Préparation
        tweets = df[text_column].tolist()
        total_batches = (len(tweets) + self.batch_size - 1) // self.batch_size
        all_results = []

        # Progress bar Streamlit
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        # Traitement par lots
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(tweets))
            batch_tweets = tweets[start_idx:end_idx]

            # Mise à jour progress
            if show_progress:
                progress = (batch_idx + 1) / total_batches
                progress_bar.progress(progress)
                status_text.text(
                    f"Classification: Lot {batch_idx + 1}/{total_batches} ({start_idx + 1}-{end_idx} tweets)"
                )

            # Classification du lot
            batch_results = self.classify_batch(batch_tweets)
            all_results.extend(batch_results)

            # Petit délai entre les lots pour ne pas surcharger Ollama
            if batch_idx < total_batches - 1:
                time.sleep(0.5)

        # Nettoyage UI avec delay pour stabilité DOM
        if show_progress:
            time.sleep(0.1)
            try:
                progress_bar.empty()
                status_text.empty()
            except Exception:
                pass  # Ignore DOM errors

        # Enrichissement du DataFrame
        df_classified = df.copy()

        # Ajout des colonnes de classification
        df_classified["sentiment"] = [r.get("sentiment", "neutre") for r in all_results]
        df_classified["categorie"] = [r.get("categorie", "autre") for r in all_results]
        df_classified["score_confiance"] = [
            r.get("score_confiance", 0.5) for r in all_results
        ]

        # Ajout de métadonnées
        df_classified["classification_method"] = "mistral"
        df_classified["model_name"] = self.model_name
        df_classified["classification_timestamp"] = pd.Timestamp.now().isoformat()

        logger.info(f"✅ Classification terminée: {len(df_classified)} tweets enrichis")

        return df_classified

    def get_classification_stats(self, df_classified: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcule les statistiques de classification

        Args:
            df_classified: DataFrame avec classifications

        Returns:
            Dictionnaire de statistiques
        """
        if "sentiment" not in df_classified.columns:
            return {}

        stats = {
            "total_classified": len(df_classified),
            "sentiment_distribution": df_classified["sentiment"]
            .value_counts()
            .to_dict(),
            "categorie_distribution": (
                df_classified["categorie"].value_counts().to_dict()
                if "categorie" in df_classified.columns
                else {}
            ),
            "avg_confidence": (
                float(df_classified["score_confiance"].mean())
                if "score_confiance" in df_classified.columns
                else 0.0
            ),
            "min_confidence": (
                float(df_classified["score_confiance"].min())
                if "score_confiance" in df_classified.columns
                else 0.0
            ),
            "max_confidence": (
                float(df_classified["score_confiance"].max())
                if "score_confiance" in df_classified.columns
                else 0.0
            ),
        }

        return stats


# Fonctions utilitaires
def check_ollama_availability() -> bool:
    """
    Vérifie si Ollama est disponible et répond avec timeout

    Returns:
        True si Ollama est accessible, False sinon
    """
    if not OLLAMA_AVAILABLE:
        logger.debug("Module ollama non disponible")
        return False

    try:
        # Vérifier avec timeout via requests si disponible
        try:
            import requests
            from requests.exceptions import RequestException, Timeout

            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.get(f"{base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                logger.debug("Ollama disponible et répond")
                return True
            else:
                logger.debug(f"Ollama répond avec code {response.status_code}")
                return False
        except (ImportError, Timeout, RequestException):
            # Fallback vers ollama.list() si requests non disponible ou timeout
            try:
                ollama.list()
                logger.debug("Ollama disponible (via ollama.list)")
                return True
            except Exception:
                return False
    except Exception as e:
        logger.debug(f"Erreur vérification Ollama: {e}")
        return False


def list_available_models() -> List[str]:
    """
    Liste les modèles Ollama disponibles

    Returns:
        Liste des noms de modèles
    """
    if not OLLAMA_AVAILABLE:
        return []

    try:
        models_response = ollama.list()
        if "models" in models_response:
            return [model["name"] for model in models_response["models"]]
        return []
    except:
        return []


def classify_single_tweet(tweet: str, model_name: str = "mistral") -> Dict[str, Any]:
    """
    Classifie un tweet unique avec Mistral

    Args:
        tweet: Texte du tweet
        model_name: Nom du modèle Ollama

    Returns:
        Dictionnaire avec classification
    """
    classifier = MistralClassifier(model_name=model_name, batch_size=1)
    results = classifier.classify_batch([tweet])
    return (
        results[0]
        if results
        else {
            "index": 0,
            "sentiment": "neutre",
            "categorie": "autre",
            "score_confiance": 0.5,
        }
    )
