"""
Script de Génération du Dataset d'Entraînement Complet
=======================================================

Génère un nouveau dataset d'entraînement avec TOUS les KPIs à partir de free_tweet_export.csv

Colonnes générées:
- sentiment (positif/neutre/négatif)
- catégorie (thème principal)
- priority (basse/moyenne/haute/critique)
- urgent (True/False)
- besoin_reponse (True/False)
- estimation_resolution (en heures)
- réclamations (oui/non)

Développé pour mémoire de Master en Data Science
Date: 2025-11-08
"""

import sys
import os
sys.path.insert(0, 'streamlit_app')

import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des services
from services.tweet_cleaner import TweetCleaner
from services.ultra_optimized_classifier import UltraOptimizedClassifier

class TrainingDatasetGenerator:
    """Générateur de dataset d'entraînement avec tous les KPIs"""
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.cleaner = TweetCleaner()
        self.classifier = None
        
    def load_data(self) -> pd.DataFrame:
        """Charge le dataset brut"""
        logger.info(f"📂 Chargement de {self.input_file}...")
        df = pd.read_csv(self.input_file)
        logger.info(f"✅ {len(df):,} tweets chargés")
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie les données"""
        logger.info("🧹 Nettoyage des données...")
        
        # Utiliser TweetCleaner
        df_cleaned, stats = self.cleaner.process_dataframe(df.copy(), 'text')
        
        logger.info(f"✅ Nettoyage terminé:")
        logger.info(f"   - Original: {stats.get('total_original', 0):,} tweets")
        logger.info(f"   - Nettoyé: {stats.get('total_cleaned', 0):,} tweets")
        logger.info(f"   - Doublons retirés: {stats.get('duplicates_removed', 0):,}")
        
        return df_cleaned
    
    def classify_data(self, df: pd.DataFrame, mode: str = 'balanced') -> pd.DataFrame:
        """Classifie les données avec tous les KPIs"""
        logger.info(f"🤖 Classification en mode {mode.upper()}...")
        logger.info(f"   Dataset: {len(df):,} tweets")
        
        # Initialiser le classificateur ultra-optimisé
        self.classifier = UltraOptimizedClassifier(
            batch_size=50,
            max_workers=4,
            use_cache=True,
            enable_logging=True
        )
        
        # Progress callback
        def progress_callback(message, progress):
            logger.info(f"   {message} ({progress*100:.0f}%)")
        
        # Classification
        df_classified, benchmark = self.classifier.classify_tweets_batch(
            df,
            'text_cleaned',
            mode=mode,
            progress_callback=progress_callback
        )
        
        logger.info(f"✅ Classification terminée:")
        logger.info(f"   - Temps: {benchmark.total_time_seconds:.1f}s")
        logger.info(f"   - Vitesse: {benchmark.tweets_per_second:.1f} tweets/s")
        
        return df_classified
    
    def add_training_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute et formate les colonnes d'entraînement"""
        logger.info("📋 Génération des colonnes d'entraînement...")
        
        df_training = df.copy()
        
        # 1. Sentiment (déjà présent)
        if 'sentiment' not in df_training.columns:
            df_training['sentiment'] = 'neutre'
        
        # 2. Catégorie (renommer 'topics' si présent)
        if 'topics' in df_training.columns:
            df_training['catégorie'] = df_training['topics']
        else:
            df_training['catégorie'] = 'autre'
        
        # 3. Priority (basée sur urgence)
        if 'urgence' in df_training.columns:
            df_training['priority'] = df_training['urgence'].map({
                'faible': 'basse',
                'moyenne': 'moyenne',
                'critique': 'haute'
            }).fillna('basse')
        else:
            df_training['priority'] = 'basse'
        
        # 4. Urgent (True/False basé sur urgence)
        if 'urgence' in df_training.columns:
            df_training['urgent'] = df_training['urgence'].isin(['critique'])
        else:
            df_training['urgent'] = False
        
        # 5. Besoin_reponse (basé sur sentiment et is_claim)
        if 'sentiment' in df_training.columns and 'is_claim' in df_training.columns:
            df_training['besoin_reponse'] = (
                (df_training['sentiment'] == 'negatif') | 
                (df_training['is_claim'] == 'oui')
            )
        else:
            df_training['besoin_reponse'] = True
        
        # 6. Estimation_resolution (en heures, basée sur priority et urgence)
        def calculate_resolution_time(row):
            if row.get('urgent', False):
                return 2  # 2 heures pour urgent
            elif row.get('priority', 'basse') == 'haute':
                return 24  # 24h pour haute priorité
            elif row.get('priority', 'basse') == 'moyenne':
                return 48  # 48h pour moyenne
            else:
                return 72  # 72h pour basse
        
        df_training['estimation_resolution'] = df_training.apply(calculate_resolution_time, axis=1)
        
        # 7. Réclamations (basé sur is_claim)
        if 'is_claim' in df_training.columns:
            df_training['réclamations'] = df_training['is_claim']
        else:
            df_training['réclamations'] = 'non'
        
        logger.info(f"✅ Colonnes générées:")
        logger.info(f"   - sentiment: {df_training['sentiment'].nunique()} valeurs uniques")
        logger.info(f"   - catégorie: {df_training['catégorie'].nunique()} valeurs uniques")
        logger.info(f"   - priority: {df_training['priority'].nunique()} valeurs uniques")
        logger.info(f"   - urgent: {df_training['urgent'].sum()} tweets urgents")
        logger.info(f"   - besoin_reponse: {df_training['besoin_reponse'].sum()} tweets nécessitant réponse")
        logger.info(f"   - estimation_resolution: Moyenne {df_training['estimation_resolution'].mean():.1f}h")
        logger.info(f"   - réclamations: {(df_training['réclamations'] == 'oui').sum()} réclamations")
        
        return df_training
    
    def select_training_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sélectionne les colonnes finales pour l'entraînement"""
        
        # Colonnes de base à conserver
        base_columns = ['tweet_id', 'author', 'text', 'date', 'url']
        
        # Colonnes d'entraînement demandées
        training_columns = [
            'sentiment',
            'catégorie',
            'priority',
            'urgent',
            'besoin_reponse',
            'estimation_resolution',
            'réclamations'
        ]
        
        # Colonnes supplémentaires utiles
        extra_columns = ['confidence', 'text_cleaned']
        
        # Sélectionner les colonnes disponibles
        available_base = [col for col in base_columns if col in df.columns]
        available_training = [col for col in training_columns if col in df.columns]
        available_extra = [col for col in extra_columns if col in df.columns]
        
        selected_columns = available_base + available_training + available_extra
        
        df_final = df[selected_columns].copy()
        
        logger.info(f"📋 Colonnes finales sélectionnées: {len(selected_columns)}")
        logger.info(f"   {', '.join(selected_columns)}")
        
        return df_final
    
    def generate(self, mode: str = 'balanced', min_tweets: int = 2600, max_tweets: int = 3500):
        """Génère le dataset d'entraînement complet"""
        
        print("\n" + "="*80)
        print("  GÉNÉRATION DATASET D'ENTRAÎNEMENT COMPLET")
        print("  Classification Mistral - Tous les KPIs")
        print("="*80 + "\n")
        
        # 1. Chargement
        df = self.load_data()
        
        # 2. Nettoyage
        df_cleaned = self.clean_data(df)
        
        # 3. Vérifier la taille
        if len(df_cleaned) < min_tweets:
            logger.warning(f"⚠️  Dataset trop petit après nettoyage: {len(df_cleaned)} < {min_tweets}")
            logger.warning(f"   On continue quand même...")
        
        # 4. Limiter si nécessaire
        if len(df_cleaned) > max_tweets:
            logger.info(f"📊 Échantillonnage de {len(df_cleaned):,} à {max_tweets:,} tweets...")
            df_cleaned = df_cleaned.sample(n=max_tweets, random_state=42).reset_index(drop=True)
        
        # 5. Classification avec tous les KPIs
        df_classified = self.classify_data(df_cleaned, mode=mode)
        
        # 6. Ajout des colonnes d'entraînement
        df_training = self.add_training_columns(df_classified)
        
        # 7. Sélection des colonnes finales
        df_final = self.select_training_columns(df_training)
        
        # 8. Sauvegarde
        logger.info(f"💾 Sauvegarde dans {self.output_file}...")
        df_final.to_csv(self.output_file, index=False, encoding='utf-8')
        
        # 9. Statistiques finales
        print("\n" + "="*80)
        print("  ✅ DATASET D'ENTRAÎNEMENT GÉNÉRÉ AVEC SUCCÈS")
        print("="*80 + "\n")
        
        print(f"📊 STATISTIQUES:")
        print(f"   - Tweets originaux:     {len(df):,}")
        print(f"   - Tweets nettoyés:      {len(df_cleaned):,}")
        print(f"   - Tweets finaux:        {len(df_final):,}")
        print(f"   - Colonnes:             {len(df_final.columns)}")
        
        print(f"\n📋 COLONNES GÉNÉRÉES:")
        for i, col in enumerate(df_final.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print(f"\n🎯 KPIs:")
        if 'sentiment' in df_final.columns:
            print(f"   - Sentiment positif:    {(df_final['sentiment'] == 'positif').sum():,} ({(df_final['sentiment'] == 'positif').sum()/len(df_final)*100:.1f}%)")
            print(f"   - Sentiment neutre:     {(df_final['sentiment'] == 'neutre').sum():,} ({(df_final['sentiment'] == 'neutre').sum()/len(df_final)*100:.1f}%)")
            print(f"   - Sentiment négatif:    {(df_final['sentiment'] == 'negatif').sum():,} ({(df_final['sentiment'] == 'negatif').sum()/len(df_final)*100:.1f}%)")
        
        if 'réclamations' in df_final.columns:
            reclamations = (df_final['réclamations'] == 'oui').sum()
            print(f"   - Réclamations:         {reclamations:,} ({reclamations/len(df_final)*100:.1f}%)")
        
        if 'urgent' in df_final.columns:
            urgent = df_final['urgent'].sum()
            print(f"   - Tweets urgents:       {urgent:,} ({urgent/len(df_final)*100:.1f}%)")
        
        if 'besoin_reponse' in df_final.columns:
            besoin = df_final['besoin_reponse'].sum()
            print(f"   - Besoin réponse:       {besoin:,} ({besoin/len(df_final)*100:.1f}%)")
        
        if 'estimation_resolution' in df_final.columns:
            print(f"   - Résolution moyenne:   {df_final['estimation_resolution'].mean():.1f}h")
        
        print(f"\n💾 FICHIER GÉNÉRÉ:")
        print(f"   {self.output_file}")
        
        file_size = os.path.getsize(self.output_file) / 1024 / 1024
        print(f"   Taille: {file_size:.2f} MB")
        
        print("\n" + "="*80)
        print("  🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS")
        print("="*80 + "\n")
        
        return df_final


def main():
    """Fonction principale"""
    
    # Configuration
    input_file = "data/raw/free_tweet_export.csv"
    output_file = "data/training/train_dataset.csv"
    
    # Mode de classification
    mode = 'balanced'  # balanced = meilleur compromis vitesse/précision
    
    # Objectif de taille
    min_tweets = 2600
    max_tweets = 3500
    
    print("\n╔════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                                        ║")
    print("║           📊 GÉNÉRATION DATASET D'ENTRAÎNEMENT AVEC TOUS LES KPIs                     ║")
    print("║                                                                                        ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════════╝\n")
    
    print(f"📁 CONFIGURATION:")
    print(f"   - Fichier source:    {input_file}")
    print(f"   - Fichier sortie:    {output_file}")
    print(f"   - Mode:              {mode.upper()} (88% précision, ~2 min)")
    print(f"   - Objectif taille:   {min_tweets:,} - {max_tweets:,} tweets")
    
    print(f"\n🎯 COLONNES À GÉNÉRER:")
    colonnes = [
        "sentiment",
        "catégorie",
        "priority",
        "urgent",
        "besoin_reponse",
        "estimation_resolution",
        "réclamations"
    ]
    for i, col in enumerate(colonnes, 1):
        print(f"   {i}. {col}")
    
    print("\n" + "-"*80 + "\n")
    
    try:
        # Vérifier l'existence du fichier source
        if not os.path.exists(input_file):
            logger.error(f"❌ Fichier source non trouvé: {input_file}")
            return
        
        # Générer le dataset
        generator = TrainingDatasetGenerator(input_file, output_file)
        df_final = generator.generate(mode=mode, min_tweets=min_tweets, max_tweets=max_tweets)
        
        # Validation finale
        print("\n✅ VALIDATION FINALE:")
        print(f"   - Dataset généré: {len(df_final):,} tweets")
        
        if min_tweets <= len(df_final) <= max_tweets:
            print(f"   - Taille cible: ✅ OK ({min_tweets:,} - {max_tweets:,})")
        else:
            print(f"   - Taille cible: ⚠️  Hors objectif")
        
        # Vérifier toutes les colonnes
        colonnes_requises = colonnes
        colonnes_presentes = [col for col in colonnes_requises if col in df_final.columns]
        
        print(f"   - Colonnes requises: {len(colonnes_presentes)}/{len(colonnes_requises)}")
        
        if len(colonnes_presentes) == len(colonnes_requises):
            print(f"   - Toutes les colonnes: ✅ Présentes")
        else:
            manquantes = [col for col in colonnes_requises if col not in df_final.columns]
            print(f"   - Colonnes manquantes: {', '.join(manquantes)}")
        
        print("\n📖 PROCHAINES ÉTAPES:")
        print(f"   1. Vérifier le fichier: {output_file}")
        print(f"   2. Utiliser ce dataset pour l'entraînement du modèle")
        print(f"   3. Générer les datasets de validation et test si nécessaire")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)








