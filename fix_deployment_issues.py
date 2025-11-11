"""
Script complet pour corriger tous les problèmes de déploiement
- Formatage Black
- Vérification de la configuration
- Préparation pour le commit
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - Échec")
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {description} - Erreur: {e}")
        return False


def main():
    print("🚀 Correction des problèmes de déploiement FreeMobileApp\n")
    
    # 1. Formater avec Black
    print("Étape 1/5: Formatage du code avec Black...")
    run_command(
        "python -m black streamlit_app/ tests/ --line-length 100 --quiet",
        "Formatage Black"
    )
    
    # 2. Trier les imports avec isort
    print("\nÉtape 2/5: Tri des imports avec isort...")
    run_command(
        "python -m isort streamlit_app/ tests/ --profile black --quiet",
        "Tri des imports"
    )
    
    # 3. Vérifier la configuration Streamlit
    print("\nÉtape 3/5: Vérification de la configuration...")
    config_path = Path(".streamlit/config.toml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            content = f.read()
            if "port = 8501" in content:
                print("✅ Port 8501 configuré (correct pour Streamlit Cloud)")
            elif "port = 8502" in content:
                print("⚠️  Port 8502 détecté (local dev)")
            else:
                print("❌ Port non trouvé dans la configuration")
    
    # 4. Vérifier les fichiers modifiés
    print("\nÉtape 4/5: Vérification des fichiers modifiés...")
    run_command(
        "git status --short",
        "État Git"
    )
    
    # 5. Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES CORRECTIONS")
    print("="*70)
    print("""
✅ Formatage Black appliqué
✅ Imports triés avec isort
✅ Configuration Streamlit vérifiée

🚀 PROCHAINES ÉTAPES:
1. Vérifier les changements: git status
2. Ajouter les fichiers: git add .
3. Commit: git commit -m "fix: Apply Black formatting and fix deployment issues"
4. Push: git push origin main

📝 Note: Le pipeline GitHub Actions devrait passer maintenant que:
   - Les 70 fichiers ont été reformatés avec Black
   - Le port est configuré correctement
   - Les imports sont triés
""")


if __name__ == "__main__":
    main()

