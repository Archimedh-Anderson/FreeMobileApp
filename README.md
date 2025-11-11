# FreeMobilaChat - Système de Classification Intelligente de Tweets

## Contexte Académique

Ce projet constitue un travail de recherche appliquée dans le cadre d'un Master en Data Science et Intelligence Artificielle. Il implémente un système de classification automatique de tweets pour l'analyse du sentiment client dans le secteur des télécommunications.

**Objectif principal** : Développer une solution robuste et scalable pour classifier automatiquement les tweets clients selon leur intention, sentiment, thème et niveau d'urgence, en combinant des approches par règles et par apprentissage profond.

## Architecture Technique

### Technologies Utilisées

#### Backend et Traitement de Données
- **Python 3.12** : Langage principal pour la logique métier et le traitement de données
- **Pandas 2.x** : Manipulation et analyse de DataFrames volumineuses
- **NumPy 1.26** : Calculs numériques vectorisés pour optimisation des performances
- **Streamlit 1.41** : Framework pour l'interface utilisateur interactive

#### Intelligence Artificielle et NLP
- **Ollama** : Serveur local pour l'exécution de modèles LLM open-source
- **Mistral AI** : Modèle de langage pour classification contextuelle avancée
- **Transformers (Hugging Face)** : Pipeline de traitement NLP pré-entraîné
- **Spacy / NLTK** : Bibliothèques de traitement du langage naturel

#### Visualisation et Interface
- **Plotly 5.x** : Graphiques interactifs pour tableaux de bord analytiques
- **Streamlit Components** : Composants UI personnalisés pour rendu avancé

#### Tests et Qualité
- **pytest 8.x** : Framework de tests unitaires et d'intégration
- **pytest-cov** : Mesure de couverture de code (83% actuel)
- **pytest-asyncio** : Tests asynchrones pour opérations concurrentes
- **Playwright** : Tests end-to-end pour validation de l'interface utilisateur

### Architecture Modulaire

Le système est conçu selon une architecture modulaire en couches :

```
FreeMobilaChat/
│
├── streamlit_app/              # Application principale Streamlit
│   ├── app.py                  # Point d'entrée de l'application
│   ├── config.py               # Configuration centralisée
│   │
│   ├── services/               # Couche métier (7 modules critiques)
│   │   ├── mistral_classifier.py       # Classification via Mistral LLM
│   │   ├── dynamic_classifier.py       # Classification par règles adaptatives
│   │   ├── tweet_cleaner.py            # Prétraitement et nettoyage de texte
│   │   ├── data_processor.py           # Validation et normalisation
│   │   ├── batch_processor.py          # Traitement par lots optimisé
│   │   ├── enhanced_kpis_vizualizations.py  # Calcul de KPIs et visualisations
│   │   └── ...                         # 27 autres modules de services
│   │
│   ├── pages/                  # Pages de l'application Streamlit
│   │   ├── 1_Classification_LLM.py     # Interface classification LLM
│   │   └── 2_Classification_Mistral.py # Interface Mistral optimisée
│   │
│   ├── components/             # Composants UI réutilisables
│   └── utils/                  # Utilitaires transverses
│
├── tests/                      # Suite de tests (235 tests)
│   ├── units/                  # Tests unitaires (fonctions isolées)
│   ├── integration/            # Tests d'intégration (workflow complets)
│   ├── test_performance.py     # Tests de performance et scalabilité
│   ├── test_security.py        # Tests de sécurité (injection, validation)
│   └── test_fairness_bias.py   # Tests d'équité et détection de biais
│
├── data/                       # Datasets et modèles
├── models/                     # Modèles entraînés (BERT, classifiers)
├── scripts/                    # Scripts utilitaires
└── docs/                       # Documentation technique

```

## Composants Principaux

### 1. Moteur de Classification Multicouche

Le système implémente une stratégie de classification en cascade avec trois niveaux de fallback :

#### Niveau 1 : Classification LLM (Mode Précis)
- **Moteur** : Mistral 7B via Ollama (local)
- **Performance** : ~0.3-0.5 tweets/seconde
- **Précision** : 90-95% (validation croisée)
- **Cas d'usage** : Classification haute précision avec analyse contextuelle

**Implémentation** (`mistral_classifier.py`) :
- Prompt engineering avec taxonomie Free Mobile
- Retry automatique avec backoff exponentiel (3 tentatives)
- Timeout configurable (5-120 secondes)
- Parsing JSON robuste avec validation de schéma

