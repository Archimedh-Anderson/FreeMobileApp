# FreeMobilaChat - Quick Start Script
# PowerShell script for easy application startup

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FreeMobilaChat - Application Launcher    " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
$expectedPath = "FreeMobilaChat"
$currentPath = (Get-Location).Path
if (-not ($currentPath -like "*$expectedPath*")) {
    Write-Host "⚠️  Warning: Not in FreeMobilaChat directory" -ForegroundColor Yellow
    Write-Host "Current: $currentPath" -ForegroundColor Yellow
    Write-Host ""
    $changePath = Read-Host "Change to FreeMobilaChat directory? (y/n)"
    if ($changePath -eq 'y') {
        Set-Location "c:\Users\ander\Desktop\FreeMobilaChat"
        Write-Host "✓ Changed to FreeMobilaChat directory" -ForegroundColor Green
    }
}

Write-Host "📍 Current Directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Menu
Write-Host "Select startup option:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] Start Application (Normal)" -ForegroundColor Green
Write-Host "  [2] Start with Cache Clear (Fresh)" -ForegroundColor Yellow
Write-Host "  [3] Run Tests First, Then Start" -ForegroundColor Cyan
Write-Host "  [4] Stop Running Instances" -ForegroundColor Red
Write-Host "  [5] Check Application Status" -ForegroundColor Magenta
Write-Host "  [6] Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter choice [1-6]"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 Starting FreeMobilaChat..." -ForegroundColor Green
        Write-Host ""
        streamlit run streamlit_app/app.py --server.port 8502 --server.headless false
    }
    
    "2" {
        Write-Host ""
        Write-Host "🧹 Clearing cache..." -ForegroundColor Yellow
        Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
        Remove-Item -Path "$env:USERPROFILE\.streamlit\cache" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Cache cleared" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 Starting FreeMobilaChat with fresh cache..." -ForegroundColor Green
        Write-Host ""
        Start-Sleep -Seconds 1
        streamlit run streamlit_app/app.py --server.port 8502 --server.headless false
    }
    
    "3" {
        Write-Host ""
        Write-Host "🧪 Running tests..." -ForegroundColor Cyan
        Write-Host ""
        python -m pytest tests/test_unit_preprocessing.py -v --tb=short
        
        $runApp = Read-Host "`nTests complete. Start application? (y/n)"
        if ($runApp -eq 'y') {
            Write-Host ""
            Write-Host "🚀 Starting FreeMobilaChat..." -ForegroundColor Green
            Write-Host ""
            streamlit run streamlit_app/app.py --server.port 8502 --server.headless false
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "🛑 Stopping Python processes..." -ForegroundColor Red
        Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
        Write-Host "✓ All Python processes stopped" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "5" {
        Write-Host ""
        Write-Host "🔍 Checking application status..." -ForegroundColor Magenta
        Write-Host ""
        
        # Check Python processes
        $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
        if ($pythonProcs) {
            Write-Host "✓ Python processes running: $($pythonProcs.Count)" -ForegroundColor Green
            $pythonProcs | Select-Object Id, ProcessName, CPU | Format-Table
        } else {
            Write-Host "✗ No Python processes running" -ForegroundColor Red
        }
        
        # Check port 8502
        Write-Host ""
        Write-Host "Checking port 8502..." -ForegroundColor Gray
        $portCheck = netstat -ano | findstr :8502
        if ($portCheck) {
            Write-Host "✓ Port 8502 is in use" -ForegroundColor Green
            Write-Host $portCheck
        } else {
            Write-Host "✗ Port 8502 is not in use" -ForegroundColor Red
        }
        
        # Try to access the app
        Write-Host ""
        Write-Host "Testing HTTP connection..." -ForegroundColor Gray
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8502" -TimeoutSec 3 -UseBasicParsing
            Write-Host "✓ Application accessible at http://localhost:8502" -ForegroundColor Green
            Write-Host "  Status Code: $($response.StatusCode)" -ForegroundColor Gray
        } catch {
            Write-Host "✗ Application not accessible at http://localhost:8502" -ForegroundColor Red
        }
        
        # Check Ollama
        Write-Host ""
        Write-Host "Checking Ollama server..." -ForegroundColor Gray
        try {
            $ollamaResponse = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
            Write-Host "✓ Ollama server running" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Ollama server not running (LLM features unavailable)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "6" {
        Write-Host ""
        Write-Host "👋 Goodbye!" -ForegroundColor Cyan
        exit
    }
    
    default {
        Write-Host ""
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
}
