# 🔐 Configuration des Secrets GitHub - Production

## 📋 Secrets à Configurer

Allez dans votre repository GitHub: **Settings** > **Secrets and variables** > **Actions** > **New repository secret**

### Secret 1: `LIGHTSAIL_HOST`

**Valeur:**
```
15.236.188.205
```

**Description:** Adresse IP publique du serveur Lightsail (freemobila-static-ip)

---

### Secret 2: `LIGHTSAIL_USER`

**Valeur:**
```
freemobila
```

**Description:** Nom d'utilisateur SSH pour se connecter au serveur

---

### Secret 3: `SSH_PRIVATE_KEY`

**Valeur:** (Voir instructions ci-dessous)

**Description:** Clé privée SSH pour l'authentification

#### Comment obtenir la clé privée:

1. **Générer une clé SSH** (si pas déjà fait):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions-freemobila" -f ~/.ssh/freemobila_deploy
   ```

2. **Copier la clé publique sur le serveur:**
   ```bash
   ssh-copy-id -i ~/.ssh/freemobila_deploy.pub freemobila@15.236.188.205
   ```

3. **Afficher la clé privée:**
   ```bash
   cat ~/.ssh/freemobila_deploy
   ```

4. **Copier TOUT le contenu** (y compris les lignes `-----BEGIN OPENSSH PRIVATE KEY-----` et `-----END OPENSSH PRIVATE KEY-----`)

5. **Coller dans GitHub Secret** `SSH_PRIVATE_KEY`

**Exemple de format:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
...
(plusieurs lignes)
...
-----END OPENSSH PRIVATE KEY-----
```

---

### Secret 4: `LIGHTSAIL_SSH_PORT` (Optionnel)

**Valeur:**
```
22
```

**Description:** Port SSH (par défaut 22, peut être omis si c'est le port par défaut)

---

## ✅ Vérification

### Test de la connexion SSH

Après avoir configuré les secrets, testez la connexion:

```bash
# Sur votre machine locale
ssh -i ~/.ssh/freemobila_deploy freemobila@15.236.188.205
```

Si la connexion fonctionne sans mot de passe, les secrets sont correctement configurés.

### Test du workflow GitHub Actions

1. Faites un petit changement dans le code
2. Committez et poussez vers `main`
3. Allez dans l'onglet **Actions** de GitHub
4. Vérifiez que le workflow "Deploy to Lightsail" se déclenche
5. Vérifiez que le déploiement réussit

## 🚨 Sécurité

⚠️ **IMPORTANT:**
- Ne jamais commiter la clé privée SSH dans le repository
- Ne jamais partager la clé privée
- Utiliser uniquement GitHub Secrets pour stocker les clés
- Régénérer la clé si elle est compromise

## 📝 Checklist

- [ ] Clé SSH générée (`~/.ssh/freemobila_deploy`)
- [ ] Clé publique copiée sur le serveur
- [ ] Connexion SSH testée et fonctionnelle
- [ ] Secret `LIGHTSAIL_HOST` configuré: `15.236.188.205`
- [ ] Secret `LIGHTSAIL_USER` configuré: `freemobila`
- [ ] Secret `SSH_PRIVATE_KEY` configuré (clé privée complète)
- [ ] Secret `LIGHTSAIL_SSH_PORT` configuré: `22` (optionnel)
- [ ] Workflow GitHub Actions testé et fonctionnel

---

**Date de configuration**: _______________
**Configuré par**: _______________