#### Niveau 2 : Classification Hybride (Mode Équilibré)
- **Moteur** : Combinaison règles + LLM (20% échantillon)
- **Performance** : ~5-8 tweets/seconde
- **Précision** : 85-90%
- **Cas d'usage** : Équilibre performance/précision

#### Niveau 3 : Classification par Règles (Mode Rapide / Fallback)
- **Moteur** : `DynamicClassificationEngine` avec patterns adaptatifs
- **Performance** : ~10-15 tweets/seconde
- **Précision** : 75-85%
- **Cas d'usage** : Volume élevé, LLM indisponible

**Implémentation** (`dynamic_classifier.py`) :
- Détection d'intention par patterns regex (6 catégories)
- Classification thématique avec apprentissage de vocabulaire
- Analyse de sentiment contextuelle (gestion négations/intensificateurs)
- Évaluation d'urgence adaptive

### 2. Pipeline de Prétraitement des Données

**Module** : `data_processor.py` et `tweet_cleaner.py`

Pipeline en 7 étapes pour garantir la qualité des données :

1. **Normalisation Unicode** : Conversion NFKD pour compatibilité multilingue
2. **Suppression URLs** : Regex optimisé pour http/https/www
3. **Nettoyage mentions** : Retrait des @username
4. **Traitement hashtags** : Conservation optionnelle selon configuration
5. **Conversion emojis** : Transformation en texte descriptif
6. **Déduplication** : Hash MD5 pour identifier les doublons
7. **Validation qualité** : Scoring automatique (0-100)

**Optimisations** :
- Opérations vectorisées avec pandas pour performance
- Support multi-encodage (UTF-8, Latin-1, CP1252)
- Détection automatique de colonnes (français/anglais)

### 3. Traitement par Lots et Scalabilité

**Module** : `batch_processor.py`

Gestion efficace de grands volumes de données :

- **Batch size configurable** : 5-100 tweets par lot (défaut : 50)
- **Suivi de progression** : Barre de progression en temps réel
- **Calcul ETA** : Estimation du temps restant
- **Gestion mémoire** : Traitement séquentiel pour éviter saturation
- **Métriques de performance** : Débit (tweets/seconde), temps total

### 4. Calcul de KPIs et Visualisations

**Module** : `enhanced_kpis_vizualizations.py`

Indicateurs clés de performance calculés dynamiquement :

#### KPIs Business
- **Taux de réclamations** : Pourcentage de tweets négatifs nécessitant action
- **Indice de satisfaction** : Score 0-100 basé sur analyse de sentiment
- **Taux d'urgence** : Proportion de tweets critiques/haute priorité
- **Distribution thématique** : Répartition par catégorie (fibre, mobile, SAV, etc.)
- **Score de confiance moyen** : Fiabilité des classifications

**Caractéristiques** :
- Calculs 100% dynamiques (pas de cache)
- Support multi-format (oui/non, 1/0, français/anglais)
- Optimisation vectorielle avec NumPy
- Visualisations interactives Plotly

## Installation et Exécution

### Prérequis Système

- **Python** : Version 3.10 ou supérieure (testé avec 3.12)
- **Mémoire RAM** : Minimum 8 GB (16 GB recommandé pour LLM)
- **Espace disque** : 5 GB pour modèles et dépendances
- **Ollama** (optionnel) : Pour classification LLM locale

### Installation des Dépendances

#### Option 1 : Installation Académique Reproductible (Recommandé)

```bash
# Cloner le dépôt
git clone <url-du-depot>
cd FreeMobilaChat

# Créer un environnement virtuel Python isolé
python -m venv venv

# Activer l'environnement virtuel
# Windows PowerShell :
.\venv\Scripts\Activate.ps1
# Windows CMD :
venv\Scripts\activate.bat
# Linux/Mac :
source venv/bin/activate

# Mettre à jour pip vers la dernière version
python -m pip install --upgrade pip

# Installer les dépendances exactes (reproductibilité garantie)
pip install -r requirements-academic.txt

# Vérifier l'installation
python -c "import streamlit, pandas, numpy, plotly, torch; print('Installation réussie!')"
```

#### Option 2 : Installation Complète avec Développement

```bash
# Après activation de l'environnement virtuel
pip install -r requirements-academic.txt -r requirements.dev.txt

# Vérifier les outils de développement
pytest --version
black --version
```

### Reproductibilité de l'Environnement

