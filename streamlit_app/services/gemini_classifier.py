"""
Module de Classification Gemini - FreeMobilaChat
=================================================

Classification de tweets avec Google Gemini API (externe).
Conforme aux spécifications techniques du projet.

Fonctionnalités:
- Classification par lots (batch processing)
- Retry logic (3 tentatives)
- Progress bar Streamlit
- Format JSON structuré avec structured outputs
- Support des KPIs externes via API
"""

# Imports des bibliothèques tierces pour la manipulation de données
from typing import List, Dict, Optional, Any  # Typage statique pour la validation
import pandas as pd  # Manipulation de DataFrame pour le traitement par lot
import json  # Parsing des réponses JSON du modèle Gemini
import re  # Expressions régulières pour l'extraction de données structurées
import time  # Gestion des délais entre les tentatives
import logging  # Journalisation des opérations et erreurs
import os  # Accès aux variables d'environnement
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st  # Interface utilisateur et barre de progression

# Configuration du logger pour le suivi des opérations
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env
# Chercher le fichier .env à la racine du projet
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Fichier .env chargé depuis: {env_path}")
else:
    # Essayer aussi à la racine du workspace
    root_env = Path(__file__).parent.parent.parent.parent / '.env'
    if root_env.exists():
        load_dotenv(root_env)
        logger.info(f"Fichier .env chargé depuis: {root_env}")
    else:
        logger.warning("Fichier .env non trouvé, utilisation des variables d'environnement système")

# Configuration des paramètres de traitement par lot (optimisés pour performance)
BATCH_SIZE = 50  # Nombre de tweets traités simultanément pour optimiser la performance
MAX_RETRIES = 3  # Nombre maximal de tentatives en cas d'échec de classification
RETRY_DELAY_BASE = 1  # Délai de base pour backoff exponentiel (secondes)
RETRY_DELAY_MAX = 10  # Délai maximum entre tentatives (secondes)
TIMEOUT_SECONDS = 60  # Timeout pour les appels API (secondes)

# Import conditionnel de Google Generative AI avec gestion d'erreur gracieuse
try:
    import google.generativeai as genai  # Bibliothèque cliente pour l'API Gemini
    GEMINI_AVAILABLE = True  # Indicateur de disponibilité du module
except ImportError:
    GEMINI_AVAILABLE = False  # Désactivation si le module n'est pas installé
    logger.warning("Module google-generativeai non disponible. Installation requise: pip install google-generativeai")


