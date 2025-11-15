"""
Orchestrateur Multi-Modèle Intelligent - FreeMobilaChat
========================================================

Combine BERT + Règles + Mistral pour classification optimale.
Mode BALANCED optimisé pour i9-13900H + RTX 5060.

Performance cible: 5000 tweets en < 2 minutes
"""

from typing import Dict, List, Optional
import pandas as pd
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

logger = logging.getLogger(__name__)


class MultiModelOrchestrator:
    """
    Orchestrateur intelligent combinant 3 modèles complémentaires:
    
    1. BERT (GPU): Sentiment rapide sur TOUS les tweets
    2. Règles: is_claim + urgence sur TOUS les tweets  
    3. Mistral: Topics + incident sur ÉCHANTILLON stratifié (20%)
    
    Optimisé pour RTX 5060 + i9-13900H + 32GB RAM
    """
    
    def __init__(self, mode: str = 'balanced', provider: str = 'mistral'):
        """
        Initialise l'orchestrateur
        
        Args:
            mode: 'fast' | 'balanced' | 'precise'
            provider: 'mistral' | 'gemini' - Provider LLM à utiliser
        """
        self.mode = mode
        self.provider = provider  # 'mistral' ou 'gemini'
        self.models_loaded = False
        
        logger.info(f" Orchestrateur multi-modèle: Mode {mode.upper()}, Provider {provider.upper()}")
        
        # Chargement lazy des modèles
        self.bert = None
        self.rules = None
        self.mistral = None
        self.gemini = None
        self.parallel_processor = None
    
    def load_models(self, progress_callback=None):
        """
        Charge les modèles selon le mode
        
        Args:
            progress_callback: Fonction callback pour progression
        """
        if self.models_loaded:
            return
        
        try:
            if progress_callback:
                progress_callback("Chargement BERT...", 0.1)
            
            # 1. BERT (toujours chargé sauf mode fast sans sentiment)
            from services.bert_classifier import BERTClassifier
            self.bert = BERTClassifier(
                batch_size=64,  # Optimisé pour RTX 5060
                use_gpu=True
            )
            logger.info(f" BERT chargé sur {self.bert.device}")
            
            if progress_callback:
                progress_callback("Chargement Règles...", 0.3)
            
            # 2. Règles (ultra-léger, toujours chargé)
            from services.rule_classifier import EnhancedRuleClassifier
            self.rules = EnhancedRuleClassifier()
            logger.info(" Classificateur par règles chargé")
            
            if progress_callback:
                provider_name = "Gemini" if self.provider == 'gemini' else "Mistral"
                progress_callback(f"Chargement {provider_name}...", 0.5)
            
            # 3. Mistral ou Gemini (pour mode balanced et precise)
            if self.mode in ['balanced', 'precise']:
                if self.provider == 'gemini':
                    try:
                        from services.gemini_classifier import GeminiClassifier
                        self.gemini = GeminiClassifier(
                            batch_size=50,
                            temperature=0.1
                        )
                        logger.info(" Gemini chargé")
                    except Exception as e:
                        logger.warning(f"Erreur chargement Gemini: {e}. Fallback vers Mistral...")
                        self.provider = 'mistral'  # Fallback vers Mistral
                        from services.mistral_classifier import MistralClassifier
                        self.mistral = MistralClassifier(
                            batch_size=50,
                            temperature=0.1
                        )
                        logger.info(" Mistral chargé (fallback)")
                else:
                    from services.mistral_classifier import MistralClassifier
                    self.mistral = MistralClassifier(
                        batch_size=50,
                        temperature=0.1
                    )
                    logger.info(" Mistral chargé")
            
            if progress_callback:
                progress_callback("Chargement Parallélisateur...", 0.7)
            
            # 4. Processeur parallèle
            from services.parallel_processor import ParallelProcessor
            self.parallel_processor = ParallelProcessor(
                n_workers=8,  # Optimisé pour i9-13900H
                show_progress=False
            )
            logger.info(" Processeur parallèle initialisé (8 workers)")
            
            if progress_callback:
                progress_callback("Modèles chargés!", 1.0)
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f" Erreur chargement modèles: {e}")
            raise
    
    def classify_intelligent(self,
                            df: pd.DataFrame,
                            text_column: str = 'text_cleaned',
                            progress_callback=None) -> pd.DataFrame:
        """
        Classification intelligente multi-modèle
        
        Pipeline optimisé:
        1. BERT sentiment (TOUS) - 10s
        2. Règles is_claim + urgence (TOUS) - < 1s
        3. Mistral topics + incident (20% échantillon) - 1-2min
        4. Agrégation résultats - < 1s
        
        Args:
            df: DataFrame avec tweets nettoyés
            text_column: Nom de la colonne de texte
            progress_callback: Callback pour progression Streamlit
            
        Returns:
            DataFrame avec les 6 KPIs complets
        """
        if not self.models_loaded:
            self.load_models(progress_callback)
        
        start_time = time.time()
        results = df.copy()
        total_tweets = len(df)
        
        logger.info(f" Classification de {total_tweets} tweets...")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 1: BERT Sentiment (TOUS les tweets) - GPU Ultra-rapide
        # ═══════════════════════════════════════════════════════════
        if progress_callback:
            progress_callback("Phase 1: BERT Sentiment (GPU)...", 0.1)
        
        phase1_start = time.time()
        logger.info(" Phase 1: BERT Sentiment...")
        
        bert_results = self.bert.predict_with_confidence(
            results[text_column].fillna('').tolist(),
            show_progress=True
        )
        
        results['sentiment'] = bert_results['sentiment']
        results['bert_confidence'] = bert_results['sentiment_confidence']
        
        phase1_time = time.time() - phase1_start
        logger.info(f" Phase 1: {total_tweets} tweets en {phase1_time:.1f}s ({total_tweets/phase1_time:.0f} tweets/s)")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 2: Règles is_claim + urgence (TOUS) - Ultra-rapide
        # ═══════════════════════════════════════════════════════════
        if progress_callback:
            progress_callback("Phase 2: Détection is_claim + urgence...", 0.3)
        
        phase2_start = time.time()
        logger.info("️ Phase 2: Règles (is_claim + urgence + topics)...")
        
        rules_results = self.rules.classify_batch_extended(
            results[text_column].fillna('').tolist()
        )
        
        results['is_claim'] = rules_results['is_claim']
        results['urgence'] = rules_results['urgence']
        results['topics_preliminary'] = rules_results['topics']
        results['incident_preliminary'] = rules_results['incident']
        
        phase2_time = time.time() - phase2_start
        logger.info(f" Phase 2: {total_tweets} tweets en {phase2_time:.1f}s ({total_tweets/phase2_time:.0f} tweets/s)")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 3: Mistral/Gemini sur ÉCHANTILLON intelligent (Mode Balanced)
        # ═══════════════════════════════════════════════════════════
        if self.mode in ['balanced', 'precise']:
            provider_name = "Gemini" if self.provider == 'gemini' else "Mistral"
            if progress_callback:
                progress_callback(f"Phase 3: {provider_name} sur échantillon stratifié...", 0.5)
            
            phase3_start = time.time()
            
            # Sélection intelligente de l'échantillon
            if self.mode == 'balanced':
                sample_df = self._select_strategic_sample(results, ratio=0.20)
            else:
                sample_df = results  # Mode precise: tous
            
            sample_size = len(sample_df)
            logger.info(f" Phase 3: {provider_name} sur {sample_size} tweets ({sample_size/total_tweets*100:.1f}%)...")
            
            if progress_callback:
                progress_callback(f"Phase 3: Classification {provider_name} de {sample_size} tweets...", 0.6)
            
            # Classification Mistral ou Gemini en parallèle
            if self.provider == 'gemini' and self.gemini:
                llm_results = self._classify_gemini_parallel(
                    sample_df,
                    text_column,
                    progress_callback
                )
            else:
                llm_results = self._classify_mistral_parallel(
                    sample_df,
                    text_column,
                    progress_callback
                )
            
            # Fusionner résultats LLM
            for idx in llm_results.index:
                if idx in results.index:
                    # Topics
                    if 'categorie' in llm_results.columns:
                        results.loc[idx, 'topics'] = llm_results.loc[idx, 'categorie']
                    
                    # Incident
                    if 'incident' in llm_results.columns:
                        results.loc[idx, 'incident'] = llm_results.loc[idx, 'incident']
                    
                    # Confidence
                    if 'score_confiance' in llm_results.columns:
                        results.loc[idx, 'confidence'] = llm_results.loc[idx, 'score_confiance']
                    
                    # is_claim validé par LLM
                    if 'is_claim' in llm_results.columns:
                        results.loc[idx, 'is_claim'] = llm_results.loc[idx, 'is_claim']
            
            phase3_time = time.time() - phase3_start
            logger.info(f" Phase 3: {sample_size} tweets en {phase3_time:.1f}s ({sample_size/phase3_time:.0f} tweets/s)")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 4: Agrégation et Finalisation
        # ═══════════════════════════════════════════════════════════
        if progress_callback:
            progress_callback("Phase 4: Agrégation finale...", 0.9)
        
        # Pour les tweets non classifiés par Mistral: utiliser résultats préliminaires
        if 'topics' not in results.columns:
            results['topics'] = results['topics_preliminary']
        else:
            results['topics'] = results['topics'].fillna(results['topics_preliminary'])
        
        if 'incident' not in results.columns:
            results['incident'] = results['incident_preliminary']
        else:
            results['incident'] = results['incident'].fillna(results['incident_preliminary'])
        
        # Confidence: agrégation BERT + règles
        if 'confidence' not in results.columns or results['confidence'].isna().any():
            results['confidence'] = results.apply(
                lambda row: self._calculate_aggregated_confidence(row), axis=1
            )
        
        # Nettoyer colonnes temporaires
        results.drop(columns=['topics_preliminary', 'incident_preliminary'], errors='ignore', inplace=True)
        
        # Statistiques finales
        total_time = time.time() - start_time
        logger.info(f"⏱️ Temps total: {total_time:.1f}s ({total_time/60:.1f}min)")
        logger.info(f" Vitesse moyenne: {total_tweets/total_time:.1f} tweets/s")
        
        if progress_callback:
            progress_callback(f" Classification terminée! {total_tweets} tweets en {total_time:.1f}s", 1.0)
        
        return results
    
    def _select_strategic_sample(self, df: pd.DataFrame, ratio: float = 0.20) -> pd.DataFrame:
        """
        Sélectionne un échantillon stratifié intelligent
        
        Priorité:
        1. Réclamations urgentes (100%)
        2. Réclamations moyennes (50%)
        3. Autres (10%)
        
        Args:
            df: DataFrame complet
            ratio: Ratio cible (20% par défaut)
            
        Returns:
            DataFrame échantillon
        """
        samples = []
        
        # Priorité 1: TOUTES les réclamations urgentes
        urgent_claims = df[(df['is_claim'] == 1) & (df['urgence'] == 'haute')]
        if len(urgent_claims) > 0:
            samples.append(urgent_claims)
            logger.info(f"   Priorité 1: {len(urgent_claims)} réclamations urgentes (100%)")
        
        # Priorité 2: 50% des réclamations moyennes
        medium_claims = df[(df['is_claim'] == 1) & (df['urgence'] == 'moyenne')]
        if len(medium_claims) > 0:
            sample_size = max(len(medium_claims) // 2, 50)
            medium_sample = medium_claims.sample(n=min(sample_size, len(medium_claims)))
            samples.append(medium_sample)
            logger.info(f"   Priorité 2: {len(medium_sample)} réclamations moyennes (50%)")
        
        # Priorité 3: Échantillon du reste pour équilibrer
        rest = df[df['is_claim'] == 0]
        if len(rest) > 0:
            target_total = int(len(df) * ratio)
            current_total = sum(len(s) for s in samples)
            remaining = max(target_total - current_total, 50)
            
            rest_sample = rest.sample(n=min(remaining, len(rest)))
            samples.append(rest_sample)
            logger.info(f"   Priorité 3: {len(rest_sample)} non-réclamations (échantillon)")
        
        # Combiner
        combined = pd.concat(samples) if samples else df.head(100)
        
        logger.info(f" Échantillon stratifié: {len(combined)}/{len(df)} ({len(combined)/len(df)*100:.1f}%)")
        
        return combined
    
    def _classify_mistral_parallel(self,
                                   df: pd.DataFrame,
                                   text_column: str,
                                   progress_callback=None) -> pd.DataFrame:
        """
        Classification Mistral en parallèle (optimisé pour i9)
        
        Args:
            df: DataFrame échantillon
            text_column: Colonne de texte
            progress_callback: Callback progression
            
        Returns:
            DataFrame avec résultats Mistral
        """
        # Découper en chunks pour parallélisation
        n_workers = 4  # 4 instances Mistral en parallèle
        chunk_size = (len(df) + n_workers - 1) // n_workers
        
        chunks = []
        for i in range(0, len(df), chunk_size):
            chunks.append(df.iloc[i:i+chunk_size].copy())
        
        logger.info(f"    {len(chunks)} chunks pour traitement parallèle")
        
        # Traitement parallèle
        results_list = []
        
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {}
            
            for idx, chunk in enumerate(chunks):
                future = executor.submit(
                    self._classify_chunk_mistral,
                    chunk,
                    text_column
                )
                futures[future] = idx
            
            # Collecter résultats
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results_list.append((idx, result))
                    
                    logger.info(f"    Chunk {idx+1}/{len(chunks)} terminé")
                    
                except Exception as e:
                    logger.error(f"    Erreur chunk {idx}: {e}")
        
        # Recombiner dans l'ordre
        results_list.sort(key=lambda x: x[0])
        combined = pd.concat([r[1] for r in results_list])
        
        return combined
    
    def _classify_gemini_parallel(self,
                                   df: pd.DataFrame,
                                   text_column: str,
                                   progress_callback=None) -> pd.DataFrame:
        """
        Classification Gemini en parallèle (optimisé pour i9)
        
        Args:
            df: DataFrame échantillon
            text_column: Colonne de texte
            progress_callback: Callback progression
            
        Returns:
            DataFrame avec résultats Gemini
        """
        if not self.gemini:
            logger.error("Gemini non initialisé")
            return df
        
        # Gemini gère déjà le batch processing, pas besoin de parallélisation complexe
        try:
            result = self.gemini.classify_dataframe(
                df,
                text_column,
                show_progress=False
            )
            return result
        except Exception as e:
            logger.error(f"Erreur classification Gemini: {e}")
            # Fallback: retourner df original avec valeurs par défaut
            df['categorie'] = 'autre'
            df['incident'] = 'non classifié'
            df['score_confiance'] = 0.5
            return df
    
    def _classify_chunk_mistral(self, chunk: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """
        Classifie un chunk avec Mistral
        
        Args:
            chunk: DataFrame chunk
            text_column: Colonne de texte
            
        Returns:
            DataFrame avec résultats
        """
        try:
            result = self.mistral.classify_dataframe(
                chunk,
                text_column,
                show_progress=False
            )
            return result
            
        except Exception as e:
            logger.error(f"Erreur classification chunk: {e}")
            # Fallback: retourner chunk original avec valeurs par défaut
            chunk['categorie'] = 'autre'
            chunk['incident'] = 'non classifié'
            chunk['score_confiance'] = 0.5
            return chunk
    
    def _calculate_aggregated_confidence(self, row: pd.Series) -> float:
        """
        Calcule un score de confiance agrégé
        
        Combine:
        - BERT confidence (sentiment)
        - Règles confidence (is_claim, urgence)
        - Mistral confidence (si disponible)
        
        Args:
            row: Ligne du DataFrame
            
        Returns:
            Score de confiance agrégé 0-1
        """
        scores = []
        
        # BERT confidence
        if 'bert_confidence' in row and not pd.isna(row['bert_confidence']):
            scores.append(row['bert_confidence'])
        
        # Règles: confiance selon détection
        if 'is_claim' in row:
            # is_claim détecté = haute confiance sur rules
            scores.append(0.85 if row['is_claim'] == 1 else 0.70)
        
        # Mistral confidence si disponible
        if 'mistral_confidence' in row and not pd.isna(row['mistral_confidence']):
            scores.append(row['mistral_confidence'])
        
        # Moyenne pondérée
        if scores:
            return sum(scores) / len(scores)
        
        return 0.70  # Par défaut
    
    def get_classification_report(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Génère un rapport détaillé de classification
        
        Args:
            df: DataFrame classifié
            
        Returns:
            Dict avec statistiques détaillées
        """
        report = {
            'total_tweets': len(df),
            
            # is_claim
            'claims_count': df['is_claim'].sum() if 'is_claim' in df.columns else 0,
            'claims_percentage': (df['is_claim'].sum() / len(df) * 100) if 'is_claim' in df.columns else 0,
            
            # Sentiment
            'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
            'sentiment_positive_pct': (df['sentiment'] == 'positif').sum() / len(df) * 100 if 'sentiment' in df.columns else 0,
            'sentiment_negatif_pct': (df['sentiment'] == 'negatif').sum() / len(df) * 100 if 'sentiment' in df.columns else 0,
            
            # Urgence
            'urgence_distribution': df['urgence'].value_counts().to_dict() if 'urgence' in df.columns else {},
            'urgence_haute_count': (df['urgence'] == 'haute').sum() if 'urgence' in df.columns else 0,
            
            # Topics
            'topics_distribution': df['topics'].value_counts().to_dict() if 'topics' in df.columns else {},
            'topics_count': df['topics'].nunique() if 'topics' in df.columns else 0,
            
            # Incidents
            'incident_distribution': df['incident'].value_counts().to_dict() if 'incident' in df.columns else {},
            'incident_count': df['incident'].nunique() if 'incident' in df.columns else 0,
            
            # Confidence
            'confidence_avg': df['confidence'].mean() if 'confidence' in df.columns else 0,
            'confidence_min': df['confidence'].min() if 'confidence' in df.columns else 0,
            'confidence_max': df['confidence'].max() if 'confidence' in df.columns else 0,
        }
        
        return report


def create_optimized_orchestrator(
    mode: str = 'balanced',
    gpu_available: bool = True,
    cpu_cores: int = 8,
    provider: str = 'mistral'
) -> MultiModelOrchestrator:
    """
    Factory pour créer un orchestrateur optimisé
    
    Args:
        mode: Mode de classification
        gpu_available: GPU disponible
        cpu_cores: Nombre de cores CPU
        provider: 'mistral' ou 'gemini' - Provider LLM à utiliser
        
    Returns:
        Orchestrateur configuré
    """
    logger.info(f"️ Création orchestrateur optimisé:")
    logger.info(f"   Mode: {mode}")
    logger.info(f"   Provider: {provider}")
    logger.info(f"   GPU: {gpu_available}")
    logger.info(f"   CPU cores: {cpu_cores}")
    
    orchestrator = MultiModelOrchestrator(mode=mode, provider=provider)
    
    return orchestrator


if __name__ == '__main__':
    # Test de l'orchestrateur
    print("\n Test de l'orchestrateur multi-modèle\n")
    
    # Données test
    test_data = pd.DataFrame({
        'text_cleaned': [
            "Panne internet depuis 3 jours, c'est urgent!",
            "Super service Free Mobile, très content",
            "Facture trop élevée ce mois",
            "Lenteur de connexion fibre",
            "Comment activer ma box Freebox?"
        ]
    })
    
    print(f" {len(test_data)} tweets de test")
    print(f"\n Classification avec orchestrateur...\n")
    
    # Créer orchestrateur
    orchestrator = create_optimized_orchestrator(mode='balanced')
    
    # Classifier
    start = time.time()
    results = orchestrator.classify_intelligent(test_data, 'text_cleaned')
    elapsed = time.time() - start
    
    print(f"\n Résultats en {elapsed:.2f}s:\n")
    print(results[['sentiment', 'is_claim', 'urgence', 'topics', 'confidence']].to_string())
    
    # Rapport
    report = orchestrator.get_classification_report(results)
    print(f"\n Rapport:")
    print(f"   Réclamations: {report['claims_count']}/{report['total_tweets']}")
    print(f"   Urgence haute: {report['urgence_haute_count']}")
    print(f"   Confiance moyenne: {report['confidence_avg']:.2f}")
    
    print("\n Test terminé!")

