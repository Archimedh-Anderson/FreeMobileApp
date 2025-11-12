"""
Script de Retraining du Dataset avec KPIs Enrichis
===================================================

Ce script retraine le dataset d'entraînement avec:
1. Correction des valeurs de réclamation (Oui/Non → valeurs précises)
2. Ajout de "Thème principal" avec classification score-based  
3. Ajout de "Incident principal" avec mapping de responsabilité
4. Calcul de statistiques (Count, Percentage) pour chaque catégorie
5. Export du dataset enrichi avec métriques de qualité

Basé sur la logique de classification de dynamic_classifier.py
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple
from collections import Counter
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedThemeClassifier:
    """Classificateur de thème basé sur score de mots-clés (pas de first-match)"""
    
    THEME_KEYWORDS = {
        'FIBRE': [
            'fibre', 'ftth', 'internet', 'débit', 'connexion', 'ligne', 'réseau',
            'box', 'freebox', 'adsl', 'vdsl', 'wifi', 'sans fil', 'routeur',
            'installation', 'technicien', 'câble', 'prise', 'étape'
        ],
        'MOBILE': [
            'mobile', 'téléphone', 'forfait', '4g', '5g', 'data', 'appel', 'sms',
            'carte sim', 'réseau mobile', 'couverture', 'signal', 'antenne'
        ],
        'TV': [
            'tv', 'télévision', 'chaîne', 'programme', 'replay', 'streaming',
            'chaines', 'player', 'décodeur', 'image', 'son', 'vidéo'
        ],
        'FACTURE': [
            'facture', 'facturation', 'prix', 'coût', 'tarif', 'paiement',
            'prélèvement', 'abonnement', 'euro', 'eur', 'rembours', 'crédit',
            'débit', 'montant', 'gratuit', 'payant'
        ],
        'SAV': [
            'sav', 'service client', 'support', 'assistance', 'conseiller',
            'contact', 'réponse', 'appel', '3244', 'messenger', 'whatsapp',
            'ticket', 'dossier', 'suivi', 'relance'
        ],
        'RESEAU': [
            'panne', 'coupure', 'interruption', 'bug', 'problème', 'incident',
            'dysfonctionnement', 'erreur', 'défaillance', 'perturbation',
            'instable', 'lent', 'slow'
        ],
        'ACTIVATION': [
            'activation', 'activer', 'mise en service', 'installation', 
            'raccordement', 'branchement', 'rendez-vous', 'technicien'
        ],
        'RESILIATION': [
            'résiliation', 'résilier', 'annulation', 'arrêt', 'fin', 'quitter',
            'partir', 'changer', 'concurrent', 'restitution'
        ]
    }
    
    def classify(self, text: str) -> Tuple[str, float, List[str]]:
        """Classifie le thème basé sur le score de mots-clés (méthode score-based)"""
        text_lower = text.lower()
        theme_scores = {}
        matched_keywords = {}
        
        # Calculer le score pour chaque thème
        for theme, keywords in self.THEME_KEYWORDS.items():
            score = 0
            matches = []
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matches.append(keyword)
            
            if score > 0:
                theme_scores[theme] = score
                matched_keywords[theme] = matches
        
        # Si aucun mot-clé détecté, retourner "autre"
        if not theme_scores:
            return 'autre', 0.5, []
        
        # Sélectionner le thème avec le score le plus élevé (pas le premier match!)
        best_theme = max(theme_scores, key=theme_scores.get)
        max_score = theme_scores[best_theme]
        
        # Calculer la confiance basée sur le nombre de mots-clés
        if max_score >= 3:
            confidence = 0.90
        elif max_score == 2:
            confidence = 0.85
        else:
            confidence = 0.75
        
        return best_theme, confidence, matched_keywords.get(best_theme, [])


class IncidentClassifier:
    """Classificateur d'incident avec mapping de responsabilité"""
    
    INCIDENT_PATTERNS = {
        'facturation': {
            'keywords': ['facture', 'facturation', 'prix', 'coût', 'tarif', 'prélèvement', 
                        'paiement', 'rembours', 'crédit', 'débit', 'montant'],
            'responsable': 'service_commercial'
        },
        'incident_reseau': {
            'keywords': ['panne', 'coupure', 'interruption', 'bug', 'erreur', 'problème',
                        'dysfonctionnement', 'défaillance', 'perturbation', 'instable'],
            'responsable': 'service_technique'
        },
        'livraison': {
            'keywords': ['livraison', 'colis', 'livré', 'réception', 'envoi', 'retour',
                        'restitution', 'matériel'],
            'responsable': 'service_logistique'
        },
        'information': {
            'keywords': ['information', 'savoir', 'connaitre', 'question', 'demande',
                        'comment', 'pourquoi', 'quand', 'quel'],
            'responsable': 'service_client'
        },
        'processus_sav': {
            'keywords': ['sav', 'support', 'assistance', 'conseiller', 'contact', 
                        'réponse', 'ticket', 'dossier', 'suivi', 'relance'],
            'responsable': 'service_client'
        },
        'technique': {
            'keywords': ['installation', 'configuration', 'paramètre', 'wifi', 'routeur',
                        'box', 'branchement', 'câble', 'technicien'],
            'responsable': 'service_technique'
        }
    }
    
    def classify(self, text: str) -> Tuple[str, str, float]:
        """Classifie l'incident et détermine le responsable"""
        text_lower = text.lower()
        incident_scores = {}
        
        # Calculer le score pour chaque type d'incident
        for incident_type, config in self.INCIDENT_PATTERNS.items():
            score = sum(1 for keyword in config['keywords'] if keyword in text_lower)
            if score > 0:
                incident_scores[incident_type] = score
        
        # Si aucun pattern détecté, retourner "aucun"
        if not incident_scores:
            return 'aucun', 'service_client', 0.5
        
        # Sélectionner l'incident avec le score le plus élevé
        best_incident = max(incident_scores, key=incident_scores.get)
        max_score = incident_scores[best_incident]
        responsable = self.INCIDENT_PATTERNS[best_incident]['responsable']
        
        # Calculer la confiance
        confidence = min(0.5 + (max_score * 0.15), 0.95)
        
        return best_incident, responsable, confidence


