"""
FreeMobilaChat - System Diagnostics
Checks all classification modules and API configurations
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"✗ .env file not found at: {env_path}")

print("\n" + "="*70)
print("FREEMOBILACHAT - SYSTEM DIAGNOSTICS")
print("="*70)

# Add streamlit_app to path
streamlit_app_path = Path(__file__).parent / 'streamlit_app'
sys.path.insert(0, str(streamlit_app_path))

print("\n[1] CHECKING ENVIRONMENT VARIABLES")
print("-"*70)

env_vars = {
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
    'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL'),
    'OLLAMA_AVAILABLE': os.getenv('OLLAMA_AVAILABLE'),
    'OFFLINE_MODE': os.getenv('OFFLINE_MODE'),
    'BERT_MODEL': os.getenv('BERT_MODEL'),
}

for key, value in env_vars.items():
    if value:
        if 'API_KEY' in key:
            masked_value = value[:10] + '...' if len(value) > 10 else '[SET]'
            print(f"  ✓ {key:20s} = {masked_value}")
        else:
            print(f"  ✓ {key:20s} = {value}")
    else:
        print(f"  ✗ {key:20s} = [NOT SET]")

print("\n[2] CHECKING PYTHON DEPENDENCIES")
print("-"*70)

dependencies = {
    'streamlit': 'Streamlit framework',
    'pandas': 'Data processing',
    'numpy': 'Numerical computing',
    'plotly': 'Visualization',
    'torch': 'PyTorch (for BERT)',
    'transformers': 'Hugging Face Transformers',
    'ollama': 'Ollama client',
    'google.generativeai': 'Google Gemini API',
    'dotenv': 'Environment variables',
}

for module_name, description in dependencies.items():
    try:
        __import__(module_name.replace('.', '/'))
        print(f"  ✓ {module_name:25s} - {description}")
    except ImportError:
        print(f"  ✗ {module_name:25s} - {description} [NOT INSTALLED]")

print("\n[3] CHECKING CLASSIFICATION MODULES")
print("-"*70)

modules_to_check = [
    ('services.tweet_cleaner', 'TweetCleaner'),
    ('services.rule_classifier', 'EnhancedRuleClassifier'),
    ('services.bert_classifier', 'BERTClassifier'),
    ('services.mistral_classifier', 'MistralClassifier'),
    ('services.gemini_classifier', 'GeminiClassifier'),
    ('services.multi_model_orchestrator', 'MultiModelOrchestrator'),
]

for module_path, class_name in modules_to_check:
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"  ✓ {class_name:30s} - Module loaded successfully")
    except ImportError as e:
        print(f"  ✗ {class_name:30s} - Import error: {str(e)[:50]}")
    except Exception as e:
        print(f"  ⚠ {class_name:30s} - Warning: {str(e)[:50]}")

print("\n[4] CHECKING API CONNECTIVITY")
print("-"*70)

# Check Ollama
print("\n  Ollama (Mistral LLM):")
try:
    from services.mistral_classifier import check_ollama_availability
    if check_ollama_availability():
        print("    ✓ Ollama service is running and accessible")
        try:
            from services.mistral_classifier import list_available_models
            models = list_available_models()
            print(f"    ✓ Available models: {', '.join(models[:3])}")
        except Exception as e:
            print(f"    ⚠ Could not list models: {e}")
    else:
        print("    ✗ Ollama service not running")
        print("    → Start with: ollama serve")
except Exception as e:
    print(f"    ✗ Error checking Ollama: {e}")

# Check Gemini
print("\n  Google Gemini API:")
try:
    from services.gemini_classifier import check_gemini_availability
    if check_gemini_availability():
        print("    ✓ Gemini API key is configured and valid")
    else:
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("    ✗ Gemini API key not configured")
            print("    → Get your key from: https://aistudio.google.com/app/apikey")
            print("    → Add to .env: GEMINI_API_KEY=your_key_here")
        else:
            print("    ⚠ API key configured but validation failed")
            print("    → Check if the key is valid")
except Exception as e:
    print(f"    ✗ Error checking Gemini: {e}")

# Check BERT
print("\n  BERT Classifier (PyTorch):")
try:
    import torch
    from services.bert_classifier import TORCH_AVAILABLE
    if TORCH_AVAILABLE:
        print(f"    ✓ PyTorch available (version {torch.__version__})")
        print(f"    ✓ CUDA available: {torch.cuda.is_available()}")
    else:
        print("    ✗ PyTorch not properly configured")
except ImportError:
    print("    ✗ PyTorch not installed")
    print("    → Install with: pip install torch transformers")
except Exception as e:
    print(f"    ⚠ Error: {e}")

print("\n[5] SYSTEM STATUS SUMMARY")
print("-"*70)

# Count available services
services_available = 0
services_total = 3

# Rule-based classifier (always available)
print("  ✓ Rule-based Classifier: Always available")
services_available += 1

# Check BERT
try:
    from services.bert_classifier import TORCH_AVAILABLE
    if TORCH_AVAILABLE:
        print("  ✓ BERT Classifier: Available")
        services_available += 1
    else:
        print("  ✗ BERT Classifier: PyTorch not installed")
except:
    print("  ✗ BERT Classifier: Not available")

# Check Mistral/Ollama
try:
    from services.mistral_classifier import check_ollama_availability
    if check_ollama_availability():
        print("  ✓ Mistral LLM: Available (Ollama running)")
        services_available += 1
        services_total += 1
    else:
        print("  ✗ Mistral LLM: Ollama not running (optional)")
        services_total += 1
except:
    print("  ✗ Mistral LLM: Not available (optional)")
    services_total += 1

# Check Gemini
try:
    from services.gemini_classifier import check_gemini_availability
    if check_gemini_availability():
        print("  ✓ Gemini API: Available")
        services_available += 1
        services_total += 1
    else:
        print("  ✗ Gemini API: Not configured (optional)")
        services_total += 1
except:
    print("  ✗ Gemini API: Not available (optional)")
    services_total += 1

print(f"\n  Overall Status: {services_available}/{services_total} services available")

if services_available >= 1:
    print("\n  ✓ SYSTEM READY - Application can run with available classifiers")
    print("  → Fallback chain will activate for unavailable services")
else:
    print("\n  ✗ CRITICAL - No classifiers available")
    print("  → Install dependencies: pip install -r requirements-streamlit.txt")

print("\n" + "="*70)
print("Diagnostic complete. To start the application:")
print("  streamlit run streamlit_app/app.py")
print("="*70 + "\n")
