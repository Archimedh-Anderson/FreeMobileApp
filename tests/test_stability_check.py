"""
Test de Stabilité et Santé de l'Application
FreeMobilaChat v4.5 Final Edition
"""

import requests
import time
import json
from datetime import datetime
import sys

class StabilityChecker:
    """Vérification complète de la stabilité de l'application"""
    
    def __init__(self, base_url="http://localhost:8502"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "errors": [],
            "warnings": [],
            "score": 0
        }
    
    def check_server_availability(self):
        """Vérifier que le serveur répond"""
        print("\n🔍 Test 1/8: Disponibilité du serveur...")
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("   ✅ Serveur accessible (HTTP 200)")
                self.results["checks"]["server_availability"] = "PASS"
                return True
            else:
                print(f"   ❌ Code HTTP inattendu: {response.status_code}")
                self.results["checks"]["server_availability"] = "FAIL"
                self.results["errors"].append(f"HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            self.results["checks"]["server_availability"] = "ERROR"
            self.results["errors"].append(str(e))
            return False
    
    def check_response_time(self):
        """Vérifier le temps de réponse"""
        print("\n🔍 Test 2/8: Temps de réponse...")
        try:
            start = time.time()
            response = requests.get(self.base_url, timeout=10)
            elapsed = time.time() - start
            
            if elapsed < 5:
                print(f"   ✅ Excellent: {elapsed:.2f}s (< 5s)")
                self.results["checks"]["response_time"] = "EXCELLENT"
            elif elapsed < 10:
                print(f"   ⚠️ Acceptable: {elapsed:.2f}s (5-10s)")
                self.results["checks"]["response_time"] = "ACCEPTABLE"
                self.results["warnings"].append(f"Response time: {elapsed:.2f}s")
            else:
                print(f"   ❌ Lent: {elapsed:.2f}s (> 10s)")
                self.results["checks"]["response_time"] = "SLOW"
                self.results["errors"].append(f"Slow response: {elapsed:.2f}s")
            
            self.results["response_time_seconds"] = round(elapsed, 2)
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            self.results["checks"]["response_time"] = "ERROR"
            self.results["errors"].append(str(e))
            return False
    
    def check_pages_accessibility(self):
        """Vérifier l'accessibilité des pages principales"""
        print("\n🔍 Test 3/8: Accessibilité des pages...")
        pages = [
            "/",
            "/Classification_LLM",
            "/Classification_Mistral"
        ]
        
        accessible_pages = 0
        for page in pages:
            try:
                url = f"{self.base_url}{page}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {page}: Accessible")
                    accessible_pages += 1
                else:
                    print(f"   ❌ {page}: HTTP {response.status_code}")
                    self.results["errors"].append(f"Page {page}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {page}: {str(e)}")
                self.results["errors"].append(f"Page {page}: {str(e)}")
        
        self.results["checks"]["pages_accessibility"] = f"{accessible_pages}/{len(pages)}"
        if accessible_pages == len(pages):
            print(f"\n   ✅ Toutes les pages accessibles ({accessible_pages}/{len(pages)})")
            return True
        else:
            print(f"\n   ⚠️ Certaines pages inaccessibles ({accessible_pages}/{len(pages)})")
            return False
    
    def check_memory_stability(self):
        """Vérifier la stabilité mémoire (requêtes multiples)"""
        print("\n🔍 Test 4/8: Stabilité mémoire (10 requêtes)...")
        try:
            times = []
            for i in range(10):
                start = time.time()
                response = requests.get(self.base_url, timeout=10)
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"   Requête {i+1}/10: {elapsed:.2f}s", end="\r")
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\n   📊 Moyenne: {avg_time:.2f}s | Min: {min_time:.2f}s | Max: {max_time:.2f}s")
            
            if max_time - min_time < 2:
                print("   ✅ Stabilité excellente (variation < 2s)")
                self.results["checks"]["memory_stability"] = "EXCELLENT"
            elif max_time - min_time < 5:
                print("   ⚠️ Stabilité acceptable (variation < 5s)")
                self.results["checks"]["memory_stability"] = "ACCEPTABLE"
                self.results["warnings"].append(f"Variation temps: {max_time - min_time:.2f}s")
            else:
                print("   ❌ Instabilité détectée (variation > 5s)")
                self.results["checks"]["memory_stability"] = "UNSTABLE"
                self.results["errors"].append(f"High variation: {max_time - min_time:.2f}s")
            
            self.results["performance"] = {
                "avg_time": round(avg_time, 2),
                "min_time": round(min_time, 2),
                "max_time": round(max_time, 2),
                "variation": round(max_time - min_time, 2)
            }
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            self.results["checks"]["memory_stability"] = "ERROR"
            self.results["errors"].append(str(e))
            return False
    
    def check_configuration_files(self):
        """Vérifier la présence des fichiers de configuration"""
        print("\n🔍 Test 5/8: Fichiers de configuration...")
        import os
        
        config_files = [
            ".streamlit/config.toml",
            "streamlit_app/.streamlit/config.toml"
        ]
        
        found = 0
        for config in config_files:
            if os.path.exists(config):
                print(f"   ✅ {config}: Présent")
                found += 1
            else:
                print(f"   ⚠️ {config}: Absent")
                self.results["warnings"].append(f"Config missing: {config}")
        
        self.results["checks"]["configuration_files"] = f"{found}/{len(config_files)}"
        return found > 0
    
    def check_critical_imports(self):
        """Vérifier que les imports critiques fonctionnent"""
        print("\n🔍 Test 6/8: Imports critiques...")
        
        critical_modules = [
            "streamlit",
            "pandas",
            "numpy",
            "playwright",
            "pytest"
        ]
        
        working_imports = 0
        for module in critical_modules:
            try:
                __import__(module)
                print(f"   ✅ {module}: OK")
                working_imports += 1
            except ImportError:
                print(f"   ❌ {module}: Non disponible")
                self.results["errors"].append(f"Import error: {module}")
        
        self.results["checks"]["critical_imports"] = f"{working_imports}/{len(critical_modules)}"
        return working_imports == len(critical_modules)
    
    def check_file_structure(self):
        """Vérifier la structure des fichiers"""
        print("\n🔍 Test 7/8: Structure des fichiers...")
        import os
        
        critical_paths = [
            "streamlit_app/app.py",
            "streamlit_app/pages/2_Classification_LLM.py",
            "streamlit_app/pages/5_Classification_Mistral.py",
            "tests/test_html_validation_playwright.py",
            "tests/quick_test.py"
        ]
        
        found = 0
        for path in critical_paths:
            if os.path.exists(path):
                print(f"   ✅ {path}: Présent")
                found += 1
            else:
                print(f"   ❌ {path}: Absent")
                self.results["errors"].append(f"Missing: {path}")
        
        self.results["checks"]["file_structure"] = f"{found}/{len(critical_paths)}"
        return found == len(critical_paths)
    
    def check_documentation(self):
        """Vérifier la présence de la documentation"""
        print("\n🔍 Test 8/8: Documentation...")
        import os
        import glob
        
        doc_patterns = [
            "*.md",
            "tests/*.md",
            "tests/README*.md"
        ]
        
        total_docs = 0
        for pattern in doc_patterns:
            files = glob.glob(pattern, recursive=True)
            total_docs += len(files)
        
        print(f"   📚 Total fichiers documentation: {total_docs}")
        
        if total_docs >= 10:
            print("   ✅ Documentation complète (10+ fichiers)")
            self.results["checks"]["documentation"] = "COMPLETE"
        elif total_docs >= 5:
            print("   ⚠️ Documentation partielle (5-9 fichiers)")
            self.results["checks"]["documentation"] = "PARTIAL"
            self.results["warnings"].append("Documentation partielle")
        else:
            print("   ❌ Documentation insuffisante (< 5 fichiers)")
            self.results["checks"]["documentation"] = "INSUFFICIENT"
            self.results["errors"].append("Documentation insuffisante")
        
        self.results["documentation_count"] = total_docs
        return total_docs >= 5
    
    def calculate_score(self):
        """Calculer le score global de stabilité"""
        checks = self.results["checks"]
        total_checks = len(checks)
        passed_checks = 0
        
        for key, value in checks.items():
            if value in ["PASS", "EXCELLENT", "COMPLETE"]:
                passed_checks += 1
            elif value in ["ACCEPTABLE", "PARTIAL"] or "/" in str(value):
                # Partial credit for acceptable/partial results
                if "/" in str(value):
                    numerator, denominator = value.split("/")
                    passed_checks += float(numerator) / float(denominator)
                else:
                    passed_checks += 0.8
        
        self.results["score"] = round((passed_checks / total_checks) * 100, 2)
        return self.results["score"]
    
    def generate_report(self):
        """Générer le rapport de stabilité"""
        print("\n" + "="*60)
        print("📊 RAPPORT DE STABILITÉ")
        print("="*60)
        
        score = self.calculate_score()
        
        print(f"\n🏆 Score Global: {score}%")
        print(f"❌ Erreurs: {len(self.results['errors'])}")
        print(f"⚠️ Avertissements: {len(self.results['warnings'])}")
        
        if score >= 90:
            status = "🌟 EXCELLENT - Production Ready"
        elif score >= 75:
            status = "✅ BON - Ajustements mineurs recommandés"
        elif score >= 50:
            status = "⚠️ MOYEN - Corrections nécessaires"
        else:
            status = "❌ INSUFFISANT - Corrections urgentes"
        
        print(f"\n{status}")
        
        if self.results["errors"]:
            print("\n❌ ERREURS DÉTECTÉES:")
            for i, error in enumerate(self.results["errors"], 1):
                print(f"   {i}. {error}")
        
        if self.results["warnings"]:
            print("\n⚠️ AVERTISSEMENTS:")
            for i, warning in enumerate(self.results["warnings"], 1):
                print(f"   {i}. {warning}")
        
        # Sauvegarder le rapport JSON
        report_path = f"tests/reports/stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("tests/reports", exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Rapport sauvegardé: {report_path}")
        print("="*60)
        
        return score >= 75  # Retourne True si acceptable
    
    def run_all_checks(self):
        """Exécuter tous les tests de stabilité"""
        print("\n🚀 DÉMARRAGE DES TESTS DE STABILITÉ")
        print("="*60)
        
        self.check_server_availability()
        self.check_response_time()
        self.check_pages_accessibility()
        self.check_memory_stability()
        self.check_configuration_files()
        self.check_critical_imports()
        self.check_file_structure()
        self.check_documentation()
        
        return self.generate_report()


def main():
    """Point d'entrée principal"""
    checker = StabilityChecker()
    
    try:
        success = checker.run_all_checks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()




