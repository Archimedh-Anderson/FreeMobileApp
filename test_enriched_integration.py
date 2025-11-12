"""
Test Script for Enriched Dataset Integration
=============================================

Vérifie que l'intégration du dataset enrichi fonctionne correctement.
"""

import sys
import os
sys.path.insert(0, 'streamlit_app')

from services.enriched_dataset_loader import EnrichedDatasetLoader, get_enriched_dataset_loader
import pandas as pd

print("\n" + "="*80)
print("  TEST D'INTÉGRATION DU DATASET ENRICHI")
print("="*80 + "\n")

# Test 1: Chargement du loader
print("[1/5] Test du chargeur de dataset enrichi...")
try:
    loader = get_enriched_dataset_loader()
    print("   ✅ Loader initialisé avec succès")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# Test 2: Vérification du dataset
print("\n[2/5] Vérification du dataset...")
try:
    dataset = loader.get_dataset()
    if dataset is not None:
        print(f"   ✅ Dataset chargé: {len(dataset):,} lignes, {len(dataset.columns)} colonnes")
        
        if loader.is_enriched():
            print("   ✅ Dataset enrichi détecté")
            enriched_cols = loader.get_enriched_columns()
            print(f"   ✅ Colonnes enrichies: {len(enriched_cols)}")
            for col in enriched_cols:
                print(f"      • {col}")
        else:
            print("   ⚠️  Dataset original utilisé (dataset enrichi non disponible)")
    else:
        print("   ❌ Dataset non chargé")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 3: Vérification des statistiques KPI
print("\n[3/5] Vérification des statistiques KPI...")
try:
    kpi_stats = loader.get_kpi_stats()
    if kpi_stats is not None:
        print(f"   ✅ Statistiques KPI chargées")
        print(f"      • Total tweets: {kpi_stats.total_tweets:,}")
        print(f"      • Date traitement: {kpi_stats.date_traitement}")
        
        # Thème principal
        top_theme, theme_pct = kpi_stats.get_top_theme()
        print(f"      • Thème principal: {top_theme} ({theme_pct:.2f}%)")
        
        # Incident principal
        top_incident, incident_pct = kpi_stats.get_top_incident()
        print(f"      • Incident principal: {top_incident} ({incident_pct:.2f}%)")
        
        # Taux de réclamations
        reclamation_rate = kpi_stats.get_reclamation_rate()
        print(f"      • Taux de réclamations: {reclamation_rate:.2f}%")
        
        print("   ✅ Toutes les métriques accessibles")
    else:
        print("   ⚠️  Statistiques KPI non disponibles")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 4: Vérification des résumés
print("\n[4/5] Vérification des résumés...")
try:
    theme_summary = loader.get_theme_summary()
    incident_summary = loader.get_incident_summary()
    reclamation_summary = loader.get_reclamation_summary()
    
    if theme_summary:
        print(f"   ✅ Résumé thèmes: {theme_summary.get('total_themes', 0)} thèmes détectés")
    
    if incident_summary:
        print(f"   ✅ Résumé incidents: {incident_summary.get('total_incidents', 0)} types d'incidents")
    
    if reclamation_summary:
        print(f"   ✅ Résumé réclamations: {reclamation_summary.get('reclamation_rate', 0):.2f}%")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 5: Échantillon de données
print("\n[5/5] Test d'échantillonnage...")
try:
    sample = loader.get_sample_data(n=10)
    if sample is not None:
        print(f"   ✅ Échantillon de {len(sample)} lignes généré")
        
        if loader.is_enriched():
            print("   ✅ Colonnes enrichies présentes dans l'échantillon:")
            enriched_cols = [col for col in sample.columns if 'Thème' in col or 'Incident' in col or 'confidence' in col]
            for col in enriched_cols:
                print(f"      • {col}: {sample[col].dtype}")
    else:
        print("   ⚠️  Échantillonnage non disponible")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Résumé final
print("\n" + "="*80)
if loader.is_enriched():
    print("  ✅ INTÉGRATION RÉUSSIE - Dataset enrichi opérationnel")
    print("\n  Le dataset enrichi est chargé et toutes les métriques sont disponibles.")
    print("  Les KPIs enrichis s'afficheront automatiquement dans les pages de classification.")
else:
    print("  ⚠️  INTÉGRATION PARTIELLE - Dataset original utilisé")
    print("\n  Le dataset enrichi n'est pas disponible.")
    print("  L'application fonctionnera avec le dataset original.")
    print("\n  Pour activer les KPIs enrichis:")
    print("     1. Exécutez: python retrain_dataset_with_kpis.py")
    print("     2. Vérifiez: data/training/train_dataset_enriched.csv")
    print("     3. Vérifiez: data/training/train_dataset_enriched_kpi_stats.json")

print("="*80 + "\n")
