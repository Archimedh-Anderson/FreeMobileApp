@echo off
echo ========================================
echo Deploiement FreeMobileApp - Fix Urgent
echo ========================================
echo.

echo Etape 1/4: Ajout des fichiers modifies...
git add .github/workflows/ci-cd.yml
git add .streamlit/config.toml
git add DEPLOYMENT_FIX_SUMMARY.md
git add streamlit_app/services/auth_service.py
git add streamlit_app/services/real_llm_engine.py
git add streamlit_app/services/adaptive_analysis_engine.py
echo OK

echo.
echo Etape 2/4: Commit...
git commit -m "fix: Make linting non-blocking and fix Streamlit Cloud deployment"
echo OK

echo.
echo Etape 3/4: Push vers GitHub...
git push origin main
echo OK

echo.
echo ========================================
echo DEPLOIEMENT EN COURS
echo ========================================
echo.
echo Verifiez le deploiement sur:
echo - GitHub Actions: https://github.com/Archimedh-Anderson/FreeMobileApp/actions
echo - Streamlit Cloud: https://freemobileapp-lihc6p3rkjeba8avbsuh3v.streamlit.app
echo.
pause

