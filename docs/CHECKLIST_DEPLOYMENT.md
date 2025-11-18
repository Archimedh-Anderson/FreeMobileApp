# ✅ Checklist de Vérification du Déploiement Lightsail

Utilisez cette checklist pour vérifier que votre déploiement automatique est correctement configuré.

## 🔐 Secrets GitHub

- [ ] `LIGHTSAIL_HOST` - Adresse IP du serveur Lightsail
- [ ] `LIGHTSAIL_USER` - Nom d'utilisateur SSH (`freemobila`)
- [ ] `LIGHTSAIL_SSH_PORT` - Port SSH (optionnel, par défaut 22)
- [ ] `SSH_PRIVATE_KEY` - Clé privée SSH pour la connexion

### Comment vérifier les secrets

1. Allez dans votre repository GitHub
2. Settings > Secrets and variables > Actions
3. Vérifiez que tous les secrets ci-dessus sont présents

## 🖥️ Configuration du Serveur Lightsail

### Prérequis installés

- [ ] Python 3.8+ installé
- [ ] Git installé
- [ ] Node.js et npm installés
- [ ] PM2 installé globalement (`npm install -g pm2`)
- [ ] PM2 configuré pour démarrer au boot (`pm2 startup systemd`)

### Structure des répertoires

- [ ] `~/FreeMobileApp/` existe
- [ ] `~/FreeMobileApp/streamlit_app/` existe
- [ ] `~/FreeMobileApp/venv/` existe (ou sera créé automatiquement)
- [ ] `~/FreeMobileApp/logs/` existe (ou sera créé automatiquement)
- [ ] `~/FreeMobileApp/backups/` existe (ou sera créé automatiquement)

### Fichiers de configuration

- [ ] `ecosystem.config.js` présent dans `~/FreeMobileApp/`
- [ ] `start_app_production.sh` présent et exécutable (`chmod +x`)
- [ ] `deploy_lightsail.sh` présent et exécutable (`chmod +x`)
- [ ] `.env` configuré dans `~/FreeMobileApp/streamlit_app/` (si nécessaire)

### Connexion SSH

- [ ] La clé SSH publique est ajoutée au serveur
- [ ] La connexion SSH fonctionne sans mot de passe
- [ ] Test: `ssh freemobila@VOTRE_IP_LIGHTSAIL` fonctionne

## 📝 Fichiers du Repository

### Workflow GitHub Actions

- [ ] `.github/workflows/deploy.yml` existe
- [ ] Le workflow utilise les bons secrets
- [ ] Le workflow se déclenche sur `push` vers `main` ou `master`

### Scripts de déploiement

- [ ] `start_app_production.sh` existe et est exécutable
- [ ] `deploy_lightsail.sh` existe et est exécutable
- [ ] `ecosystem.config.js` est configuré correctement

## 🔥 Pare-feu Lightsail

- [ ] Port 22 (SSH) ouvert
- [ ] Port 8502 (Streamlit) ouvert pour TCP
- [ ] Source autorisée: `0.0.0.0/0` (ou votre IP spécifique)

### Comment vérifier dans Lightsail

1. Allez dans votre instance Lightsail
2. Networking > Firewall
3. Vérifiez que le port 8502 est ouvert

## 🧪 Tests de Déploiement

### Test manuel sur le serveur

```bash
ssh freemobila@VOTRE_IP_LIGHTSAIL
cd ~/FreeMobileApp
bash deploy_lightsail.sh deploy
```

- [ ] Le déploiement manuel fonctionne
- [ ] L'application démarre avec PM2
- [ ] L'application est accessible sur `http://VOTRE_IP:8502`

### Test du workflow GitHub Actions

1. Faites un petit changement (ex: commentaire dans un fichier)
2. Committez et poussez vers `main`
3. Allez dans l'onglet "Actions" de GitHub

- [ ] Le workflow se déclenche automatiquement
- [ ] Le workflow se termine avec succès
- [ ] L'application est accessible après le déploiement

## 📊 Vérification Post-Déploiement

### PM2

```bash
pm2 status
```

- [ ] `freemobile-app` est en ligne (status: `online`)
- [ ] Pas d'erreurs dans les logs

### Logs

```bash
pm2 logs freemobile-app --lines 50
```

- [ ] Pas d'erreurs critiques
- [ ] Streamlit démarre correctement
- [ ] L'application écoute sur `0.0.0.0:8502`

### Accès HTTP

```bash
curl http://localhost:8502
```

- [ ] La requête HTTP retourne du contenu (code 200 ou redirection)
- [ ] L'application est accessible depuis l'extérieur

### Processus

```bash
ps aux | grep streamlit
```

- [ ] Le processus Streamlit est en cours d'exécution
- [ ] Le processus écoute sur le port 8502

## 🔄 Fonctionnalités de Rollback

- [ ] Les sauvegardes sont créées dans `~/FreeMobileApp/backups/`
- [ ] Le rollback fonctionne: `bash deploy_lightsail.sh rollback`
- [ ] Seulement les 5 dernières sauvegardes sont conservées

## 📋 Commandes Utiles

Ajoutez ces commandes à vos favoris:

```bash
# Statut PM2
pm2 status

# Logs en temps réel
pm2 logs freemobile-app -f

# Redémarrer
pm2 restart freemobile-app

# Déploiement manuel
cd ~/FreeMobileApp && bash deploy_lightsail.sh deploy

# Health check
cd ~/FreeMobileApp && bash deploy_lightsail.sh health
```

## ✅ Validation Finale

Une fois toutes les cases cochées:

- [ ] Le déploiement automatique fonctionne
- [ ] L'application est accessible publiquement
- [ ] Les logs sont correctement configurés
- [ ] Le rollback est testé et fonctionne
- [ ] La documentation est à jour

## 🆘 En Cas de Problème

1. **Workflow GitHub Actions échoue**:
   - Vérifier les secrets GitHub
   - Vérifier la connexion SSH
   - Consulter les logs du workflow

2. **Application ne démarre pas**:
   - Vérifier les logs PM2: `pm2 logs freemobile-app`
   - Vérifier l'environnement virtuel: `source venv/bin/activate && pip list`
   - Vérifier la syntaxe Python: `python3 -m py_compile streamlit_app/app.py`

3. **Application non accessible**:
   - Vérifier le pare-feu Lightsail
   - Vérifier que Streamlit écoute sur `0.0.0.0`: `ps aux | grep streamlit`
   - Tester localement: `curl http://localhost:8502`

4. **PM2 ne démarre pas au boot**:
   - Réexécuter: `pm2 startup systemd`
   - Suivre les instructions affichées
   - Sauvegarder: `pm2 save`

---

**Date de dernière vérification**: _______________
**Vérifié par**: _______________

