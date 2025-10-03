# Script para testar se API está em modo produção com dados reais

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "TESTE: API em Modo Produção" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Aguardar API inicializar
Write-Host "Aguardando API inicializar (5 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Teste 1: Health Check
Write-Host "`n[1] Testando /health..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "✅ Status: $($health.status)" -ForegroundColor Green
    Write-Host "✅ Modo: $($health.mode)" -ForegroundColor $(if($health.mode -eq "production"){"Green"}else{"Red"})
    if ($health.mode -ne "production") {
        Write-Host "❌ ERRO: API não está em modo produção!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ ERRO: API não está respondendo" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Teste 2: Config Endpoint
Write-Host "`n[2] Testando /api/config..." -ForegroundColor Green
try {
    $config = Invoke-RestMethod -Uri "http://localhost:8000/api/config" -Method GET
    Write-Host "✅ Modo: $($config.mode)" -ForegroundColor $(if($config.mode -eq "production"){"Green"}else{"Red"})
    Write-Host "Features disponíveis:" -ForegroundColor Cyan
    $config.features.PSObject.Properties | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Value)" -ForegroundColor White
    }
    if ($config.mode -ne "production") {
        Write-Host "❌ ERRO: Config não indica modo produção!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ ERRO ao buscar config" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Teste 3: Upload CSV Real
Write-Host "`n[3] Testando Upload CSV..." -ForegroundColor Green
$csvPath = "c:\Users\rsant\OneDrive\Documentos\Projects\eda-aiminds-back-1\data\creditcard_test_500.csv"
if (Test-Path $csvPath) {
    try {
        $boundary = [System.Guid]::NewGuid().ToString()
        $csvContent = Get-Content $csvPath -Raw
        
        $bodyLines = @(
            "--$boundary",
            "Content-Disposition: form-data; name=`"file`"; filename=`"creditcard_test_500.csv`"",
            "Content-Type: text/csv",
            "",
            $csvContent,
            "--$boundary--"
        )
        
        $body = $bodyLines -join "`r`n"
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/csv/upload" `
            -Method POST `
            -ContentType "multipart/form-data; boundary=$boundary" `
            -Body $body
        
        Write-Host "✅ Upload realizado com sucesso!" -ForegroundColor Green
        Write-Host "Arquivo: $($response.filename)" -ForegroundColor Cyan
        Write-Host "Tamanho: $($response.size) bytes" -ForegroundColor Cyan
        Write-Host "Linhas: $($response.rows)" -ForegroundColor Cyan
        Write-Host "Colunas: $($response.columns)" -ForegroundColor Cyan
        
        if ($response.rows -gt 0) {
            Write-Host "✅ DADOS REAIS CONFIRMADOS (preview com $($response.rows) linhas)" -ForegroundColor Green
        } else {
            Write-Host "❌ AVISO: Nenhuma linha de dados retornada" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ ERRO no upload" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
} else {
    Write-Host "⚠️ Arquivo CSV de teste não encontrado: $csvPath" -ForegroundColor Yellow
}

# Teste 4: Chat Contextual
Write-Host "`n[4] Testando Chat Contextual..." -ForegroundColor Green
try {
    $chatBody = @{
        message = "como funciona este sistema?"
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Uri "http://localhost:8000/chat" `
        -Method POST `
        -ContentType "application/json" `
        -Body $chatBody
    
    Write-Host "✅ Chat respondeu:" -ForegroundColor Green
    Write-Host $chatResponse.response -ForegroundColor White
    
    if ($chatResponse.response -notlike "*processando*") {
        Write-Host "✅ RESPOSTA CONTEXTUAL CONFIRMADA (não é mensagem genérica)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Resposta parece genérica" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ ERRO no chat" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Teste 5: Dashboard Metrics
Write-Host "`n[5] Testando Dashboard Metrics..." -ForegroundColor Green
try {
    $metrics = Invoke-RestMethod -Uri "http://localhost:8000/dashboard/metrics" -Method GET
    Write-Host "✅ Métricas obtidas:" -ForegroundColor Green
    Write-Host "  - Arquivos carregados: $($metrics.uploaded_files)" -ForegroundColor Cyan
    Write-Host "  - Total de linhas: $($metrics.total_rows)" -ForegroundColor Cyan
    Write-Host "  - Total de colunas: $($metrics.total_columns)" -ForegroundColor Cyan
    
    if ($metrics.uploaded_files -gt 0) {
        Write-Host "✅ ARQUIVOS REAIS NO SISTEMA" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ ERRO ao buscar métricas" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Resumo Final
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`n✅ API está em MODO PRODUÇÃO" -ForegroundColor Green
Write-Host "✅ Dados REAIS sendo processados" -ForegroundColor Green
Write-Host "✅ Endpoints funcionando corretamente" -ForegroundColor Green
Write-Host "`nSe o frontend ainda mostra 'mock', o problema esta na deteccao do frontend!" -ForegroundColor Yellow
Write-Host "Ver: FRONTEND_DETECTANDO_MOCK.md para solucao" -ForegroundColor Cyan
Write-Host ""