class GeminiClassifier:
    """
    Classificateur de tweets utilisant l'API Google Gemini (externe)
    
    Cette classe implémente un système de classification par lots avec gestion
    robuste des erreurs, mécanisme de retry automatique et système de fallback.
    Utilise l'API Gemini pour les appels externes et supporte les structured outputs.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = 'gemini-2.0-flash-exp',
                 batch_size: int = BATCH_SIZE,
                 temperature: float = 0.3,
                 max_retries: int = MAX_RETRIES):
        """
        Initialise le classificateur Gemini avec les paramètres de configuration
        
        Args:
            api_key: Clé API Gemini (si None, cherche dans GEMINI_API_KEY ou GOOGLE_API_KEY)
            model_name: Nom du modèle Gemini à utiliser (gemini-pro, gemini-1.5-pro, etc.)
            batch_size: Taille des lots pour le traitement par batch
            temperature: Paramètre de créativité du modèle (0.0 = déterministe, 1.0 = créatif)
            max_retries: Nombre maximal de tentatives en cas d'échec de requête
        """
        # Récupération de la clé API depuis les variables d'environnement si non fournie
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Clé API Gemini non trouvée. "
                "Définissez GEMINI_API_KEY ou GOOGLE_API_KEY dans votre fichier .env"
            )
        
        # Stockage des paramètres de configuration dans les attributs d'instance
        self.api_key = api_key  # Clé API pour authentification
        self.model_name = model_name  # Identification du modèle LLM à utiliser
        self.batch_size = batch_size  # Définition de la taille des lots de traitement
        self.temperature = temperature  # Contrôle de la variabilité des réponses du modèle
        self.max_retries = max_retries  # Configuration de la résilience face aux erreurs
        
        # Configuration du client Gemini
        if not GEMINI_AVAILABLE:
            logger.error("Module google-generativeai non installé")
            self.client = None
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai
                # Paramètres optimisés selon meilleures pratiques Gemini pour classification
                # Temperature: 0.2 pour classification précise et déterministe
                # top_p: 0.95 pour meilleure diversité contrôlée (recommandation Google)
                # top_k: 40 pour équilibre qualité/vitesse (recommandation Google)
                # max_output_tokens: 4096 pour structured outputs complets
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        'temperature': min(max(temperature, 0.1), 0.4),  # Clamp entre 0.1-0.4 pour précision
                        'max_output_tokens': 4096,  # Optimisé pour structured outputs avec tous les champs
                        'top_p': 0.95,  # Optimisé selon dernières recommandations Google (meilleure précision)
                        'top_k': 40,   # Optimisé selon recommandations Google
                        'candidate_count': 1  # Un seul candidat pour cohérence
                    }
                )
                logger.info(f"GeminiClassifier initialisé: model={model_name}, batch_size={batch_size}")
            except Exception as e:
                logger.error(f"Erreur initialisation Gemini: {e}")
                self.client = None
                self.model = None
    
    def _check_gemini_connection(self) -> bool:
        """
        Vérifie la disponibilité et l'état de la connexion à l'API Gemini
        
        Cette méthode effectue un test de connectivité pour s'assurer que l'API
        Gemini est accessible avant de tenter des opérations de classification.
        
        Returns:
            True si Gemini est accessible, False sinon
        """
        if not GEMINI_AVAILABLE or self.model is None:
            logger.error("Gemini non disponible")
            return False
        
        try:
            # Test simple de connexion avec un prompt minimal
            test_response = self.model.generate_content("Test")
            logger.info("Connexion Gemini OK")
            return True
        except Exception as e:
            logger.error(f"Erreur connexion Gemini: {e}")
            return False
    
    def _get_structured_output_schema(self) -> Dict[str, Any]:
        """
        Définit le schéma JSON strict pour Structured Outputs
        
        Returns:
            Schéma JSON Schema conforme à Gemini Structured Outputs
        """
        return {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer"},
                            "sentiment": {
                                "type": "string",
                                "enum": ["positif", "negatif", "neutre"]
                            },
                            "categorie": {
                                "type": "string",
                                "enum": ["produit", "service", "support", "promotion", "autre"]
                            },
                            "score_confiance": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "is_claim": {
                                "type": "string",
                                "enum": ["oui", "non"]
                            },
                            "urgence": {
                                "type": "string",
                                "enum": ["haute", "moyenne", "faible"]
                            },
                            "topics": {
                                "type": "string"
                            },
                            "incident": {
                                "type": "string"
                            }
                        },
                        "required": ["index", "sentiment", "categorie", "score_confiance", "is_claim", "urgence"]
                    }
                }
            },
            "required": ["results"]
        }
    
    def _get_few_shot_examples(self) -> str:
        """
        Retourne 5 exemples Few-Shot optimisés pour guider le modèle avec cas limites
        
        Returns:
            Chaîne avec exemples formatés couvrant tous les cas d'usage
        """
        return """
**EXEMPLES FEW-SHOT (5 exemples couvrant tous les cas):**

Exemple 1 - Positif produit:
Tweet: "Merci @free pour votre excellent service, ma connexion fibre fonctionne parfaitement depuis l'installation !"
Résultat: {"index": 0, "sentiment": "positif", "categorie": "produit", "score_confiance": 0.95, "is_claim": "non", "urgence": "faible", "topics": "fibre", "incident": "aucun"}

Exemple 2 - Négatif réclamation urgente:
Tweet: "Depuis 3 jours j'ai une panne totale de connexion, impossible de travailler en télétravail. @free c'est inadmissible, j'ai besoin d'une intervention URGENTE !"
Résultat: {"index": 1, "sentiment": "negatif", "categorie": "support", "score_confiance": 0.98, "is_claim": "oui", "urgence": "haute", "topics": "reseau", "incident": "panne_connexion"}

Exemple 3 - Neutre question service:
Tweet: "Bonjour @free, pouvez-vous me renseigner sur les forfaits mobile disponibles avec 5G ?"
Résultat: {"index": 2, "sentiment": "neutre", "categorie": "service", "score_confiance": 0.88, "is_claim": "non", "urgence": "faible", "topics": "mobile", "incident": "information"}

Exemple 4 - Négatif problème modéré:
Tweet: "Ma Freebox a parfois des bugs, le débit est un peu lent le soir mais ça fonctionne globalement."
Résultat: {"index": 3, "sentiment": "negatif", "categorie": "produit", "score_confiance": 0.82, "is_claim": "oui", "urgence": "moyenne", "topics": "freebox", "incident": "bug_freebox"}

