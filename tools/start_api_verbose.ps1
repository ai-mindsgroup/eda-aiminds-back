# Iniciar API Completa com Monitoramento de Progresso

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando API Completa - Modo Verbose" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "AVISO: Primeira execucao pode demorar 2-5 minutos" -ForegroundColor Yellow
Write-Host "Motivo: Download de modelos de embeddings (~500MB)" -ForegroundColor Gray
Write-Host ""

Write-Host "Progresso:" -ForegroundColor White
Write-Host "  [1/4] Carregando modulos Python..." -ForegroundColor Cyan

# Definir log level como INFO para ver mais detalhes
$env:LOG_LEVEL = "INFO"

Write-Host "  [2/4] Inicializando FastAPI..." -ForegroundColor Cyan
Write-Host "  [3/4] Baixando modelos de embeddings (se necessario)..." -ForegroundColor Cyan
Write-Host "  [4/4] Iniciando servidor..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Aguarde... (pode demorar na primeira vez)" -ForegroundColor Yellow
Write-Host "Pressione Ctrl+C para cancelar" -ForegroundColor Gray
Write-Host ""

# Iniciar com verbose
python -m src.api.main
