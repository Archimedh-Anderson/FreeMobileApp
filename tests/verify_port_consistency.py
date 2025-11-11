"""
Script de vérification de la cohérence du port Streamlit
Vérifie que tous les fichiers utilisent le port 8502
"""

import re
from pathlib import Path
from typing import List, Tuple


def find_port_references(directory: Path, port: int) -> List[Tuple[str, int, str]]:
    """Trouve toutes les références à un port dans les fichiers"""
    references = []
    port_pattern = re.compile(rf'\b{port}\b')
    
    # Fichiers à vérifier
    files_to_check = [
        ".streamlit/config.toml",
        "tests/quick_test.py",
        "tests/test_html_validation_playwright.py",
        "tests/test_stability_check.py",
        "tests/setup_and_run_tests.ps1",
        "tests/test_streamlit_deployment.py",
        "Procfile"
    ]
    
    for file_path in files_to_check:
        full_path = directory / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        if port_pattern.search(line):
                            references.append((str(full_path), line_num, line.strip()))
            except Exception as e:
                print(f"⚠️  Erreur lecture {full_path}: {e}")
    
    return references


def verify_port_consistency():
    """Vérifie la cohérence du port dans tous les fichiers"""
    print("🔍 Vérification de la cohérence du port Streamlit\n")
    print("=" * 70)
    
    repo_path = Path.cwd()
    expected_port = 8502
    
    # Trouver toutes les références aux ports
    port_8501_refs = find_port_references(repo_path, 8501)
    port_8502_refs = find_port_references(repo_path, 8502)
    
    print(f"\n📊 Références trouvées:")
    print(f"   Port 8501: {len(port_8501_refs)} référence(s)")
    print(f"   Port 8502: {len(port_8502_refs)} référence(s)")
    
    # Vérifier le fichier de configuration principal
    config_path = repo_path / ".streamlit" / "config.toml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
            if f"port = {expected_port}" in config_content:
                print(f"\n✅ .streamlit/config.toml utilise le port {expected_port}")
            else:
                print(f"\n❌ .streamlit/config.toml n'utilise PAS le port {expected_port}")
                if "port = 8501" in config_content:
                    print("   ⚠️  Port trouvé: 8501 (incorrect)")
    
    # Afficher les références au port incorrect
    if port_8501_refs:
        print(f"\n⚠️  Fichiers utilisant le port 8501 (incorrect):")
        for file_path, line_num, line_content in port_8501_refs:
            # Ignorer les commentaires et les tests qui vérifient les deux ports
            if "8501" in line_content and "8502" not in line_content and not line_content.strip().startswith("#"):
                print(f"   • {file_path}:{line_num}")
                print(f"     {line_content[:80]}")
    
    # Vérifier que tous les fichiers de test utilisent 8502
    test_files = [
        "tests/quick_test.py",
        "tests/test_html_validation_playwright.py",
        "tests/test_stability_check.py",
        "tests/setup_and_run_tests.ps1"
    ]
    
    print(f"\n📋 Vérification des fichiers de test:")
    all_correct = True
    
    for test_file in test_files:
        test_path = repo_path / test_file
        if test_path.exists():
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if f":8502" in content or f"port=8502" in content or f"port=8502" in content:
                    print(f"   ✅ {test_file} utilise le port 8502")
                elif ":8501" in content or "port=8501" in content:
                    print(f"   ❌ {test_file} utilise le port 8501 (incorrect)")
                    all_correct = False
                else:
                    print(f"   ⚠️  {test_file} ne contient pas de référence explicite au port")
        else:
            print(f"   ⚠️  {test_file} non trouvé")
    
    print("\n" + "=" * 70)
    
    if port_8501_refs and not all_correct:
        print("❌ INCOHÉRENCE DÉTECTÉE: Certains fichiers utilisent encore le port 8501")
        print("   Le port correct est 8502 pour le développement local")
        return False
    else:
        print("✅ COHÉRENCE CONFIRMÉE: Tous les fichiers utilisent le port 8502")
        return True


if __name__ == "__main__":
    import sys
    success = verify_port_consistency()
    sys.exit(0 if success else 1)

