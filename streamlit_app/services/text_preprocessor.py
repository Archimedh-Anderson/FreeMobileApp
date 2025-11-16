"""
Text Preprocessor - Advanced NLP Preprocessing
===============================================

Robust text preprocessing for French tweet classification.
Implements PROMPT CURSOR.txt specifications for improved classification accuracy.

Features:
- URL, mention, hashtag removal
- Special character normalization
- Language detection
- Optional spaCy lemmatization
- Emoji handling
"""

import re
import warnings
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Optional imports with graceful degradation
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy && python -m spacy download fr_core_news_lg")

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available. Install with: pip install langdetect")

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class TextPreprocessor:
    """
    Robust text preprocessor for French NLP tasks.
    
    Implements comprehensive cleaning and normalization following
    PROMPT CURSOR.txt specifications for optimal classification performance.
    
    Features:
    - URL removal (http://, https://, www.)
    - Mention removal (@username)
    - Hashtag normalization (#hashtag -> hashtag)
    - Special character cleaning
    - Multi-space normalization
    - Language detection (optional)
    - spaCy lemmatization (optional)
    
    Example:
        >>> prep = TextPreprocessor()
        >>> text = "@Free Bonjour! Ma #fibre ne marche pas http://example.com 😞"
        >>> prep.clean(text)
        'bonjour ma fibre ne marche pas'
    """
    
    def __init__(self, use_spacy: bool = False, enable_language_detection: bool = False):
        """
        Initialize the text preprocessor.
        
        Args:
            use_spacy: Enable spaCy for advanced lemmatization (slower but more accurate)
            enable_language_detection: Enable language detection for each text
        """
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.enable_language_detection = enable_language_detection and LANGDETECT_AVAILABLE
        self.nlp = None
        
        # Initialize spaCy if requested and available
        if self.use_spacy:
            try:
                self.nlp = spacy.load("fr_core_news_lg")
                logger.info("✓ spaCy French model loaded successfully")
            except OSError:
                logger.warning(
                    "⚠️ spaCy French model not found. Download with:\n"
                    "python -m spacy download fr_core_news_lg"
                )
                self.use_spacy = False
        
        # Compile regex patterns for performance
        self.url_pattern = re.compile(r'http\S+|www\.\S+|https\S+', re.IGNORECASE)
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#(\w+)')
        # Keep French accented characters
        self.special_chars_pattern = re.compile(r'[^\w\s\-.,!?àâäéèêëïîôùûüÿæœç]', re.UNICODE)
        self.spaces_pattern = re.compile(r'\s+')
        
        # Emoji pattern (optional, can be kept for sentiment analysis)
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE
        )
    
    def clean(self, text: str, preserve_case: bool = False, remove_emojis: bool = False) -> str:
        """
        Clean and normalize text for NLP processing.
        
        Implements comprehensive cleaning pipeline:
        1. Handle NaN/invalid input
        2. Optional case preservation
        3. Remove URLs
        4. Remove mentions
        5. Normalize hashtags
        6. Remove special characters (keep French accents)
        7. Normalize whitespace
        8. Optional emoji removal
        
        Args:
            text: Input text to clean
            preserve_case: If True, keep original case (default: False = lowercase)
            remove_emojis: If True, remove emoji characters (default: False)
        
        Returns:
            Cleaned text string, empty string if invalid input
        """
        # Handle NaN and non-string inputs
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Lowercase transformation (optional)
        if not preserve_case:
            text = text.lower()
        
        # Remove URLs (http, https, www)
        text = self.url_pattern.sub('', text)
        
        # Remove mentions (@username)
        text = self.mention_pattern.sub('', text)
        
        # Normalize hashtags: #hashtag -> hashtag
        text = self.hashtag_pattern.sub(r'\1', text)
        
        # Remove emojis if requested
        if remove_emojis:
            text = self.emoji_pattern.sub('', text)
        
        # Remove special characters (keep French accents, basic punctuation)
        text = self.special_chars_pattern.sub('', text)
        
        # Normalize multiple spaces to single space
        text = self.spaces_pattern.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        
        Uses langdetect library for probabilistic language detection.
        Useful for filtering non-French content or adapting classification.
        
        Args:
            text: Input text
        
        Returns:
            ISO 639-1 language code (e.g., 'fr', 'en'), 'unknown' on error
        """
        if not self.enable_language_detection:
            return "fr"  # Assume French by default
        
        try:
            return detect(text)
        except (LangDetectException, Exception):
            return "unknown"
    
    def lemmatize(self, text: str) -> str:
        """
        Lemmatize text using spaCy (reduce words to base form).
        
        Example: 'fonctionnent' -> 'fonctionner'
        
        Only available if spaCy is installed and initialized.
        
        Args:
            text: Cleaned text to lemmatize
        
        Returns:
            Lemmatized text, or original text if spaCy unavailable
        """
        if not self.use_spacy or self.nlp is None:
            return text
        
        try:
            doc = self.nlp(text)
            lemmas = [token.lemma_ for token in doc if not token.is_stop]
            return ' '.join(lemmas)
        except Exception as e:
            logger.warning(f"Lemmatization error: {e}")
            return text
    
    def preprocess_batch(self, texts: list[str], **kwargs) -> list[str]:
        """
        Preprocess a batch of texts efficiently.
        
        Applies the same cleaning pipeline to multiple texts.
        Vectorized for better performance on large datasets.
        
        Args:
            texts: List of raw text strings
            **kwargs: Additional arguments passed to clean()
        
        Returns:
            List of cleaned text strings
        """
        return [self.clean(text, **kwargs) for text in texts]
    
    def get_stats(self) -> dict:
        """
        Get preprocessor configuration statistics.
        
        Returns:
            Dictionary with configuration info
        """
        return {
            'spacy_enabled': self.use_spacy,
            'spacy_available': SPACY_AVAILABLE,
            'language_detection_enabled': self.enable_language_detection,
            'langdetect_available': LANGDETECT_AVAILABLE
        }


# Convenience function for quick cleaning
def quick_clean(text: str) -> str:
    """
    Quick text cleaning without initialization overhead.
    
    For simple use cases where you don't need advanced features.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    preprocessor = TextPreprocessor(use_spacy=False, enable_language_detection=False)
    return preprocessor.clean(text)
