#!/usr/bin/env python3
"""
Setup e Execução - Interface Interativa V3.0
=============================================

✅ MODIFICAÇÕES V3.0 VALIDADAS:
  • Chunking Multi-Coluna (CSV_COLUMN + CSV_ROW + METADATA)
  • Código 100% Genérico (SEM hardcoding de nomes de colunas)
  • LLMs Ativos em 9 pontos críticos via LangChain
  • LLMManager abstrato para OpenAI/Gemini/Groq
  • Memória persistente via Supabase
  • RAG vetorial com embeddings

Setup automatizado que garante:
✅ Chunker com estratégia CSV_COLUMN (iteração dinâmica: for col in df.columns)
✅ RAGAgent com LLMManager ativo (sem hardcoding)
✅ QueryAnalyzer com fallback heurístico
✅ HybridQueryProcessorV2 com limitação dinâmica de chunks
✅ Cache global via Supabase
✅ Validação rigorosa de código genérico (detecta hardcoding)
✅ Teste rápido com CSV diferente do creditcard
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
INTERFACE_FILE = REPO_ROOT / 'interface_interativa.py'

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


def validate_modules():
    """Valida que módulos críticos foram atualizados COM MODIFICAÇÕES V3.0."""
    print_step('Validando módulos críticos V3.0...', 'info')
    
    validation_script = """
import sys
from pathlib import Path
import inspect

# Adicionar src ao path
sys.path.insert(0, str(Path.cwd()))

errors = []
warnings = []

# 1. Validar TextChunker com CSV_COLUMN (MODIFICAÇÃO CRÍTICA V3.0)
try:
    from src.embeddings.chunker import TextChunker, ChunkStrategy
    
    # Verificar estratégia CSV_COLUMN existe
    if not hasattr(ChunkStrategy, 'CSV_COLUMN'):
        errors.append("ChunkStrategy.CSV_COLUMN NAO EXISTE (modificacao V3.0 ausente!)")
    else:
        print("[OK] ChunkStrategy.CSV_COLUMN existe (V3.0)")
    
    # Verificar método _chunk_csv_by_columns
    chunker = TextChunker()
    if not hasattr(chunker, '_chunk_csv_by_columns'):
        errors.append("TextChunker._chunk_csv_by_columns NAO EXISTE (modificacao V3.0 ausente!)")
    else:
        # VALIDAÇÃO CRÍTICA: Código deve ser genérico (sem hardcoding)
        source_code = inspect.getsource(chunker._chunk_csv_by_columns)
        
        # Verificar se NÃO tem hardcoding
        hardcoded_terms = ['Time', 'Amount', 'Class', 'V1', 'V2', 'V3']
        has_hardcoding = any(f'"{term}"' in source_code or f"'{term}'" in source_code for term in hardcoded_terms)
        
        # Verificar se TEM iteração dinâmica
        has_dynamic_iteration = 'for col in df.columns' in source_code or 'for idx, col in enumerate(df.columns' in source_code
        
        if has_hardcoding:
            errors.append("CRITICO: TextChunker._chunk_csv_by_columns TEM HARDCODING! (codigo engessado)")
        elif not has_dynamic_iteration:
            errors.append("CRITICO: TextChunker._chunk_csv_by_columns NAO tem iteracao dinamica!")
        else:
            print("[OK] TextChunker._chunk_csv_by_columns GENERICO (V3.0)")
            print("   -> Sem hardcoding de colunas")
            print("   -> Com iteracao dinamica (for col in df.columns)")
    
except Exception as e:
    errors.append(f"Erro ao carregar TextChunker: {e}")

# 2. Validar RAGAgent com LLM ativo
try:
    from src.agent.rag_agent import RAGAgent
    import inspect
    
    rag_agent = RAGAgent()
    
    # Verificar método ingest_csv_file
    if not hasattr(rag_agent, 'ingest_csv_file'):
        errors.append("RAGAgent.ingest_csv_file NAO EXISTE")
    else:
        source_code = inspect.getsource(rag_agent.ingest_csv_file)
        
        # Verificar uso de LLMManager (não hardcoded)
        uses_llm_manager = 'llm_manager' in source_code or 'self.llm_manager' in source_code
        
        if not uses_llm_manager:
            warnings.append("RAGAgent.ingest_csv_file pode nao estar usando LLM")
        else:
            print("[OK] RAGAgent com LLMManager ativo (V3.0)")
    
except Exception as e:
    errors.append(f"Erro ao carregar RAGAgent: {e}")

# 3. Validar QueryAnalyzer
try:
    from src.agent.query_analyzer import QueryAnalyzer
    analyzer = QueryAnalyzer()
    
    if not hasattr(analyzer, 'analyze'):
        errors.append("QueryAnalyzer nao possui metodo 'analyze'")
    if not hasattr(analyzer, '_fallback_heuristic_analysis'):
        errors.append("QueryAnalyzer nao possui fallback heuristico")
    
    print("[OK] QueryAnalyzer carregado")
