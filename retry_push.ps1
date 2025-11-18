# Script PowerShell pour réessayer le push vers GitHub
# Usage: .\retry_push.ps1

$maxAttempts = 10
$attempt = 1
$delay = 10

Write-Host "🔄 Tentative de push vers GitHub..." -ForegroundColor Cyan
Write-Host ""

while ($attempt -le $maxAttempts) {
    Write-Host "[Tentative $attempt/$maxAttempts] Push vers origin/main..." -ForegroundColor Yellow
    
    $result = git push origin main 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Push réussi!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Prochaines étapes:" -ForegroundColor Cyan
        Write-Host "1. Vérifier le workflow dans GitHub Actions"
        Write-Host "2. Le workflow devrait maintenant gérer les erreurs Git avec retry"
        exit 0
    }
    
    Write-Host "❌ Échec (code: $LASTEXITCODE)" -ForegroundColor Red
    Write-Host $result
    
    if ($attempt -lt $maxAttempts) {
        Write-Host ""
        Write-Host "⏳ Attente de ${delay}s avant nouvelle tentative..." -ForegroundColor Yellow
        Start-Sleep -Seconds $delay
        $delay = [Math]::Min($delay * 1.5, 60)  # Max 60 secondes
    }
    
    $attempt++
}

Write-Host ""
Write-Host "❌ Échec après $maxAttempts tentatives" -ForegroundColor Red
Write-Host ""
Write-Host "GitHub semble avoir des problèmes. Réessayez plus tard ou:" -ForegroundColor Yellow
Write-Host "1. Vérifiez https://www.githubstatus.com/"
Write-Host "2. Le commit est prêt localement (e0009a55)"
Write-Host "3. Vous pouvez pousser manuellement plus tard avec: git push origin main"
exit 1

