# 📋 Résumé des Améliorations du Déploiement Lightsail

## ✅ Ce qui a été fait

### 1. Workflow GitHub Actions amélioré (`.github/workflows/deploy.yml`)

**Améliorations apportées:**
- ✅ Sauvegarde automatique avant chaque déploiement
- ✅ Gestion robuste des erreurs avec `set -e`
- ✅ Vérification de l'environnement virtuel Python
- ✅ Installation automatique de PM2 si nécessaire
- ✅ Health checks après déploiement
- ✅ Affichage détaillé des logs
- ✅ Support des branches `main` et `master`
- ✅ Notifications de succès/échec
- ✅ Timeout configuré (10 minutes)

**Secrets GitHub requis:**
- `LIGHTSAIL_HOST` - Adresse IP du serveur
- `LIGHTSAIL_USER` - Utilisateur SSH (`freemobila`)
- `LIGHTSAIL_SSH_PORT` - Port SSH (optionnel, défaut: 22)
- `SSH_PRIVATE_KEY` - Clé privée SSH

### 2. Script de démarrage production (`start_app_production.sh`)

**Fonctionnalités:**
- ✅ Démarre Streamlit sur `0.0.0.0:8502` (accessible depuis l'extérieur)
- ✅ Gestion automatique de l'environnement virtuel
- ✅ Vérification des dépendances
- ✅ Test de syntaxe Python avant démarrage
- ✅ Logging structuré dans `logs/startup_*.log`
- ✅ Configuration optimisée pour la production

**Différences avec `start_app.sh`:**
- Utilise `0.0.0.0` au lieu de `localhost` (accessible depuis l'extérieur)
- Mode headless activé
- CORS et XSRF protection configurés
- Logs détaillés

### 3. Script de déploiement Lightsail (`deploy_lightsail.sh`)

**Fonctionnalités:**
- ✅ Sauvegarde automatique (5 dernières conservées)
- ✅ Récupération du code depuis GitHub
- ✅ Installation des dépendances Python
- ✅ Vérification de la configuration
- ✅ Redémarrage avec PM2
- ✅ Health checks
- ✅ Rollback automatique disponible
- ✅ Commandes multiples: `deploy`, `rollback`, `logs`, `status`, `restart`, `health`

**Usage:**
```bash
bash deploy_lightsail.sh deploy    # Déploiement complet
bash deploy_lightsail.sh rollback  # Restauration
bash deploy_lightsail.sh logs      # Afficher les logs
bash deploy_lightsail.sh status    # Statut PM2
bash deploy_lightsail.sh restart   # Redémarrer uniquement
bash deploy_lightsail.sh health    # Health check
```

### 4. Configuration PM2 mise à jour (`ecosystem.config.js`)

**Améliorations:**
- ✅ Utilise `start_app_production.sh` au lieu de `start_app.sh`
- ✅ Variables d'environnement: `PORT=8502`, `ADDRESS=0.0.0.0`
- ✅ Configuration de redémarrage automatique améliorée
- ✅ Gestion des logs améliorée
- ✅ Timeout de kill configuré

### 5. Documentation complète

**Fichiers créés:**
- ✅ `docs/LIGHTSAIL_DEPLOYMENT.md` - Guide complet de déploiement
- ✅ `docs/CHECKLIST_DEPLOYMENT.md` - Checklist de vérification

## 🔍 Points de Vérification

### Sur GitHub

1. **Secrets configurés:**
   - Settings > Secrets and variables > Actions
   - Vérifier: `LIGHTSAIL_HOST`, `LIGHTSAIL_USER`, `SSH_PRIVATE_KEY`

2. **Workflow présent:**
   - `.github/workflows/deploy.yml` existe
   - Le workflow se déclenche sur push vers `main` ou `master`

### Sur le Serveur Lightsail

1. **Fichiers présents:**
   ```bash
   ~/FreeMobileApp/
   ├── ecosystem.config.js
   ├── start_app_production.sh (exécutable)
   ├── deploy_lightsail.sh (exécutable)
   └── streamlit_app/
   ```

2. **PM2 configuré:**
   ```bash
   pm2 status  # Doit montrer freemobile-app
   pm2 startup systemd  # Si pas encore fait
   ```

3. **Pare-feu Lightsail:**
   - Port 8502 ouvert (TCP)
   - Source: `0.0.0.0/0` (ou votre IP)

## 🚀 Prochaines Étapes

### 1. Configurer les secrets GitHub

```bash
# Sur votre machine locale
ssh-keygen -t rsa -b 4096 -C "github-actions"
ssh-copy-id -i ~/.ssh/id_rsa.pub freemobila@VOTRE_IP_LIGHTSAIL

# Dans GitHub: Settings > Secrets > Actions
# Ajouter SSH_PRIVATE_KEY avec le contenu de ~/.ssh/id_rsa
```

### 2. Tester le déploiement manuel

```bash
ssh freemobila@VOTRE_IP_LIGHTSAIL
cd ~/FreeMobileApp
bash deploy_lightsail.sh deploy
```

### 3. Tester le workflow GitHub Actions

1. Faire un petit changement
2. Committer et pousser vers `main`
3. Vérifier dans l'onglet "Actions" de GitHub

### 4. Vérifier l'application

```bash
# Sur le serveur
pm2 status
pm2 logs freemobile-app

# Depuis votre machine
curl http://VOTRE_IP_LIGHTSAIL:8502
```

## 📊 Monitoring

### Logs disponibles

- **PM2**: `pm2 logs freemobile-app`
- **Application**: `~/FreeMobileApp/logs/startup_*.log`
- **PM2 combiné**: `~/FreeMobileApp/logs/combined.log`

### Commandes de monitoring

```bash
# Statut
pm2 status
pm2 describe freemobile-app

# Logs en temps réel
pm2 logs freemobile-app -f

# Monitoring interactif
pm2 monit

# Statistiques
pm2 info freemobile-app
```

## 🔄 Workflow de Déploiement

```
1. Push vers main/master
   ↓
2. GitHub Actions se déclenche
   ↓
3. Connexion SSH au serveur Lightsail
   ↓
4. Sauvegarde de l'application actuelle
   ↓
5. Récupération du code depuis GitHub
   ↓
6. Installation/mise à jour des dépendances
   ↓
7. Vérification de la configuration
   ↓
8. Redémarrage avec PM2
   ↓
9. Health checks
   ↓
10. ✅ Déploiement terminé
```

## 🛡️ Sécurité

- ✅ Clés SSH stockées dans GitHub Secrets (jamais dans le code)
- ✅ Sauvegardes automatiques avant chaque déploiement
- ✅ Rollback disponible en cas de problème
- ✅ Vérifications de syntaxe avant déploiement
- ✅ Health checks après déploiement

## 📝 Notes Importantes

1. **Premier déploiement**: Le workflow créera automatiquement l'environnement virtuel si nécessaire
2. **PM2**: S'assurer que PM2 est installé et configuré pour démarrer au boot
3. **Pare-feu**: Vérifier que le port 8502 est ouvert dans Lightsail
4. **Sauvegardes**: Les 5 dernières sauvegardes sont conservées automatiquement
5. **Rollback**: Utiliser `bash deploy_lightsail.sh rollback` en cas de problème

## 🆘 Dépannage Rapide

### Le workflow échoue
- Vérifier les secrets GitHub
- Tester la connexion SSH manuellement
- Consulter les logs du workflow dans GitHub Actions

### L'application ne démarre pas
```bash
pm2 logs freemobile-app --lines 100
source ~/FreeMobileApp/venv/bin/activate
python3 -m py_compile ~/FreeMobileApp/streamlit_app/app.py
```

### L'application n'est pas accessible
- Vérifier le pare-feu Lightsail (port 8502)
- Vérifier que Streamlit écoute sur `0.0.0.0`: `ps aux | grep streamlit`
- Tester localement: `curl http://localhost:8502`

---

**Date de création**: $(date)
**Version**: 1.0
**Status**: ✅ Prêt pour production

