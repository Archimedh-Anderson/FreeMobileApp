# Guide de Configuration Locale - FreeMobilaChat

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git (optionnel)

## 🚀 Installation Rapide

### Windows

1. **Créer et activer l'environnement virtuel :**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Installer les dépendances :**
   ```bash
   pip install -r streamlit_app\requirements.txt
   ```

3. **Configurer les variables d'environnement :**
   - Le fichier `.env` existe déjà à la racine
   - Vérifiez qu'il contient vos clés API :
     ```
     GEMINI_API_KEY=votre_cle_gemini
     MISTRAL_API_KEY=votre_cle_mistral (optionnel)
     OLLAMA_BASE_URL=http://localhost:11434 (pour Mistral local)
     ```

4. **Lancer l'application :**
   ```bash
   streamlit run streamlit_app\app.py --server.port 8502
   ```
   
   Ou utilisez le script automatique :
   ```bash
   start_app.bat
   ```

### Linux/Mac

1. **Créer et activer l'environnement virtuel :**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Installer les dépendances :**
   ```bash
   pip install -r streamlit_app/requirements.txt
   ```

3. **Configurer les variables d'environnement :**
   - Le fichier `.env` existe déjà à la racine
   - Vérifiez qu'il contient vos clés API

4. **Lancer l'application :**
   ```bash
   streamlit run streamlit_app/app.py --server.port 8502
   ```
   
   Ou utilisez le script automatique :
   ```bash
   chmod +x start_app.sh
   ./start_app.sh
   ```

## ⚙️ Configuration

### Fichier `.env`

Le fichier `.env` doit contenir :

```env
ENV=development
PORT=8502
HOST=localhost
DOMAIN=localhost

# Clés API (à remplacer par vos vraies clés)
MISTRAL_API_KEY=votre_cle_mistral
GEMINI_API_KEY=votre_cle_gemini
OLLAMA_BASE_URL=http://localhost:11434
```

### Fichier `.streamlit/config.toml`

La configuration Streamlit est déjà configurée :
- Port : 8502
- Address : localhost
- CORS : désactivé
- Protection XSRF : activée

## 🔧 Scripts Disponibles

### `setup_local.bat` / `setup_local.sh`
Script de configuration automatique qui :
- Crée l'environnement virtuel si nécessaire
- Installe toutes les dépendances
- Crée le fichier `.env` avec un template si absent
- Vérifie la configuration

### `start_app.bat` / `start_app.sh`
Script de démarrage qui :
- Active l'environnement virtuel
- Vérifie les dépendances
- Lance l'application sur `http://localhost:8502`

## 🐛 Dépannage

### L'application ne démarre pas

1. **Vérifier Python :**
   ```bash
   python --version  # Doit être 3.8+
   ```

2. **Vérifier le venv :**
   ```bash
   # Windows
   venv\Scripts\python.exe --version
   
   # Linux/Mac
   venv/bin/python --version
   ```

3. **Réinstaller les dépendances :**
   ```bash
   pip install --upgrade pip
   pip install -r streamlit_app/requirements.txt --force-reinstall
   ```

### Erreurs d'import de modules

1. **Vérifier que vous êtes dans le bon répertoire :**
   ```bash
   cd C:\Users\ander\Desktop\FreeMobilaChat
   ```

2. **Vérifier que le venv est activé :**
   - Windows : `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`

### Erreurs avec les clés API

1. **Vérifier le fichier `.env` :**
   - Le fichier doit être à la racine du projet
   - Les clés doivent être au format `KEY=value` (sans espaces)

2. **Vérifier les variables d'environnement :**
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
   ```

### Port 8502 déjà utilisé

1. **Changer le port dans `.streamlit/config.toml` :**
   ```toml
   [server]
   port = 8503
   ```

2. **Ou libérer le port :**
   ```bash
   # Windows
   netstat -ano | findstr :8502
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:8502 | xargs kill -9
   ```

## 📊 Vérification

Une fois l'application lancée, vous devriez voir :

1. **Page d'accueil** : `http://localhost:8502`
   - Interface de connexion/inscription
   - Accès à la classification

2. **Page de classification** : `http://localhost:8502/Classification_Mistral`
   - Upload de fichiers CSV
   - Sélection du provider (Mistral/Gemini)
   - Classification des tweets
   - Visualisation des KPIs

## 🔄 Mise à jour depuis Git

```bash
git pull origin main
pip install -r streamlit_app/requirements.txt --upgrade
```

## 📝 Notes Importantes

- **Mode développement** : L'application est en mode `development` par défaut (voir `.env`)
- **Données locales** : Les fichiers uploadés sont stockés dans `uploads/remote/`
- **Logs** : Les logs sont disponibles dans le terminal où l'application tourne
- **Cache** : Le cache Streamlit est dans `.streamlit/`

## 🎯 Pour la Soutenance

1. **Tester toutes les fonctionnalités** :
   - Upload de CSV
   - Classification avec Mistral (local)
   - Classification avec Gemini (API)
   - Visualisation des KPIs
   - Export des résultats

2. **Préparer des données de test** :
   - CSV avec des tweets Free Mobile
   - Données variées (positif/négatif/neutre)
   - Différents types d'incidents

3. **Vérifier la stabilité** :
   - Lancer plusieurs classifications
   - Vérifier les KPIs
   - Tester l'export

## 🆘 Support

En cas de problème, vérifiez :
1. Les logs dans le terminal
2. Le fichier `.env` est correctement configuré
3. Toutes les dépendances sont installées
4. Le port 8502 est libre

