# 🚀 Guide de Finalisation - Mise en Production Lightsail

## 📋 Informations du Serveur

- **IP Publique**: `15.236.188.205` (freemobila-static-ip)
- **Utilisateur SSH**: `freemobila`
- **Port SSH**: `22`
- **Port Application**: `8502`
- **URL Production**: `http://15.236.188.205:8502`

## 🔐 Configuration des Secrets GitHub

### Étape 1: Générer une clé SSH (si pas déjà fait)

```bash
# Sur votre machine locale
ssh-keygen -t rsa -b 4096 -C "github-actions-freemobila" -f ~/.ssh/freemobila_deploy
```

### Étape 2: Copier la clé publique sur le serveur

```bash
# Option 1: Si vous avez déjà accès SSH
ssh-copy-id -i ~/.ssh/freemobila_deploy.pub freemobila@15.236.188.205

# Option 2: Manuellement
cat ~/.ssh/freemobila_deploy.pub
# Copier le contenu, puis sur le serveur:
ssh freemobila@15.236.188.205
mkdir -p ~/.ssh
echo "VOTRE_CLE_PUBLIQUE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Étape 3: Tester la connexion SSH

```bash
ssh -i ~/.ssh/freemobila_deploy freemobila@15.236.188.205
```

### Étape 4: Configurer les Secrets GitHub

1. Allez dans votre repository GitHub
2. **Settings** > **Secrets and variables** > **Actions**
3. Cliquez sur **New repository secret** pour chaque secret:

#### Secret 1: `LIGHTSAIL_HOST`
```
15.236.188.205
```

#### Secret 2: `LIGHTSAIL_USER`
```
freemobila
```

#### Secret 3: `SSH_PRIVATE_KEY`
```bash
# Sur votre machine locale
cat ~/.ssh/freemobila_deploy
# Copier TOUT le contenu (y compris -----BEGIN et -----END)
```

#### Secret 4: `LIGHTSAIL_SSH_PORT` (optionnel)
```
22
```

## 🖥️ Configuration Initiale du Serveur

### Connexion au serveur

```bash
ssh freemobila@15.236.188.205
```

### Installation des prérequis

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Python et pip
sudo apt install -y python3 python3-pip python3-venv git curl

# Installation de Node.js et npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Vérification des versions
python3 --version  # Doit être 3.8+
node --version     # Doit être 18+
npm --version

# Installation de PM2 globalement
sudo npm install -g pm2

# Configuration de PM2 pour démarrer au boot
pm2 startup systemd
# Suivre les instructions affichées (copier-coller la commande sudo)
```

### Clonage du Repository

```bash
cd ~
git clone https://github.com/VOTRE_USERNAME/FreeMobilaChat.git FreeMobileApp
cd FreeMobileApp

# Vérifier que les fichiers sont présents
ls -la
# Doit contenir: ecosystem.config.js, start_app_production.sh, deploy_lightsail.sh
```

### Configuration Initiale

```bash
cd ~/FreeMobileApp

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r streamlit_app/requirements.txt

# Configuration du fichier .env (si nécessaire)
cd streamlit_app
# Créer .env avec vos clés API
nano .env
# Ajouter:
# GEMINI_API_KEY=votre_cle_ici
# MISTRAL_API_KEY=votre_cle_ici
# STREAMLIT_PORT=8502
# ENVIRONMENT=production
cd ..

# Rendre les scripts exécutables
chmod +x start_app_production.sh
chmod +x deploy_lightsail.sh

# Vérifier ecosystem.config.js
cat ecosystem.config.js
# Doit contenir: cwd: '/home/freemobila/FreeMobileApp'
```

### Démarrage Initial avec PM2

```bash
cd ~/FreeMobileApp

# Démarrer l'application
pm2 start ecosystem.config.js

# Vérifier le statut
pm2 status

# Vérifier les logs
pm2 logs freemobile-app --lines 50

# Sauvegarder la configuration PM2
pm2 save
```

### Vérification de l'Application

```bash
# Sur le serveur
curl http://localhost:8502

# Depuis votre machine locale
curl http://15.236.188.205:8502
```

## ✅ Vérification du Pare-feu Lightsail

Les règles suivantes doivent être configurées dans Lightsail:

| Application | Protocol | Port | Restriction |
|------------|----------|------|-------------|
| SSH | TCP | 22 | Any IPv4 address |
| HTTP | TCP | 80 | Any IPv4 address |
| HTTPS | TCP | 443 | Any IPv4 address |
| Custom | TCP | 8502 | Any IPv4 address |

**Vérification:**
1. Allez dans votre instance Lightsail sur AWS Console
2. **Networking** > **Firewall**
3. Vérifiez que toutes les règles ci-dessus sont présentes

## 🚀 Test du Déploiement Automatique

### Test 1: Déploiement Manuel

