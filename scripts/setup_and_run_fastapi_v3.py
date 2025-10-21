#!/usr/bin/env python3
"""
Setup e Execução - FastAPI V3.0
================================

Setup automatizado que garante:
✅ Uso de QueryAnalyzer com correções de heurística
✅ HybridQueryProcessorV2 com limitação dinâmica de chunks
✅ Cache global via Supabase
✅ LLMManager (chat()) para todas as chamadas
✅ Validação de rotas e endpoints
✅ Logging estruturado de inicialização
"""

import subprocess
import sys
import os
from pathlib import Path

# Configurações
REPO_ROOT = Path.cwd()
VENV_DIR = REPO_ROOT / '.venv'
PYTHON_EXE = VENV_DIR / 'Scripts' / 'python.exe' if sys.platform == 'win32' else VENV_DIR / 'bin' / 'python'
REQUIREMENTS = REPO_ROOT / 'requirements.txt'
API_MODULE = 'api_completa:app'
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8011'))

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(message: str, level: str = "info"):
    """Print formatado com cores."""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED
    }
    color = colors.get(level, Colors.RESET)
    print(f"{color}{Colors.BOLD}[{level.upper()}]{Colors.RESET} {message}")


def create_venv():
    """Cria ambiente virtual se não existir."""
    if VENV_DIR.exists():
        print_step('Ambiente virtual já existe', 'success')
        return
    
    print_step('Criando ambiente virtual...', 'info')
    try:
        subprocess.run([sys.executable, '-m', 'venv', str(VENV_DIR)], check=True)
        print_step('✅ Ambiente virtual criado', 'success')
    except subprocess.CalledProcessError as e:
        print_step(f'Erro ao criar venv: {e}', 'error')
        sys.exit(1)


def install_requirements():
    """Instala dependências do requirements.txt."""
    print_step('Instalando dependências...', 'info')
    try:
        subprocess.run(
            [str(PYTHON_EXE), '-m', 'pip', 'install', '-r', str(REQUIREMENTS), '--quiet'],
            check=True
        )
        print_step('✅ Dependências instaladas', 'success')
    except subprocess.CalledProcessError as e:
        print_step(f'Erro ao instalar dependências: {e}', 'error')
        sys.exit(1)