class ReclamationClassifier:
    """Classificateur de réclamation (Oui/Non) basé sur intention"""
    
    RECLAMATION_KEYWORDS = [
        'problème', 'panne', 'bug', 'erreur', 'dysfonctionnement',
        'insatisfait', 'mécontent', 'déçu', 'inacceptable', 'inadmissible',
        'scandaleux', 'honteux', 'nul', 'mauvais', 'pire', 'catastrophique',
        'ras le bol', 'en avoir marre', 'résilier', 'partir', 'concurrent'
    ]
    
    NEGATIVE_SENTIMENT_KEYWORDS = [
        'pas', 'plus', 'aucun', 'jamais', 'rien', 'impossible', 'incapable',
        'toujours pas', 'encore', 'depuis', 'jours', 'semaine', 'mois'
    ]
    
    def classify(self, text: str) -> Tuple[str, float]:
        """Détermine si le tweet est une réclamation (Oui/Non)"""
        text_lower = text.lower()
        
        # Compter les mots-clés de réclamation
        reclamation_score = sum(1 for keyword in self.RECLAMATION_KEYWORDS 
                               if keyword in text_lower)
        
        # Compter les marqueurs de sentiment négatif
        negative_score = sum(1 for keyword in self.NEGATIVE_SENTIMENT_KEYWORDS 
                            if keyword in text_lower)
        
        # Score total
        total_score = reclamation_score + (negative_score * 0.5)
        
        # Décision
        if total_score >= 2.0:
            return 'Oui', min(0.6 + (total_score * 0.1), 0.95)
        elif total_score >= 1.0:
            return 'Oui', 0.7
        else:
            return 'Non', 0.6