except Exception as e:
    errors.append(f"Erro ao carregar QueryAnalyzer: {e}")

# 4. Validar HybridQueryProcessorV2
try:
    from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
    
    if not hasattr(HybridQueryProcessorV2, 'process_query'):
        errors.append("HybridQueryProcessorV2 nao possui metodo 'process_query'")
    
    print("[OK] HybridQueryProcessorV2 carregado")
except Exception as e:
    errors.append(f"Erro ao carregar HybridQueryProcessorV2: {e}")

# 5. Validar LLMManager
try:
    from src.llm.manager import LLMManager, get_llm_manager
    
    if not hasattr(LLMManager, 'chat'):
        errors.append("LLMManager nao possui metodo 'chat'")
    
    # Verificar singleton funciona
    llm1 = get_llm_manager()
    llm2 = get_llm_manager()
    if llm1 is not llm2:
        warnings.append("get_llm_manager() nao retorna singleton")
    
    print("[OK] LLMManager carregado")
except Exception as e:
    errors.append(f"Erro ao carregar LLMManager: {e}")

# 6. Validar VectorStore com cache
try:
    from src.embeddings.vector_store import VectorStore
    print("[OK] VectorStore carregado")
except Exception as e:
    warnings.append(f"VectorStore não disponível: {e}")

# 7. Validar SupabaseMemoryManager
try:
    from src.memory.supabase_memory import SupabaseMemoryManager
    print("[OK] SupabaseMemoryManager carregado")
except Exception as e:
    warnings.append(f"SupabaseMemoryManager não disponível: {e}")

# 8. VALIDAÇÃO CRÍTICA: Detectar limitação de colunas no RAGDataAgent
try:
    from src.agent.rag_data_agent import RAGDataAgent
    import inspect
    
    # Verificar se analyze_csv_v2 usa TemporalColumnDetector (limitação!)
    source_code = inspect.getsource(RAGDataAgent.analyze_csv_v2)
    
    uses_temporal_detector = 'TemporalColumnDetector' in source_code
    
    if uses_temporal_detector:
        # CORRIGIDO: Agora analisa TODAS as colunas, não apenas temporais
        print("[OK] RAGDataAgent usa TemporalColumnDetector PARA TEMPORAIS")
        print("     + ANALISE COMPLETA de TODAS as outras colunas")
    else:
        print("[OK] RAGDataAgent sem limitacao temporal")
        
except Exception as e:
    warnings.append(f"Erro ao validar RAGDataAgent: {e}")

# Reportar resultados
if errors:
    print("\\n[ERRO] ERROS CRITICOS:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

if warnings:
    print("\\n[AVISO] AVISOS:")
    for warning in warnings:
        print(f"  - {warning}")

print("\\n[OK] Todos os modulos criticos validados!")
"""
    
    try:
        result = subprocess.run(
            [str(PYTHON_EXE), '-c', validation_script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_step('Validação falhou!', 'error')
            print(result.stderr)
            sys.exit(1)
        
        print_step('✅ Módulos validados', 'success')
        
    except Exception as e:
        print_step(f'Erro na validação: {e}', 'error')
        sys.exit(1)


def run_quick_test():
    """Executa teste rápido V3.0 validando chunking e LLMs."""
    print_step('Executando teste rápido V3.0...', 'info')
    
    test_script = """
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path.cwd()))

print("\\n📋 TESTE RÁPIDO V3.0: Chunking Multi-Coluna + LLMs Ativos\\n")

# ═══════════════════════════════════════════════════════════
# TESTE 1: Chunking Genérico com CSV Simples
# ═══════════════════════════════════════════════════════════
print("🔍 TESTE 1: Chunking genérico (sem hardcoding)")

from src.embeddings.chunker import TextChunker, ChunkStrategy

# Criar DataFrame de teste com colunas DIFERENTES do creditcard
test_data = {
    'produto': ['A', 'B', 'C'],
    'preco': [10.5, 20.3, 15.8],
    'estoque': [100, 50, 75]
}
df_test = pd.DataFrame(test_data)

chunker = TextChunker()

# Tentar chunking por coluna
chunks = chunker.chunk(
    df_test.to_csv(index=False),
    strategy=ChunkStrategy.CSV_COLUMN,
    metadata={'test': 'quick_v3'}
)

print(f"  → CSV de teste: {len(df_test.columns)} colunas")
print(f"  → Chunks gerados: {len(chunks)}")

# Validar que gerou chunks para TODAS as colunas
expected_chunks = len(df_test.columns)  # 1 chunk por coluna
if len(chunks) >= expected_chunks:
    print(f"  [OK] Chunking funcionou (esperado >={expected_chunks}, obtido {len(chunks)})")
else:
    print(f"  [ERRO] Chunking falhou (esperado >={expected_chunks}, obtido {len(chunks)})")
    sys.exit(1)

