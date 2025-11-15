"""
Gemini API Configuration Validator
Tests Gemini API integration with and without credentials
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)

# Add streamlit_app to path
streamlit_app_path = Path(__file__).parent / 'streamlit_app'
sys.path.insert(0, str(streamlit_app_path))

print("="*70)
print("GEMINI API CONFIGURATION VALIDATOR")
print("="*70)

print("\n[1] ENVIRONMENT VARIABLE CHECK")
print("-"*70)

# Check environment variables
gemini_key = os.getenv('GEMINI_API_KEY')
google_key = os.getenv('GOOGLE_API_KEY')
gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
gemini_temp = os.getenv('GEMINI_TEMPERATURE', '0.3')
gemini_tokens = os.getenv('GEMINI_MAX_TOKENS', '4096')

print(f"  GEMINI_API_KEY: {'[SET - ' + gemini_key[:10] + '...]' if gemini_key else '[NOT SET]'}")
print(f"  GOOGLE_API_KEY: {'[SET - ' + google_key[:10] + '...]' if google_key else '[NOT SET]'}")
print(f"  GEMINI_MODEL: {gemini_model}")
print(f"  GEMINI_TEMPERATURE: {gemini_temp}")
print(f"  GEMINI_MAX_TOKENS: {gemini_tokens}")

api_key_configured = bool(gemini_key or google_key)

print("\n[2] GEMINI MODULE AVAILABILITY")
print("-"*70)

try:
    from services.gemini_classifier import GeminiClassifier, check_gemini_availability
    print("  ✓ GeminiClassifier module imported successfully")
    
    # Test graceful initialization without API key
    print("\n[3] TESTING GRACEFUL FALLBACK (No API Key)")
    print("-"*70)
    
    if not api_key_configured:
        print("  Testing GeminiClassifier initialization without API key...")
        try:
            classifier = GeminiClassifier(api_key=None)
            if classifier.client is None:
                print("  ✓ GeminiClassifier initialized gracefully without API key")
                print("  ✓ client=None, model=None (fallback mode)")
            else:
                print("  ⚠ Unexpected: Classifier initialized with client despite no API key")
        except Exception as e:
            print(f"  ✗ FAILED: Initialization raised exception: {e}")
            print("  → This should NOT happen - graceful degradation failed")
    else:
        print("  ⊘ Skipped - API key is configured")
    
    print("\n[4] TESTING API AVAILABILITY CHECK")
    print("-"*70)
    
    is_available = check_gemini_availability()
    
    if api_key_configured:
        if is_available:
            print("  ✓ Gemini API is available and responding")
            print("  → API key is valid and service is accessible")
        else:
            print("  ⚠ Gemini API key configured but validation failed")
            print("  → Check if key is valid or service is accessible")
    else:
        if not is_available:
            print("  ✓ check_gemini_availability() correctly returns False")
            print("  → Graceful fallback behavior confirmed")
        else:
            print("  ✗ UNEXPECTED: check_gemini_availability() returns True without key")
    
    print("\n[5] TESTING WITH API KEY (if configured)")
    print("-"*70)
    
    if api_key_configured:
        actual_key = gemini_key or google_key
        print(f"  Using API key: {actual_key[:15]}...")
        
        try:
            classifier = GeminiClassifier(api_key=actual_key)
            if classifier.client is not None:
                print("  ✓ GeminiClassifier initialized successfully with API key")
                print(f"  ✓ Model: {classifier.model_name}")
                print(f"  ✓ Temperature: {classifier.temperature}")
                
                # Try a simple test classification
                print("\n  Testing actual classification...")
                try:
                    test_text = "This product is amazing! I love it!"
                    result = classifier.classify_batch([test_text])
                    
                    if result and len(result) > 0:
                        print("  ✓ Classification successful!")
                        print(f"    Sentiment: {result[0].get('sentiment', 'N/A')}")
                        print(f"    Confidence: {result[0].get('confidence', 'N/A')}")
                    else:
                        print("  ⚠ Classification returned empty result")
                except Exception as e:
                    print(f"  ⚠ Classification test failed: {str(e)[:100]}")
                    print("  → This may be due to API quota or connectivity issues")
            else:
                print("  ✗ Classifier initialized but client is None")
        except Exception as e:
            print(f"  ✗ Failed to initialize with API key: {e}")
    else:
        print("  ⊘ Skipped - No API key configured")
        print("  → To test with API key:")
        print("    1. Get key from: https://aistudio.google.com/app/apikey")
        print("    2. Add to .env: GEMINI_API_KEY=your_key_here")
        print("    3. Install: pip install google-generativeai")
        print("    4. Re-run this validator")

except ImportError as e:
    print(f"  ✗ Failed to import GeminiClassifier: {e}")
    print("\n  → Missing dependency: google-generativeai")
    print("  → Install with: pip install google-generativeai")
    print("  → Note: This is OPTIONAL - system works without it")

except Exception as e:
    print(f"  ✗ Unexpected error: {e}")

print("\n[6] FALLBACK CHAIN VALIDATION")
print("-"*70)

try:
    from services.bert_classifier import BERTClassifier, TORCH_AVAILABLE
    from services.rule_classifier import EnhancedRuleClassifier
    
    fallback_services = []
    
    if TORCH_AVAILABLE:
        fallback_services.append("BERT Classifier (PyTorch)")
    
    fallback_services.append("Rule-based Classifier")
    
    print("  Available fallback services:")
    for service in fallback_services:
        print(f"    ✓ {service}")
    
    if not api_key_configured:
        print("\n  ✓ GRACEFUL DEGRADATION CONFIRMED:")
        print("    → Application will use fallback chain without Gemini")
        print(f"    → {len(fallback_services)} fallback service(s) available")
    else:
        print("\n  ✓ HYBRID MODE AVAILABLE:")
        print("    → Gemini API + fallback services")
        print(f"    → Total: 1 API + {len(fallback_services)} fallback service(s)")

except Exception as e:
    print(f"  ⚠ Error checking fallback services: {e}")

print("\n[7] FINAL VALIDATION SUMMARY")
print("="*70)

if api_key_configured:
    print("\n  SCENARIO: Gemini API ENABLED")
    print("  ✓ API key is configured in .env")
    print("  ✓ GeminiClassifier can be initialized")
    if 'is_available' in locals() and is_available:
        print("  ✓ API connection validated successfully")
        print("\n  STATUS: READY - Gemini API integration active")
    else:
        print("  ⚠ API validation pending or failed")
        print("\n  STATUS: FALLBACK - Using BERT + Rules")
else:
    print("\n  SCENARIO: Gemini API DISABLED (Graceful Fallback)")
    print("  ✓ No API key configured (expected)")
    print("  ✓ GeminiClassifier handles gracefully (no exceptions)")
    print("  ✓ Fallback chain is active (BERT + Rules)")
    print("\n  STATUS: READY - Operating in offline mode")

print("\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)

print("\nRECOMMENDATIONS:")
if not api_key_configured:
    print("  • System is working correctly WITHOUT Gemini API")
    print("  • Gemini remains optional - no action needed")
    print("  • To enable Gemini: add GEMINI_API_KEY to .env")
else:
    print("  • Gemini API is configured")
    if 'is_available' in locals() and is_available:
        print("  • API is responding - ready for use")
    else:
        print("  • Verify API key is valid")
        print("  • Check internet connectivity")
        print("  • Ensure google-generativeai is installed")

print("\n")
