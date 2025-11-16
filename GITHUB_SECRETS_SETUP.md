# 🔐 Configuration des Secrets GitHub - Guide Rapide

## 📌 Secrets à configurer

Pour que le déploiement automatique fonctionne, vous devez configurer 3 secrets dans votre repository GitHub.

---

## 🚀 Étapes de configuration

### 1. Accéder aux paramètres du repository

1. Ouvrez votre repository: https://github.com/Archimedh-Anderson/FreeMobileApp
2. Cliquez sur **Settings** (⚙️ en haut à droite)
3. Dans le menu latéral gauche, cliquez sur **Secrets and variables** → **Actions**
4. Cliquez sur **New repository secret**

---

### 2. Ajouter les secrets

#### Secret 1: EC2_HOST

```
Name: EC2_HOST
Secret: 13.37.186.191
```

**Description:** Adresse IP de votre serveur EC2

---

#### Secret 2: EC2_USERNAME

```
Name: EC2_USERNAME
Secret: ec2-user
```

**Description:** Nom d'utilisateur SSH pour la connexion

---

#### Secret 3: EC2_SSH_KEY

**IMPORTANT:** C'est le secret le plus critique!

##### Sur votre machine locale:

```bash
# Affichez le contenu de votre clé privée
cat /chemin/vers/votre_cle.pem

# Ou sur Windows (PowerShell):
Get-Content C:\chemin\vers\votre_cle.pem
```

##### Copiez TOUT le contenu, y compris:

```
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA... (votre clé complète sur plusieurs lignes)
...
-----END RSA PRIVATE KEY-----
```

##### Dans GitHub:

```
Name: EC2_SSH_KEY
Secret: [Collez ici le contenu complet de la clé]
```

**⚠️ ATTENTION:**
- Copiez la clé **EXACTEMENT** comme elle apparaît (avec les retours à la ligne)
- Ne supprimez AUCUN caractère
- Ne modifiez AUCUNE ligne
- Incluez les lignes `-----BEGIN...-----` et `-----END...-----`

---

## ✅ Vérification

Après avoir ajouté les 3 secrets, vous devriez voir:

```
EC2_HOST         Updated X seconds ago
EC2_USERNAME     Updated X seconds ago  
EC2_SSH_KEY      Updated X seconds ago
```

---

## 🧪 Test du déploiement

### Option 1: Push vers main

```bash
git add .
git commit -m "test: Déclenchement du CI/CD"
git push origin main
```

Le workflow se lancera automatiquement.

### Option 2: Déclenchement manuel

1. Allez sur **Actions** dans votre repository
2. Sélectionnez **Deploy to AWS EC2**
3. Cliquez sur **Run workflow** (à droite)
4. Sélectionnez la branche **main**
5. Cliquez sur **Run workflow**

---

## 📊 Suivi du déploiement

### Dans GitHub:

1. **Actions** → Sélectionnez le workflow en cours
2. Cliquez sur le job "Déploiement sur EC2"
3. Observez les logs en temps réel

### Sur le serveur EC2:

```bash
# Connexion SSH
ssh -i votre_cle.pem ec2-user@13.37.186.191

# Logs du service
sudo journalctl -u streamlit.service -f

# Logs de l'application
sudo tail -f /var/log/streamlit.log

# Statut du service
sudo systemctl status streamlit.service
```

---

## 🐛 Dépannage

### Erreur: "Permission denied (publickey)"

**Cause:** La clé SSH est incorrecte ou mal formatée

**Solution:**
1. Vérifiez que vous avez copié **toute** la clé
2. Assurez-vous qu'il n'y a pas d'espaces supplémentaires
3. Recréez le secret EC2_SSH_KEY

### Erreur: "Host key verification failed"

**Cause:** Le serveur n'est pas dans known_hosts

**Solution:** Le workflow utilise `StrictHostKeyChecking=no` - cette erreur ne devrait pas se produire.

### Erreur: "sudo: no tty present"

**Cause:** Permissions sudo mal configurées

**Solution:** Sur EC2, exécutez:

```bash
sudo visudo
```

Ajoutez:
```
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl is-active streamlit.service
ec2-user ALL=(ALL) NOPASSWD: /bin/journalctl
ec2-user ALL=(ALL) NOPASSWD: /bin/tail /var/log/streamlit.log
```

### Le service ne démarre pas

**Diagnostic:**

```bash
# Vérifier les logs d'erreur
sudo journalctl -u streamlit.service -n 100 --no-pager

# Vérifier l'état détaillé
sudo systemctl status streamlit.service -l

# Tester manuellement
cd /home/ec2-user/FreeMobileApp/streamlit_app
source venv/bin/activate
streamlit run app.py --server.port 8503
```

**Causes communes:**
- Dépendances manquantes
- Erreur de syntaxe Python
- Port 8503 déjà utilisé
- Fichier .env mal configuré

---

## 📞 Support

En cas de problème:

1. Consultez les logs GitHub Actions
2. Vérifiez les logs sur le serveur EC2
3. Testez le déploiement manuellement: `bash /home/ec2-user/deploy.sh`
4. Ouvrez une issue GitHub avec les logs d'erreur

---

## 🔒 Sécurité

**NE JAMAIS:**
- ❌ Committer la clé privée SSH dans le code
- ❌ Partager les secrets GitHub
- ❌ Afficher les secrets dans les logs

**TOUJOURS:**
- ✅ Utiliser GitHub Secrets pour les données sensibles
- ✅ Limiter l'accès SSH à votre IP (Security Group)
- ✅ Changer les clés SSH régulièrement
- ✅ Activer l'authentification à deux facteurs sur GitHub

---

## 📚 Ressources

- [Documentation GitHub Actions](https://docs.github.com/en/actions)
- [SSH Action](https://github.com/appleboy/ssh-action)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Streamlit Deployment](https://docs.streamlit.io/deploy)