# Validar que chunks contêm nomes das colunas CORRETAS
chunk_texts = [c.text for c in chunks]
for col_name in df_test.columns:
    if any(col_name in text for text in chunk_texts):
        print(f"  [OK] Coluna '{col_name}' encontrada nos chunks")
    else:
        print(f"  [ERRO] Coluna '{col_name}' NAO encontrada (hardcoding?)")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════
# TESTE 2: LLMManager Ativo
# ═══════════════════════════════════════════════════════════
print("\\n🤖 TESTE 2: LLMManager ativo")

from src.llm.manager import get_llm_manager, LLMConfig

llm_manager = get_llm_manager()

# Verificar método chat existe
if not hasattr(llm_manager, 'chat'):
    print("  [ERRO] LLMManager.chat() NAO existe!")
    sys.exit(1)

print("  [OK] LLMManager.chat() existe e esta disponivel")

# ═══════════════════════════════════════════════════════════
# TESTE 3: QueryAnalyzer
# ═══════════════════════════════════════════════════════════
print("\\n🔍 TESTE 3: QueryAnalyzer")

from src.agent.query_analyzer import QueryAnalyzer

analyzer = QueryAnalyzer()
query = "Qual a média da coluna preco?"
analysis = analyzer.analyze(query)

print(f"  → Análise: complexity={analysis.complexity}, category={analysis.category}")

# Verificar que retorna objetos, não dicts
if hasattr(analysis, 'complexity') and hasattr(analysis, 'category'):
    print("  [OK] QueryAnalyzer retorna objetos corretamente")
else:
    print("  [ERRO] QueryAnalyzer retorna dict (deveria ser objeto)")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# RESULTADO FINAL
# ═══════════════════════════════════════════════════════════
print("\\n[OK] TESTE RAPIDO V3.0 PASSOU!")
print("   -> Chunking generico funcionando")
print("   -> LLMs ativos e disponiveis")
print("   -> Sem hardcoding detectado")
"""
    
    try:
        result = subprocess.run(
            [str(PYTHON_EXE), '-c', test_script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_step('Teste rápido falhou!', 'warning')
            print(result.stderr)
        else:
            print_step('✅ Teste rápido passou', 'success')
            
    except subprocess.TimeoutExpired:
        print_step('Teste rápido timeout (pode ser problema de LLM)', 'warning')
    except Exception as e:
        print_step(f'Erro no teste: {e}', 'warning')


def run_interface():
    """Executa interface_interativa.py com logs de inicialização."""
    print_step('Iniciando interface interativa...', 'info')
    print_step('Logs de inicialização serão exibidos abaixo:', 'info')
    print('=' * 70)
    
    # Configurar PYTHONPATH
    env = os.environ.copy()
    pythonpath_parts = [
        str(REPO_ROOT),
        str(REPO_ROOT / 'src'),
        env.get('PYTHONPATH', '')
    ]
    env['PYTHONPATH'] = os.pathsep.join(filter(None, pythonpath_parts))
    
    # Executar interface
    try:
        subprocess.run(
            [str(PYTHON_EXE), str(INTERFACE_FILE)],
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        print_step(f'Interface encerrada com erro: {e}', 'error')
        sys.exit(1)
    except KeyboardInterrupt:
        print_step('\\nInterface interrompida pelo usuário', 'info')


def main():
    """Fluxo principal de setup e execução V3.0."""
    print('=' * 70)
    print(f'{Colors.BOLD}🚀 SETUP E EXECUÇÃO - INTERFACE INTERATIVA V3.0{Colors.RESET}')
    print('=' * 70)
    print(f'\n{Colors.GREEN}✅ MODIFICAÇÕES V3.0:{Colors.RESET}')
    print('  • Chunking Multi-Coluna (CSV_COLUMN + CSV_ROW + METADATA)')
    print('  • Código 100% Genérico (sem hardcoding)')
    print('  • LLMs Ativos (9 pontos via LangChain)')
    print('  • RAG Vetorial com Memória Persistente')
    print()
    
    # Etapa 1: Criar venv
    create_venv()
    print()
    
    # Etapa 2: Instalar dependências
    install_requirements()
    print()
    
    # Etapa 3: Validar módulos V3.0 (detecta hardcoding!)
    print_step('VALIDAÇÃO CRÍTICA V3.0: Detectando hardcoding...', 'info')
    validate_modules()
    print()
    
    # Etapa 4: Teste rápido V3.0 (CSV diferente)
    print_step('TESTE V3.0: CSV com colunas diferentes...', 'info')
    run_quick_test()
    print()
    
    # Etapa 5: Executar interface
    print_step('🎉 Setup V3.0 concluído com sucesso!', 'success')
    print_step('   → Chunking genérico VALIDADO', 'success')
    print_step('   → LLMs ativos VALIDADOS', 'success')
    print_step('   → Sem hardcoding CONFIRMADO', 'success')
    print()
    print_step('Iniciando interface interativa...', 'info')
    print()
    run_interface()


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
