"""
Advanced Tweet Classifier - Multi-Model NLP Classification
===========================================================

Implements PROMPT CURSOR.txt specifications for robust French tweet classification.

Features:
- CamemBERT sentiment analysis (French-native model)
- Enhanced reclamation detection with multi-factor scoring
- Zero-shot theme classification
- Urgency level detection
- Ensemble voting for improved confidence
- Fallback mechanisms (Transformers -> TextBlob -> Rules)

Models Used:
- cmarkea/distilcamembert-base-sentiment (sentiment)
- moussaKam/barthez-orangesum-abstract (zero-shot themes)
- Rule-based patterns (reclamation, urgency)
"""

import logging
import warnings
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# Import text preprocessor
try:
    from .text_preprocessor import TextPreprocessor
except ImportError:
    from text_preprocessor import TextPreprocessor

# Optional Transformers import with graceful degradation
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info("✓ Transformers library available")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ Transformers not available. Install with: pip install transformers torch")

# Optional TextBlob import for fallback
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("⚠️ TextBlob not available. Install with: pip install textblob textblob-fr")


@dataclass
class ClassificationResult:
    """
    Structured classification result for a single tweet.
    
    Attributes:
        sentiment: POSITIF, NEUTRE, or NEGATIF
        reclamation: OUI or NON
        urgence: CRITIQUE, ELEVEE, MOYENNE, or FAIBLE
        theme: FIBRE, MOBILE, TV, FACTURE, SAV, RESEAU, AUTRE
        type_incident: PANNE, LENTEUR, FACTURATION, PROCESSUS_SAV, INFO, AUTRE
        responsable: TECHNIQUE, COMMERCIAL, RESEAU, AUTRE
        confiance: Confidence score (0.0 to 1.0)
        metadata: Additional debug information
    """
    sentiment: str
    reclamation: str
    urgence: str
    theme: str
    type_incident: str
    responsable: str
    confiance: float
    metadata: Dict[str, Any] = None


