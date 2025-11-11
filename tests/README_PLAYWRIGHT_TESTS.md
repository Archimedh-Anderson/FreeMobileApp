# 🧪 Tests Playwright - FreeMobilaChat v4.5

## 📋 Description

Script de validation HTML complet utilisant Playwright pour tester automatiquement toutes les pages de l'application FreeMobilaChat et détecter les erreurs HTML, CSS et JavaScript.

---

## 🚀 Installation

### 1. Installer Playwright

```bash
pip install playwright pytest-playwright
```

### 2. Installer les navigateurs

```bash
playwright install chromium
```

---

## ▶️ Exécution

### Lancer tous les tests

```bash
cd C:\Users\ander\Desktop\FreeMobilaChat
python tests/test_html_validation_playwright.py
```

### Avec pytest

```bash
pytest tests/test_html_validation_playwright.py -v
```

---

## 📊 Fonctionnalités

### ✅ Validations Effectuées

1. **Structure HTML**
   - Balises non fermées
   - Attributs invalides
   - Hiérarchie DOM correcte

2. **Icônes Font Awesome**
   - Bibliothèque chargée
   - Format correct: `<i class='fas fa-xxx'></i>`
   - Icônes valides

3. **Contraintes Techniques**
   - Taille max upload: 500 MB
   - Instructions erreur 403 (6 vérifications)
   - Icônes de sécurité présentes

4. **Interactions Utilisateur**
   - Rafraîchissement page (F5)
   - Animations hover
   - Boutons cliquables

5. **Console JavaScript**
   - Erreurs JS
   - Avertissements
   - Logs réseau

---

## 📁 Sorties Générées

### 1. Screenshots

```
tests/screenshots/
├── Homepage.png
├── Classification_LLM.png
└── Classification_Mistral.png
```

### 2. Rapports JSON

```
tests/reports/
└── html_validation_report_20251110_142530.json
```

### 3. Console

Rapport détaillé affiché dans le terminal avec:
- Statistiques globales
- Détail par page
- Liste des erreurs
- Recommandations

---

## 🎯 Critères de Validation

### ✅ PASS

- HTML 100% valide
- Toutes les icônes Font Awesome correctes
- 6 instructions erreur 403 présentes
- Interactions fonctionnelles

### ⚠️ PASS WITH WARNINGS

- HTML valide
- Quelques avertissements mineurs
- Fonctionnalités principales OK

### ❌ FAIL

- Erreurs HTML structurelles
- Icônes manquantes/invalides
- Instructions 403 incomplètes

### 🔴 ERROR

- Page inaccessible
- Timeout
- Erreur critique

---

## 📋 Exemple de Rapport

```
================================================================================
📊 RAPPORT FINAL DES TESTS
================================================================================

🕒 Durée totale: 45.32s
📄 Pages testées: 3
✅ Succès: 2
⚠️ Succès avec avertissements: 1
❌ Échecs: 0
🔴 Erreurs: 0

📋 Détail par page:
--------------------------------------------------------------------------------

✅ Homepage
   URL: /
   Status: PASS
   HTML valide: ✅
   Instructions 403: ✅
   Interactions: ✅
   Screenshot: tests/screenshots/Homepage.png

✅ Classification LLM
   URL: /Classification_LLM
   Status: PASS
   HTML valide: ✅
   Instructions 403: ✅
   Interactions: ✅
   Screenshot: tests/screenshots/Classification_LLM.png

⚠️ Classification Mistral
   URL: /Classification_Mistral
   Status: PASS_WITH_WARNINGS
   HTML valide: ✅
   Instructions 403: ✅
   Interactions: ✅
   Screenshot: tests/screenshots/Classification_Mistral.png

================================================================================
❌ ERREURS DÉTECTÉES
================================================================================

✅ Aucune erreur détectée

================================================================================
⚠️ AVERTISSEMENTS
================================================================================

Total: 2 avertissements

📌 INVALID_ICON: 1 occurrences
📌 CSS_WARNING: 1 occurrences

================================================================================
💡 RECOMMANDATIONS
================================================================================

  ✅ Toutes les validations sont passées avec succès!

📄 Rapport JSON sauvegardé: tests/reports/html_validation_report_20251110_142530.json

================================================================================
🏆 SCORE FINAL
================================================================================

Score: 280/300 (93.3%)
🌟 EXCELLENT - Production Ready!

================================================================================
✅ TESTS TERMINÉS
================================================================================
```

---

## 🔧 Configuration

### Modifier les pages testées

Dans `test_html_validation_playwright.py`:

```python
self.pages_to_test = [
    {"name": "Homepage", "url": "/", "wait_for": "app"},
    {"name": "Classification LLM", "url": "/Classification_LLM", "wait_for": "Classification LLM"},
    {"name": "Classification Mistral", "url": "/Classification_Mistral", "wait_for": "Classification Automatisé"},
    # Ajouter vos pages ici
]
```

### Changer le port Streamlit

```python
def __init__(self, base_url: str = "http://localhost:8502"):
```

---

## 🐛 Debugging

### Mode headless

Pour voir le navigateur pendant les tests:

```python
browser = await p.chromium.launch(
    headless=False  # Changé de True à False
)
```

### Augmenter les timeouts

```python
await page.goto(url, timeout=60000)  # 60 secondes
```

### Capturer plus de logs

```python
page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
page.on("pageerror", lambda exc: print(f"ERROR: {exc}"))
```

---

## 📚 Ressources

- **Playwright Docs:** https://playwright.dev/python/
- **Font Awesome:** https://fontawesome.com/
- **Streamlit:** https://docs.streamlit.io/

---

## ✅ Checklist de Validation

Avant de déployer en production:

- [ ] Tous les tests passent (PASS ou PASS_WITH_WARNINGS)
- [ ] Aucune erreur critique
- [ ] Score > 90%
- [ ] Font Awesome chargé sur toutes les pages
- [ ] Instructions erreur 403 complètes (6/6)
- [ ] Interactions fonctionnelles
- [ ] Screenshots générées
- [ ] Rapport JSON sauvegardé

---

**Version:** 1.0  
**Date:** 10 Novembre 2025  
**Status:** ✅ Production Ready





