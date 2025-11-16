# 🚀 FreeMobilaChat - Analyse de Tweets avec IA

Application Streamlit pour l'analyse de sentiments et la classification automatique de tweets en temps réel.

---

## 📋 Table des matières

- [Aperçu](#aperçu)
- [Architecture](#architecture)
- [Déploiement](#déploiement)
- [Configuration CI/CD](#configuration-cicd)
- [Développement local](#développement-local)
- [Contribution](#contribution)

---

## 🎯 Aperçu

FreeMobilaChat est une solution d'analyse de tweets alimentée par l'intelligence artificielle, offrant:

- **Analyse de sentiments** multi-niveaux (Positif, Neutre, Négatif)
- **Classification automatique** des réclamations et urgences
- **Tableaux de bord interactifs** avec KPIs en temps réel
- **Support multi-modèles IA** (Mistral, Gemini, BERT)
- **Visualisations dynamiques** avec Plotly

### Fonctionnalités principales

- ✅ Analyse de sentiment avec CamemBERT
- ✅ Classification LLM avec Mistral AI
- ✅ Détection automatique de réclamations
- ✅ Évaluation des niveaux d'urgence
- ✅ Catégorisation thématique
- ✅ Export multi-format (CSV, Excel, JSON)
- ✅ Authentification multi-rôles

---

## 🏗️ Architecture

```
FreeMobilaChat/
│
├── streamlit_app/              # Application principale
│   ├── app.py                  # Point d'entrée
│   ├── requirements.txt        # Dépendances Python
│   │
│   ├── assets/                 # Ressources statiques
│   │   ├── css/
│   │   └── images/
│   │
│   ├── components/             # Composants réutilisables
│   │   ├── auth_forms.py       # Formulaires d'authentification
│   │   └── kpi_cards.py        # Cartes KPI
│   │
│   ├── pages/                  # Pages Streamlit
│   │   ├── 0_Home.py
│   │   └── Classification_Mistral.py
│   │
│   ├── services/               # Logique métier
│   │   ├── auth_service.py     # Gestion authentification
│   │   ├── gemini_classifier.py
│   │   ├── mistral_classifier.py
│   │   ├── enhanced_kpis_vizualizations.py
│   │   └── nlp_classifier.py
│   │
│   └── utils/                  # Utilitaires
│       └── role_manager.py
│
├── .github/                    # GitHub Actions
│   └── workflows/
│       └── deploy.yml          # Workflow CI/CD
│
├── docs/                       # Documentation
├── tests/                      # Tests unitaires
└── README.md                   # Ce fichier
```

---

## 🚀 Déploiement

### Prérequis

- **Python:** 3.11+
- **Serveur:** AWS EC2 (Amazon Linux 2023)
- **Git:** Installé sur le serveur
- **Clé SSH:** Accès au serveur

### 📦 Installation sur EC2

#### 1. Connexion au serveur

```bash
ssh -i votre_cle.pem ec2-user@13.37.186.191
```

#### 2. Installation des prérequis

```bash
# Mise à jour du système
sudo yum update -y

# Installation de Python 3.11
sudo yum install python3.11 python3.11-pip git -y

# Installation de systemd (si nécessaire)
sudo yum install systemd -y
```

#### 3. Clonage du repository

```bash
cd /home/ec2-user
git clone https://github.com/Archimedh-Anderson/FreeMobileApp.git
cd FreeMobileApp/streamlit_app
```

#### 4. Installation des dépendances

```bash
# Création d'un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installation des packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configuration du fichier .env

```bash
cd /home/ec2-user/FreeMobileApp/streamlit_app
nano .env
```

Ajoutez vos clés API:

```env
# API Keys
GEMINI_API_KEY=votre_cle_gemini
MISTRAL_API_KEY=votre_cle_mistral

# Configuration Streamlit
STREAMLIT_PORT=8503
ENVIRONMENT=production
```

#### 6. Configuration du service systemd

Créez `/etc/systemd/system/streamlit.service`:

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Contenu du fichier:

```ini
[Unit]
Description=FreeMobilaChat Streamlit Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/FreeMobileApp/streamlit_app
Environment="PATH=/home/ec2-user/FreeMobileApp/streamlit_app/venv/bin"
ExecStart=/home/ec2-user/FreeMobileApp/streamlit_app/venv/bin/streamlit run app.py --server.port 8503 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:/var/log/streamlit.log
StandardError=append:/var/log/streamlit.log

[Install]
WantedBy=multi-user.target
```

#### 7. Activation du service

```bash
# Rechargement des configurations systemd
sudo systemctl daemon-reload

# Activation du service au démarrage
sudo systemctl enable streamlit.service

# Démarrage du service
sudo systemctl start streamlit.service

# Vérification du statut
sudo systemctl status streamlit.service
```

#### 8. Configuration du pare-feu (AWS Security Group)

Dans la console AWS EC2, configurez le Security Group pour autoriser:

- **Port 8503** (TCP) depuis votre IP ou 0.0.0.0/0 (public)
- **Port 22** (SSH) depuis votre IP uniquement

#### 9. Test de l'application

Ouvrez votre navigateur:
```
http://13.37.186.191:8503
```

---

## ⚙️ Configuration CI/CD

### Secrets GitHub à configurer

1. Accédez à **Settings** → **Secrets and variables** → **Actions**
2. Ajoutez les secrets suivants:

| Secret | Valeur | Description |
|--------|--------|-------------|
| `EC2_HOST` | `13.37.186.191` | Adresse IP du serveur EC2 |
| `EC2_USERNAME` | `ec2-user` | Utilisateur SSH |
| `EC2_SSH_KEY` | Contenu de `votre_cle.pem` | Clé privée SSH complète |

### Récupération de la clé SSH

Sur votre machine locale:

```bash
cat /chemin/vers/votre_cle.pem
```

Copiez **tout le contenu** (y compris `-----BEGIN RSA PRIVATE KEY-----` et `-----END RSA PRIVATE KEY-----`)

### Configuration sudo sans mot de passe

Sur le serveur EC2:

```bash
sudo visudo
```

Ajoutez à la fin du fichier:

```
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl is-active streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/journalctl
ec2-user ALL=(ALL) NOPASSWD: /bin/tail /var/log/streamlit.log
```

### Workflow de déploiement

Le workflow GitHub Actions (`..github/workflows/deploy.yml`) s'exécute automatiquement à chaque push sur `main`:

1. ✅ Vérification de la syntaxe Python
2. 🔐 Connexion SSH au serveur EC2
3. ⬇️ Récupération du code (git pull)
4. 📦 Installation des dépendances
5. 🔄 Redémarrage du service Streamlit
6. ✅ Vérification du statut

### Déclenchement manuel

Depuis GitHub → **Actions** → **Deploy to AWS EC2** → **Run workflow**

### Logs de déploiement

**Logs GitHub Actions:**
```
GitHub → Actions → Sélectionner le workflow → Voir les détails
```

**Logs sur EC2:**
```bash
# Logs du service
sudo journalctl -u streamlit.service -f

# Logs de l'application
sudo tail -f /var/log/streamlit.log
```

---

## 💻 Développement local

### Installation

```bash
# Cloner le repository
git clone https://github.com/Archimedh-Anderson/FreeMobileApp.git
cd FreeMobileApp/streamlit_app

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration locale

Créez un fichier `.env`:

```env
GEMINI_API_KEY=votre_cle
MISTRAL_API_KEY=votre_cle
STREAMLIT_PORT=8503
ENVIRONMENT=development
```

### Lancement

```bash
streamlit run app.py
```

L'application sera accessible sur `http://localhost:8503`

### Tests

```bash
# Installation des dépendances de test
pip install pytest playwright

# Exécution des tests
pytest tests/

# Tests avec couverture
pytest --cov=streamlit_app tests/
```

---

## 🤝 Contribution

### Workflow de contribution

1. **Fork** le repository
2. Créez une **branche feature**: `git checkout -b feature/nouvelle-fonctionnalite`
3. **Committez** vos changements: `git commit -m 'Ajout nouvelle fonctionnalité'`
4. **Push** vers la branche: `git push origin feature/nouvelle-fonctionnalite`
5. Ouvrez une **Pull Request**

### Standards de code

- **Python:** PEP 8
- **Commits:** Messages clairs et descriptifs en français
- **Tests:** Ajouter des tests pour toute nouvelle fonctionnalité
- **Documentation:** Documenter les fonctions complexes

### Structure d'un commit

```
type: Description courte (max 50 caractères)

Description détaillée si nécessaire.

- Point 1
- Point 2
```

**Types de commits:**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `style`: Formatage du code
- `refactor`: Refactoring
- `test`: Ajout de tests
- `chore`: Maintenance

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Archimedh-Anderson/FreeMobileApp/issues)
- **Email:** contact@freemobilachat.com
- **Documentation:** [Wiki du projet](https://github.com/Archimedh-Anderson/FreeMobileApp/wiki)

---

## 📄 Licence

Ce projet est développé dans le cadre d'un Master en Data Science.

---

## 🎓 Crédits

Développé par Anderson Archimedh  
Master Data Science - 2025

---

**⚠️ Note de sécurité:**  
Ne **jamais** committer de fichiers `.env`, clés API, ou secrets dans le repository. Utilisez toujours GitHub Secrets pour les données sensibles.
