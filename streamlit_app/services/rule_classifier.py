"""
Classificateur par Règles Optimisé - FreeMobilaChat
====================================================

Classification ultra-rapide par patterns et règles.
Spécialisé pour is_claim et urgence.

Performance: 1000+ tweets/s
"""

from typing import List, Dict, Tuple
import pandas as pd
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class RuleClassifier:
    """
    Classificateur basé sur règles et patterns

    Spécialisé pour:
    - is_claim: Détection de réclamations (0 ou 1)
    - urgence: Niveau de priorité (haute/moyenne/basse)
    - topics_basic: Catégories basiques (fibre/mobile/facture)
    """

    # Patterns compilés pour performance - VERSION AMÉLIORÉE
    CLAIM_KEYWORDS = [
        # Réclamations explicites
        "réclamation",
        "plainte",
        "réclame",
        "je réclame",
        # Problèmes et pannes
        "problème",
        "souci",
        "bug",
        "erreur",
        "dysfonctionnement",
        "défaillance",
        "panne",
        "coupure",
        "interruption",
        "déconnexion",
        "perte de connexion",
        # Non fonctionnement
        "ne fonctionne pas",
        "ne marche pas",
        "ça ne marche pas",
        "ne fonctionne plus",
        "marche plus",
        "fonctionne plus",
        "impossible de",
        "n'arrive pas",
        "ne peut pas",
        # Perte de service - CORRECTION ISSUE-001
        "plus de connexion",
        "plus d'internet",
        "plus de réseau",
        "sans connexion",
        "sans internet",
        "sans réseau",
        "aucune connexion",
        "aucun internet",
        "aucun réseau",
        # Insatisfaction et mécontentement
        "déçu",
        "mécontent",
        "insatisfait",
        "catastrophe",
        "scandale",
        "honteux",
        "inadmissible",
        "inacceptable",
        "ras le bol",
        "en ai marre",
        "j'en ai marre",
        # Demandes de remboursement/résiliation
        "remboursement",
        "dédommagement",
        "compensation",
        "résiliation",
        "résilier",
        "changer d'opérateur",
        "partir de",
        "quitter free",
        # Qualificatifs négatifs forts
        "nul",
        "pourri",
        "minable",
        "catastrophique",
        "lamentable",
        "pire",
        # Durée prolongée (indicateur de réclamation)
        "depuis plusieurs jours",
        "depuis une semaine",
        "toujours pas",
        "encore rien",
    ]

    URGENCE_HAUTE_KEYWORDS = [
        # Urgence explicite
        "urgent",
        "urgence",
        "immédiat",
        "tout de suite",
        "rapidement",
        "au plus vite",
        # Gravité
        "critique",
        "grave",
        "sérieux",
        "important",
        "prioritaire",
        # Impact fort - AMÉLI ORATIONS ISSUE-001 & ISSUE-002
        "panne totale",
        "coupure totale",
        "coupure complète",
        "coupure générale",
        "plus de connexion",
        "plus d'internet",
        "plus de réseau",
        "sans connexion",
        "sans internet",
        "sans réseau",
        "aucune connexion",
        "aucun réseau",
        "aucun internet",
        "plus rien",
        "complètement HS",
        "totalement HS",
        # Durée prolongée - CORRECTION ISSUE-001
        "depuis plusieurs jours",
        "depuis une semaine",
        "depuis des jours",
        r"depuis \d+ jours",
        r"depuis \d+ semaines",
        r"depuis \d+ heures",
        r"ça fait \d+ jours",
        r"ça fait \d+ semaines",
        # Contexte professionnel - CORRECTION ISSUE-001 & ISSUE-002
        "télétravail",
        "travail",
        "professionnel",
        "professionnelle",
        "entreprise",
        "société",
        "business",
        "bureau",
        "en télétravail",
        "pour le travail",
        "au travail",
        # Réseau entreprise - CORRECTION ISSUE-002
        "réseau entreprise",
        "réseau professionnel",
        "connexion entreprise",
        # Récurrent
        "toujours",
        "encore",
        "systématiquement",
        "à chaque fois",
        "tous les jours",
        "chaque jour",
        "en permanence",
    ]

    URGENCE_MOYENNE_KEYWORDS = [
        "problème",
        "souci",
        "bug",
        "lenteur",
        "ralentissement",
        "parfois",
        "de temps en temps",
        "occasionnellement",
    ]

    # Topics (fibre, mobile, facture)
    FIBRE_KEYWORDS = [
        "fibre",
        "box",
        "freebox",
        "internet",
        "wifi",
        "connexion internet",
        "débit",
        "ligne",
        "adsl",
        "réseau fixe",
    ]

    MOBILE_KEYWORDS = [
        "mobile",
        "4g",
        "5g",
        "forfait mobile",
        "réseau mobile",
        "appel",
        "sms",
        "data",
        "roaming",
        "carte sim",
        "free mobile",
    ]

    FACTURE_KEYWORDS = [
        "facture",
        "facturation",
        "paiement",
        "prélèvement",
        "montant",
        "prix",
        "tarif",
        "abonnement",
        "coût",
        "euros",
        "€",
    ]

    def __init__(self):
        """Compile les patterns pour performance"""

        # Compiler les patterns regex
        self.claim_pattern = re.compile(
            "|".join([re.escape(kw) for kw in self.CLAIM_KEYWORDS]), re.IGNORECASE
        )

        self.urgence_haute_pattern = re.compile(
            "|".join(
                [re.escape(kw) if not "\\d" in kw else kw for kw in self.URGENCE_HAUTE_KEYWORDS]
            ),
            re.IGNORECASE,
        )

        self.urgence_moyenne_pattern = re.compile(
            "|".join([re.escape(kw) for kw in self.URGENCE_MOYENNE_KEYWORDS]), re.IGNORECASE
        )

        logger.info(" Patterns compilés pour détection rapide")

    def detect_claim(self, text: str) -> int:
        """
        Détecte si le tweet est une réclamation

        Args:
            text: Texte du tweet

        Returns:
            1 si réclamation, 0 sinon
        """
        if pd.isna(text):
            return 0

        # Recherche de patterns de réclamation
        if self.claim_pattern.search(text):
            return 1

        return 0

    def detect_urgence(self, text: str) -> str:
        """
        Détecte le niveau d'urgence

        Args:
            text: Texte du tweet

        Returns:
            'haute', 'moyenne', ou 'basse'
        """
        if pd.isna(text):
            return "basse"

        # Haute urgence
        if self.urgence_haute_pattern.search(text):
            return "haute"

        # Moyenne urgence
        if self.urgence_moyenne_pattern.search(text):
            return "moyenne"

        # Basse par défaut
        return "basse"

    def detect_topic(self, text: str) -> str:
        """
        Détecte le topic principal (fibre/mobile/facture)

        Args:
            text: Texte du tweet

        Returns:
            'fibre', 'mobile', 'facture', ou 'autre'
        """
        if pd.isna(text):
            return "autre"

        text_lower = text.lower()

        # Compter les occurrences
        fibre_count = sum(1 for kw in self.FIBRE_KEYWORDS if kw in text_lower)
        mobile_count = sum(1 for kw in self.MOBILE_KEYWORDS if kw in text_lower)
        facture_count = sum(1 for kw in self.FACTURE_KEYWORDS if kw in text_lower)

        # Sélectionner le topic dominant
        if fibre_count > mobile_count and fibre_count > facture_count:
            return "fibre"
        elif mobile_count > facture_count:
            return "mobile"
        elif facture_count > 0:
            return "facture"

        return "autre"

    def classify_batch(self, texts: List[str], show_progress: bool = False) -> pd.DataFrame:
        """
        Classification vectorisée ultra-rapide

        Args:
            texts: Liste de tweets
            show_progress: Afficher progression

        Returns:
            DataFrame avec is_claim, urgence, topics
        """
        logger.info(f" Classification par règles de {len(texts)} tweets...")

        # Conversion en Series pour vectorisation pandas
        series = pd.Series(texts)

        # Détections vectorisées (TRÈS RAPIDE)
        results = pd.DataFrame(
            {
                "is_claim": series.apply(self.detect_claim),
                "urgence": series.apply(self.detect_urgence),
                "topics": series.apply(self.detect_topic),
            }
        )

        logger.info(f" {len(texts)} tweets classifiés par règles")

        return results

    def get_statistics(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Calcule les statistiques de classification

        Args:
            df: DataFrame avec résultats

        Returns:
            Dict avec stats
        """
        stats = {
            "total": len(df),
            "claims_count": df["is_claim"].sum() if "is_claim" in df.columns else 0,
            "claims_percentage": (
                (df["is_claim"].sum() / len(df) * 100) if "is_claim" in df.columns else 0
            ),
            "urgence_distribution": (
                df["urgence"].value_counts().to_dict() if "urgence" in df.columns else {}
            ),
            "topics_distribution": (
                df["topics"].value_counts().to_dict() if "topics" in df.columns else {}
            ),
        }

        return stats


class EnhancedRuleClassifier(RuleClassifier):
    """
    Version améliorée avec détection d'incident
    """

    INCIDENT_PATTERNS = {
        "connexion": r"\b(panne|coupure|déconnexion|pas de connexion|plus de connexion)\b",
        "débit": r"\b(lent|lenteur|ralentissement|débit|vitesse)\b",
        "activation": r"\b(activation|activer|installer|installation)\b",
        "facturation": r"\b(facture|surfacturation|prélèvement|montant erroné)\b",
        "technique": r"\b(bug|erreur|dysfonctionnement|ne fonctionne pas)\b",
        "service_client": r"\b(service client|sav|support|assistance|hotline)\b",
    }

    def __init__(self):
        super().__init__()

        # Compiler patterns d'incident
        self.incident_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.INCIDENT_PATTERNS.items()
        }

    def detect_incident(self, text: str) -> str:
        """
        Détecte le type d'incident

        Returns:
            Type d'incident ou 'aucun'
        """
        if pd.isna(text):
            return "aucun"

        # Vérifier chaque type
        detected = []
        for incident_type, pattern in self.incident_patterns.items():
            if pattern.search(text):
                detected.append(incident_type)

        # Retourner le premier détecté ou 'aucun'
        return detected[0] if detected else "aucun"

    def classify(self, text: str) -> Dict[str, str]:
        """
        Classification complète d'un seul tweet

        Args:
            text: Texte du tweet

        Returns:
            Dict avec is_claim, urgence, topics, incident
        """
        is_claim_val = self.detect_claim(text)
        urgence_val = self.detect_urgence(text)
        topic_val = self.detect_topic(text)
        incident_val = self.detect_incident(text)

        return {
            "is_claim": "oui" if is_claim_val == 1 else "non",
            "urgence": urgence_val,  # 'haute', 'moyenne', 'basse'
            "topics": topic_val,
            "incident": incident_val,
        }

    def classify_batch_extended(self, texts: List[str]) -> pd.DataFrame:
        """
        Classification étendue avec incident

        Returns:
            DataFrame avec is_claim, urgence, topics, incident
        """
        # Classification de base
        results = self.classify_batch(texts, show_progress=False)

        # Ajouter détection incident
        series = pd.Series(texts)
        results["incident"] = series.apply(self.detect_incident)

        # Convertir is_claim en 'oui'/'non' pour compatibilité Streamlit
        results["is_claim"] = results["is_claim"].map({1: "oui", 0: "non"})

        return results


if __name__ == "__main__":
    # Test du classificateur
    print("\n Test du classificateur par règles\n")

    test_tweets = [
        "Panne internet depuis ce matin, urgent!",
        "Super service Free Mobile",
        "Facture trop élevée ce mois",
        "Lenteur de connexion fibre",
        "Comment activer ma box?",
    ]

    classifier = EnhancedRuleClassifier()
    results = classifier.classify_batch_extended(test_tweets)

    print(" Résultats:\n")
    for i, tweet in enumerate(test_tweets):
        print(f"{i+1}. {tweet}")
        print(f"   is_claim: {results['is_claim'].iloc[i]}")
        print(f"   urgence: {results['urgence'].iloc[i]}")
        print(f"   topics: {results['topics'].iloc[i]}")
        print(f"   incident: {results['incident'].iloc[i]}\n")

    stats = classifier.get_statistics(results)
    print(f"\n Statistiques:")
    print(
        f"   Réclamations: {stats['claims_count']}/{stats['total']} ({stats['claims_percentage']:.1f}%)"
    )
    print(f"   Urgence: {stats['urgence_distribution']}")
    print(f"   Topics: {stats['topics_distribution']}")

    print("\n Test terminé!")
