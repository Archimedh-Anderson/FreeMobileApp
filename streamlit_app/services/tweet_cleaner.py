"""
Module de Nettoyage de Tweets - FreeMobilaChat
===============================================

Module avancé pour le prétraitement et la déduplication de tweets.
Conforme aux spécifications techniques du projet académique.

Fonctionnalités:
- Suppression des doublons (hash MD5)
- Nettoyage du texte (URLs, mentions, hashtags, emojis)
- Normalisation unicode
- Statistiques de nettoyage
"""

# Imports pour la manipulation de types et de données
from typing import Tuple, Dict, List, Optional  # Annotations de types pour la clarté du code
import pandas as pd  # Traitement de données tabulaires (DataFrames)
import hashlib  # Génération de hash MD5 pour détection de doublons
import re  # Expressions régulières pour le nettoyage de texte
from unidecode import unidecode  # Normalisation des caractères unicode vers ASCII
import emoji  # Conversion des emojis en représentation textuelle
import logging  # Journalisation des opérations de nettoyage

# Configuration du logger pour le suivi des opérations
logger = logging.getLogger(__name__)

# Définition des patterns regex pour le nettoyage (conformes aux spécifications)
URL_PATTERN = r'http\S+|www\S+|https\S+'  # Détection de toutes les URLs (http, https, www)
MENTION_PATTERN = r'@\w+'  # Détection des mentions Twitter (@username)
HASHTAG_PATTERN = r'#\w+'  # Détection des hashtags (#tag)
PUNCTUATION_PATTERN = r'[^\w\s,.\?!]'  # Suppression ponctuation exceptée (garde , . ? !)
WHITESPACE_PATTERN = r'\s+'  # Normalisation des espaces multiples en espace unique


DEFAULT_DOMAIN_KEYWORDS = [
    "free", "freebox", "free mobile", "freebox delta", "freebox pop",
    "fibre", "fiber", "connexion", "connection", "reseau", "réseau",
    "4g", "5g", "data", "debit", "débit", "facture", "facturation",
    "reclamation", "réclamation", "incident", "panne", "bug", "sav",
    "support", "service client", "assistance", "wifi", "box", "modem"
]