```bash
ssh freemobila@15.236.188.205
cd ~/FreeMobileApp
bash deploy_lightsail.sh deploy
```

**Résultat attendu:**
- ✅ Sauvegarde créée
- ✅ Code mis à jour
- ✅ Dépendances installées
- ✅ Application redémarrée avec PM2
- ✅ Health check réussi

### Test 2: Déploiement via GitHub Actions

1. Faire un petit changement dans le code (ex: commentaire)
2. Committer et pousser vers `main`:
   ```bash
   git add .
   git commit -m "test: vérification déploiement automatique"
   git push origin main
   ```
3. Aller dans l'onglet **Actions** de GitHub
4. Vérifier que le workflow "Deploy to Lightsail" se déclenche
5. Vérifier que le déploiement réussit

### Test 3: Accès à l'Application

```bash
# Depuis votre navigateur
http://15.236.188.205:8502

# Ou depuis la ligne de commande
curl http://15.236.188.205:8502
```

## 📊 Commandes de Monitoring

### PM2

```bash
# Statut
pm2 status

# Logs en temps réel
pm2 logs freemobile-app -f

# Monitoring interactif
pm2 monit

# Redémarrer
pm2 restart freemobile-app

# Statistiques détaillées
pm2 describe freemobile-app
```

### Déploiement

```bash
cd ~/FreeMobileApp

# Déploiement complet
bash deploy_lightsail.sh deploy

# Rollback
bash deploy_lightsail.sh rollback

# Health check
bash deploy_lightsail.sh health

# Logs
bash deploy_lightsail.sh logs

# Statut
bash deploy_lightsail.sh status
```

### Vérification Système

```bash
# Processus Streamlit
ps aux | grep streamlit

# Ports en écoute
sudo netstat -tlnp | grep 8502

# Espace disque
df -h

# Mémoire
free -h

# Logs système
journalctl -u pm2-freemobila -f  # Si configuré
```

## 🔍 Dépannage

### Le workflow GitHub Actions échoue

1. **Vérifier les secrets GitHub:**
   - Settings > Secrets > Actions
   - Vérifier que tous les secrets sont présents et corrects

2. **Tester la connexion SSH:**
   ```bash
   ssh -i ~/.ssh/freemobila_deploy freemobila@15.236.188.205
   ```

3. **Vérifier les logs du workflow:**
   - Onglet Actions > Dernier workflow > Voir les logs détaillés

### L'application ne démarre pas

```bash
# Vérifier les logs PM2
pm2 logs freemobile-app --lines 100

# Vérifier l'environnement virtuel
source ~/FreeMobileApp/venv/bin/activate
python --version
pip list

# Vérifier la syntaxe Python
python3 -m py_compile ~/FreeMobileApp/streamlit_app/app.py

# Redémarrer manuellement
cd ~/FreeMobileApp
source venv/bin/activate
streamlit run streamlit_app/app.py --server.port 8502 --server.address 0.0.0.0
```

### L'application n'est pas accessible

1. **Vérifier le pare-feu Lightsail:**
   - Port 8502 doit être ouvert

2. **Vérifier que Streamlit écoute sur 0.0.0.0:**
   ```bash
   ps aux | grep streamlit
   # Doit contenir: --server.address 0.0.0.0
   ```

3. **Tester localement sur le serveur:**
   ```bash
   curl http://localhost:8502
   ```

4. **Vérifier les logs:**
   ```bash
   pm2 logs freemobile-app --lines 50
   ```

## 📝 Checklist de Finalisation

- [ ] Secrets GitHub configurés (LIGHTSAIL_HOST, LIGHTSAIL_USER, SSH_PRIVATE_KEY)
- [ ] Connexion SSH testée et fonctionnelle
- [ ] Prérequis installés sur le serveur (Python, Node.js, PM2)
- [ ] Repository cloné dans ~/FreeMobileApp
- [ ] Environnement virtuel créé et dépendances installées
- [ ] Fichier .env configuré avec les clés API
- [ ] Scripts rendus exécutables
- [ ] PM2 configuré pour démarrer au boot
- [ ] Application démarrée avec PM2
- [ ] Pare-feu Lightsail configuré (port 8502 ouvert)
- [ ] Application accessible sur http://15.236.188.205:8502
- [ ] Déploiement manuel testé et fonctionnel
- [ ] Déploiement automatique via GitHub Actions testé et fonctionnel

## 🎉 Mise en Production Réussie

Une fois toutes les étapes complétées:

1. ✅ L'application est accessible publiquement
2. ✅ Le déploiement automatique fonctionne
3. ✅ Les sauvegardes sont automatiques
4. ✅ Le monitoring est en place
5. ✅ Le rollback est disponible

**URL de Production:** http://15.236.188.205:8502

---

**Date de mise en production**: _______________
**Dernière vérification**: _______________

