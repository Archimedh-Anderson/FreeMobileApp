# Script d'installation et d'exécution des tests Playwright
# FreeMobilaChat v4.5

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Tests Playwright - Setup & Run" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier Python
Write-Host "[1/5] Vérification Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ERREUR: Python non trouvé" -ForegroundColor Red
    exit 1
}

# 2. Installer Playwright si nécessaire
Write-Host ""
Write-Host "[2/5] Installation Playwright..." -ForegroundColor Yellow

$playwrightInstalled = pip show playwright 2>&1
if ($playwrightInstalled -match "Name: playwright") {
    Write-Host "  OK Playwright déjà installé" -ForegroundColor Green
} else {
    Write-Host "  Installation de Playwright..." -ForegroundColor Yellow
    pip install playwright pytest-playwright
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Playwright installé" -ForegroundColor Green
    } else {
        Write-Host "  ERREUR: Installation échouée" -ForegroundColor Red
        exit 1
    }
}

# 3. Installer les navigateurs
Write-Host ""
Write-Host "[3/5] Installation navigateurs Playwright..." -ForegroundColor Yellow
Write-Host "  (Cela peut prendre quelques minutes...)" -ForegroundColor Gray

playwright install chromium

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Chromium installé" -ForegroundColor Green
} else {
    Write-Host "  ERREUR: Installation navigateur échouée" -ForegroundColor Red
    exit 1
}

# 4. Créer les dossiers nécessaires
Write-Host ""
Write-Host "[4/5] Création dossiers..." -ForegroundColor Yellow

if (-not (Test-Path "tests/screenshots")) {
    New-Item -ItemType Directory -Path "tests/screenshots" -Force | Out-Null
    Write-Host "  OK Dossier screenshots créé" -ForegroundColor Green
} else {
    Write-Host "  OK Dossier screenshots existe" -ForegroundColor Green
}

if (-not (Test-Path "tests/reports")) {
    New-Item -ItemType Directory -Path "tests/reports" -Force | Out-Null
    Write-Host "  OK Dossier reports créé" -ForegroundColor Green
} else {
    Write-Host "  OK Dossier reports existe" -ForegroundColor Green
}

# 5. Vérifier que Streamlit tourne
Write-Host ""
Write-Host "[5/5] Vérification application Streamlit..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8502" -TimeoutSec 5 -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "  OK Application accessible" -ForegroundColor Green
    } else {
        Write-Host "  AVERTISSEMENT: Application inaccessible" -ForegroundColor Yellow
        Write-Host "  Le script tentera de la redémarrer" -ForegroundColor Gray
    }
} catch {
    Write-Host "  AVERTISSEMENT: Application non démarrée" -ForegroundColor Yellow
    Write-Host "  Le script tentera de la démarrer" -ForegroundColor Gray
}

# Lancer les tests
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Lancement des tests..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

python tests/test_html_validation_playwright.py

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Tests terminés!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Consultez:" -ForegroundColor Yellow
Write-Host "  - tests/screenshots/ pour les captures d'écran" -ForegroundColor Gray
Write-Host "  - tests/reports/ pour les rapports JSON" -ForegroundColor Gray
Write-Host ""






