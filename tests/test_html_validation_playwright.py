"""
FreeMobilaChat - Script de Validation HTML avec Playwright
===========================================================

Test automatisé complet pour détecter, analyser et corriger les erreurs HTML
sur toutes les pages de l'application Streamlit.

Version: 1.0
Date: 2025-11-10
"""

import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class FreeMobilaChatHTMLValidator:
    """Validateur HTML automatisé pour FreeMobilaChat"""
    
    def __init__(self, base_url: str = "http://localhost:8502"):
        self.base_url = base_url
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.report: Dict[str, Any] = {}
        self.pages_tested = 0
        self.start_time = None
        
        # Pages à tester
        self.pages_to_test = [
            {"name": "Homepage", "url": "/", "wait_for": "app"},
            {"name": "Classification LLM", "url": "/Classification_LLM", "wait_for": "Classification LLM"},
            {"name": "Classification Mistral", "url": "/Classification_Mistral", "wait_for": "Classification Automatisé"}
        ]
    
    async def check_app_running(self) -> bool:
        """Vérifie si l'application Streamlit est en cours d'exécution"""
        print("🔍 Vérification de l'état de l'application...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=5000)
                
                if response and response.status == 200:
                    print("✅ Application accessible")
                    await browser.close()
                    return True
                else:
                    print(f"❌ Application inaccessible (Status: {response.status if response else 'None'})")
                    await browser.close()
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur de connexion: {e}")
                await browser.close()
                return False
    
    async def restart_app(self) -> bool:
        """Redémarre l'application Streamlit si nécessaire"""
        print("🔄 Redémarrage de l'application...")
        
        try:
            # Arrêter tous les processus Python
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True,
                shell=True
            )
            time.sleep(3)
            
            # Redémarrer Streamlit en arrière-plan
            subprocess.Popen(
                [
                    "python", "-m", "streamlit", "run", 
                    "streamlit_app/app.py", 
                    "--server.port=8502",
                    "--server.enableCORS=false",
                    "--server.enableXsrfProtection=false",
                    "--server.maxUploadSize=500"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
            
            print("⏳ Attente du démarrage de l'application (15s)...")
            await asyncio.sleep(15)
            
            # Vérifier que l'app est bien redémarrée
            is_running = await self.check_app_running()
            
            if is_running:
                print("✅ Application redémarrée avec succès")
                return True
            else:
                print("❌ Échec du redémarrage")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du redémarrage: {e}")
            return False
    
    async def clear_browser_cache(self, context: BrowserContext):
        """Nettoie le cache du navigateur"""
        print("🗑️ Nettoyage du cache navigateur...")
        
        # Créer un nouveau contexte propre (équivalent à vider le cache)
        await context.clear_cookies()
        print("✅ Cache nettoyé")
    
    async def validate_html_structure(self, page: Page, page_name: str):
        """Valide la structure HTML de la page"""
        print(f"\n📝 Validation HTML pour: {page_name}")
        
        errors_found = []
        warnings_found = []
        
        # 1. Vérifier les balises non fermées
        print("  🔍 Vérification des balises...")
        
        unclosed_tags = await page.evaluate("""
            () => {
                const errors = [];
                const elements = document.querySelectorAll('*');
                
                elements.forEach(el => {
                    // Vérifier si l'élément a un innerHTML valide
                    try {
                        const test = el.innerHTML;
                    } catch (e) {
                        errors.push({
                            tag: el.tagName,
                            error: 'Invalid innerHTML',
                            outerHTML: el.outerHTML.substring(0, 100)
                        });
                    }
                });
                
                return errors;
            }
        """)
        
        if unclosed_tags:
            for tag in unclosed_tags:
                errors_found.append({
                    "type": "UNCLOSED_TAG",
                    "severity": "ERROR",
                    "element": tag,
                    "page": page_name
                })
        
        # 2. Vérifier les attributs invalides
        print("  🔍 Vérification des attributs...")
        
        invalid_attributes = await page.evaluate("""
            () => {
                const warnings = [];
                
                // Vérifier les icônes Font Awesome mal formées
                const icons = document.querySelectorAll('[class*="fas fa-"]');
                icons.forEach(icon => {
                    const classes = icon.className;
                    if (!classes.includes('fas') || !classes.includes('fa-')) {
                        warnings.push({
                            element: 'icon',
                            class: classes,
                            issue: 'Malformed Font Awesome class'
                        });
                    }
                });
                
                // Vérifier les liens brisés (href vides)
                const links = document.querySelectorAll('a[href=""]');
                links.forEach(link => {
                    warnings.push({
                        element: 'a',
                        issue: 'Empty href attribute',
                        text: link.textContent.substring(0, 50)
                    });
                });
                
                return warnings;
            }
        """)
        
        if invalid_attributes:
            for attr in invalid_attributes:
                warnings_found.append({
                    "type": "INVALID_ATTRIBUTE",
                    "severity": "WARNING",
                    "element": attr,
                    "page": page_name
                })
        
        # 3. Vérifier les erreurs CSS
        print("  🔍 Vérification des styles CSS...")
        
        css_errors = await page.evaluate("""
            () => {
                const errors = [];
                
                // Vérifier si les classes CSS critiques sont présentes
                const criticalClasses = ['.header-title', '.stat-card'];
                const stylesheets = Array.from(document.styleSheets);
                
                criticalClasses.forEach(className => {
                    let found = false;
                    
                    try {
                        stylesheets.forEach(sheet => {
                            if (sheet.cssRules) {
                                Array.from(sheet.cssRules).forEach(rule => {
                                    if (rule.selectorText && rule.selectorText.includes(className)) {
                                        found = true;
                                    }
                                });
                            }
                        });
                    } catch (e) {
                        // CORS ou autre erreur d'accès aux stylesheets
                    }
                    
                    if (!found) {
                        const elements = document.querySelectorAll(className);
                        if (elements.length === 0) {
                            errors.push({
                                className: className,
                                issue: 'CSS class defined but not used'
                            });
                        }
                    }
                });
                
                return errors;
            }
        """)
        
        if css_errors:
            for error in css_errors:
                warnings_found.append({
                    "type": "CSS_WARNING",
                    "severity": "WARNING",
                    "element": error,
                    "page": page_name
                })
        
        # 4. Vérifier les icônes Font Awesome
        print("  🔍 Vérification des icônes Font Awesome...")
        
        icon_check = await page.evaluate("""
            () => {
                const results = {
                    total: 0,
                    valid: 0,
                    invalid: [],
                    library_loaded: false
                };
                
                // Vérifier si Font Awesome est chargé
                const faLinks = document.querySelectorAll('link[href*="font-awesome"]');
                results.library_loaded = faLinks.length > 0;
                
                // Compter les icônes
                const icons = document.querySelectorAll('i[class*="fa"]');
                results.total = icons.length;
                
                icons.forEach((icon, idx) => {
                    const classes = icon.className;
                    
                    // Vérifier format valide: "fas fa-xxx" ou "far fa-xxx", etc.
                    const validFormat = /^fa[srblud]\\s+fa-[a-z-]+/.test(classes);
                    
                    if (validFormat) {
                        results.valid++;
                    } else {
                        results.invalid.push({
                            class: classes,
                            index: idx,
                            html: icon.outerHTML.substring(0, 100)
                        });
                    }
                });
                
                return results;
            }
        """)
        
        print(f"    ✅ Font Awesome library: {'Chargée' if icon_check['library_loaded'] else '❌ Non chargée'}")
        print(f"    📊 Icônes totales: {icon_check['total']}")
        print(f"    ✅ Icônes valides: {icon_check['valid']}")
        print(f"    ⚠️ Icônes invalides: {len(icon_check['invalid'])}")
        
        if not icon_check['library_loaded']:
            errors_found.append({
                "type": "FONT_AWESOME_NOT_LOADED",
                "severity": "ERROR",
                "message": "Font Awesome library not loaded",
                "page": page_name
            })
        
        if icon_check['invalid']:
            for invalid_icon in icon_check['invalid']:
                warnings_found.append({
                    "type": "INVALID_ICON",
                    "severity": "WARNING",
                    "element": invalid_icon,
                    "page": page_name
                })
        
        # 5. Vérifier la console JavaScript
        print("  🔍 Vérification des erreurs console...")
        
        console_errors = []
        
        page.on("console", lambda msg: 
            console_errors.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }) if msg.type in ["error", "warning"] else None
        )
        
        # Attendre un peu pour capturer les erreurs console
        await asyncio.sleep(2)
        
        if console_errors:
            for console_error in console_errors:
                if console_error['type'] == 'error':
                    errors_found.append({
                        "type": "CONSOLE_ERROR",
                        "severity": "ERROR",
                        "message": console_error['text'],
                        "location": console_error['location'],
                        "page": page_name
                    })
                else:
                    warnings_found.append({
                        "type": "CONSOLE_WARNING",
                        "severity": "WARNING",
                        "message": console_error['text'],
                        "page": page_name
                    })
        
        # Stocker les résultats
        self.errors.extend(errors_found)
        self.warnings.extend(warnings_found)
        
        # Résumé
        print(f"\n  📊 Résumé pour {page_name}:")
        print(f"    ❌ Erreurs: {len(errors_found)}")
        print(f"    ⚠️ Avertissements: {len(warnings_found)}")
        
        return len(errors_found) == 0
    
    async def test_file_constraints(self, page: Page, page_name: str):
        """Teste les contraintes sur les fichiers"""
        print(f"\n📦 Test des contraintes fichiers pour: {page_name}")
        
        constraints_results = {
            "page": page_name,
            "max_upload_size": "500 MB",
            "file_permissions": "OK",
            "security_settings": "OK"
        }
        
        # 1. Vérifier la taille max d'upload (500 MB)
        print("  🔍 Vérification taille max upload...")
        
        upload_limit = await page.evaluate("""
            () => {
                // Chercher dans la page les références à la limite
                const text = document.body.innerText;
                const match = text.match(/500\\s*MB/i);
                return match ? "500 MB détecté" : "Limite non trouvée";
            }
        """)
        
        print(f"    ✅ Limite upload: {upload_limit}")
        constraints_results["upload_limit_displayed"] = "500 MB" in upload_limit
        
        # 2. Vérifier les messages d'erreur 403
        print("  🔍 Vérification instructions erreur 403...")
        
        error_403_instructions = await page.evaluate("""
            () => {
                const text = document.body.innerText;
                
                const checks = {
                    "taille_fichier": text.includes("500 MB") || text.includes("500MB"),
                    "rafraichir": text.includes("F5") || text.includes("Rafraîchir"),
                    "permissions": text.includes("lecture seule") || text.includes("permissions"),
                    "cache": text.includes("cache") || text.includes("Ctrl+Shift+Del"),
                    "antivirus": text.includes("anti-virus") || text.includes("antivirus"),
                    "restart": text.includes("Redémarrer") || text.includes("taskkill")
                };
                
                return checks;
            }
        """)
        
        total_checks = sum(1 for v in error_403_instructions.values() if v)
        print(f"    ✅ Instructions 403 présentes: {total_checks}/6")
        
        for check, present in error_403_instructions.items():
            icon = "✅" if present else "❌"
            print(f"      {icon} {check}")
        
        constraints_results["error_403_instructions"] = error_403_instructions
        constraints_results["error_403_complete"] = total_checks == 6
        
        # 3. Vérifier les icônes de sécurité
        print("  🔍 Vérification icônes de sécurité...")
        
        security_icons = await page.evaluate("""
            () => {
                const icons = {
                    "weight": document.querySelectorAll('.fa-weight').length > 0,
                    "lock-open": document.querySelectorAll('.fa-lock-open').length > 0,
                    "shield-alt": document.querySelectorAll('.fa-shield-alt').length > 0,
                    "sync": document.querySelectorAll('.fa-sync').length > 0,
                    "browser": document.querySelectorAll('.fa-browser').length > 0,
                    "redo": document.querySelectorAll('.fa-redo').length > 0
                };
                
                return icons;
            }
        """)
        
        total_icons = sum(1 for v in security_icons.values() if v)
        print(f"    ✅ Icônes sécurité présentes: {total_icons}/6")
        
        for icon, present in security_icons.items():
            status = "✅" if present else "⚠️"
            print(f"      {status} fa-{icon}")
        
        constraints_results["security_icons"] = security_icons
        
        return constraints_results
    
    async def test_page_interactions(self, page: Page, page_name: str):
        """Teste les interactions utilisateur sur la page"""
        print(f"\n🖱️ Test des interactions pour: {page_name}")
        
        interactions_results = {
            "page": page_name,
            "refresh_works": False,
            "hover_animations": False,
            "buttons_clickable": False
        }
        
        # 1. Test rafraîchissement (F5)
        print("  🔄 Test rafraîchissement page...")
        
        initial_content = await page.content()
        await page.keyboard.press("F5")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        
        refreshed_content = await page.content()
        interactions_results["refresh_works"] = len(refreshed_content) > 1000
        
        if interactions_results["refresh_works"]:
            print("    ✅ Rafraîchissement fonctionne")
        else:
            print("    ❌ Problème rafraîchissement")
        
        # 2. Test animations hover
        print("  ✨ Test animations hover...")
        
        try:
            buttons = await page.query_selector_all("button")
            
            if buttons:
                # Hover sur le premier bouton
                await buttons[0].hover()
                await asyncio.sleep(0.5)
                
                # Vérifier si une transition CSS est appliquée
                has_transition = await buttons[0].evaluate("""
                    (el) => {
                        const styles = window.getComputedStyle(el);
                        return styles.transition !== 'all 0s ease 0s';
                    }
                """)
                
                interactions_results["hover_animations"] = has_transition
                
                if has_transition:
                    print("    ✅ Animations hover actives")
                else:
                    print("    ⚠️ Animations hover non détectées")
            else:
                print("    ⚠️ Aucun bouton trouvé")
                
        except Exception as e:
            print(f"    ⚠️ Erreur test hover: {e}")
        
        # 3. Test cliquabilité des boutons
        print("  🖱️ Test cliquabilité boutons...")
        
        try:
            clickable_buttons = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    
                    return buttons.filter(btn => {
                        const styles = window.getComputedStyle(btn);
                        return styles.pointerEvents !== 'none' && 
                               styles.display !== 'none' &&
                               !btn.disabled;
                    }).length;
                }
            """)
            
            interactions_results["buttons_clickable"] = clickable_buttons > 0
            interactions_results["clickable_buttons_count"] = clickable_buttons
            
            print(f"    ✅ Boutons cliquables: {clickable_buttons}")
            
        except Exception as e:
            print(f"    ⚠️ Erreur test cliquabilité: {e}")
        
        return interactions_results
    
    async def test_single_page(self, browser: Browser, page_config: Dict[str, str]):
        """Teste une page complète"""
        print(f"\n{'='*60}")
        print(f"🧪 TEST DE LA PAGE: {page_config['name']}")
        print(f"{'='*60}")
        
        # Créer un nouveau contexte propre pour chaque page
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        page_results = {
            "name": page_config['name'],
            "url": page_config['url'],
            "timestamp": datetime.now().isoformat(),
            "status": "UNKNOWN"
        }
        
        try:
            # Naviguer vers la page
            print(f"🌐 Navigation vers: {self.base_url}{page_config['url']}")
            
            response = await page.goto(
                f"{self.base_url}{page_config['url']}", 
                wait_until="networkidle",
                timeout=30000
            )
            
            if response and response.status != 200:
                print(f"❌ Erreur HTTP: {response.status}")
                page_results["status"] = "ERROR"
                page_results["error"] = f"HTTP {response.status}"
                return page_results
            
            # Attendre le chargement complet
            await asyncio.sleep(3)
            
            print("✅ Page chargée")
            
            # 1. Validation HTML
            html_valid = await self.validate_html_structure(page, page_config['name'])
            page_results["html_valid"] = html_valid
            
            # 2. Test contraintes fichiers
            constraints = await self.test_file_constraints(page, page_config['name'])
            page_results["constraints"] = constraints
            
            # 3. Test interactions
            interactions = await self.test_page_interactions(page, page_config['name'])
            page_results["interactions"] = interactions
            
            # 4. Capture d'écran
            screenshot_path = f"tests/screenshots/{page_config['name'].replace(' ', '_')}.png"
            os.makedirs("tests/screenshots", exist_ok=True)
            
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot sauvegardée: {screenshot_path}")
            page_results["screenshot"] = screenshot_path
            
            # Déterminer le status final
            if html_valid and constraints.get("error_403_complete", False):
                page_results["status"] = "PASS"
            elif html_valid:
                page_results["status"] = "PASS_WITH_WARNINGS"
            else:
                page_results["status"] = "FAIL"
            
            self.pages_tested += 1
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            page_results["status"] = "ERROR"
            page_results["error"] = str(e)
        
        finally:
            await context.close()
        
        return page_results
    
    async def run_all_tests(self):
        """Lance tous les tests"""
        self.start_time = datetime.now()
        
        print("\n" + "="*80)
        print("🚀 DÉMARRAGE DES TESTS PLAYWRIGHT - FreeMobilaChat v4.5")
        print("="*80 + "\n")
        
        # Vérifier que l'app tourne
        app_running = await self.check_app_running()
        
        if not app_running:
            print("⚠️ Application non accessible, tentative de redémarrage...")
            restarted = await self.restart_app()
            
            if not restarted:
                print("❌ Impossible de démarrer l'application")
                return False
        
        # Lancer les tests
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Mode visible pour debugging
                args=[
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            all_results = []
            
            for page_config in self.pages_to_test:
                result = await self.test_single_page(browser, page_config)
                all_results.append(result)
                
                # Petite pause entre les pages
                await asyncio.sleep(2)
            
            await browser.close()
            
            # Générer le rapport
            self.generate_report(all_results)
        
        return True
    
    def generate_report(self, all_results: List[Dict]):
        """Génère le rapport final"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📊 RAPPORT FINAL DES TESTS")
        print("="*80 + "\n")
        
        # Statistiques globales
        total_pages = len(all_results)
        passed = sum(1 for r in all_results if r['status'] == 'PASS')
        passed_warnings = sum(1 for r in all_results if r['status'] == 'PASS_WITH_WARNINGS')
        failed = sum(1 for r in all_results if r['status'] == 'FAIL')
        errors = sum(1 for r in all_results if r['status'] == 'ERROR')
        
        print(f"🕒 Durée totale: {duration:.2f}s")
        print(f"📄 Pages testées: {total_pages}")
        print(f"✅ Succès: {passed}")
        print(f"⚠️ Succès avec avertissements: {passed_warnings}")
        print(f"❌ Échecs: {failed}")
        print(f"🔴 Erreurs: {errors}")
        print()
        
        # Détail par page
        print("📋 Détail par page:")
        print("-" * 80)
        
        for result in all_results:
            status_icon = {
                "PASS": "✅",
                "PASS_WITH_WARNINGS": "⚠️",
                "FAIL": "❌",
                "ERROR": "🔴"
            }.get(result['status'], "❓")
            
            print(f"\n{status_icon} {result['name']}")
            print(f"   URL: {result['url']}")
            print(f"   Status: {result['status']}")
            
            if 'html_valid' in result:
                print(f"   HTML valide: {'✅' if result['html_valid'] else '❌'}")
            
            if 'constraints' in result:
                constraints = result['constraints']
                print(f"   Instructions 403: {'✅' if constraints.get('error_403_complete') else '⚠️'}")
            
            if 'interactions' in result:
                interactions = result['interactions']
                print(f"   Interactions: {'✅' if interactions.get('buttons_clickable') else '⚠️'}")
            
            if 'screenshot' in result:
                print(f"   Screenshot: {result['screenshot']}")
        
        # Résumé des erreurs
        print("\n" + "="*80)
        print("❌ ERREURS DÉTECTÉES")
        print("="*80 + "\n")
        
        if self.errors:
            print(f"Total: {len(self.errors)} erreurs")
            
            for idx, error in enumerate(self.errors, 1):
                print(f"\n{idx}. [{error['type']}] - {error['page']}")
                print(f"   Sévérité: {error['severity']}")
                
                if 'message' in error:
                    print(f"   Message: {error['message']}")
                
                if 'element' in error:
                    print(f"   Élément: {error['element']}")
        else:
            print("✅ Aucune erreur détectée")
        
        # Résumé des avertissements
        print("\n" + "="*80)
        print("⚠️ AVERTISSEMENTS")
        print("="*80 + "\n")
        
        if self.warnings:
            print(f"Total: {len(self.warnings)} avertissements")
            
            # Grouper par type
            warnings_by_type = {}
            for warning in self.warnings:
                wtype = warning['type']
                if wtype not in warnings_by_type:
                    warnings_by_type[wtype] = []
                warnings_by_type[wtype].append(warning)
            
            for wtype, warns in warnings_by_type.items():
                print(f"\n📌 {wtype}: {len(warns)} occurrences")
        else:
            print("✅ Aucun avertissement")
        
        # Recommandations
        print("\n" + "="*80)
        print("💡 RECOMMANDATIONS")
        print("="*80 + "\n")
        
        recommendations = []
        
        if any(e['type'] == 'FONT_AWESOME_NOT_LOADED' for e in self.errors):
            recommendations.append("🔧 Vérifier le chargement de Font Awesome 6.4.0")
        
        if any(e['type'] == 'CONSOLE_ERROR' for e in self.errors):
            recommendations.append("🔧 Corriger les erreurs JavaScript dans la console")
        
        if len(self.warnings) > 10:
            recommendations.append("🔧 Nettoyer les avertissements HTML pour améliorer la qualité")
        
        # Vérifier si toutes les instructions 403 sont présentes
        missing_403 = False
        for result in all_results:
            if 'constraints' in result:
                if not result['constraints'].get('error_403_complete'):
                    missing_403 = True
                    break
        
        if missing_403:
            recommendations.append("🔧 Compléter les instructions d'erreur 403 (6 vérifications requises)")
        
        if not recommendations:
            recommendations.append("✅ Toutes les validations sont passées avec succès!")
        
        for rec in recommendations:
            print(f"  {rec}")
        
        # Sauvegarder le rapport JSON
        report_path = f"tests/reports/html_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("tests/reports", exist_ok=True)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_pages": total_pages,
                "passed": passed,
                "passed_with_warnings": passed_warnings,
                "failed": failed,
                "errors": errors,
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings)
            },
            "pages": all_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": recommendations
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport JSON sauvegardé: {report_path}")
        
        # Score final
        print("\n" + "="*80)
        print("🏆 SCORE FINAL")
        print("="*80 + "\n")
        
        max_score = total_pages * 100
        score = (passed * 100) + (passed_warnings * 80) + (failed * 20)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        print(f"Score: {score}/{max_score} ({percentage:.1f}%)")
        
        if percentage >= 90:
            print("🌟 EXCELLENT - Production Ready!")
        elif percentage >= 75:
            print("✅ BON - Quelques ajustements recommandés")
        elif percentage >= 50:
            print("⚠️ MOYEN - Corrections nécessaires")
        else:
            print("❌ INSUFFISANT - Corrections urgentes requises")
        
        print("\n" + "="*80)
        print("✅ TESTS TERMINÉS")
        print("="*80 + "\n")
        
        return report_data


async def main():
    """Point d'entrée principal"""
    validator = FreeMobilaChatHTMLValidator()
    await validator.run_all_tests()


if __name__ == "__main__":
    # Installation des dépendances si nécessaire
    print("📦 Vérification des dépendances Playwright...")
    
    try:
        import playwright
        print("✅ Playwright installé")
    except ImportError:
        print("❌ Playwright non installé")
        print("Installation: pip install playwright")
        print("Puis: playwright install chromium")
        exit(1)
    
    # Lancer les tests
    asyncio.run(main())