class TweetCleaner:
    """
    Nettoyage et déduplication de tweets
    
    Cette classe implémente un pipeline complet de nettoyage selon les
    spécifications techniques du projet. Elle garantit des données
    propres et déduplicées pour la classification.
    """
    
    def __init__(self, 
                 remove_urls: bool = True,
                 remove_mentions: bool = True,
                 remove_hashtags: bool = False,
                 convert_emojis: bool = True,
                 normalize_unicode: bool = True,
                 lowercase: bool = True,
                 preserve_domain_keywords: bool = True,
                 extra_stopwords: Optional[List[str]] = None):
        """
        Initialise le nettoyeur de tweets
        
        Args:
            remove_urls: Supprimer les URLs
            remove_mentions: Supprimer les mentions @username
            remove_hashtags: Supprimer les hashtags #tag
            convert_emojis: Convertir les emojis en texte
            normalize_unicode: Normaliser les caractères unicode
            lowercase: Forcer en minuscules pour homogénéité
            preserve_domain_keywords: Conserver les mots-clés Free Mobile
            extra_stopwords: Liste personnalisée de stopwords à supprimer
        """
        self.remove_urls = remove_urls
        self.remove_mentions = remove_mentions
        self.remove_hashtags = remove_hashtags
        self.convert_emojis = convert_emojis
        self.normalize_unicode = normalize_unicode
        self.lowercase = lowercase
        self.preserve_domain_keywords = preserve_domain_keywords
        self.extra_stopwords = set(s.lower() for s in (extra_stopwords or []))
        self.domain_keywords = set(DEFAULT_DOMAIN_KEYWORDS)
        
        logger.info(f"TweetCleaner initialisé avec options: URLs={remove_urls}, Mentions={remove_mentions}, Hashtags={remove_hashtags}")
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
        """
        Suppression des doublons par hash MD5
        
        Utilise un hash MD5 du texte pour identifier les tweets identiques,
        même avec des variations mineures.
        
        Args:
            df: DataFrame avec tweets
            text_column: Nom de la colonne texte
            
        Returns:
            DataFrame sans doublons
        """
        if text_column not in df.columns:
            logger.warning(f"Colonne '{text_column}' non trouvée, pas de déduplication")
            return df
        
        # Création des hash MD5
        df['_hash'] = df[text_column].apply(
            lambda x: hashlib.md5(str(x).encode()).hexdigest() if pd.notna(x) else None
        )
        
        # Comptage avant
        count_before = len(df)
        
        # Suppression des doublons basée sur le hash
        df_dedup = df.drop_duplicates(subset=['_hash'], keep='first')
        
        # Suppression de la colonne temporaire
        df_dedup = df_dedup.drop(columns=['_hash'])
        
        # Comptage après
        count_after = len(df_dedup)
        duplicates_removed = count_before - count_after
        
        logger.info(f"Déduplication: {duplicates_removed} doublons supprimés ({count_before} → {count_after})")
        
        return df_dedup.reset_index(drop=True)
    
    def clean_text(self, text: str) -> str:
        """
        Nettoyage complet d'un tweet
        
        Ordre des opérations (conforme aux specs):
        1. Suppression URLs (http/https/www)
        2. Suppression mentions (@username)
        3. Suppression hashtags (#tag)
        4. Conversion emojis en texte
        5. Normalisation unicode
        6. Suppression ponctuation excessive
        7. Normalisation espaces
        
        Args:
            text: Tweet brut
            
        Returns:
            Tweet nettoyé
        """
        if not isinstance(text, str) or pd.isna(text):
            return ""
        
        cleaned = text
        
        if self.lowercase:
            cleaned = cleaned.lower()
        
        # 1. Suppression des URLs
        if self.remove_urls:
            cleaned = re.sub(URL_PATTERN, '', cleaned)
        
        # 2. Suppression des mentions
        if self.remove_mentions:
            cleaned = re.sub(MENTION_PATTERN, '', cleaned)
        
        # 3. Suppression des hashtags
        if self.remove_hashtags:
            cleaned = re.sub(HASHTAG_PATTERN, '', cleaned)
        
        # 4. Conversion des emojis en texte
        if self.convert_emojis:
            try:
                cleaned = emoji.demojize(cleaned, delimiters=(" ", " "))
            except:
                pass  # Si emoji pose problème, continuer
        
        # 5. Normalisation unicode
        if self.normalize_unicode:
            try:
                cleaned = unidecode(cleaned)
            except:
                pass  # Si unidecode pose problème, continuer
        
        # 6. Suppression ponctuation excessive (garder , . ? !)
        # cleaned = re.sub(PUNCTUATION_PATTERN, '', cleaned)
        
        # 7. Normalisation des espaces
        cleaned = re.sub(WHITESPACE_PATTERN, ' ', cleaned)
        cleaned = cleaned.strip()
        
        # 8. Suppression des stopwords supplémentaires
        if self.extra_stopwords:
            tokens = []
            for token in cleaned.split():
                if token not in self.extra_stopwords:
                    tokens.append(token)
            cleaned = " ".join(tokens)
        
        # 9. Optionnel: préserver mots-clés métiers (en les ré-injectant si supprimés)
        if self.preserve_domain_keywords and cleaned:
            preserved_tokens = []
            for keyword in self.domain_keywords:
                if keyword in text.lower() and keyword not in cleaned:
                    preserved_tokens.append(keyword.replace(" ", "_"))
            if preserved_tokens:
                cleaned = f"{cleaned} {' '.join(preserved_tokens)}".strip()
        
        return cleaned
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = 'text') -> Tuple[pd.DataFrame, Dict]:
        """
        Pipeline complet de nettoyage
        
        Applique toutes les opérations de nettoyage et génère des statistiques
        détaillées sur le processus.
        
        Args:
            df: DataFrame brut
            text_column: Colonne à nettoyer
            
        Returns:
            (df_cleaned, stats_dict) - DataFrame nettoyé et statistiques
        """
        logger.info(f"Démarrage du nettoyage de {len(df)} tweets")
        
        # Statistiques initiales
        stats = {
            'total_original': len(df),
            'empty_tweets': 0,
            'duplicates_removed': 0,
            'total_cleaned': 0,
            'avg_length_before': 0,
            'avg_length_after': 0,
            'cleaning_operations': []
        }
        
        # Vérifier que la colonne existe
        if text_column not in df.columns:
            logger.error(f"Colonne '{text_column}' non trouvée dans le DataFrame")
            return df, stats
        
        # Copie pour ne pas modifier l'original
        df_clean = df.copy()
        
        # 1. Suppression des valeurs manquantes
        empty_count = df_clean[text_column].isna().sum()
        df_clean = df_clean.dropna(subset=[text_column])
        stats['empty_tweets'] = int(empty_count)
        stats['cleaning_operations'].append(f"Valeurs manquantes supprimées: {empty_count}")
        
        # 2. Suppression des doublons
        count_before_dedup = len(df_clean)
        df_clean = self.remove_duplicates(df_clean, text_column)
        duplicates = count_before_dedup - len(df_clean)
        stats['duplicates_removed'] = int(duplicates)
        stats['cleaning_operations'].append(f"Doublons supprimés: {duplicates}")
        
        # 3. Calcul de la longueur moyenne avant nettoyage
        if len(df_clean) > 0:
            stats['avg_length_before'] = float(df_clean[text_column].astype(str).str.len().mean())
        else:
            stats['avg_length_before'] = 0.0
        
        # 4. Nettoyage du texte
        df_clean[f'{text_column}_cleaned'] = df_clean[text_column].apply(self.clean_text)
        
        # 5. Calcul de la longueur moyenne après nettoyage
        if len(df_clean) > 0:
            stats['avg_length_after'] = float(df_clean[f'{text_column}_cleaned'].str.len().mean())
        else:
            stats['avg_length_after'] = 0.0
        
        # 6. Suppression des tweets vides après nettoyage
        if len(df_clean) > 0:
            df_clean = df_clean[df_clean[f'{text_column}_cleaned'].str.len() > 0]
        
        # Statistiques finales
        stats['total_cleaned'] = len(df_clean)
        stats['cleaning_operations'].append(f"Tweets nettoyés: {len(df_clean)}")
        
        logger.info(f"Nettoyage terminé: {stats['total_original']} → {stats['total_cleaned']} tweets")
        
        return df_clean.reset_index(drop=True), stats
    
    def get_cleaning_report(self, stats: Dict) -> str:
        """
        Génère un rapport de nettoyage formaté
        
        Args:
            stats: Dictionnaire de statistiques
            
        Returns:
            Rapport formaté en markdown
        """
        report = f"""
## 🧹 Rapport de Nettoyage

**Tweets originaux:** {stats['total_original']:,}
**Tweets nettoyés:** {stats['total_cleaned']:,}
**Tweets supprimés:** {stats['total_original'] - stats['total_cleaned']:,}

### Détails
- **Valeurs manquantes:** {stats['empty_tweets']}
- **Doublons:** {stats['duplicates_removed']}
- **Longueur moyenne avant:** {stats['avg_length_before']:.1f} caractères
- **Longueur moyenne après:** {stats['avg_length_after']:.1f} caractères

### Opérations effectuées
"""
        for op in stats['cleaning_operations']:
            report += f"- {op}\n"
        
        return report


# Fonctions utilitaires
def clean_tweet_text(text: str, 
                     remove_urls: bool = True,
                     remove_mentions: bool = True,
                     remove_hashtags: bool = False,
                     lowercase: bool = True) -> str:
    """
    Fonction helper pour nettoyer un tweet unique
    
    Args:
        text: Texte du tweet
        remove_urls: Supprimer les URLs
        remove_mentions: Supprimer les mentions
        remove_hashtags: Supprimer les hashtags
        
    Returns:
        Texte nettoyé
    """
    cleaner = TweetCleaner(
        remove_urls=remove_urls,
        remove_mentions=remove_mentions,
        remove_hashtags=remove_hashtags,
        lowercase=lowercase
    )
    return cleaner.clean_text(text)


def batch_clean_tweets(tweets: List[str], **kwargs) -> List[str]:
    """
    Nettoie un lot de tweets
    
    Args:
        tweets: Liste de tweets à nettoyer
        **kwargs: Options de nettoyage
        
    Returns:
        Liste de tweets nettoyés
    """
    cleaner = TweetCleaner(**kwargs)
    return [cleaner.clean_text(tweet) for tweet in tweets]

