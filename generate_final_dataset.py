"""
Génération Finale du Dataset d'Entraînement avec Tous les KPIs
"""
import sys
import os
sys.path.insert(0, 'streamlit_app')

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("  GÉNÉRATION DATASET FINAL - TOUS LES KPIs")
print("="*80 + "\n")

# 1. Chargement
print("[1/5] Chargement des données...")
df = pd.read_csv("data/raw/free_tweet_export.csv")
print(f"✅ {len(df):,} tweets chargés\n")

# 2. Nettoyage
print("[2/5] Nettoyage...")
from services.tweet_cleaner import TweetCleaner

cleaner = TweetCleaner()
df_clean, stats = cleaner.process_dataframe(df.copy(), 'text')
print(f"✅ {len(df_clean):,} tweets après nettoyage\n")

# 3. Échantillonnage à 3000
print("[3/5] Échantillonnage à 3000 tweets...")
if len(df_clean) > 3000:
    df_sample = df_clean.sample(n=3000, random_state=42).reset_index(drop=True)
else:
    df_sample = df_clean
print(f"✅ {len(df_sample):,} tweets sélectionnés\n")

# 4. Classification BERT + Rules
print("[4/5] Classification (BERT + Rules)...")
print("   Cela peut prendre 1-2 minutes...\n")

from services.bert_classifier import BERTClassifier
from services.rule_classifier import EnhancedRuleClassifier

# BERT
bert = BERTClassifier(use_gpu=False)
rule = EnhancedRuleClassifier()

results = []
for idx, row in df_sample.iterrows():
    text = str(row.get('text_cleaned', row.get('text', '')))
    
    # Classification BERT
    bert_result = bert.classify_sentiment(text) if text else {'sentiment': 'neutre'}
    
    # Classification Rules
    rule_result = rule.classify(text) if text else {}
    
    # Combinaison
    sentiment = bert_result.get('sentiment', 'neutre')
    is_claim = rule_result.get('is_claim', 'non')
    urgence = rule_result.get('urgence', 'faible')
    topics = rule_result.get('topics', 'autre')
    
    # Calcul des KPIs dérivés
    priority = {'faible': 'basse', 'moyenne': 'moyenne', 'critique': 'haute'}[urgence]
    urgent = urgence == 'critique'
    besoin_reponse = (sentiment == 'negatif') or (is_claim == 'oui')
    
    if urgent:
        estimation_resolution = 2
    elif priority == 'haute':
        estimation_resolution = 24
    elif priority == 'moyenne':
        estimation_resolution = 48
    else:
        estimation_resolution = 72
    
    results.append({
        'tweet_id': row.get('tweet_id', idx),
        'author': row.get('author', ''),
        'text': row.get('text', ''),
        'date': row.get('date', ''),
        'url': row.get('url', ''),
        'text_cleaned': row.get('text_cleaned', text),
        'sentiment': sentiment,
        'catégorie': topics,
        'priority': priority,
        'urgent': urgent,
        'besoin_reponse': besoin_reponse,
        'estimation_resolution': estimation_resolution,
        'réclamations': is_claim
    })
    
    if (idx + 1) % 500 == 0:
        print(f"   Progrès: {idx + 1:,}/{len(df_sample):,} tweets...")

print(f"✅ Classification terminée\n")

# 5. Création du DataFrame final
print("[5/5] Création du dataset final...")
df_final = pd.DataFrame(results)

# Sauvegarde
output_file = "data/training/train_dataset.csv"
df_final.to_csv(output_file, index=False, encoding='utf-8')

file_size = os.path.getsize(output_file) / 1024 / 1024
print(f"✅ Dataset sauvegardé: {file_size:.2f} MB\n")

# Statistiques
print("="*80)
print("  ✅ GÉNÉRATION RÉUSSIE")
print("="*80 + "\n")

print(f"📊 RÉSUMÉ:")
print(f"   Tweets: {len(df_final):,}")
print(f"   Colonnes: {len(df_final.columns)}")
print(f"   Fichier: {output_file}\n")

print(f"📋 COLONNES ({len(df_final.columns)}):")
for i, col in enumerate(df_final.columns, 1):
    print(f"   {i:2d}. {col}")

print(f"\n🎯 DISTRIBUTION:")
print(f"   Sentiment positif:  {(df_final['sentiment'] == 'positif').sum():,} ({(df_final['sentiment'] == 'positif').sum()/len(df_final)*100:.1f}%)")
print(f"   Sentiment neutre:   {(df_final['sentiment'] == 'neutre').sum():,} ({(df_final['sentiment'] == 'neutre').sum()/len(df_final)*100:.1f}%)")
print(f"   Sentiment négatif:  {(df_final['sentiment'] == 'negatif').sum():,} ({(df_final['sentiment'] == 'negatif').sum()/len(df_final)*100:.1f}%)")
print(f"   Réclamations (oui): {(df_final['réclamations'] == 'oui').sum():,} ({(df_final['réclamations'] == 'oui').sum()/len(df_final)*100:.1f}%)")
print(f"   Tweets urgents:     {df_final['urgent'].sum():,} ({df_final['urgent'].sum()/len(df_final)*100:.1f}%)")
print(f"   Besoin réponse:     {df_final['besoin_reponse'].sum():,} ({df_final['besoin_reponse'].sum()/len(df_final)*100:.1f}%)")

print("\n" + "="*80)
print("  🎉 DATASET PRÊT POUR L'ENTRAÎNEMENT")
print("="*80 + "\n")








