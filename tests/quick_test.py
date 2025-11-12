"""
Test rapide pour vérifier l'installation Playwright
"""

import asyncio
from playwright.async_api import async_playwright


async def quick_test():
    """Test rapide de connexion"""
    
    print("🧪 Test rapide Playwright\n")
    print("=" * 50)
    
    async with async_playwright() as p:
        print("✅ Playwright importé")
        
        browser = await p.chromium.launch(headless=True)
        print("✅ Navigateur Chromium lancé")
        
        page = await browser.new_page()
        print("✅ Nouvelle page créée")
        
        try:
            response = await page.goto("http://localhost:8502", timeout=5000)
            
            if response and response.status == 200:
                print("✅ Application accessible (HTTP 200)")
                
                title = await page.title()
                print(f"📄 Titre de la page: {title}")
                
                # Compter les icônes Font Awesome
                icons = await page.evaluate("""
                    () => document.querySelectorAll('i[class*="fa"]').length
                """)
                print(f"🎨 Icônes Font Awesome détectées: {icons}")
                
                print("\n" + "=" * 50)
                print("✅ SUCCÈS - Prêt pour les tests complets!")
                print("=" * 50)
                
            else:
                print(f"⚠️ Application retourne: HTTP {response.status if response else 'None'}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            print("\n💡 Vérifiez que Streamlit est lancé:")
            print("   python -m streamlit run streamlit_app/app.py --server.port=8502")
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(quick_test())






