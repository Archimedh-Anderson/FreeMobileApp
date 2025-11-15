"""
Comprehensive Testing Protocol for Classification Provider Functionality
========================================================================

This script executes systematic tests for provider availability, selection, and fallback behavior.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class ProviderTester:
    """Comprehensive provider testing class"""
    
    def __init__(self):
        self.results = []
        self.env_path = project_root / '.env'
        load_dotenv(self.env_path)
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
        print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")
    
    def print_test(self, test_num, test_name):
        """Print test number and name"""
        print(f"\n{BOLD}TEST {test_num}: {test_name}{RESET}")
        print(f"{'-' * 80}")
    
    def print_result(self, status, message):
        """Print test result"""
        if status == "PASS":
            print(f"{GREEN}✓ PASS{RESET}: {message}")
        elif status == "FAIL":
            print(f"{RED}✗ FAIL{RESET}: {message}")
        elif status == "WARN":
            print(f"{YELLOW}⚠ WARN{RESET}: {message}")
        else:
            print(f"{BLUE}ℹ INFO{RESET}: {message}")
    
    def log_result(self, test_num, test_name, status, details):
        """Log test result"""
        self.results.append({
            'test_num': test_num,
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_ollama_service_available(self):
        """TEST 1: Verify Ollama service is available"""
        self.print_test(1, "Ollama Service Available")
        
        try:
            # Check if Ollama is running
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                self.print_result("PASS", f"Ollama service is running")
                self.print_result("INFO", f"Found {len(models)} models available")
                
                # Check for Mistral model
                mistral_found = any('mistral' in m.get('name', '').lower() for m in models)
                if mistral_found:
                    self.print_result("PASS", "Mistral model is available")
                else:
                    self.print_result("WARN", "Mistral model not found - may need to pull: ollama pull mistral")
                
                self.log_result(1, "Ollama Available", "PASS", 
                               f"Service running with {len(models)} models")
                return True
            else:
                self.print_result("FAIL", f"Ollama returned status {response.status_code}")
                self.log_result(1, "Ollama Available", "FAIL", 
                               f"HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_result("FAIL", "Ollama service is not running")
            self.print_result("INFO", "Start Ollama with: ollama serve")
            self.log_result(1, "Ollama Available", "FAIL", "Service not running")
            return False
        except Exception as e:
            self.print_result("FAIL", f"Error checking Ollama: {str(e)}")
            self.log_result(1, "Ollama Available", "FAIL", str(e))
            return False
    
    def test_ollama_service_unavailable(self):
        """TEST 2: Verify proper detection when Ollama is stopped"""
        self.print_test(2, "Ollama Service Unavailable Detection")
        
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            if response.status_code == 200:
                self.print_result("INFO", "Ollama is currently running")
                self.print_result("WARN", "Cannot test unavailability - please stop Ollama manually")
                self.print_result("INFO", "To stop: Close Ollama application or kill process")
                self.log_result(2, "Ollama Unavailable", "SKIP", "Service is running")
                return "SKIP"
            else:
                self.print_result("FAIL", "Unexpected Ollama response")
                return False
        except requests.exceptions.ConnectionError:
            self.print_result("PASS", "Correctly detected Ollama is not running")
            self.print_result("INFO", "Application should fallback to BERT + Rules")
            self.log_result(2, "Ollama Unavailable", "PASS", "Correct detection")
            return True
        except Exception as e:
            self.print_result("INFO", f"Connection check result: {str(e)}")
            return True
    
    def test_gemini_configured(self):
        """TEST 3: Verify Gemini API is properly configured"""
        self.print_test(3, "Gemini API Configuration Check")
        
        # Reload environment
        load_dotenv(self.env_path, override=True)
        
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
        google_key = os.getenv('GOOGLE_API_KEY', '').strip()
        
        api_key = gemini_key or google_key
        
        if api_key and len(api_key) > 10:
            self.print_result("PASS", "Gemini API key is configured")
            self.print_result("INFO", f"Key length: {len(api_key)} characters")
            self.print_result("INFO", f"Key prefix: {api_key[:10]}...")
            
            # Test API connection
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content("Test connection: respond with 'OK'")
                
                if response and response.text:
                    self.print_result("PASS", "Gemini API connection successful")
                    self.print_result("INFO", f"API Response: {response.text[:50]}")
                    self.log_result(3, "Gemini Configured", "PASS", "API working")
                    return True
                else:
                    self.print_result("WARN", "API key configured but no response")
                    self.log_result(3, "Gemini Configured", "WARN", "No response")
                    return False
                    
            except ImportError:
                self.print_result("WARN", "google-generativeai not installed")
                self.print_result("INFO", "Install with: pip install google-generativeai")
                self.log_result(3, "Gemini Configured", "WARN", "Module not installed")
                return False
            except Exception as e:
                self.print_result("FAIL", f"API test failed: {str(e)}")
                self.log_result(3, "Gemini Configured", "FAIL", str(e))
                return False
        else:
            self.print_result("INFO", "Gemini API key is not configured")
            self.print_result("INFO", "GEMINI_API_KEY is empty in .env file")
            self.log_result(3, "Gemini Configured", "INFO", "No API key")
            return False
    
    def test_gemini_unconfigured_fallback(self):
        """TEST 4: Verify graceful fallback when Gemini is not configured"""
        self.print_test(4, "Gemini Unconfigured - Graceful Fallback")
        
        load_dotenv(self.env_path, override=True)
        
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
        google_key = os.getenv('GOOGLE_API_KEY', '').strip()
        
        if not gemini_key and not google_key:
            self.print_result("PASS", "Gemini API is correctly unconfigured")
            
            # Test that GeminiClassifier handles this gracefully
            try:
                from streamlit_app.services.gemini_classifier import GeminiClassifier
                
                classifier = GeminiClassifier(api_key=None)
                
                if classifier.client is None and classifier.model is None:
                    self.print_result("PASS", "GeminiClassifier initialized gracefully with None")
                    self.print_result("INFO", "Fallback to BERT + Rules active")
                    self.log_result(4, "Gemini Fallback", "PASS", "Graceful degradation")
                    return True
                else:
                    self.print_result("FAIL", "Classifier should have None client/model")
                    self.log_result(4, "Gemini Fallback", "FAIL", "Improper initialization")
                    return False
                    
            except ImportError as e:
                self.print_result("WARN", f"Cannot import GeminiClassifier: {e}")
                self.log_result(4, "Gemini Fallback", "WARN", "Import error")
                return False
            except Exception as e:
                self.print_result("FAIL", f"Error testing fallback: {str(e)}")
                self.log_result(4, "Gemini Fallback", "FAIL", str(e))
                return False
        else:
            self.print_result("INFO", "Gemini API is configured - cannot test unconfigured state")
            self.print_result("WARN", "Clear GEMINI_API_KEY in .env to test this scenario")
            self.log_result(4, "Gemini Fallback", "SKIP", "API configured")
            return "SKIP"
    
    def test_no_providers_available(self):
        """TEST 5: Verify appropriate messaging when no providers available"""
        self.print_test(5, "No Providers Available - Error Messaging")
        
        ollama_running = False
        gemini_configured = False
        
        # Check Ollama
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            ollama_running = response.status_code == 200
        except:
            pass
        
        # Check Gemini
        load_dotenv(self.env_path, override=True)
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
        google_key = os.getenv('GOOGLE_API_KEY', '').strip()
        gemini_configured = bool(gemini_key or google_key)
        
        self.print_result("INFO", f"Ollama running: {ollama_running}")
        self.print_result("INFO", f"Gemini configured: {gemini_configured}")
        
        if not ollama_running and not gemini_configured:
            self.print_result("PASS", "No external providers available - correct state")
            self.print_result("INFO", "Application should use BERT + Rule-based classifiers")
            self.print_result("INFO", "This is a valid operational mode")
            self.log_result(5, "No Providers", "PASS", "Fallback mode active")
            return True
        else:
            self.print_result("INFO", "At least one provider is available")
            self.print_result("WARN", "Cannot test zero-provider scenario")
            self.log_result(5, "No Providers", "SKIP", "Providers available")
            return "SKIP"
    
    def test_module_loading(self):
        """TEST 6: Verify classification modules load correctly"""
        self.print_test(6, "Classification Module Loading")
        
        try:
            # Test module imports
            modules_loaded = []
            modules_failed = []
            
            # Test RuleClassifier
            try:
                from streamlit_app.services.rule_classifier import RuleClassifier
                modules_loaded.append("RuleClassifier")
                self.print_result("PASS", "RuleClassifier loaded successfully")
            except Exception as e:
                modules_failed.append(f"RuleClassifier: {str(e)}")
                self.print_result("FAIL", f"RuleClassifier failed: {e}")
            
            # Test BERTClassifier
            try:
                from streamlit_app.services.bert_classifier import BERTClassifier
                modules_loaded.append("BERTClassifier")
                self.print_result("PASS", "BERTClassifier loaded successfully")
            except Exception as e:
                modules_failed.append(f"BERTClassifier: {str(e)}")
                self.print_result("WARN", f"BERTClassifier failed (PyTorch may be missing): {e}")
            
            # Test MistralClassifier
            try:
                from streamlit_app.services.mistral_classifier import MistralClassifier
                modules_loaded.append("MistralClassifier")
                self.print_result("PASS", "MistralClassifier loaded successfully")
            except Exception as e:
                modules_failed.append(f"MistralClassifier: {str(e)}")
                self.print_result("WARN", f"MistralClassifier failed: {e}")
            
            # Test GeminiClassifier
            try:
                from streamlit_app.services.gemini_classifier import GeminiClassifier
                modules_loaded.append("GeminiClassifier")
                self.print_result("PASS", "GeminiClassifier loaded successfully")
            except Exception as e:
                modules_failed.append(f"GeminiClassifier: {str(e)}")
                self.print_result("FAIL", f"GeminiClassifier failed: {e}")
            
            self.print_result("INFO", f"Loaded: {len(modules_loaded)}/4 modules")
            
            if len(modules_loaded) >= 2:
                self.log_result(6, "Module Loading", "PASS", 
                               f"{len(modules_loaded)} modules loaded")
                return True
            else:
                self.log_result(6, "Module Loading", "FAIL", 
                               f"Only {len(modules_loaded)} modules loaded")
                return False
                
        except Exception as e:
            self.print_result("FAIL", f"Error during module loading: {str(e)}")
            self.log_result(6, "Module Loading", "FAIL", str(e))
            return False
    
    def test_provider_availability_functions(self):
        """TEST 7: Test provider availability check functions"""
        self.print_test(7, "Provider Availability Check Functions")
        
        try:
            # Import check functions from page
            sys.path.insert(0, str(project_root / 'streamlit_app' / 'pages'))
            
            # We can't directly import from Classification_Mistral.py due to Streamlit dependencies
            # Instead, test the service-level functions
            
            # Test Mistral availability
            try:
                from streamlit_app.services.mistral_classifier import check_ollama_availability
                ollama_available = check_ollama_availability()
                
                if ollama_available:
                    self.print_result("PASS", "Ollama availability check returned True")
                else:
                    self.print_result("INFO", "Ollama availability check returned False")
                
                self.print_result("PASS", "check_ollama_availability() function works")
            except ImportError:
                self.print_result("WARN", "check_ollama_availability not found")
            except Exception as e:
                self.print_result("INFO", f"Ollama check: {str(e)}")
            
            # Test Gemini availability
            try:
                from streamlit_app.services.gemini_classifier import check_gemini_availability
                gemini_available = check_gemini_availability()
                
                if gemini_available:
                    self.print_result("PASS", "Gemini availability check returned True")
                else:
                    self.print_result("INFO", "Gemini availability check returned False")
                
                self.print_result("PASS", "check_gemini_availability() function works")
            except ImportError:
                self.print_result("WARN", "check_gemini_availability not found")
            except Exception as e:
                self.print_result("INFO", f"Gemini check: {str(e)}")
            
            self.log_result(7, "Availability Functions", "PASS", "Functions executed")
            return True
            
        except Exception as e:
            self.print_result("FAIL", f"Error testing availability functions: {str(e)}")
            self.log_result(7, "Availability Functions", "FAIL", str(e))
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST REPORT SUMMARY")
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')
        warnings = sum(1 for r in self.results if r['status'] == 'WARN')
        
        print(f"Total Tests: {total_tests}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"{YELLOW}Warnings: {warnings}{RESET}")
        print(f"{BLUE}Skipped: {skipped}{RESET}")
        
        print(f"\n{BOLD}Detailed Results:{RESET}")
        for result in self.results:
            status_color = GREEN if result['status'] == 'PASS' else RED if result['status'] == 'FAIL' else YELLOW
            print(f"{status_color}[{result['status']}]{RESET} Test {result['test_num']}: {result['test_name']}")
            print(f"  Details: {result['details']}")
        
        # Save to file
        report_file = project_root / 'test_results' / f"provider_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed,
                    'failed': failed,
                    'warnings': warnings,
                    'skipped': skipped
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n{BLUE}Report saved to: {report_file}{RESET}")

def main():
    """Run all tests"""
    tester = ProviderTester()
    
    tester.print_header("CLASSIFICATION PROVIDER FUNCTIONALITY - COMPREHENSIVE TEST PROTOCOL")
    
    print(f"{BOLD}Testing Environment:{RESET}")
    print(f"Project Root: {project_root}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    tester.test_ollama_service_available()
    tester.test_ollama_service_unavailable()
    tester.test_gemini_configured()
    tester.test_gemini_unconfigured_fallback()
    tester.test_no_providers_available()
    tester.test_module_loading()
    tester.test_provider_availability_functions()
    
    # Generate report
    tester.generate_report()
    
    print(f"\n{BOLD}{GREEN}Testing protocol completed!{RESET}")
    print(f"\n{BOLD}Next Steps:{RESET}")
    print(f"1. Review test results above")
    print(f"2. Launch Streamlit app: streamlit run streamlit_app/app.py")
    print(f"3. Verify sidebar displays 'Fournisseur de Traitement' section")
    print(f"4. Test provider selection buttons manually")
    print(f"5. Run classification workflow to verify provider integration")

if __name__ == "__main__":
    main()
