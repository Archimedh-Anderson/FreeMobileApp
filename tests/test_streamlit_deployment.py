"""
TestSprite - Streamlit Cloud Deployment Diagnostic & Fix Tool
============================================================

Script complet pour diagnostiquer et corriger les erreurs de déploiement
sur Streamlit Cloud. Vérifie tous les aspects critiques du déploiement.
"""

import os
import sys
import subprocess
import json
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class StreamlitDeploymentTester:
    """Classe principale pour tester et corriger le déploiement Streamlit Cloud"""
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.streamlit_app_path = self.repo_path / "streamlit_app"
        self.app_py_path = self.streamlit_app_path / "app.py"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "fixes": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
    
    def _add_test_result(self, name: str, passed: bool, message: str, fix: Optional[str] = None):
        """Ajoute un résultat de test"""
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "message": message
        })
        self.results["summary"]["total"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
            self.results["summary"]["errors"].append(f"{name}: {message}")
            if fix:
                self.results["fixes"].append({"test": name, "fix": fix})
    
    def test_streamlit_app_exists(self) -> bool:
        """Test 1: Vérifie que streamlit_app/app.py existe"""
        test_name = "Streamlit App File Exists"
        
        if self.app_py_path.exists():
            self._add_test_result(test_name, True, f"app.py found at {self.app_py_path}")
            return True
        else:
            self._add_test_result(
                test_name, 
                False, 
                f"app.py not found at {self.app_py_path}",
                "Create streamlit_app/app.py file"
            )
            return False
    
    def test_app_py_syntax(self) -> bool:
        """Test 2: Vérifie la syntaxe Python de app.py"""
        test_name = "app.py Syntax Valid"
        
        if not self.app_py_path.exists():
            return False
        
        try:
            with open(self.app_py_path, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code)
            self._add_test_result(test_name, True, "app.py syntax is valid")
            return True
        except SyntaxError as e:
            self._add_test_result(
                test_name,
                False,
                f"Syntax error in app.py: {str(e)}",
                f"Fix syntax error at line {e.lineno}: {e.msg}"
            )
            return False
        except Exception as e:
            self._add_test_result(
                test_name,
                False,
                f"Error parsing app.py: {str(e)}",
                "Check app.py for errors"
            )
            return False
    
    def test_main_function_exists(self) -> bool:
        """Test 3: Vérifie que la fonction main() existe"""
        test_name = "main() Function Exists"
        
        if not self.app_py_path.exists():
            return False
        
        try:
            with open(self.app_py_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            has_main = any(
                isinstance(node, ast.FunctionDef) and node.name == "main"
                for node in ast.walk(tree)
            )
            
            has_main_call = "__name__" in code and "__main__" in code and "main()" in code
            
            if has_main and has_main_call:
                self._add_test_result(test_name, True, "main() function exists and is called")
                return True
            else:
                self._add_test_result(
                    test_name,
                    False,
                    "main() function missing or not called",
                    "Add 'def main():' function and 'if __name__ == \"__main__\": main()' at end of file"
                )
                return False
        except Exception as e:
            self._add_test_result(
                test_name,
                False,
                f"Error checking main(): {str(e)}",
                "Verify app.py structure"
            )
            return False
    
    def test_imports_valid(self) -> bool:
        """Test 4: Vérifie que les imports sont valides"""
        test_name = "Imports Valid"
        
        if not self.app_py_path.exists():
            return False
        
        try:
            with open(self.app_py_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    imports.extend([f"{module}.{alias.name}" for alias in node.names])
            
            # Vérifier les imports critiques
            critical_imports = ["streamlit", "services.auth_service", "components.auth_forms"]
            missing_imports = []
            
            for imp in critical_imports:
                if imp not in code:
                    missing_imports.append(imp)
            
            if not missing_imports:
                self._add_test_result(test_name, True, "All critical imports present")
                return True
            else:
                self._add_test_result(
                    test_name,
                    False,
                    f"Missing imports: {', '.join(missing_imports)}",
                    f"Add missing imports: {', '.join(missing_imports)}"
                )
                return False
        except Exception as e:
            self._add_test_result(
                test_name,
                False,
                f"Error checking imports: {str(e)}",
                "Verify import statements"
            )
            return False
    
    def test_streamlit_config_exists(self) -> bool:
        """Test 5: Vérifie que .streamlit/config.toml existe"""
        test_name = "Streamlit Config Exists"
        
        config_path = self.repo_path / ".streamlit" / "config.toml"
        
        if config_path.exists():
            self._add_test_result(test_name, True, f"config.toml found at {config_path}")
            return True
        else:
            self._add_test_result(
                test_name,
                False,
                ".streamlit/config.toml not found",
                "Create .streamlit/config.toml with proper configuration"
            )
            return False
    
    def test_requirements_txt_exists(self) -> bool:
        """Test 6: Vérifie que requirements.txt existe"""
        test_name = "Requirements.txt Exists"
        
        req_path = self.streamlit_app_path / "requirements.txt"
        
        if req_path.exists():
            self._add_test_result(test_name, True, f"requirements.txt found at {req_path}")
            return True
        else:
            self._add_test_result(
                test_name,
                False,
                "streamlit_app/requirements.txt not found",
                "Create streamlit_app/requirements.txt with dependencies"
            )
            return False
    
    def test_requirements_content(self) -> bool:
        """Test 7: Vérifie le contenu de requirements.txt"""
        test_name = "Requirements.txt Content Valid"
        
        req_path = self.streamlit_app_path / "requirements.txt"
        
        if not req_path.exists():
            return False
        
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_packages = ["streamlit", "pandas"]
            missing = [pkg for pkg in required_packages if pkg not in content.lower()]
            
            if not missing:
                self._add_test_result(test_name, True, "requirements.txt contains required packages")
                return True
            else:
                self._add_test_result(
                    test_name,
                    False,
                    f"Missing packages in requirements.txt: {', '.join(missing)}",
                    f"Add missing packages to requirements.txt: {', '.join(missing)}"
                )
                return False
        except Exception as e:
            self._add_test_result(
                test_name,
                False,
                f"Error reading requirements.txt: {str(e)}",
                "Check requirements.txt file"
            )
            return False
    
    def test_set_page_config(self) -> bool:
        """Test 8: Vérifie que st.set_page_config est appelé"""
        test_name = "set_page_config Called"
        
        if not self.app_py_path.exists():
            return False
        
        try:
            with open(self.app_py_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if "st.set_page_config" in code:
                self._add_test_result(test_name, True, "st.set_page_config is called")
                return True
            else:
                self._add_test_result(
                    test_name,
                    False,
                    "st.set_page_config not found",
                    "Add st.set_page_config() call at the beginning of app.py"
                )
                return False
        except Exception as e:
            self._add_test_result(
                test_name,
                False,
                f"Error checking set_page_config: {str(e)}",
                "Verify app.py structure"
            )
            return False
    
    def test_no_hardcoded_localhost(self) -> bool:
        """Test 9: Vérifie qu'il n'y a pas de localhost hardcodé"""
        test_name = "No Hardcoded Localhost"
        
        # Vérifier dans auth_service.py
        auth_service_path = self.streamlit_app_path / "services" / "auth_service.py"
        
        if auth_service_path.exists():
            try:
                with open(auth_service_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Vérifier si localhost est hardcodé (pas dans os.getenv)
                has_hardcoded = (
                    ('BACKEND_URL = "http://localhost:8000"' in content and 'os.getenv' not in content) or
                    ('BACKEND_URL = \'http://localhost:8000\'' in content and 'os.getenv' not in content)
                )
                
                if has_hardcoded:
                    self._add_test_result(
                        test_name,
                        False,
                        "Hardcoded localhost found in auth_service.py",
                        "Replace localhost with environment variable or remove backend dependency for Streamlit Cloud"
                    )
                    return False
                else:
                    self._add_test_result(test_name, True, "No hardcoded localhost found (using environment variable)")
                    return True
            except Exception as e:
                self._add_test_result(
                    test_name,
                    False,
                    f"Error checking auth_service.py: {str(e)}",
                    "Verify auth_service.py configuration"
                )
                return False
        else:
            self._add_test_result(test_name, True, "auth_service.py not found, skipping check")
            return True
    
    def test_procfile_exists(self) -> bool:
        """Test 10: Vérifie que Procfile existe (optionnel pour Streamlit Cloud)"""
        test_name = "Procfile Exists"
        
        procfile_path = self.repo_path / "Procfile"
        
        if procfile_path.exists():
            self._add_test_result(test_name, True, "Procfile found (optional for Streamlit Cloud)")
            return True
        else:
            self._add_test_result(
                test_name,
                True,  # Pas critique pour Streamlit Cloud
                "Procfile not found (optional for Streamlit Cloud)"
            )
            return True
    
    def run_all_tests(self) -> Dict:
        """Exécute tous les tests"""
        print("🧪 TestSprite - Streamlit Cloud Deployment Diagnostic\n")
        print("=" * 70)
        
        # Exécuter tous les tests
        self.test_streamlit_app_exists()
        self.test_app_py_syntax()
        self.test_main_function_exists()
        self.test_imports_valid()
        self.test_streamlit_config_exists()
        self.test_requirements_txt_exists()
        self.test_requirements_content()
        self.test_set_page_config()
        self.test_no_hardcoded_localhost()
        self.test_procfile_exists()
        
        # Afficher les résultats
        self._print_results()
        
        # Appliquer les corrections
        if self.results["summary"]["failed"] > 0:
            print("\n" + "=" * 70)
            print("🔧 APPLYING FIXES...")
            print("=" * 70)
            self._apply_fixes()
        
        # Sauvegarder le rapport
        self._save_report()
        
        return self.results
    
    def _print_results(self):
        """Affiche les résultats des tests"""
        print("\n" + "=" * 70)
        print("📊 RÉSULTATS DES TESTS")
        print("=" * 70 + "\n")
        
        for test in self.results["tests"]:
            status = "✅" if test["passed"] else "❌"
            print(f"{status} {test['name']}")
            if not test["passed"]:
                print(f"   ⚠️  {test['message']}")
        
        print("\n" + "=" * 70)
        print("📈 RÉSUMÉ")
        print("=" * 70)
        summary = self.results["summary"]
        print(f"Total de tests: {summary['total']}")
        print(f"✅ Réussis: {summary['passed']}")
        print(f"❌ Échoués: {summary['failed']}")
        
        if summary['failed'] == 0:
            print("\n🎉 Tous les tests sont passés!")
        else:
            print(f"\n⚠️  {summary['failed']} test(s) ont échoué")
            print("\nErreurs détectées:")
            for error in summary['errors']:
                print(f"  • {error}")
        
        print("=" * 70)
    
    def _apply_fixes(self):
        """Applique les corrections automatiques"""
        fixes_applied = []
        
        for fix_info in self.results["fixes"]:
            test_name = fix_info["test"]
            fix = fix_info["fix"]
            
            print(f"\n🔧 Fixing: {test_name}")
            print(f"   Action: {fix}")
            
            # Appliquer les corrections spécifiques
            if "config.toml" in fix:
                self._create_streamlit_config()
                fixes_applied.append("Created .streamlit/config.toml")
            
            if "auth_service.py" in fix and "localhost" in fix:
                self._fix_localhost_in_auth_service()
                fixes_applied.append("Fixed localhost in auth_service.py")
        
        if fixes_applied:
            print("\n✅ Fixes applied:")
            for fix in fixes_applied:
                print(f"   • {fix}")
        else:
            print("\n⚠️  Some fixes require manual intervention")
    
    def _create_streamlit_config(self):
        """Crée le fichier .streamlit/config.toml"""
        config_dir = self.repo_path / ".streamlit"
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "config.toml"
        
        config_content = """[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#CC0000"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"   ✅ Created {config_path}")
    
    def _fix_localhost_in_auth_service(self):
        """Corrige les références localhost dans auth_service.py"""
        auth_service_path = self.streamlit_app_path / "services" / "auth_service.py"
        
        if not auth_service_path.exists():
            return
        
        try:
            with open(auth_service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer localhost par une variable d'environnement
            import re
            content = re.sub(
                r'BACKEND_URL\s*=\s*["\']http://localhost:8000["\']',
                'BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")',
                content
            )
            
            # Ajouter l'import os si nécessaire
            if "import os" not in content and "BACKEND_URL" in content:
                # Trouver la première ligne d'import
                lines = content.split('\n')
                import_idx = next((i for i, line in enumerate(lines) if line.startswith('import ') or line.startswith('from ')), 0)
                lines.insert(import_idx, "import os")
                content = '\n'.join(lines)
            
            with open(auth_service_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ Fixed {auth_service_path}")
        except Exception as e:
            print(f"   ⚠️  Error fixing auth_service.py: {str(e)}")
    
    def _save_report(self):
        """Sauvegarde le rapport JSON"""
        report_path = self.repo_path / "tests" / "streamlit_deployment_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport sauvegardé: {report_path}")


def main():
    """Point d'entrée principal"""
    tester = StreamlitDeploymentTester()
    results = tester.run_all_tests()
    
    # Code de sortie basé sur les résultats
    exit_code = 0 if results["summary"]["failed"] == 0 else 1
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())