def retrain_dataset_with_enhanced_kpis(input_csv: str, output_csv: str):
    """
    Retraine le dataset avec les nouvelles colonnes KPI
    
    Args:
        input_csv: Chemin vers train_dataset.csv
        output_csv: Chemin vers le dataset enrichi
    """
    logger.info(f"Chargement du dataset: {input_csv}")
    
    # Charger le dataset
    df = pd.read_csv(input_csv)
    initial_count = len(df)
    logger.info(f"Dataset chargé: {initial_count} lignes")
    
    # Initialiser les classificateurs
    theme_clf = EnhancedThemeClassifier()
    incident_clf = IncidentClassifier()
    reclamation_clf = ReclamationClassifier()
    
    # Créer les nouvelles colonnes
    logger.info("Classification en cours...")
    
    themes = []
    theme_confidences = []
    incidents = []
    incident_responsables = []
    incident_confidences = []
    reclamations = []
    reclamation_confidences = []
    
    for idx, row in df.iterrows():
        text = str(row.get('text_cleaned', row.get('text', '')))
        
        # Classification du thème
        theme, theme_conf, _ = theme_clf.classify(text)
        themes.append(theme)
        theme_confidences.append(theme_conf)
        
        # Classification de l'incident
        incident, responsable, inc_conf = incident_clf.classify(text)
        incidents.append(incident)
        incident_responsables.append(responsable)
        incident_confidences.append(inc_conf)
        
        # Classification de réclamation
        is_reclamation, rec_conf = reclamation_clf.classify(text)
        reclamations.append(is_reclamation)
        reclamation_confidences.append(rec_conf)
        
        if (idx + 1) % 500 == 0:
            logger.info(f"Traité {idx + 1}/{initial_count} lignes...")
    
    # Ajouter les nouvelles colonnes
    df['Thème principal'] = themes
    df['theme_confidence'] = theme_confidences
    df['Incident principal'] = incidents
    df['incident_responsable'] = incident_responsables
    df['incident_confidence'] = incident_confidences
    df['réclamations'] = reclamations  # Remplacer l'ancienne colonne
    df['reclamation_confidence'] = reclamation_confidences
    
    logger.info("Classification terminée")
    
    # Calculer les statistiques KPI
    logger.info("Calcul des statistiques KPI...")
    
    kpi_stats = {
        'total_tweets': len(df),
        'date_traitement': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        'themes': {},
        'incidents': {},
        'reclamations': {},
        'responsables': {}
    }
    
    # Statistiques par thème
    theme_counts = df['Thème principal'].value_counts()
    for theme, count in theme_counts.items():
        percentage = (count / len(df)) * 100
        kpi_stats['themes'][theme] = {
            'count': int(count),
            'percentage': round(percentage, 2),
            'avg_confidence': round(df[df['Thème principal'] == theme]['theme_confidence'].mean(), 2)
        }
    
    # Statistiques par incident
    incident_counts = df['Incident principal'].value_counts()
    for incident, count in incident_counts.items():
        percentage = (count / len(df)) * 100
        kpi_stats['incidents'][incident] = {
            'count': int(count),
            'percentage': round(percentage, 2),
            'avg_confidence': round(df[df['Incident principal'] == incident]['incident_confidence'].mean(), 2)
        }
    
    # Statistiques réclamations
    reclamation_counts = df['réclamations'].value_counts()
    for reclamation, count in reclamation_counts.items():
        percentage = (count / len(df)) * 100
        kpi_stats['reclamations'][reclamation] = {
            'count': int(count),
            'percentage': round(percentage, 2)
        }
    
    # Statistiques par responsable
    responsable_counts = df['incident_responsable'].value_counts()
    for responsable, count in responsable_counts.items():
        percentage = (count / len(df)) * 100
        kpi_stats['responsables'][responsable] = {
            'count': int(count),
            'percentage': round(percentage, 2)
        }
    
    # Sauvegarder le dataset enrichi
    logger.info(f"Sauvegarde du dataset enrichi: {output_csv}")
    df.to_csv(output_csv, index=False, encoding='utf-8')
    
    # Sauvegarder les statistiques KPI
    stats_file = output_csv.replace('.csv', '_kpi_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(kpi_stats, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Statistiques KPI sauvegardées: {stats_file}")
    
    # Afficher un résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DU RETRAINING - DATASET ENRICHI")
    print("="*80)
    print(f"\n✅ Dataset original: {initial_count} lignes")
    print(f"✅ Dataset enrichi: {len(df)} lignes")
    print(f"✅ Nouvelles colonnes ajoutées: 7")
    
    print("\n📈 DISTRIBUTION DES THÈMES PRINCIPAUX:")
    for theme, stats in sorted(kpi_stats['themes'].items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"   • {theme:20s}: {stats['count']:5d} tweets ({stats['percentage']:5.2f}%) - Conf: {stats['avg_confidence']:.2f}")
    
    print("\n🔧 DISTRIBUTION DES INCIDENTS PRINCIPAUX:")
    for incident, stats in sorted(kpi_stats['incidents'].items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"   • {incident:20s}: {stats['count']:5d} tweets ({stats['percentage']:5.2f}%) - Conf: {stats['avg_confidence']:.2f}")
    
    print("\n📋 DISTRIBUTION DES RÉCLAMATIONS:")
    for reclamation, stats in kpi_stats['reclamations'].items():
        print(f"   • {reclamation:20s}: {stats['count']:5d} tweets ({stats['percentage']:5.2f}%)")
    
    print("\n👥 DISTRIBUTION PAR RESPONSABLE:")
    for responsable, stats in sorted(kpi_stats['responsables'].items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"   • {responsable:25s}: {stats['count']:5d} tweets ({stats['percentage']:5.2f}%)")
    
    print("\n" + "="*80)
    print(f"✅ Dataset enrichi sauvegardé: {output_csv}")
    print(f"✅ Statistiques KPI sauvegardées: {stats_file}")
    print("="*80 + "\n")
    
    return df, kpi_stats


if __name__ == "__main__":
    # Chemins des fichiers
    INPUT_CSV = "data/training/train_dataset.csv"
    OUTPUT_CSV = "data/training/train_dataset_enriched.csv"
    
    # Exécuter le retraining
    df_enriched, kpi_stats = retrain_dataset_with_enhanced_kpis(INPUT_CSV, OUTPUT_CSV)
    
    print("🎉 Retraining terminé avec succès!")
    print(f"\n📂 Fichiers générés:")
    print(f"   • Dataset enrichi: {OUTPUT_CSV}")
    print(f"   • Statistiques KPI: {OUTPUT_CSV.replace('.csv', '_kpi_stats.json')}")
