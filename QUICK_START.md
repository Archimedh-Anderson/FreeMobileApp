# ⚡ Quick Start - FreeMobilaChat CI/CD

Guide de démarrage rapide pour le déploiement automatique sur AWS EC2.

---

## 🚀 Configuration initiale (À faire une seule fois)

### 1. Configurer les secrets GitHub (2 minutes)

```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

| Secret Name | Value |
|-------------|-------|
| `EC2_HOST` | `13.37.186.191` |
| `EC2_USERNAME` | `ec2-user` |
| `EC2_SSH_KEY` | Contenu complet de votre fichier `.pem` |

**📝 Astuce:** Copiez la clé SSH avec:
```bash
cat /chemin/vers/votre_cle.pem
```

### 2. Configuration EC2 - Permissions sudo (1 minute)

```bash
# Connectez-vous à EC2
ssh -i votre_cle.pem ec2-user@13.37.186.191

# Configurez sudo sans mot de passe
sudo visudo

# Ajoutez à la fin:
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl is-active streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/journalctl
ec2-user ALL=(ALL) NOPASSWD: /bin/tail /var/log/streamlit.log

# Sauvegardez (Ctrl+X, Y, Enter)
```

---

## 🎯 Déploiement automatique

### Push vers GitHub

```bash
git add .
git commit -m "feat: Nouvelle fonctionnalité"
git push origin main
```

✅ **Le déploiement démarre automatiquement!**

---

## 📊 Suivi du déploiement

### GitHub Actions (Web)

```
GitHub → Actions → Sélectionner le workflow
```

Vous verrez:
- ✅ Vérification de la syntaxe Python
- 🚀 Déploiement via SSH
- ✅ Redémarrage du service
- ✅ Health check

### Logs en temps réel (SSH)

```bash
# Connexion
ssh -i votre_cle.pem ec2-user@13.37.186.191

# Logs du service
sudo journalctl -u streamlit.service -f

# Logs de l'application
sudo tail -f /var/log/streamlit.log

# Statut du service
sudo systemctl status streamlit.service
```

---

## 🛠️ Commandes utiles

### Sur EC2

```bash
# Déploiement manuel complet
bash /home/ec2-user/deploy.sh

# Restauration depuis la dernière sauvegarde
bash /home/ec2-user/deploy.sh rollback

# Afficher les logs
bash /home/ec2-user/deploy.sh logs

# Redémarrer le service
bash /home/ec2-user/deploy.sh restart

# Vérifier l'état de santé
bash /home/ec2-user/deploy.sh health

# Statut du service
bash /home/ec2-user/deploy.sh status
```

### Depuis GitHub

**Déclenchement manuel:**
```
Actions → Deploy to AWS EC2 → Run workflow
```

**Annuler un déploiement en cours:**
```
Actions → Workflow en cours → Cancel workflow
```

---

## 🔍 Vérifications

### Application fonctionne?

```bash
# Test HTTP local (sur EC2)
curl http://localhost:8503

# Test depuis navigateur
http://13.37.186.191:8503
```

### Service actif?

```bash
sudo systemctl is-active streamlit.service
# Doit retourner: active
```

### Logs d'erreur?

```bash
sudo journalctl -u streamlit.service -n 50 --no-pager
```

---

## 🐛 Dépannage rapide

### Problème 1: "Permission denied (publickey)"

**Cause:** Clé SSH incorrecte

**Solution:**
1. Vérifiez le secret `EC2_SSH_KEY` dans GitHub
2. Assurez-vous d'avoir copié toute la clé (avec BEGIN/END)
3. Recréez le secret

### Problème 2: Service ne démarre pas

**Diagnostic:**
```bash
# Vérifier les erreurs
sudo journalctl -u streamlit.service -n 100

# Tester manuellement
cd /home/ec2-user/FreeMobileApp/streamlit_app
source venv/bin/activate
streamlit run app.py
```

**Solutions courantes:**
- Dépendances manquantes: `pip install -r requirements.txt`
- Port occupé: `sudo lsof -i :8503`
- Fichier .env manquant: Créez-le avec les clés API

### Problème 3: Modifications non déployées

**Solution:**
```bash
# Sur EC2
cd /home/ec2-user/FreeMobileApp
git fetch origin main
git reset --hard origin/main
sudo systemctl restart streamlit.service
```

---

## 📈 Workflow typique

```bash
# 1. Développement local
git checkout -b feature/nouvelle-fonctionnalite
# ... faire vos modifications ...

# 2. Test local
streamlit run streamlit_app/app.py

# 3. Commit
git add .
git commit -m "feat: Description de la fonctionnalité"

# 4. Push vers GitHub
git push origin feature/nouvelle-fonctionnalite

# 5. Créer une Pull Request
# GitHub → Pull Requests → New Pull Request

# 6. Merge vers main (après review)
# → Déploiement automatique sur EC2!
```

---

## 🔐 Sécurité

**✅ À FAIRE:**
- Utiliser GitHub Secrets pour les données sensibles
- Limiter l'accès SSH dans le Security Group
- Changer les clés SSH régulièrement
- Activer 2FA sur GitHub

**❌ NE JAMAIS:**
- Committer des fichiers `.env` ou `.pem`
- Partager les secrets GitHub
- Exposer les clés API dans les logs

---

## 📞 Support

**Logs GitHub Actions:**
```
https://github.com/Archimedh-Anderson/FreeMobileApp/actions
```

**Documentation complète:**
- `DEPLOYMENT_README.md` - Guide complet
- `GITHUB_SECRETS_SETUP.md` - Configuration des secrets

**En cas de problème:**
1. Vérifiez les logs GitHub Actions
2. Vérifiez les logs EC2
3. Testez avec `bash deploy.sh`
4. Ouvrez une issue avec les logs d'erreur

---

## ✅ Checklist de déploiement

- [ ] Secrets GitHub configurés (EC2_HOST, EC2_USERNAME, EC2_SSH_KEY)
- [ ] Permissions sudo configurées sur EC2
- [ ] Service streamlit.service actif
- [ ] Fichier .env configuré avec les clés API
- [ ] Security Group autorise le port 8503
- [ ] Application accessible via http://13.37.186.191:8503
- [ ] Workflow GitHub Actions s'exécute sans erreur

---

**Prêt à déployer! 🚀**

Prochain push vers `main` = déploiement automatique!