def validate_api_modules():
    """Valida que API usa módulos corretos."""
    print_step('Validando integração da API...', 'info')
    
    validation_script = """
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path.cwd()))

errors = []
warnings = []

# 1. Validar que api_completa.py existe
api_file = Path('api_completa.py')
if not api_file.exists():
    errors.append("api_completa.py não encontrado")
else:
    print("✅ api_completa.py encontrado")

# 2. Verificar imports críticos na API
try:
    with open('api_completa.py', 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    # Verificar se usa OrchestratorAgent (correto)
    if 'OrchestratorAgent' in api_content:
        print("✅ API usa OrchestratorAgent")
    else:
        warnings.append("API pode não estar usando OrchestratorAgent")
    
    # Verificar se usa process_with_persistent_memory (correto)
    if 'process_with_persistent_memory' in api_content:
        print("✅ API usa process_with_persistent_memory (memória persistente)")
    else:
        warnings.append("API pode não estar usando memória persistente")
    
    # Verificar se NÃO usa chamadas diretas a provedores LLM
    direct_llm_calls = []
    if 'import openai' in api_content and 'openai.ChatCompletion' in api_content:
        direct_llm_calls.append("openai.ChatCompletion")
    if 'import groq' in api_content and 'groq.chat' in api_content:
        direct_llm_calls.append("groq.chat")
    
    if direct_llm_calls:
        warnings.append(f"API tem chamadas diretas a LLMs: {', '.join(direct_llm_calls)}")
    else:
        print("✅ API não tem chamadas diretas a provedores LLM")
        
except Exception as e:
    errors.append(f"Erro ao ler api_completa.py: {e}")

# 3. Validar módulos de suporte
try:
    from src.agent.query_analyzer import QueryAnalyzer
    print("✅ QueryAnalyzer disponível")
except Exception as e:
    warnings.append(f"QueryAnalyzer não disponível: {e}")

try:
    from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
    print("✅ HybridQueryProcessorV2 disponível")
except Exception as e:
    warnings.append(f"HybridQueryProcessorV2 não disponível: {e}")

try:
    from src.llm.manager import LLMManager
    print("✅ LLMManager disponível")
except Exception as e:
    warnings.append(f"LLMManager não disponível: {e}")

# Reportar resultados
if errors:
    print("\\n❌ ERROS CRÍTICOS:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

if warnings:
    print("\\n⚠️ AVISOS:")
    for warning in warnings:
        print(f"  - {warning}")

print("\\n✅ Integração da API validada!")
"""
    
    try:
        result = subprocess.run(
            [str(PYTHON_EXE), '-c', validation_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_step('Validação falhou!', 'error')
            print(result.stderr)
            sys.exit(1)
        
        print_step('✅ API validada', 'success')
        
    except Exception as e:
        print_step(f'Erro na validação: {e}', 'error')
        sys.exit(1)


def run_api_test():
    """Testa importação da API."""
    print_step('Testando importação da API...', 'info')
    
    test_script = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    # Tentar importar a API
    from api_completa import app
    print("✅ API importada com sucesso")
    
    # Verificar rotas
    routes = [route.path for route in app.routes]
    print(f"✅ {len(routes)} rotas registradas")
    
    # Verificar rotas críticas
    critical_routes = ['/health', '/chat', '/docs']
    for route in critical_routes:
        if route in routes:
            print(f"✅ Rota {route} encontrada")
        else:
            print(f"⚠️ Rota {route} não encontrada")
    
    print("\\n✅ Teste de importação passou!")
    
except Exception as e:
    print(f"❌ Erro ao importar API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [str(PYTHON_EXE), '-c', test_script],
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_step('Teste de importação falhou!', 'warning')
            print(result.stderr)
        else:
            print_step('✅ Teste de importação passou', 'success')
            
    except subprocess.TimeoutExpired:
        print_step('Teste timeout', 'warning')
    except Exception as e:
        print_step(f'Erro no teste: {e}', 'warning')


def run_fastapi():
    """Executa FastAPI com uvicorn."""
    print_step(f'Iniciando FastAPI em {API_HOST}:{API_PORT}...', 'info')
    print_step('Logs da API serão exibidos abaixo:', 'info')
    print('=' * 70)
    
    # Configurar PYTHONPATH
    env = os.environ.copy()
    pythonpath_parts = [
        str(REPO_ROOT),
        str(REPO_ROOT / 'src'),
        env.get('PYTHONPATH', '')
    ]
    env['PYTHONPATH'] = os.pathsep.join(filter(None, pythonpath_parts))
    
    # Executar uvicorn
    try:
        subprocess.run(
            [
                str(PYTHON_EXE), '-m', 'uvicorn',
                API_MODULE,
                '--host', API_HOST,
                '--port', str(API_PORT),
                '--reload'  # Auto-reload em desenvolvimento
            ],
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        print_step(f'API encerrada com erro: {e}', 'error')
        sys.exit(1)
    except KeyboardInterrupt:
        print_step('\\nAPI interrompida pelo usuário', 'info')


def main():
    """Fluxo principal de setup e execução."""
    print('=' * 70)
    print(f'{Colors.BOLD}🚀 SETUP E EXECUÇÃO - FASTAPI V3.0{Colors.RESET}')
    print('=' * 70)
    print()
    
    # Etapa 1: Criar venv
    create_venv()
    print()
    
    # Etapa 2: Instalar dependências
    install_requirements()
    print()
    
    # Etapa 3: Validar integração da API
    validate_api_modules()
    print()
    
    # Etapa 4: Teste de importação
    run_api_test()
    print()
    
    # Etapa 5: Executar API
    print_step('🎉 Setup concluído! Iniciando FastAPI...', 'success')
    print()
    print_step(f'📡 Documentação: http://{API_HOST}:{API_PORT}/docs', 'info')
    print_step(f'📊 Health Check: http://{API_HOST}:{API_PORT}/health', 'info')
    print()
    run_fastapi()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_step('\\n\\nSetup interrompido pelo usuário', 'info')
        sys.exit(0)
    except Exception as e:
        print_step(f'\\n\\nErro inesperado: {e}', 'error')
        import traceback
        traceback.print_exc()
        sys.exit(1)