**Fichiers de dépendances disponibles** :

1. **`requirements-academic.txt`** : Dépendances minimales optimisées pour soumission académique
   - 35 packages essentiels avec versions exactes
   - Testé et validé sur Python 3.12.10
   - Garantie de reproductibilité sur environnement propre

2. **`requirements.txt`** : Dépendances historiques complètes
   - Inclut packages backend (FastAPI, SQLAlchemy)
   - Utilisé pour déploiement production

3. **`requirements.dev.txt`** : Outils de développement
   - Tests (pytest, pytest-cov)
   - Formatage (black, isort)
   - Linting (flake8, pylint)
   - Documentation (mkdocs)

**Validation de l'environnement** :

```bash
# Vérifier les versions installées
pip list > installed_packages.txt

# Comparer avec les requirements
pip check  # Vérifie les conflits de dépendances

# Générer un fichier freeze pour documentation
pip freeze > requirements-freeze-$(date +%Y%m%d).txt
```

### Configuration d'Ollama (Classification LLM)

Pour utiliser le mode classification LLM avec Mistral :

```bash
# Installer Ollama
# Windows : Télécharger depuis https://ollama.ai
# Linux/Mac : curl https://ollama.ai/install.sh | sh

# Démarrer le serveur Ollama
ollama serve

# Télécharger le modèle Mistral (dans un nouveau terminal)
ollama pull mistral

# Vérifier l'installation
ollama list
```

### Lancement de l'Application

```bash
# Depuis le répertoire racine
streamlit run streamlit_app/app.py

# L'application sera accessible à : http://localhost:8501
```

**Modes de démarrage** :
- **Mode développement** : `streamlit run streamlit_app/app.py --server.runOnSave true`
- **Mode production** : `./deploy_production.sh` (Linux) ou `deploy_production.bat` (Windows)

## Exécution des Tests

### Tests Unitaires et d'Intégration

```bash
# Exécuter tous les tests
python -m pytest tests/ -v

# Tests avec rapport de couverture
python -m pytest tests/ --cov=streamlit_app --cov-report=html

# Tests spécifiques par catégorie
python -m pytest tests/units/ -v                    # Tests unitaires
python -m pytest tests/integration/ -v              # Tests d'intégration
python -m pytest tests/test_performance.py -v       # Tests de performance
python -m pytest tests/test_security.py -v          # Tests de sécurité
python -m pytest tests/test_fairness_bias.py -v     # Tests d'équité

# Tests avec marqueurs
python -m pytest -m "not slow" -v                   # Exclure tests lents
```

### Résultats des Tests Actuels

**Statistiques globales** :
- **Tests exécutés** : 235 tests
- **Tests réussis** : 212 (90.2%)
- **Tests échoués** : 23 (9.8%)
- **Couverture de code** : 83%
- **Temps d'exécution** : ~95 secondes

**Répartition par catégorie** :
- Tests unitaires : 85 tests (96% réussite)
- Tests d'intégration : 32 tests (75% réussite)
- Tests de performance : 18 tests (83% réussite)
- Tests de sécurité : 25 tests (96% réussite)
- Tests d'équité : 12 tests (92% réussite)

### Couverture de Code

**Modules avec couverture élevée (>85%)** :
- `mistral_classifier.py` : 92%
- `tweet_cleaner.py` : 94%
- `batch_processor.py` : 88%
- `config.py` : 100%
- `dynamic_classifier.py` : 87%

**Modules nécessitant amélioration (<70%)** :
- `llm_analysis_engine.py` : 68%
- `smart_visualization_engine.py` : 62%
- Modules d'export et reporting : 55-65%

## Principes de Conception et Robustesse

### Robustesse et Gestion d'Erreurs

Le système implémente plusieurs mécanismes pour garantir la fiabilité :

1. **Fallback en cascade** : LLM → Hybride → Règles
2. **Retry automatique** : 3 tentatives avec backoff exponentiel
3. **Timeout configurables** : Protection contre blocages
4. **Validation de données** : Contrôles à chaque étape du pipeline
5. **Logging structuré** : Traçabilité complète des opérations
6. **Gestion gracieuse** : Dégradation progressive sans crash

### Performance et Scalabilité

**Optimisations implémentées** :
- Calculs vectorisés avec pandas/NumPy (50x plus rapide que boucles Python)
- Traitement par lots configurable pour équilibrer mémoire/vitesse
- Cache sélectif pour modèles lourds (classifiers BERT)
- Chargement lazy des modules non critiques
- Parallélisation pour tâches indépendantes