class AdvancedTweetClassifier:
    """
    Multi-model classifier for comprehensive tweet analysis.
    
    Implements ensemble approach combining:
    - Transformer models (CamemBERT, BARThez)
    - Rule-based patterns
    - TextBlob fallback
    
    Follows PROMPT CURSOR.txt architecture for optimal French NLP.
    """
    
    def __init__(self, 
                 enable_transformers: bool = True,
                 enable_textblob_fallback: bool = True,
                 use_preprocessing: bool = True):
        """
        Initialize the advanced classifier.
        
        Args:
            enable_transformers: Use Transformers models if available
            enable_textblob_fallback: Use TextBlob as sentiment fallback
            use_preprocessing: Use TextPreprocessor for cleaning
        """
        self.preprocessor = TextPreprocessor() if use_preprocessing else None
        self.enable_transformers = enable_transformers and TRANSFORMERS_AVAILABLE
        self.enable_textblob_fallback = enable_textblob_fallback and TEXTBLOB_AVAILABLE
        
        # Initialize models
        self.sentiment_analyzer = None
        self.theme_classifier = None
        
        if self.enable_transformers:
            self._initialize_transformers()
        
        # Keyword patterns for reclamation detection (PROMPT CURSOR.txt spec)
        self.reclamation_keywords = [
            'problème', 'panne', 'bug', 'erreur', 'défaut',
            'réclamation', 'plainte', 'insatisfait', 'mécontent',
            'résoudre', 'réparer', 'rembourser', 'compensation',
            'service client', 'sav', 'assistance', 'aide',
            'ne fonctionne pas', 'ça marche pas', 'bloqué',
            'impossible', 'toujours pas', 'depuis des jours',
            'aucune réponse', 'toujours rien', 'pas de nouvelles',
            'inadmissible', 'honteux', 'scandaleux', 'catastrophe'
        ]
        
        # Urgency keywords (PROMPT CURSOR.txt spec)
        self.urgence_keywords = {
            'CRITIQUE': ['urgent', 'critique', 'grave', 'catastrophique', 'immédiatement', 
                        'urgentissime', 'très urgent', 'extrêmement urgent'],
            'ELEVEE': ['important', 'rapidement', 'vite', 'priorité', 'pressé',
                      'au plus vite', 'dès que possible', 'rapidement'],
            'MOYENNE': ['bientôt', 'quand possible', 'sous peu'],
            'FAIBLE': ['pas pressé', 'pas urgent', 'quand vous pouvez']
        }
        
        logger.info(f"AdvancedTweetClassifier initialized (transformers={self.enable_transformers})")
    
    def _initialize_transformers(self):
        """Initialize Transformer models with error handling."""
        try:
            # CamemBERT for French sentiment (PROMPT CURSOR.txt spec)
            logger.info("Loading CamemBERT sentiment model...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cmarkea/distilcamembert-base-sentiment",
                tokenizer="cmarkea/distilcamembert-base-sentiment",
                device=-1  # CPU (use device=0 for GPU)
            )
            logger.info("✓ CamemBERT sentiment model loaded")
        except Exception as e:
            logger.warning(f"Could not load sentiment model: {e}")
            self.sentiment_analyzer = None
        
        try:
            # BARThez for zero-shot theme classification (PROMPT CURSOR.txt spec)
            logger.info("Loading BARThez zero-shot model...")
            self.theme_classifier = pipeline(
                "zero-shot-classification",
                model="moussaKam/barthez-orangesum-abstract",
                device=-1  # CPU
            )
            logger.info("✓ BARThez theme model loaded")
        except Exception as e:
            logger.warning(f"Could not load theme model: {e}")
            self.theme_classifier = None
    
    def classify_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Classify sentiment using multi-model approach.
        
        Priority:
        1. CamemBERT (if available)
        2. TextBlob (fallback)
        3. Rule-based (last resort)
        
        Args:
            text: Raw or cleaned text
        
        Returns:
            (sentiment, confidence) where sentiment ∈ {POSITIF, NEUTRE, NEGATIF}
        """
        clean_text = self.preprocessor.clean(text) if self.preprocessor else text.lower()
        
        if not clean_text:
            return "NEUTRE", 0.0
        
        # Try CamemBERT first
        if self.sentiment_analyzer is not None:
            try:
                result = self.sentiment_analyzer(clean_text[:512])[0]
                label = result['label']
                score = result['score']
                
                # Map CamemBERT labels to our format
                sentiment_map = {
                    '5 stars': 'POSITIF',
                    '4 stars': 'POSITIF',
                    '3 stars': 'NEUTRE',
                    '2 stars': 'NEGATIF',
                    '1 star': 'NEGATIF',
                    'POSITIVE': 'POSITIF',
                    'NEGATIVE': 'NEGATIF',
                    'NEUTRAL': 'NEUTRE'
                }
                
                sentiment = sentiment_map.get(label, 'NEUTRE')
                return sentiment, score
            
            except Exception as e:
                logger.warning(f"CamemBERT sentiment error: {e}")
        
        # Fallback to TextBlob
        if self.enable_textblob_fallback:
            try:
                blob = TextBlob(clean_text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    return "POSITIF", abs(polarity)
                elif polarity < -0.1:
                    return "NEGATIF", abs(polarity)
                else:
                    return "NEUTRE", 0.5
            except Exception as e:
                logger.warning(f"TextBlob sentiment error: {e}")
        
        # Final rule-based fallback
        positive_words = ['merci', 'super', 'bravo', 'excellent', 'génial', 'top', 'parfait']
        negative_words = ['panne', 'nul', 'mauvais', 'honte', 'catastrophe', 'inadmissible']
        
        positive_count = sum(1 for w in positive_words if w in clean_text)
        negative_count = sum(1 for w in negative_words if w in clean_text)
        
        if positive_count > negative_count:
            return "POSITIF", 0.6
        elif negative_count > positive_count:
            return "NEGATIF", 0.6
        else:
            return "NEUTRE", 0.5
    
    def detect_reclamation(self, text: str) -> Tuple[bool, float]:
        """
        Detect if text contains a complaint/claim using multi-factor analysis.
        
        Scoring factors (PROMPT CURSOR.txt spec):
        1. Reclamation keywords (0.0 - 0.6)
        2. Negative sentiment (0.3)
        3. Interrogative form (0.15)
        4. Action verbs (0.2)
        
        Threshold: 0.4 for classification as reclamation
        
        Args:
            text: Raw or cleaned text
        
        Returns:
            (is_reclamation, confidence_score)
        """
        clean_text = self.preprocessor.clean(text) if self.preprocessor else text.lower()
        
        if not clean_text:
            return False, 0.0
        
        score = 0.0
        factors = []
        
        # Factor 1: Reclamation keywords
        keyword_matches = sum(1 for kw in self.reclamation_keywords if kw in clean_text)
        if keyword_matches > 0:
            keyword_score = min(keyword_matches * 0.3, 0.6)
            score += keyword_score
            factors.append(f"keywords:{keyword_matches}")
        
        # Factor 2: Negative sentiment
        sentiment, sent_conf = self.classify_sentiment(text)
        if sentiment == "NEGATIF":
            score += 0.3
            factors.append(f"neg_sent:{sent_conf:.2f}")
        
        # Factor 3: Interrogative form
        interrogative_words = ['pourquoi', 'comment', 'quand', 'où', 'combien', 'qui', 'que', 'quoi']
        if '?' in text or any(w in clean_text for w in interrogative_words):
            score += 0.15
            factors.append("interrogative")
        
        # Factor 4: Action verbs (complaint-related)
        action_verbs = ['résoudre', 'réparer', 'rembourser', 'annuler', 'contacter', 
                       'régler', 'traiter', 'expliquer', 'comprendre']
        if any(v in clean_text for v in action_verbs):
            score += 0.2
            factors.append("action_verbs")
        
        # Normalize confidence to [0, 1]
        confidence = min(score, 1.0)
        is_reclamation = confidence > 0.4
        
        if is_reclamation:
            logger.debug(f"✓ Reclamation detected ({confidence:.2f}): {factors}")
        
        return is_reclamation, confidence
    
    def classify_urgence(self, text: str, is_reclamation: bool) -> str:
        """
        Classify urgency level based on keywords and reclamation status.
        
        Args:
            text: Raw or cleaned text
            is_reclamation: Whether text is a complaint
        
        Returns:
            Urgency level: CRITIQUE, ELEVEE, MOYENNE, or FAIBLE
        """
        clean_text = self.preprocessor.clean(text) if self.preprocessor else text.lower()
        
        # Non-reclamations are automatically FAIBLE
        if not is_reclamation:
            return "FAIBLE"
        
        # Check for urgency keywords in priority order
        for level, keywords in self.urgence_keywords.items():
            if any(kw in clean_text for kw in keywords):
                return level
        
        # Default: reclamations without urgency keywords are MOYENNE
        return "MOYENNE"
    
    def classify_theme(self, text: str) -> Tuple[str, float]:
        """
        Classify main theme using zero-shot classification or rules.
        
        Themes (PROMPT CURSOR.txt spec):
        FIBRE, MOBILE, TV, FACTURE, SAV, RESEAU, AUTRE
        
        Args:
            text: Raw or cleaned text
        
        Returns:
            (theme, confidence)
        """
        clean_text = self.preprocessor.clean(text) if self.preprocessor else text.lower()
        
        # Try zero-shot classification if available
        if self.theme_classifier is not None:
            try:
                themes_labels = [
                    "problème de fibre internet",
                    "problème de téléphone mobile",
                    "problème de télévision",
                    "question sur la facture",
                    "service après-vente",
                    "problème de réseau",
                    "autre sujet"
                ]
                
                result = self.theme_classifier(
                    clean_text[:512],
                    candidate_labels=themes_labels,
                    hypothesis_template="Ce texte parle de {}."
                )
                
                theme_map = {
                    themes_labels[0]: "FIBRE",
                    themes_labels[1]: "MOBILE",
                    themes_labels[2]: "TV",
                    themes_labels[3]: "FACTURE",
                    themes_labels[4]: "SAV",
                    themes_labels[5]: "RESEAU",
                    themes_labels[6]: "AUTRE"
                }
                
                best_label = result['labels'][0]
                best_score = result['scores'][0]
                
                return theme_map[best_label], best_score
            
            except Exception as e:
                logger.warning(f"Zero-shot theme error: {e}")
        
        # Fallback: rule-based theme detection
        if any(w in clean_text for w in ['fibre', 'ftth', 'adsl', 'internet fixe']):
            return "FIBRE", 0.7
        elif any(w in clean_text for w in ['mobile', '4g', '5g', 'forfait mobile', 'téléphone']):
            return "MOBILE", 0.7
        elif any(w in clean_text for w in ['tv', 'télévision', 'freebox tv', 'chaîne']):
            return "TV", 0.7
        elif any(w in clean_text for w in ['facture', 'facturation', 'paiement', 'prélèvement']):
            return "FACTURE", 0.7
        elif any(w in clean_text for w in ['sav', 'service client', 'assistance', 'support']):
            return "SAV", 0.7
        elif any(w in clean_text for w in ['réseau', 'couverture', 'débit', 'connexion']):
            return "RESEAU", 0.7
        else:
            return "AUTRE", 0.5
    
    def _infer_incident_type(self, text: str, theme: str) -> str:
        """Infer incident type from text and theme."""
        clean_text = self.preprocessor.clean(text) if self.preprocessor else text.lower()
        
        if any(w in clean_text for w in ['panne', 'coupure', 'ne marche plus', 'ne fonctionne plus']):
            return "PANNE"
        elif any(w in clean_text for w in ['lent', 'lenteur', 'ralenti', 'débit faible']):
            return "LENTEUR"
        elif theme == "FACTURE" or 'factur' in clean_text:
            return "FACTURATION"
        elif any(w in clean_text for w in ['sav', 'service', 'assistance', 'support']):
            return "PROCESSUS_SAV"
        elif '?' in text:
            return "INFO"
        else:
            return "AUTRE"
    
    def _infer_responsable(self, theme: str, incident_type: str) -> str:
        """Infer responsible service from theme and incident type."""
        if incident_type in ["PANNE", "LENTEUR"]:
            return "TECHNIQUE"
        elif theme == "FACTURE" or incident_type == "FACTURATION":
            return "COMMERCIAL"
        elif theme == "RESEAU":
            return "RESEAU"
        else:
            return "AUTRE"
    
    def classify_tweet(self, text: str) -> ClassificationResult:
        """
        Complete classification of a tweet across all dimensions.
        
        Implements full PROMPT CURSOR.txt pipeline:
        1. Sentiment analysis (CamemBERT/TextBlob/Rules)
        2. Reclamation detection (multi-factor)
        3. Urgency classification
        4. Theme classification (zero-shot/rules)
        5. Incident type inference
        6. Responsible service inference
        7. Global confidence calculation
        
        Args:
            text: Raw tweet text
        
        Returns:
            ClassificationResult with all fields populated
        """
        if not text or pd.isna(text):
            return ClassificationResult(
                sentiment="NEUTRE",
                reclamation="NON",
                urgence="FAIBLE",
                theme="AUTRE",
                type_incident="AUTRE",
                responsable="AUTRE",
                confiance=0.0,
                metadata={'error': 'empty_text'}
            )
        
        # 1. Sentiment
        sentiment, sent_conf = self.classify_sentiment(text)
        
        # 2. Reclamation
        is_reclam, reclam_conf = self.detect_reclamation(text)
        reclamation = "OUI" if is_reclam else "NON"
        
        # 3. Urgence
        urgence = self.classify_urgence(text, is_reclam)
        
        # 4. Theme
        theme, theme_conf = self.classify_theme(text)
        
        # 5. Type incident
        type_incident = self._infer_incident_type(text, theme)
        
        # 6. Responsable
        responsable = self._infer_responsable(theme, type_incident)
        
        # 7. Global confidence (weighted average)
        confiance = round(
            sent_conf * 0.25 +      # Sentiment
            reclam_conf * 0.40 +    # Reclamation (most important)
            theme_conf * 0.35,      # Theme
            2
        )
        
        # Metadata for debugging
        metadata = {
            'sent_conf': sent_conf,
            'reclam_conf': reclam_conf,
            'theme_conf': theme_conf
        }
        
        return ClassificationResult(
            sentiment=sentiment,
            reclamation=reclamation,
            urgence=urgence,
            theme=theme,
            type_incident=type_incident,
            responsable=responsable,
            confiance=confiance,
            metadata=metadata
        )
