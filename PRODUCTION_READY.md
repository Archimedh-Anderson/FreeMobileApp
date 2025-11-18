# ✅ Application Prête pour la Production

## 🎯 Informations de Production

- **URL Production**: http://15.236.188.205:8502
- **Serveur**: AWS Lightsail
- **IP Statique**: 15.236.188.205 (freemobila-static-ip)
- **Utilisateur**: freemobila
- **Port Application**: 8502

## 📋 État de Configuration

### ✅ Fichiers Configurés

- [x] `.github/workflows/deploy.yml` - Workflow de déploiement automatique
- [x] `start_app_production.sh` - Script de démarrage production
- [x] `deploy_lightsail.sh` - Script de déploiement manuel
- [x] `ecosystem.config.js` - Configuration PM2 (chemin: `/home/freemobila/FreeMobileApp`)
- [x] Documentation complète

### ✅ Pare-feu Lightsail

Les règles suivantes sont configurées:

| Application | Protocol | Port | Restriction |
|------------|----------|------|-------------|
| SSH | TCP | 22 | Any IPv4 address |
| HTTP | TCP | 80 | Any IPv4 address |
| HTTPS | TCP | 443 | Any IPv4 address |
| Custom | TCP | 8502 | Any IPv4 address |

## 🔐 Secrets GitHub à Configurer

**IMPORTANT:** Configurez ces secrets dans GitHub avant le premier déploiement.

Voir le fichier `GITHUB_SECRETS_CONFIG.md` pour les instructions détaillées.

### Secrets Requis:

1. **LIGHTSAIL_HOST**: `15.236.188.205`
2. **LIGHTSAIL_USER**: `freemobila`
3. **SSH_PRIVATE_KEY**: (Votre clé privée SSH)
4. **LIGHTSAIL_SSH_PORT**: `22` (optionnel)

## 🚀 Étapes de Mise en Production

### Étape 1: Configuration des Secrets GitHub

1. Allez dans votre repository GitHub
2. **Settings** > **Secrets and variables** > **Actions**
3. Ajoutez les 4 secrets listés ci-dessus
4. Voir `GITHUB_SECRETS_CONFIG.md` pour les détails

### Étape 2: Configuration Initiale du Serveur

```bash
# Connexion au serveur
ssh freemobila@15.236.188.205

# Installation des prérequis
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Clonage du repository
cd ~
git clone https://github.com/VOTRE_USERNAME/FreeMobilaChat.git FreeMobileApp
cd FreeMobileApp

# Configuration initiale
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r streamlit_app/requirements.txt

# Configuration .env (si nécessaire)
cd streamlit_app
nano .env  # Ajouter vos clés API
cd ..

# Rendre les scripts exécutables
chmod +x start_app_production.sh
chmod +x deploy_lightsail.sh

# Configuration PM2
pm2 startup systemd
# Suivre les instructions affichées

# Démarrage initial
pm2 start ecosystem.config.js
pm2 save
```

### Étape 3: Test du Déploiement

#### Test Manuel

```bash
ssh freemobila@15.236.188.205
cd ~/FreeMobileApp
bash deploy_lightsail.sh deploy
```

#### Test Automatique

1. Faire un petit changement dans le code
2. Committer et pousser vers `main`
3. Vérifier dans l'onglet **Actions** de GitHub

### Étape 4: Vérification

```bash
# Vérifier que l'application est accessible
curl http://15.236.188.205:8502

# Vérifier PM2
pm2 status
pm2 logs freemobile-app
```

## 📊 Commandes Utiles

### Sur le Serveur

```bash
# PM2
pm2 status
pm2 logs freemobile-app -f
pm2 restart freemobile-app
pm2 monit

# Déploiement
cd ~/FreeMobileApp
bash deploy_lightsail.sh deploy    # Déploiement complet
bash deploy_lightsail.sh rollback  # Rollback
bash deploy_lightsail.sh health    # Health check
bash deploy_lightsail.sh logs       # Afficher les logs
```

### Depuis GitHub

- **Déploiement automatique**: Push vers `main` ou `master`
- **Déploiement manuel**: Actions > Deploy to Lightsail > Run workflow

## 🔍 Monitoring

### Logs

- **PM2**: `pm2 logs freemobile-app`
- **Application**: `~/FreeMobileApp/logs/`
- **PM2 combiné**: `~/FreeMobileApp/logs/combined.log`

### Health Checks

```bash
# Sur le serveur
bash deploy_lightsail.sh health

# Depuis l'extérieur
curl http://15.236.188.205:8502
```

## 🛡️ Sécurité

- ✅ Clés SSH stockées dans GitHub Secrets
- ✅ Sauvegardes automatiques avant chaque déploiement
- ✅ Rollback disponible
- ✅ Vérifications de syntaxe avant déploiement
- ✅ Health checks après déploiement

## 📝 Documentation

- **`PRODUCTION_SETUP.md`** - Guide complet de mise en production
- **`GITHUB_SECRETS_CONFIG.md`** - Configuration des secrets GitHub
- **`docs/LIGHTSAIL_DEPLOYMENT.md`** - Documentation détaillée
- **`docs/CHECKLIST_DEPLOYMENT.md`** - Checklist de vérification

## 🆘 Dépannage

### Le workflow GitHub Actions échoue

1. Vérifier les secrets GitHub
2. Tester la connexion SSH: `ssh -i ~/.ssh/freemobila_deploy freemobila@15.236.188.205`
3. Consulter les logs du workflow dans GitHub Actions

### L'application ne démarre pas

```bash
pm2 logs freemobile-app --lines 100
source ~/FreeMobileApp/venv/bin/activate
python3 -m py_compile ~/FreeMobileApp/streamlit_app/app.py
```

### L'application n'est pas accessible

1. Vérifier le pare-feu Lightsail (port 8502)
2. Vérifier que Streamlit écoute sur 0.0.0.0: `ps aux | grep streamlit`
3. Tester localement: `curl http://localhost:8502`

## ✅ Checklist Finale

- [ ] Secrets GitHub configurés
- [ ] Connexion SSH testée
- [ ] Prérequis installés sur le serveur
- [ ] Repository cloné
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Fichier .env configuré
- [ ] PM2 configuré et démarré
- [ ] Pare-feu Lightsail configuré
- [ ] Application accessible sur http://15.236.188.205:8502
- [ ] Déploiement manuel testé
- [ ] Déploiement automatique testé

## 🎉 Prêt pour la Production!

Une fois toutes les étapes complétées:

✅ L'application est accessible publiquement  
✅ Le déploiement automatique fonctionne  
✅ Les sauvegardes sont automatiques  
✅ Le monitoring est en place  
✅ Le rollback est disponible  

**URL de Production:** http://15.236.188.205:8502

---

**Date de mise en production**: _______________  
**Dernière vérification**: _______________  
**Status**: ✅ Prêt

