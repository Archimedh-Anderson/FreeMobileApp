# 🔐 Configuration SSH pour Windows - Guide Rapide

## ✅ Étape 1: Clé SSH Générée

La clé SSH a été générée avec succès:
- **Clé privée**: `C:\Users\ander\.ssh\freemobila_deploy`
- **Clé publique**: `C:\Users\ander\.ssh\freemobila_deploy.pub`

## 📋 Étape 2: Copier la Clé Publique sur le Serveur

### Option A: Si vous avez déjà accès SSH au serveur

```powershell
# Afficher la clé publique
Get-Content $env:USERPROFILE\.ssh\freemobila_deploy.pub

# Copier la clé sur le serveur (remplacez par votre méthode d'accès actuelle)
# Par exemple, si vous avez un mot de passe:
ssh freemobila@15.236.188.205
# Puis sur le serveur:
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Coller la clé publique (une ligne complète)
chmod 600 ~/.ssh/authorized_keys
exit
```

### Option B: Via le Console Lightsail (Recommandé)

1. Allez dans AWS Lightsail Console
2. Ouvrez votre instance
3. Cliquez sur **Connect using SSH** (ou utilisez le terminal du navigateur)
4. Exécutez ces commandes:

```bash
# Créer le répertoire .ssh si nécessaire
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ajouter la clé publique
echo "VOTRE_CLE_PUBLIQUE_ICI" >> ~/.ssh/authorized_keys

# Sécuriser les permissions
chmod 600 ~/.ssh/authorized_keys
```

**Important**: Remplacez `VOTRE_CLE_PUBLIQUE_ICI` par le contenu de `freemobila_deploy.pub`

### Option C: Via un autre utilisateur/admin

Si vous avez accès via un autre utilisateur (comme `ubuntu` ou `admin`):

```bash
# Se connecter avec l'autre utilisateur
ssh autre_utilisateur@15.236.188.205

# Ajouter la clé pour freemobila
sudo mkdir -p /home/freemobila/.ssh
sudo chmod 700 /home/freemobila/.ssh
sudo bash -c "echo 'VOTRE_CLE_PUBLIQUE_ICI' >> /home/freemobila/.ssh/authorized_keys"
sudo chmod 600 /home/freemobila/.ssh/authorized_keys
sudo chown -R freemobila:freemobila /home/freemobila/.ssh
```

## 🧪 Étape 3: Tester la Connexion

Une fois la clé publique copiée sur le serveur:

```powershell
# Tester la connexion
ssh -i $env:USERPROFILE\.ssh\freemobila_deploy freemobila@15.236.188.205
```

Si ça fonctionne, vous devriez vous connecter sans mot de passe!

## 🔐 Étape 4: Configurer le Secret GitHub

1. Afficher la clé privée:
   ```powershell
   Get-Content $env:USERPROFILE\.ssh\freemobila_deploy
   ```

2. Copier **TOUT** le contenu (y compris `-----BEGIN` et `-----END`)

3. Dans GitHub:
   - Allez dans **Settings** > **Secrets and variables** > **Actions**
   - Créez un nouveau secret: `SSH_PRIVATE_KEY`
   - Collez le contenu complet de la clé privée

## 📝 Configuration SSH Simplifiée (Optionnel)

Pour éviter de spécifier `-i` à chaque fois, créez/modifiez `~/.ssh/config`:

```powershell
# Créer/modifier le fichier config
notepad $env:USERPROFILE\.ssh\config
```

Ajoutez:

```
Host freemobila-lightsail
    HostName 15.236.188.205
    User freemobila
    IdentityFile ~/.ssh/freemobila_deploy
    IdentitiesOnly yes
```

Ensuite, vous pourrez vous connecter simplement avec:
```powershell
ssh freemobila-lightsail
```

## ✅ Checklist

- [x] Clé SSH générée
- [ ] Clé publique copiée sur le serveur
- [ ] Connexion SSH testée (sans mot de passe)
- [ ] Secret `SSH_PRIVATE_KEY` configuré dans GitHub
- [ ] Workflow GitHub Actions testé

## 🆘 Dépannage

### "Permission denied (publickey)"

- Vérifiez que la clé publique est bien dans `~/.ssh/authorized_keys` sur le serveur
- Vérifiez les permissions: `chmod 600 ~/.ssh/authorized_keys` et `chmod 700 ~/.ssh`
- Vérifiez que l'utilisateur `freemobila` existe sur le serveur

### "Identity file not accessible"

- Vérifiez que le fichier existe: `Test-Path $env:USERPROFILE\.ssh\freemobila_deploy`
- Vérifiez les permissions du fichier

### "Host key verification failed"

- Supprimez l'ancienne entrée: `ssh-keygen -R 15.236.188.205`
- Réessayez la connexion

---

**Date**: $(Get-Date -Format "yyyy-MM-dd")
**Clé générée**: ✅