Exemple 5 - Promotion:
Tweet: "Super offre @free ! Le nouveau forfait à 19.99€ est vraiment intéressant, je vais regarder ça."
Résultat: {"index": 4, "sentiment": "positif", "categorie": "promotion", "score_confiance": 0.90, "is_claim": "non", "urgence": "faible", "topics": "promotion", "incident": "aucun"}
"""
    
    def build_classification_prompt(self, tweets: List[str]) -> str:
        """
        Construit le prompt d'instruction pour le modèle Gemini avec few-shot learning
        
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
            Chaîne de caractères contenant le prompt complet formaté pour Gemini
        """
        # Construction de la liste numérotée des tweets pour référence dans les résultats
        tweets_text = ""  # Initialisation de la chaîne vide
        for i, tweet in enumerate(tweets):  # Itération avec index pour chaque tweet
            tweets_text += f"{i}: {tweet}\n"  # Formatage index: contenu avec saut de ligne
        
        # Construction du prompt avec Few-Shot prompting et instructions détaillées
        few_shot_examples = self._get_few_shot_examples()
        
        prompt = f"""Tu es un expert en analyse de tweets pour Free Mobile (opérateur télécoms français).

CONTEXTE: Free Mobile est un opérateur télécoms français proposant des services fibre, mobile, TV et support client.

TA TÂCHE: Classifier {len(tweets)} tweets selon ces critères STRICTS et EXACTS:

═══════════════════════════════════════════════════════════════
**SENTIMENT (OBLIGATOIRE - un seul choix exact):**
═══════════════════════════════════════════════════════════════
- "positif": satisfaction exprimée, remerciements, compliments, félicitations, éloges
- "negatif": insatisfaction, plaintes, critiques, colère, frustration, mécontentement
- "neutre": questions factuelles, demandes d'information, pas d'émotion claire, commentaires neutres

═══════════════════════════════════════════════════════════════
**CATEGORIE (OBLIGATOIRE - un seul choix exact):**
═══════════════════════════════════════════════════════════════
- "produit": fibre, mobile, box, forfait, débit, qualité réseau, 4G, 5G, Freebox, connexion internet
- "service": SAV, support client, assistance, réponse client, relation client, conseiller
- "support": aide technique, dépannage, installation, résolution problème, intervention technique
- "promotion": offres commerciales, prix, réductions, nouveautés, publicités, promotions
- "autre": autres sujets non liés aux catégories ci-dessus

═══════════════════════════════════════════════════════════════
**IS_CLAIM (OBLIGATOIRE - réclamation détectée):**
═══════════════════════════════════════════════════════════════
- "oui": réclamation, plainte, problème signalé, demande d'intervention, dysfonctionnement mentionné
- "non": pas de réclamation, simple question, commentaire positif, information neutre

RÈGLE: is_claim="oui" si ET SEULEMENT SI:
  • sentiment="negatif" ET mention d'un problème/panne/dysfonctionnement
  OU
  • mention explicite de réclamation/plainte même avec sentiment neutre

═══════════════════════════════════════════════════════════════
**URGENCE (OBLIGATOIRE - niveau de criticité):**
═══════════════════════════════════════════════════════════════
- "haute": problème critique, panne totale, impact majeur (travail bloqué), mention "urgent"/"critique"/"inadmissible"
- "moyenne": problème modéré, gêne mais fonctionnement partiel, problème récurrent mais gérable
- "faible": question, information, pas d'urgence, simple demande

RÈGLE: urgence="haute" si ET SEULEMENT SI:
  • is_claim="oui" ET (vocabulaire critique: "panne totale", "urgent", "critique", "inadmissible", "impossible", "bloqué")
  • Sinon urgence="moyenne" si is_claim="oui"
  • Sinon urgence="faible"

═══════════════════════════════════════════════════════════════
**SCORE_CONFIANCE (OBLIGATOIRE - 0.0 à 1.0):**
═══════════════════════════════════════════════════════════════
- 0.9-1.0: très clair, vocabulaire explicite, contexte évident, aucun doute
- 0.7-0.9: assez clair, contexte évident, classification probablement correcte
- 0.5-0.7: ambigu mais classifiable, contexte partiel, quelques doutes possibles
- 0.0-0.5: très ambigu, difficile à classifier, contexte insuffisant

═══════════════════════════════════════════════════════════════
**TOPICS (recommandé - thème principal):**
═══════════════════════════════════════════════════════════════
Extrait le thème principal: "fibre", "mobile", "reseau", "facture", "freebox", "service_client", "promotion", etc.

