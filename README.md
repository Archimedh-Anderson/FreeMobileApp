# FreeMobilaChat - Plateforme d'Analyse de Sentiment Multi-KPI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-0A66C2.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-D94435.svg)
![CI/CD](https://img.shields.io/badge/EC2%20Auto%20Deploy-GitHub%20Actions-232F3E.svg)
![License](https://img.shields.io/badge/License-MIT-4CAF50.svg)

**Classification multi-modèles (BERT + Gemini + Mistral + règles métier) | Déploiement AWS EC2 automatisé | Dashboard KPI temps réel**

[Installation](#installation)  [Architecture](#architecture-technique)  [Classification](#pipeline-de-classification)  [Visualisations](#visualisations-analytiques)  [Déploiement](#déploiement)  [Documentation](#documentation-connexe)

</div>

---

## Executive Snapshot

- <img src="https://raw.githubusercontent.com/primer/octicons/main/icons/check-16.svg" width="16" style="vertical-align:middle;margin-right:6px;"> Classification sur 7 KPI synchronisés (sentiment, réclamation, urgence, thème, incident, responsable, confiance)
- <img src="https://raw.githubusercontent.com/primer/octicons/main/icons/cpu-16.svg" width="16" style="vertical-align:middle;margin-right:6px;"> Chaîne multi-modèles combinant BERT, Mistral (Ollama), Gemini API et règles heuristiques renforcées
- <img src="https://raw.githubusercontent.com/primer/octicons/main/icons/graph-16.svg" width="16" style="vertical-align:middle;margin-right:6px;"> Visualisations Plotly modernisées (donut sentiments, barres incidents/thèmes, panneau qualité KPI)
- <img src="https://raw.githubusercontent.com/primer/octicons/main/icons/workflow-16.svg" width="16" style="vertical-align:middle;margin-right:6px;"> Pipeline CI/CD GitHub Actions  AWS EC2 avec health-checks, contrôles systemd et monitoring post-déploiement
- <img src="https://raw.githubusercontent.com/primer/octicons/main/icons/shield-check-16.svg" width="16" style="vertical-align:middle;margin-right:6px;"> Nettoyage renforcé (stopwords FR, normalisation unicode, heuristiques de cohérence KPI)

---

## Sommaire

1. [Nouveautés clés](#nouveautés-clés-q4-2025)
2. [Vue d'ensemble](#vue-densemble-du-projet)
3. [Architecture technique](#architecture-technique)
4. [Pipeline de classification](#pipeline-de-classification)
5. [Visualisations analytiques](#visualisations-analytiques)
6. [Installation](#installation)
7. [Utilisation & Modes](#utilisation--modes)
8. [Déploiement](#déploiement)
9. [Qualité & Tests](#qualité--tests)
10. [Structure du dépôt](#structure-du-dépôt)
11. [Documentation connexe](#documentation-connexe)
12. [Licence](#licence)

---

## Nouveautés clés (Q4 2025)

| Domaine | Améliorations |
| --- | --- |
| KPI & NLP | Prompts Gemini/Mistral réécrits, configurations strictes, `quality_guard` croisant texte brut + résultat LLM, harmonisation finale via `MultiModelOrchestrator` |
| Nettoyage | `TweetCleaner` enrichi (stopwords FR, normalisation casse, pipeline paramétrable) + `TextPreprocessor` pour cas avancés |
| Visualisations | Section "Visualisations Analytiques" reposant sur Plotly Express avec chartes couleur sémantiques, encart "Contrôle Qualité KPI" |
| UI | Suppression des doublons, navigation clarifiée, messages d'état professionnels |
| Déploiement | Workflow `.github/workflows/deploy.yml` entièrement automatisé (triggers sur `push main`, création service `systemd`, health checks HTTP/port/process, monitoring 30 s) |
| Observabilité | Logs détaillés, collecte diagnostics côté EC2, métriques de couverture dans l'app |

---

## Vue d'ensemble du projet

FreeMobilaChat est une plateforme d'analyse des retours clients pour les télécoms. Elle traite des milliers de tweets et extrait automatiquement les KPI critiques pour les équipes SAV et management.

### Objectifs principaux

- Classification multi-dimensionnelle (sentiment, réclamation, urgence, thème métier, incident détaillé, responsable, score de confiance)
- Architecture multi-modèles hybride pour équilibrer précision, coûts et latence
- Tableau de bord Streamlit interactif, orienté business
- Infrastructure reproducible: environnement local, pipelines CI/CD, scripts de déploiement EC2

### Résultats

- Précision empirique: 8595% selon KPI (après calibration heuristique)
- Traitement vectorisé: >100 tweets/s sur machine 8 vCPU
- Déploiement continu: <5 min entre push et mise à jour EC2 (selon actions GitHub)

---

## Architecture technique

```

                    Couche Présentation                      
    
    Streamlit Frontend (app.py)                           
    - Auth & rôles / Provider selector                    
    - Pages KPI (Classification_Mistral.py)               
    - Visualisations interactives Plotly                  
    

                            
                            

                     Couche Traitement                      
    
    MultiModelOrchestrator                                
     TweetCleaner / TextPreprocessor                    
     BERTClassifier                                     
     RuleClassifier                                     
     MistralClassifier (Ollama)                         
     GeminiClassifier (Google API)                      
    
    
    Enhanced KPIs & Charts                                
    - Calcul de métriques                                 
    - Panel Contrôle Qualité                              
    

                            
                            

                        Couche Données                      
   Datasets labellisés / CSV bruts                        
   Cache model / monitoring                               
   Secrets gérés via `.env` / `secrets.toml`              

```

Les diagrammes UML, séquence et déploiement historiques sont conservés dans `docs/` pour référence détaillée.

---

## Pipeline de classification

| Étape | Description |
| --- | --- |
| 1. Ingestion | Upload CSV ou base SQLite  détection d'encodage (`chardet` fallback) |
| 2. Nettoyage | `TweetCleaner` (URLs, mentions, hashtags, emojis, stopwords, casse) |
| 3. NLP rapide | `BERTClassifier` pour sentiment + confiance, heuristiques négatives supplémentaires |
| 4. Règles métier | `RuleClassifier` pour réclamations/urgence immédiates |
| 5. LLM locaux | `MistralClassifier` via Ollama (batching, prompts calibrés, quality guard) |
| 6. LLM cloud | `GeminiClassifier` (few-shots ciblés, validation, quality guard) |
| 7. Orchestration | `MultiModelOrchestrator` fusionne, harmonise KPI, applique `enforce_kpi_consistency` |
| 8. Visualisation | KPIs calculés, dashboards Plotly, Contrôle Qualité KPI |

Modes disponibles :
- **Balanced** (hybride)  par défaut, combine tous les providers
- **Cloud**  Gemini + règles (utile sur Streamlit Cloud)
- **Local+LLM**  maximise précision Mistral/BERT si ressources disponibles

---

## Visualisations analytiques

- Distribution des thèmes (Top 10)  barres verticales gradient, labels combinés nombre/%
- Distribution des incidents  barres horizontales avec palettes sémantiques (information vs incidents critiques)
- Distribution des sentiments  donut chart moderne, légende centrée, textes formatés
- Contrôle Qualité KPI  cartes `st.metric` (couverture réclamations, tweets classés, incidents critiques)
- Cartes récapitulatives (claims par topic, tendances d'urgence) accessibles par onglets

Tous les graphiques sont recalculés dynamiquement après filtrage/échantillonnage.

---

## Installation

### Prérequis système

- Python 3.11+
- Git, make (optionnel), accès internet (Gemini) et/ou service Ollama local pour Mistral
- Accès AWS EC2 (Amazon Linux 2) si déploiement serveur

### Setup local rapide

```bash
python -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\activate sous Windows
pip install --upgrade pip
pip install -r streamlit_app/requirements.txt
cp docs/.env.example streamlit_app/.env   # puis renseigner les clés API
```

### Lancement

```bash
streamlit run streamlit_app/app.py --server.port 8502 --server.address 0.0.0.0
```

Ollama (optionnel) :
```bash
ollama serve &
ollama pull mistral
export OLLAMA_HOST=http://localhost:11434
```

---

## Utilisation & Modes

1. Se connecter (si auth activée), choisir le provider mixte ou ciblé.
2. Uploader un CSV (colonnes libres, seul le champ texte est requis).
3. Configurer options (nettoyage avancé, taille d'échantillon, mode Balanced/Cloud/Local).
4. Lancer la classification  suivre progression affichée.
5. Explorer onglets Résultats, Sentiment, Visualisations Analytiques, Export.

Les exports (CSV enrichi, JSON KPI, rapports) se trouvent dans le répertoire `uploads/`.

---

## Déploiement

### CI/CD GitHub  AWS EC2

- Déclencheur automatique: `push` sur `main` ou `workflow_dispatch`
- Étapes clés :
  - Pré-diagnostics (commit, RAM, disque, latence SSH)
  - Synchronisation code + création `venv`
  - Installation dépendances (`pip install --no-cache-dir`)
  - Création/validation service `streamlit.service` (`/etc/systemd/system`)
  - `systemctl daemon-reload`, stop/start avec retries, enable au boot
  - Post-checks : statut service, HTTP `curl` sur port 8502, `pgrep`, `ss/netstat`, monitoring stabilité 30 s
  - Journalisation exhaustive accessible depuis l'onglet Actions

Secrets requis côté GitHub :
- `EC2_HOST`, `EC2_USERNAME`, `EC2_KEY` (clé privée), `EC2_SSH_PORT` (optionnel)

### Déploiement manuel sur EC2

```bash
ssh ec2-user@<ip>
cd /home/ec2-user/FreeMobileApp
bash deploy.sh
```

Le script gère backups, `git reset --hard origin/main`, installation dépendances, vérification `.env`, redémarrage service.

### Streamlit Cloud (option d'appoint)

- Utiliser `streamlit_app/requirements.txt`
- Ajouter les secrets `GEMINI_API_KEY`, `GOOGLE_API_KEY`, etc. via l'interface Streamlit Cloud
- Sélectionner le mode *Cloud* dans l'application (Gemini + règles)

---

## Qualité & Tests

- `pytest` (tests ciblés) : `pytest tests/test_modern_ui.py -q`
- Lint léger : `python -m compileall streamlit_app` ou `ruff` si installé
- Monitoring live : `streamlit_app/cache/monitoring/` et journaux `logs/`
- Health-check post-déploiement assuré via workflow Actions (HTTP + `systemctl status`)

> Remarque : certains tests nécessitent les dépendances lourdes (PyTorch, Ollama, navigateur). Utiliser l'environnement virtuel local pour des résultats fiables.

---

## Structure du dépôt

```text
FreeMobilaChat/
 streamlit_app/
    app.py
    pages/Classification_Mistral.py
    services/
       bert_classifier.py
       gemini_classifier.py
       mistral_classifier.py
       multi_model_orchestrator.py
       tweet_cleaner.py
       ultra_optimized_classifier.py
    components/, utils/, assets/
    requirements.txt
 .github/workflows/deploy.yml
 docs/ (guides, scripts de démarrage, secrets templates)
 models/ (prompts, modèles de base)
 data/ (datasets bruts/traités, stats)
 tests/ (UI & NLP)
 deploy.sh (script EC2)
 README.md
```

---

## Documentation connexe

- `docs/DEPLOYMENT_GUIDE.txt`  guide complet (local, cloud, EC2)
- `docs/STREAMLIT_CLOUD_SETUP.txt`  checklist Streamlit Cloud
- `docs/deploy_production.{sh,bat}` / `start_application.{sh,bat,ps1}`  scripts prêts à l'emploi
- `docs/.env.example` & `docs/secrets.toml.example`  modèles de configuration
- `models/prompts/*.txt`  prompts historiques pour calibration LLM

---

## Licence

Projet distribué sous licence [MIT](LICENSE). Toute contribution doit respecter le cadre documentaire et la politique de secrets (pas de clés dans le dépôt).
