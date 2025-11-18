# Guide de Déploiement Automatique sur AWS Lightsail

Ce guide explique la configuration du déploiement automatique de FreeMobilaChat sur AWS Lightsail via GitHub Actions.

## 📋 Prérequis

### Sur le serveur Lightsail

1. **Utilisateur**: `freemobila` (utilisateur personnalisé)
2. **Répertoire de l'application**: `~/FreeMobileApp`
3. **Outils requis**:
   - Git
   - Python 3.8+
   - Node.js et npm (pour PM2)
   - PM2 (gestionnaire de processus)

### Configuration GitHub Secrets

Les secrets suivants doivent être configurés dans les paramètres GitHub du repository:

- `LIGHTSAIL_HOST`: Adresse IP ou hostname du serveur Lightsail (ex: `15.236.188.205`)
- `LIGHTSAIL_USER`: Nom d'utilisateur SSH (`freemobila`)
- `LIGHTSAIL_SSH_PORT`: Port SSH (optionnel, par défaut `22`)
- `SSH_PRIVATE_KEY`: Clé privée SSH pour se connecter au serveur

#### Comment obtenir la clé SSH privée

1. Sur votre machine locale, générez une paire de clés SSH si vous n'en avez pas:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions"
   ```

2. Copiez la clé publique sur le serveur Lightsail:
   ```bash
   ssh-copy-id -i ~/.ssh/id_rsa.pub freemobila@VOTRE_IP_LIGHTSAIL
   ```

3. Dans GitHub, allez dans Settings > Secrets and variables > Actions
4. Ajoutez le secret `SSH_PRIVATE_KEY` avec le contenu de `~/.ssh/id_rsa` (clé privée)

## 🚀 Architecture de Déploiement

```
GitHub Repository (main/master)
    ↓ (push event)
GitHub Actions Workflow
    ↓ (SSH)
AWS Lightsail Server
    ├── ~/FreeMobileApp/
    │   ├── streamlit_app/
    │   ├── venv/
    │   ├── ecosystem.config.js
    │   ├── start_app_production.sh
    │   └── deploy_lightsail.sh
    └── PM2 (gestionnaire de processus)
```

## 📁 Fichiers de Déploiement

### 1. `.github/workflows/deploy.yml`
Workflow GitHub Actions qui:
- Se déclenche sur push vers `main` ou `master`
- Se connecte au serveur via SSH
- Crée une sauvegarde
- Récupère le code depuis GitHub
- Installe les dépendances
- Redémarre l'application avec PM2
- Effectue des health checks

### 2. `start_app_production.sh`
Script de démarrage pour la production:
- Active l'environnement virtuel Python
- Vérifie les dépendances
- Démarre Streamlit sur `0.0.0.0:8502` (accessible depuis l'extérieur)
- Gère les logs

### 3. `deploy_lightsail.sh`
Script de déploiement manuel sur le serveur:
- Peut être exécuté directement sur le serveur
- Offre les mêmes fonctionnalités que le workflow GitHub Actions
- Utile pour les déploiements manuels ou le debugging

### 4. `ecosystem.config.js`
Configuration PM2:
- Définit comment PM2 gère l'application
- Configure les variables d'environnement
- Gère les logs et les redémarrages automatiques

## 🔧 Installation Initiale sur le Serveur

### 1. Connexion au serveur

```bash
ssh freemobila@VOTRE_IP_LIGHTSAIL
```

### 2. Installation des prérequis

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Python et pip
sudo apt install -y python3 python3-pip python3-venv git

# Installation de Node.js et npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Installation de PM2 globalement
sudo npm install -g pm2

# Configuration de PM2 pour démarrer au boot
pm2 startup systemd
# Suivre les instructions affichées
```

### 3. Clonage du repository

```bash
cd ~
git clone https://github.com/VOTRE_USERNAME/FreeMobilaChat.git FreeMobileApp
cd FreeMobileApp
```

### 4. Configuration initiale

```bash
# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r streamlit_app/requirements.txt

# Configuration du fichier .env (si nécessaire)
cd streamlit_app
cp .env.example .env  # Éditer avec vos clés API
nano .env
cd ..

# Rendre les scripts exécutables
chmod +x start_app_production.sh
chmod +x deploy_lightsail.sh
```

### 5. Démarrage initial avec PM2

```bash
# Démarrer l'application
pm2 start ecosystem.config.js

# Sauvegarder la configuration PM2
pm2 save

# Vérifier le statut
pm2 status
pm2 logs freemobile-app
```

## 🔄 Déploiement Automatique

Une fois configuré, le déploiement se fait automatiquement:

