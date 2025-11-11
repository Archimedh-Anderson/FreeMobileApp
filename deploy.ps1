# Script de déploiement FreeMobileApp
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Déploiement FreeMobileApp" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Ajouter les fichiers
Write-Host "Étape 1/3: Ajout des fichiers..." -ForegroundColor Yellow
git add .github/workflows/ci-cd.yml
git add .streamlit/config.toml
git add DEPLOYMENT_FIX_SUMMARY.md
git add QUICK_DEPLOY_STEPS.md
git add streamlit_app/services/auth_service.py
git add streamlit_app/services/real_llm_engine.py
git add streamlit_app/services/adaptive_analysis_engine.py
Write-Host "✅ Fichiers ajoutés" -ForegroundColor Green

# Étape 2: Commit
Write-Host ""
Write-Host "Étape 2/3: Commit..." -ForegroundColor Yellow
git commit -m "fix: Make linting non-blocking for Streamlit Cloud deployment"
Write-Host "✅ Commit créé" -ForegroundColor Green

# Étape 3: Push
Write-Host ""
Write-Host "Étape 3/3: Push vers GitHub..." -ForegroundColor Yellow
git push origin main
Write-Host "✅ Push effectué" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ DÉPLOIEMENT TERMINÉ" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Vérifiez:" -ForegroundColor Yellow
Write-Host "  - GitHub Actions: https://github.com/Archimedh-Anderson/FreeMobileApp/actions" -ForegroundColor Gray
Write-Host "  - Streamlit App: https://freemobileapp-lihc6p3rkjeba8avbsuh3v.streamlit.app" -ForegroundColor Gray
Write-Host ""