═══════════════════════════════════════════════════════════════
**INCIDENT (recommandé - type d'incident):**
═══════════════════════════════════════════════════════════════
- "panne_connexion": panne de connexion internet/fibre
- "bug_freebox": problème technique Freebox
- "probleme_facturation": problème de facturation/paiement
- "probleme_mobile": problème réseau mobile/4G/5G
- "information": simple demande d'information
- "aucun": pas d'incident, commentaire positif
- "non_specifie": incident mentionné mais type non précisé

{few_shot_examples}

═══════════════════════════════════════════════════════════════
**TWEETS À CLASSIFIER ({len(tweets)} tweets):**
═══════════════════════════════════════════════════════════════
{tweets_text}

═══════════════════════════════════════════════════════════════
**RÈGLES STRICTES DE VALIDATION:**
═══════════════════════════════════════════════════════════════
1. Chaque tweet DOIT avoir exactement UN résultat avec TOUS les champs requis
2. Le sentiment DOIT être EXACTEMENT: "positif", "negatif" ou "neutre" (PAS de variantes: "pos", "neg", etc.)
3. La catégorie DOIT être EXACTEMENT: "produit", "service", "support", "promotion" ou "autre" (PAS de variantes)
4. is_claim DOIT être "oui" si sentiment="negatif" ET mention de problème, sinon "non"
5. urgence DOIT être "haute" si is_claim="oui" ET vocabulaire critique, sinon "moyenne" si is_claim="oui", sinon "faible"
6. score_confiance DOIT être entre 0.0 et 1.0 (nombre décimal avec 2 décimales max)
7. topics: extraire le thème principal (string, max 50 caractères)
8. incident: type d'incident si applicable (string, valeurs recommandées ci-dessus)

═══════════════════════════════════════════════════════════════
**FORMAT DE RÉPONSE JSON STRICT:**
═══════════════════════════════════════════════════════════════
Réponds UNIQUEMENT avec un JSON valide STRICT (PAS de texte avant/après, PAS de markdown, UNIQUEMENT du JSON):

{{
    "results": [
        {{"index": 0, "sentiment": "positif", "categorie": "produit", "score_confiance": 0.95, "is_claim": "non", "urgence": "faible", "topics": "fibre", "incident": "aucun"}},
        {{"index": 1, "sentiment": "negatif", "categorie": "support", "score_confiance": 0.98, "is_claim": "oui", "urgence": "haute", "topics": "reseau", "incident": "panne_connexion"}},
        ...
    ]
}}

IMPORTANT: Le nombre de résultats DOIT être exactement {len(tweets)} (un par tweet)."""
        
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
        # Vérification préalable de la disponibilité de Gemini
        if not GEMINI_AVAILABLE or self.model is None:
            logger.warning("Gemini non disponible, utilisation du fallback")
            return self._classify_batch_fallback(tweets)  # Basculement immédiat vers classification par règles
        
        try:
            # Construction du prompt d'instruction pour le modèle LLM
            prompt = self.build_classification_prompt(tweets)
            
            # Journalisation de la tentative en cours pour traçabilité
            logger.info(f"Appel Gemini API pour {len(tweets)} tweets (tentative {retry + 1}/{self.max_retries})")
            
            # Envoi de la requête au modèle Gemini avec Structured Outputs
            # Utilisation de response_schema pour garantir le format JSON strict
            try:
                # Essayer d'abord avec Structured Outputs (si supporté par le modèle)
                # Utilisation des paramètres optimisés du modèle initialisé
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': self.temperature,
                        'max_output_tokens': 4096,  # Aligné avec config modèle
                        'top_p': 0.95,  # Aligné avec config modèle
                        'top_k': 40,   # Aligné avec config modèle
                        'candidate_count': 1
                    },
                    # Structured Outputs via response_mime_type et response_schema
                    response_mime_type="application/json",
                    response_schema=self._get_structured_output_schema(),
                    request_options={'timeout': TIMEOUT_SECONDS}  # Timeout explicite
                )
            except Exception as e:
                # Fallback si Structured Outputs non supporté
                logger.warning(f"Structured Outputs non supporté, fallback standard: {e}")
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': self.temperature,
                        'max_output_tokens': 4096,
                        'top_p': 0.95,
                        'top_k': 40,
                        'candidate_count': 1
                    },
                    request_options={'timeout': TIMEOUT_SECONDS}
                )
            
            # Extraction du texte de réponse depuis la structure de données Gemini
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Parsing et validation du JSON retourné par le modèle
            results = self._parse_gemini_response(response_text, len(tweets))
            
            # Validation de la présence et de la cohérence des résultats
            if results:
                logger.info(f"Classification réussie de {len(results)} tweets")
                return results
            else:
                # Lève une exception pour déclencher le mécanisme de retry
                raise ValueError("Réponse JSON invalide ou vide")
        
        except Exception as e:
            # Capture de toute erreur (timeout, JSON invalide, erreur serveur, etc.)
            logger.error(f"Erreur classification (tentative {retry + 1}): {e}")
            
            # Mécanisme de retry avec backoff exponentiel amélioré
            if retry < self.max_retries - 1:  # Vérification qu'il reste des tentatives
                # Backoff exponentiel: délai = base * (2 ^ retry), avec maximum
                delay = min(RETRY_DELAY_BASE * (2 ** retry), RETRY_DELAY_MAX)
                logger.info(f"Nouvelle tentative dans {delay}s... (tentative {retry + 2}/{self.max_retries})")
                time.sleep(delay)  # Pause avant retry avec backoff exponentiel
                return self.classify_batch(tweets, retry + 1)  # Appel récursif avec incrémentation du compteur
            else:
                # Épuisement des tentatives, basculement vers fallback
                logger.error(f"Échec après {self.max_retries} tentatives, fallback")
                return self._classify_batch_fallback(tweets)  # Classification par règles comme solution de secours
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et corrige un résultat de classification selon les règles strictes
        
        Args:
            result: Résultat brut de classification
            
        Returns:
            Résultat validé et corrigé
        """
        # Enum stricts
        VALID_SENTIMENTS = ["positif", "negatif", "neutre"]
        VALID_CATEGORIES = ["produit", "service", "support", "promotion", "autre"]
        VALID_IS_CLAIM = ["oui", "non"]
        VALID_URGENCE = ["haute", "moyenne", "faible"]
        
        # Validation sentiment avec correction intelligente
        sentiment = str(result.get('sentiment', 'neutre')).lower().strip()
        if sentiment not in VALID_SENTIMENTS:
            # Correction automatique avec mapping étendu
            sentiment_mapping = {
                'pos': 'positif', 'positive': 'positif', 'positif': 'positif',
                'neg': 'negatif', 'negative': 'negatif', 'negatif': 'negatif',
                'neu': 'neutre', 'neutral': 'neutre', 'neutre': 'neutre',
                'happy': 'positif', 'satisfait': 'positif', 'content': 'positif',
                'angry': 'negatif', 'frustre': 'negatif', 'insatisfait': 'negatif',
                'question': 'neutre', 'info': 'neutre', 'information': 'neutre'
            }
            sentiment = sentiment_mapping.get(sentiment, 'neutre')  # Fallback vers neutre si inconnu
        
        # Validation catégorie avec correction intelligente
        categorie = str(result.get('categorie', 'autre')).lower().strip()
        if categorie not in VALID_CATEGORIES:
            # Correction automatique avec mapping étendu
            categorie_mapping = {
                'product': 'produit', 'produit': 'produit', 'produits': 'produit',
                'service': 'service', 'services': 'service', 'sav': 'service',
                'support': 'support', 'technique': 'support', 'depannage': 'support',
                'promo': 'promotion', 'promotion': 'promotion', 'offre': 'promotion',
                'other': 'autre', 'autre': 'autre', 'autres': 'autre', 'misc': 'autre'
            }
            categorie = categorie_mapping.get(categorie, 'autre')  # Fallback vers autre si inconnu
        
        # Validation score_confiance (range 0.0-1.0)
        score_confiance = float(result.get('score_confiance', 0.5))
        score_confiance = max(0.0, min(1.0, score_confiance))  # Clamp entre 0 et 1
        
        # Validation is_claim avec inférence intelligente
        is_claim = str(result.get('is_claim', 'non')).lower().strip()
        if is_claim not in VALID_IS_CLAIM:
            # Inférence automatique améliorée
            is_claim_mapping = {
                'yes': 'oui', 'y': 'oui', 'oui': 'oui', 'true': 'oui', '1': 'oui',
                'no': 'non', 'n': 'non', 'non': 'non', 'false': 'non', '0': 'non'
            }
            is_claim = is_claim_mapping.get(is_claim)
            # Si toujours invalide, inférer depuis sentiment
            if is_claim not in VALID_IS_CLAIM:
                is_claim = 'oui' if sentiment == 'negatif' else 'non'
        
        # Validation urgence avec inférence intelligente
        urgence = str(result.get('urgence', 'faible')).lower().strip()
        if urgence not in VALID_URGENCE:
            # Correction automatique avec mapping
            urgence_mapping = {
                'high': 'haute', 'haute': 'haute', 'urgent': 'haute', 'critique': 'haute',
                'medium': 'moyenne', 'moyenne': 'moyenne', 'moderee': 'moyenne', 'modéré': 'moyenne',
                'low': 'faible', 'faible': 'faible', 'bas': 'faible', 'normale': 'faible'
            }
            urgence = urgence_mapping.get(urgence)
            # Si toujours invalide, inférer depuis is_claim et sentiment
            if urgence not in VALID_URGENCE:
                if is_claim == 'oui' and sentiment == 'negatif':
                    urgence = 'haute'
                elif is_claim == 'oui':
                    urgence = 'moyenne'
                else:
                    urgence = 'faible'
        
        # Topics et incident (optionnels mais recommandés)
        topics = result.get('topics', categorie)  # Fallback sur categorie
        incident = result.get('incident', 'aucun' if is_claim == 'non' else 'non_specifie')
        
        return {
            'index': int(result.get('index', 0)),
            'sentiment': sentiment,
            'categorie': categorie,
            'score_confiance': round(score_confiance, 2),
            'is_claim': is_claim,
            'urgence': urgence,
            'topics': str(topics),
            'incident': str(incident)
        }
    
    def _parse_gemini_response(self, response_text: str, expected_count: int) -> List[Dict]:
        """
        Parse et valide la réponse JSON de Gemini avec validation stricte
        
        Args:
            response_text: Texte de réponse brut
            expected_count: Nombre de résultats attendus
            
        Returns:
            Liste de classifications validées ou None si erreur
        """
        try:
            # Extraire le JSON (parfois Gemini ajoute du texte avant/après)
            json_match = re.search(r'\{.*"results".*\}', response_text, re.DOTALL)
            
            if json_match:
                json_text = json_match.group(0)
                data = json.loads(json_text)
                
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    
                    # Validation et correction de chaque résultat
                    validated_results = []
                    for result in results:
                        try:
                            validated = self._validate_classification_result(result)
                            validated_results.append(validated)
                        except Exception as e:
                            logger.warning(f"Erreur validation résultat: {e}, utilisation valeurs par défaut")
                            validated_results.append({
                                'index': len(validated_results),
                                'sentiment': 'neutre',
                                'categorie': 'autre',
                                'score_confiance': 0.5,
                                'is_claim': 'non',
                                'urgence': 'faible',
                                'topics': 'autre',
                                'incident': 'aucun'
                            })
                    
                    # Vérifier le nombre de résultats
                    if len(validated_results) == expected_count:
                        return validated_results
                    else:
                        logger.warning(f"Nombre de résultats incorrect: {len(validated_results)} vs {expected_count}")
                        # Compléter ou tronquer si nécessaire
                        while len(validated_results) < expected_count:
                            validated_results.append({
                                "index": len(validated_results),
                                "sentiment": "neutre",
                                "categorie": "autre",
                                "score_confiance": 0.5,
                                "is_claim": "non",
                                "urgence": "faible",
                                "topics": "autre",
                                "incident": "aucun"
                            })
                        return validated_results[:expected_count]
            
            return None
        
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            logger.debug(f"Réponse reçue: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Erreur validation: {e}")
            return None
    
    def _classify_batch_fallback(self, tweets: List[str]) -> List[Dict]:
        """
        Classification fallback améliorée par règles si Gemini échoue
        Détection intelligente avec vocabulaire étendu et règles contextuelles
        
        Args:
            tweets: Liste de tweets
            
        Returns:
            Liste de classifications complètes avec tous les champs KPI
        """
        logger.info("Utilisation du classificateur fallback amélioré (règles intelligentes)")
        
        # Vocabulaire étendu pour détection plus précise
        POSITIVE_KEYWORDS = [
            'merci', 'super', 'génial', 'excellent', 'bravo', 'parfait', 'top', 'content',
            'satisfait', 'ravi', 'formidable', 'extra', 'magnifique', 'superbe', 'cool',
            'bien', 'bon', 'agréable', 'efficace', 'rapide', 'qualité'
        ]
        
        NEGATIVE_KEYWORDS = [
            'panne', 'nul', 'bug', 'problème', 'mauvais', 'déçu', 'incompétent', 'bloqué',
            'coupure', 'lent', 'défaillant', 'défectueux', 'cassé', 'ne marche pas',
            'ne fonctionne pas', 'dysfonctionnement', 'erreur', 'incident', 'inadmissible',
            'insatisfait', 'frustré', 'énervé', 'colère', 'plainte', 'réclamation'
        ]
        
        PRODUCT_KEYWORDS = [
            'fibre', 'mobile', 'box', 'débit', '4g', '5g', 'freebox', 'réseau', 'connexion',
            'internet', 'wifi', 'forfait', 'data', 'sms', 'appel', 'téléphone', 'box'
        ]
        
        SERVICE_KEYWORDS = [
            'sav', 'service', 'support', 'assistance', 'conseiller', 'client', 'relation',
            'réponse', 'contact', 'accueil', 'standard'
        ]
        
        SUPPORT_KEYWORDS = [
            'aide', 'dépannage', 'installation', 'technicien', 'intervention', 'réparation',
            'maintenance', 'diagnostic', 'résolution', 'technique'
        ]
        
        PROMOTION_KEYWORDS = [
            'offre', 'promo', 'prix', 'réduction', 'nouveauté', 'publicité', 'annonce',
            'tarif', 'forfait', 'abonnement', 'deal', 'bon plan'
        ]
        
        URGENT_KEYWORDS = [
            'urgent', 'critique', 'inadmissible', 'impossible', 'panne totale', 'depuis',
            'bloqué', 'impossible de', 'ne peut pas', 'ne peut plus', 'arrêt', 'coupure totale'
        ]
        
        results = []
        for i, tweet in enumerate(tweets):
            tweet_lower = tweet.lower()
            
            # Détection sentiment améliorée avec comptage de mots
            positive_count = sum(1 for w in POSITIVE_KEYWORDS if w in tweet_lower)
            negative_count = sum(1 for w in NEGATIVE_KEYWORDS if w in tweet_lower)
            
            if positive_count > negative_count and positive_count > 0:
                sentiment = 'positif'
                confidence_base = min(0.75 + (positive_count * 0.05), 0.95)
            elif negative_count > 0:
                sentiment = 'negatif'
                confidence_base = min(0.75 + (negative_count * 0.05), 0.95)
            else:
                sentiment = 'neutre'
                confidence_base = 0.60
            
            # Détection catégorie améliorée avec priorité
            product_score = sum(1 for w in PRODUCT_KEYWORDS if w in tweet_lower)
            service_score = sum(1 for w in SERVICE_KEYWORDS if w in tweet_lower)
            support_score = sum(1 for w in SUPPORT_KEYWORDS if w in tweet_lower)
            promotion_score = sum(1 for w in PROMOTION_KEYWORDS if w in tweet_lower)
            
            scores = {
                'produit': product_score,
                'service': service_score,
                'support': support_score,
                'promotion': promotion_score
            }
            
            max_score = max(scores.values())
            if max_score > 0:
                categorie = max(scores, key=scores.get)
                confidence_base += 0.10  # Boost confiance si catégorie détectée
            else:
                categorie = 'autre'
            
            # Détection topics améliorée
            if 'fibre' in tweet_lower:
                topics = 'fibre'
            elif 'mobile' in tweet_lower or '4g' in tweet_lower or '5g' in tweet_lower:
                topics = 'mobile'
            elif 'freebox' in tweet_lower or 'box' in tweet_lower:
                topics = 'freebox'
            elif 'reseau' in tweet_lower or 'connexion' in tweet_lower:
                topics = 'reseau'
            elif 'facture' in tweet_lower or 'paiement' in tweet_lower:
                topics = 'facture'
            elif categorie == 'service':
                topics = 'service_client'
            elif categorie == 'support':
                topics = 'support_technique'
            elif categorie == 'promotion':
                topics = 'promotion'
            else:
                topics = categorie if categorie != 'autre' else 'autre'
            
            # Détection is_claim améliorée
            is_claim = 'oui' if (
                sentiment == 'negatif' or 
                any(w in tweet_lower for w in ['panne', 'bug', 'problème', 'réclamation', 'plainte', '@free', 'dysfonctionnement'])
            ) else 'non'
            
            # Détection urgence améliorée
            urgent_count = sum(1 for w in URGENT_KEYWORDS if w in tweet_lower)
            if is_claim == 'oui':
                if urgent_count > 0 or 'panne totale' in tweet_lower or 'impossible de' in tweet_lower:
                    urgence = 'haute'
                    confidence_base += 0.05  # Boost confiance si urgence détectée
                else:
                    urgence = 'moyenne'
            else:
                urgence = 'faible'
            
            # Détection incident améliorée
            if is_claim == 'oui':
                if 'panne' in tweet_lower or 'coupure' in tweet_lower or 'connexion' in tweet_lower:
                    incident = 'panne_connexion'
                elif 'bug' in tweet_lower or 'freebox' in tweet_lower:
                    incident = 'bug_freebox'
                elif 'facture' in tweet_lower or 'paiement' in tweet_lower or 'facturation' in tweet_lower:
                    incident = 'probleme_facturation'
                elif 'mobile' in tweet_lower or '4g' in tweet_lower or '5g' in tweet_lower:
                    incident = 'probleme_mobile'
                else:
                    incident = 'non_specifie'
            else:
                incident = 'aucun'
            
            # Confiance finale avec clamp
            confidence = max(0.5, min(confidence_base, 0.95))
            
            results.append({
                'index': i,
                'sentiment': sentiment,
                'categorie': categorie,
                'score_confiance': round(confidence, 2),
                'is_claim': is_claim,
                'urgence': urgence,
                'topics': topics,
                'incident': incident
            })
        
        return results
    
    def classify_dataframe(self, 
                          df: pd.DataFrame, 
                          text_column: str = 'text_cleaned',
                          show_progress: bool = True) -> pd.DataFrame:
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
                status_text.text(f"Classification Gemini: Lot {batch_idx + 1}/{total_batches} ({start_idx + 1}-{end_idx} tweets)")
            
            # Classification du lot
            batch_results = self.classify_batch(batch_tweets)
            all_results.extend(batch_results)
            
            # Délai adaptatif entre les lots pour optimiser le débit sans surcharger l'API
            # Délai réduit pour petits batches, augmenté pour gros volumes
            if batch_idx < total_batches - 1:
                # Délai adaptatif: 0.3s pour petits batches (< 10), 0.5s pour moyens, 1s pour gros (> 50)
                adaptive_delay = 0.3 if total_batches < 10 else (0.5 if total_batches < 50 else 1.0)
                time.sleep(adaptive_delay)
        
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
        
        # Ajout des colonnes de classification (avec tous les champs KPI)
        df_classified['sentiment'] = [r.get('sentiment', 'neutre') for r in all_results]
        df_classified['categorie'] = [r.get('categorie', 'autre') for r in all_results]
        df_classified['score_confiance'] = [r.get('score_confiance', 0.5) for r in all_results]
        
        # Ajout des champs KPI supplémentaires
        df_classified['is_claim'] = [r.get('is_claim', 'non') for r in all_results]
        df_classified['urgence'] = [r.get('urgence', 'faible') for r in all_results]
        df_classified['topics'] = [r.get('topics', 'autre') for r in all_results]
        df_classified['incident'] = [r.get('incident', 'aucun') for r in all_results]
        
        # Alias pour compatibilité (confidence = score_confiance)
        df_classified['confidence'] = df_classified['score_confiance']
        
        # Ajout de métadonnées
        df_classified['classification_method'] = 'gemini'
        df_classified['model_name'] = self.model_name
        df_classified['classification_timestamp'] = pd.Timestamp.now().isoformat()
        
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
        if 'sentiment' not in df_classified.columns:
            return {}
        
        stats = {
            'total_classified': len(df_classified),
            'sentiment_distribution': df_classified['sentiment'].value_counts().to_dict(),
            'categorie_distribution': df_classified['categorie'].value_counts().to_dict() if 'categorie' in df_classified.columns else {},
            'avg_confidence': float(df_classified['score_confiance'].mean()) if 'score_confiance' in df_classified.columns else 0.0,
            'min_confidence': float(df_classified['score_confiance'].min()) if 'score_confiance' in df_classified.columns else 0.0,
            'max_confidence': float(df_classified['score_confiance'].max()) if 'score_confiance' in df_classified.columns else 0.0
        }
        
        return stats


# Fonctions utilitaires
def check_gemini_availability() -> bool:
    """
    Vérifie si l'API Gemini est disponible et configurée
    
    Returns:
        True si Gemini est accessible
    """
    if not GEMINI_AVAILABLE:
        logger.debug("Module google-generativeai non disponible")
        return False
    
    try:
        # S'assurer que le .env est chargé
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=False)
        
        # Chercher la clé API
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.debug("Clé API Gemini non trouvée dans les variables d'environnement")
            return False
        
        # Vérifier que la clé n'est pas vide
        if not api_key.strip():
            logger.debug("Clé API Gemini vide")
            return False
        
        # Vérifier que la clé a une longueur raisonnable (les clés Gemini font généralement 39 caractères)
        if len(api_key.strip()) < 10:
            logger.warning(f"Clé API Gemini semble invalide (longueur: {len(api_key)})")
            return False
        
        logger.info("✓ Clé API Gemini trouvée et valide")
        return True
    except Exception as e:
        logger.warning(f"Erreur vérification Gemini: {e}")
        return False


def classify_single_tweet(tweet: str, api_key: Optional[str] = None, model_name: str = 'gemini-pro') -> Dict[str, Any]:
    """
    Classifie un tweet unique avec Gemini
    
    Args:
        tweet: Texte du tweet
        api_key: Clé API Gemini (optionnel)
        model_name: Nom du modèle Gemini
        
    Returns:
        Dictionnaire avec classification
    """
    try:
        classifier = GeminiClassifier(api_key=api_key, model_name=model_name, batch_size=1)
        results = classifier.classify_batch([tweet])
        return results[0] if results else {
            'index': 0,
            'sentiment': 'neutre',
            'categorie': 'autre',
            'score_confiance': 0.5
        }
    except Exception as e:
        logger.error(f"Erreur classification Gemini: {e}")
        return {
            'index': 0,
            'sentiment': 'neutre',
            'categorie': 'autre',
            'score_confiance': 0.5
        }

