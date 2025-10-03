# Script para Iniciar API - Modo Produção
# ==========================================

Write-Host "🚀 Iniciando EDA AI Minds API" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

# Verificar se Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado! Instale Python primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se está no diretório correto
if (-not (Test-Path "api_simple.py")) {
    Write-Host "❌ Arquivo api_simple.py não encontrado!" -ForegroundColor Red
    Write-Host "   Execute este script no diretório raiz do projeto." -ForegroundColor Yellow
    exit 1
}

# Parar qualquer processo na porta 8000
Write-Host "🔍 Verificando porta 8000..." -ForegroundColor Yellow
try {
    $port = 8000
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $processes = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($proc in $processes) {
            Write-Host "⏹️  Parando processo $proc na porta $port..." -ForegroundColor Yellow
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        Write-Host "✅ Porta $port liberada" -ForegroundColor Green
    } else {
        Write-Host "✅ Porta $port disponível" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Não foi possível verificar a porta, mas continuando..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Informações da API:" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8000" -ForegroundColor White
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Config: http://localhost:8000/api/config" -ForegroundColor White
Write-Host "   Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "📋 Funcionalidades Disponíveis:" -ForegroundColor Cyan
Write-Host "   ✅ Upload de CSV" -ForegroundColor Green
Write-Host "   ✅ Análise de Dados" -ForegroundColor Green
Write-Host "   ✅ Dashboard com Métricas" -ForegroundColor Green
Write-Host "   ✅ Chat Básico" -ForegroundColor Green
Write-Host "   ⚠️  Modo: Produção (sem LLM avançado)" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏹️  Pressione Ctrl+C para parar o servidor" -ForegroundColor Red
Write-Host "=" * 60
Write-Host ""

# Iniciar API
try {
    uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host ""
    Write-Host "❌ Erro ao iniciar API: $_" -ForegroundColor Red
    Write-Host "   Verifique se uvicorn está instalado: pip install uvicorn" -ForegroundColor Yellow
    exit 1
}