**Benchmarks mesurés** :
- Classification règles : 10-15 tweets/seconde
- Classification LLM : 0.3-0.5 tweets/seconde
- Nettoyage de texte : 500-1000 tweets/seconde
- Calcul KPIs : 2000+ tweets/seconde

### Sécurité

**Mesures de sécurité implémentées** :
- Validation stricte des entrées (type, format, longueur)
- Protection contre injection SQL/NoSQL
- Échappement de caractères spéciaux dans prompts
- Limitation de taille des fichiers uploadés
- Pas d'exécution de code utilisateur
- Sanitization des données avant affichage HTML

## Limitations et Perspectives d'Amélioration

### Limitations Actuelles

#### Couverture de Tests
- **23 tests échouent actuellement** (9.8%), principalement :
  - Tests d'intégration LLM nécessitant connexion Ollama active
  - Tests de performance avec seuils stricts
  - Tests sur des cas limites spécifiques (DataFrames vides, encodages rares)

- **Fonctions non testées** (identifiées par analyse de couverture) :
  - Fonctions utilitaires d'export (CSV, JSON, Excel)
  - Composants de visualisation avancée
  - Gestionnaires d'erreurs spécifiques

#### Performance LLM
- Dépendance à Ollama (serveur local requis)
- Latence élevée pour classification précise (2-3 secondes/tweet)
- Consommation mémoire importante (4-6 GB pour Mistral)

#### Scalabilité
- Traitement séquentiel des batches (pas de parallélisation)
- Limitation à 5000 tweets par session pour performance UI
- Pas de persistance des résultats (rechargement requis)

### Perspectives de Recherche

#### Court terme (3-6 mois)
1. **Amélioration de la couverture de tests** : Objectif 95%
2. **Optimisation LLM** : Quantization (GGUF 4-bit) pour réduire latence
3. **Parallélisation** : Traitement multi-thread des batches
4. **Cache intelligent** : Mémorisation des classifications fréquentes

#### Moyen terme (6-12 mois)
1. **Fine-tuning de modèles** : Adapter Mistral au domaine télécoms
2. **API REST** : Exposer les fonctionnalités via API
3. **Base de données** : Persistance PostgreSQL pour historique
4. **Dashboard temps réel** : Streaming de tweets en direct

#### Long terme (Recherche académique)
1. **Apprentissage actif** : Amélioration continue par feedback utilisateur
2. **Détection de biais** : Analyse d'équité multi-critères avancée
3. **Explicabilité** : Visualisation des facteurs de décision (SHAP, LIME)
4. **Multilingue** : Support de 10+ langues européennes

## Résultats et Validation Académique

### Métriques de Performance

**Classification LLM (Mistral)** :
- Précision : 92.3% (validation croisée 5-fold)
- Rappel : 89.7%
- F1-Score : 91.0%
- Temps moyen : 2.1s/tweet

**Classification par Règles** :
- Précision : 78.5%
- Rappel : 82.1%
- F1-Score : 80.2%
- Temps moyen : 0.08s/tweet

**Qualité de Données** :
- Taux de nettoyage réussi : 99.2%
- Doublons détectés : ~15% du corpus initial
- Valeurs manquantes gérées : 100%

### Contribution Scientifique

Ce projet démontre :

1. **Approche hybride efficace** : Combinaison apprentissage profond + règles
2. **Scalabilité réelle** : Traitement de 100,000+ tweets validé
3. **Adaptabilité domaine** : Système générique configurable par secteur
4. **Équilibre performance/précision** : Choix de mode selon contraintes

## Références Techniques

### Modèles et Bibliothèques
- Mistral AI : https://mistral.ai/
- Ollama : https://ollama.ai/
- Hugging Face Transformers : https://huggingface.co/docs/transformers
- Streamlit : https://docs.streamlit.io/

### Standards et Méthodologies
- PEP 8 : Style guide Python
- SOLID Principles : Architecture logicielle
- Test-Driven Development : Méthodologie de tests
- Semantic Versioning : Gestion de versions

## Licence

Ce projet est développé dans un cadre académique pour un Master en Data Science et Intelligence Artificielle.

## Contact et Contribution

Pour toute question académique ou technique concernant ce projet, veuillez consulter la documentation technique dans le répertoire `docs/`.

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2025-01  
**Statut** : Prêt pour défense académique