1. **Push vers main/master**: Le workflow GitHub Actions se déclenche automatiquement
2. **Déploiement**: Le workflow se connecte au serveur et déploie
3. **Vérification**: Health checks et logs sont vérifiés

### Déploiement manuel via GitHub Actions

Vous pouvez aussi déclencher le déploiement manuellement:
1. Allez dans l'onglet "Actions" de votre repository GitHub
2. Sélectionnez le workflow "Deploy to Lightsail"
3. Cliquez sur "Run workflow"

## 🛠️ Commandes Utiles sur le Serveur

### PM2

```bash
# Statut de l'application
pm2 status

# Logs en temps réel
pm2 logs freemobile-app

# Redémarrer l'application
pm2 restart freemobile-app

# Arrêter l'application
pm2 stop freemobile-app

# Démarrer l'application
pm2 start freemobile-app

# Supprimer l'application de PM2
pm2 delete freemobile-app
```

### Déploiement manuel

```bash
cd ~/FreeMobileApp

# Déploiement complet
bash deploy_lightsail.sh

# Ou avec options
bash deploy_lightsail.sh deploy    # Déploiement complet
bash deploy_lightsail.sh rollback  # Restauration
bash deploy_lightsail.sh logs      # Afficher les logs
bash deploy_lightsail.sh status    # Statut PM2
bash deploy_lightsail.sh restart   # Redémarrer uniquement
bash deploy_lightsail.sh health    # Health check
```

### Vérification de l'application

```bash
# Vérifier que l'application écoute sur le port 8502
sudo netstat -tlnp | grep 8502

# Tester la connexion HTTP
curl http://localhost:8502

# Vérifier les processus
ps aux | grep streamlit
```

## 🔍 Dépannage

### L'application ne démarre pas

1. Vérifier les logs PM2:
   ```bash
   pm2 logs freemobile-app --lines 100
   ```

2. Vérifier les logs de démarrage:
   ```bash
   tail -f ~/FreeMobileApp/logs/startup_*.log
   ```

3. Vérifier que l'environnement virtuel est correct:
   ```bash
   source ~/FreeMobileApp/venv/bin/activate
   python --version
   pip list
   ```

### Le déploiement GitHub Actions échoue

1. Vérifier les secrets GitHub:
   - `LIGHTSAIL_HOST` est correct
   - `SSH_PRIVATE_KEY` est valide
   - Les permissions SSH sont correctes

2. Tester la connexion SSH manuellement:
   ```bash
   ssh -i ~/.ssh/id_rsa freemobila@VOTRE_IP_LIGHTSAIL
   ```

3. Vérifier les logs GitHub Actions dans l'onglet "Actions"

### L'application n'est pas accessible depuis l'extérieur

1. Vérifier les règles de pare-feu Lightsail:
   - Port 8502 doit être ouvert (TCP)
   - Source: `0.0.0.0/0` (ou votre IP spécifique)

2. Vérifier que Streamlit écoute sur `0.0.0.0`:
   ```bash
   ps aux | grep streamlit
   # Doit contenir: --server.address 0.0.0.0
   ```

3. Vérifier la configuration réseau Lightsail:
   - Le serveur doit avoir une IP publique
   - Les règles de sécurité doivent autoriser le trafic

## 📊 Monitoring

### Logs

- **PM2**: `pm2 logs freemobile-app`
- **Application**: `~/FreeMobileApp/logs/`
- **Système**: `journalctl -u pm2-freemobila` (si configuré)

### Métriques

```bash
# Utilisation mémoire
pm2 monit

# Statistiques
pm2 describe freemobile-app
```

## 🔐 Sécurité

1. **Clés SSH**: Ne jamais commiter les clés privées
2. **Secrets**: Utiliser GitHub Secrets pour les informations sensibles
3. **Firewall**: Limiter l'accès au port 8502 si possible
4. **HTTPS**: Considérer l'ajout d'un reverse proxy (nginx) avec SSL

## 📝 Notes

- Le script `start_app_production.sh` démarre Streamlit sur `0.0.0.0:8502` pour être accessible depuis l'extérieur
- Les sauvegardes sont conservées dans `~/FreeMobileApp/backups/` (5 dernières)
- PM2 redémarre automatiquement l'application en cas de crash
- Les logs sont stockés dans `~/FreeMobileApp/logs/`

## 🆘 Support

En cas de problème:
1. Vérifier les logs (PM2 et application)
2. Vérifier la configuration GitHub Secrets
3. Tester la connexion SSH manuellement
4. Vérifier les règles de pare-feu Lightsail

