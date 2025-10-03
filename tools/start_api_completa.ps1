# Script para Iniciar API COMPLETA do Sistema Multiagente
# Com Orquestrador, LLMs, RAG e todos os recursos

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API COMPLETA - Sistema Multiagente" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar ambiente virtual
Write-Host "[1/5] Verificando ambiente virtual..." -ForegroundColor Yellow

if ($env:VIRTUAL_ENV) {
    Write-Host "  OK: Ambiente virtual ativo" -ForegroundColor Green
    Write-Host "  Path: $env:VIRTUAL_ENV" -ForegroundColor Gray
} else {
    Write-Host "  AVISO: Ambiente virtual nao ativo" -ForegroundColor Red
    Write-Host "  Ativando .venv..." -ForegroundColor Yellow
    
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        . .\.venv\Scripts\Activate.ps1
        Write-Host "  OK: Ambiente virtual ativado" -ForegroundColor Green
    } else {
        Write-Host "  ERRO: .venv nao encontrado" -ForegroundColor Red
        Write-Host "  Crie com: python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
}

# 2. Verificar Python
Write-Host ""
Write-Host "[2/5] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Green

# 3. Verificar configuracao
Write-Host ""
Write-Host "[3/5] Verificando configuracao..." -ForegroundColor Yellow

if (Test-Path "configs\.env") {
    Write-Host "  OK: Arquivo .env encontrado" -ForegroundColor Green
    
    # Verificar variaveis criticas
    $envContent = Get-Content "configs\.env" -Raw
    
    $checks = @{
        "SUPABASE_URL" = $envContent -match "SUPABASE_URL=.+";
        "SUPABASE_KEY" = $envContent -match "SUPABASE_KEY=.+";
        "GOOGLE_API_KEY" = $envContent -match "GOOGLE_API_KEY=.+";
        "GROQ_API_KEY" = $envContent -match "GROQ_API_KEY=.+";
        "OPENAI_API_KEY" = $envContent -match "OPENAI_API_KEY=.+";
    }
    
    foreach ($check in $checks.GetEnumerator()) {
        if ($check.Value) {
            Write-Host "    $($check.Key): Configurado" -ForegroundColor Green
        } else {
            Write-Host "    $($check.Key): Nao configurado" -ForegroundColor Yellow
        }
    }
    
    # Verificar se pelo menos 1 LLM está configurado
    $hasLLM = $checks["GOOGLE_API_KEY"] -or $checks["GROQ_API_KEY"] -or $checks["OPENAI_API_KEY"]
    
    if (-not $hasLLM) {
        Write-Host ""
        Write-Host "  AVISO: Nenhum LLM configurado!" -ForegroundColor Red
        Write-Host "  Configure pelo menos um:" -ForegroundColor Yellow
        Write-Host "    - GOOGLE_API_KEY (Google Gemini)" -ForegroundColor Gray
        Write-Host "    - GROQ_API_KEY (Groq)" -ForegroundColor Gray
        Write-Host "    - OPENAI_API_KEY (OpenAI)" -ForegroundColor Gray
        Write-Host ""
        $continue = Read-Host "Continuar mesmo assim? (s/N)"
        if ($continue -ne "s" -and $continue -ne "S") {
            exit 1
        }
    }
    
} else {
    Write-Host "  ERRO: configs\.env nao encontrado" -ForegroundColor Red
    Write-Host "  Copie de: configs\.env.example" -ForegroundColor Yellow
    exit 1
}

# 4. Verificar dependencias criticas
Write-Host ""
Write-Host "[4/5] Verificando dependencias criticas..." -ForegroundColor Yellow

$packages = @("fastapi", "uvicorn", "langchain", "supabase", "pandas")
$missing = @()

foreach ($pkg in $packages) {
    try {
        $result = python -c "import $($pkg.Replace('-','_')); print('OK')" 2>&1
        if ($result -like "*OK*") {
            Write-Host "    $pkg OK" -ForegroundColor Green
        } else {
            $missing += $pkg
            Write-Host "    $pkg Ausente" -ForegroundColor Red
        }
    } catch {
        $missing += $pkg
        Write-Host "    $pkg Ausente" -ForegroundColor Red
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "  ERRO: Dependencias ausentes: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "  Instale com: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 5. Iniciar API
Write-Host ""
Write-Host "[5/5] Iniciando API COMPLETA..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SISTEMA MULTIAGENTE INICIANDO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Componentes:" -ForegroundColor White
Write-Host "  - Orquestrador Central" -ForegroundColor Gray
Write-Host "  - LLMs (Google Gemini / Groq / OpenAI)" -ForegroundColor Gray
Write-Host "  - Sistema RAG com Busca Semantica" -ForegroundColor Gray
Write-Host "  - Analise CSV Avancada" -ForegroundColor Gray
Write-Host "  - Deteccao de Fraudes com IA" -ForegroundColor Gray
Write-Host "  - Chat Contextual" -ForegroundColor Gray
Write-Host "  - Supabase (Persistencia)" -ForegroundColor Gray
Write-Host ""
Write-Host "Endpoints:" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - ReDoc: http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Aguarde inicializacao..." -ForegroundColor Yellow
Write-Host ""

# Iniciar com uvicorn
try {
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host ""
    Write-Host "ERRO ao iniciar API:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente:" -ForegroundColor Yellow
    Write-Host "  python src/api/main.py" -ForegroundColor Gray
    Write-Host "  OU" -ForegroundColor Gray
    Write-Host "  python -m src.api.main" -ForegroundColor Gray
    exit 1
}
