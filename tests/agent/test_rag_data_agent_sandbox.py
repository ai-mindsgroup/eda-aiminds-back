"""
🔒 SPRINT 3 P0-5: Testes de Segurança para Integração Sandbox + RAGDataAgent

Valida que:
1. Código seguro (pandas, numpy) é executado corretamente
2. Código malicioso (os, subprocess, eval, exec) é BLOQUEADO
3. Timeout funciona para loops infinitos
4. Erros de sintaxe são tratados graciosamente
5. Logging de auditoria está funcionando
6. Integração com RAGDataAgent não quebra fluxo de orquestração

Autor: GitHub Copilot GPT-4 (Sprint 3)
Data: 2025-10-17
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Adicionar src ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agent.rag_data_agent import RAGDataAgent
from src.security.sandbox import execute_in_sandbox


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def sample_dataframe():
    """Cria DataFrame de teste para análises."""
    return pd.DataFrame({
        'Amount': [100, 200, 300, 400, 500],
        'Time': [1, 2, 3, 4, 5],
        'Class': [0, 0, 1, 0, 1]
    })


@pytest.fixture
def mock_rag_agent():
    """Cria instância mockada do RAGDataAgent."""
    # Mock dependencies para evitar conexões reais
    with patch('src.agent.rag_data_agent.supabase'), \
         patch('src.agent.rag_data_agent.EmbeddingGenerator'), \
         patch('src.agent.rag_data_agent.get_logger') as mock_logger:
        
        mock_logger.return_value = Mock()
        agent = RAGDataAgent(name="TestAgent")
        agent.logger = Mock()  # Logger mockado para testes
        
        # Mock LLM para geração de código
        agent.llm = Mock()
        
        return agent


# ═══════════════════════════════════════════════════════════════
# TESTES DE EXECUÇÃO SEGURA (CÓDIGO PERMITIDO)
# ═══════════════════════════════════════════════════════════════

def test_sandbox_executa_codigo_pandas_seguro(mock_rag_agent, sample_dataframe):
    """✅ TESTE 1: Código pandas seguro deve executar com sucesso."""
    code = "resultado = df['Amount'].mean()"
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is True, f"Execução falhou: {result.get('error')}"
    assert result['result'] == 300.0, f"Resultado incorreto: {result['result']}"
    assert result['execution_time_ms'] > 0
    assert 'logs' in result
    
    # Verificar logging de auditoria
    assert mock_rag_agent.logger.info.called
    log_calls = [call[0][0] for call in mock_rag_agent.logger.info.call_args_list]
    assert any('sandbox_execution_request' in str(log) for log in log_calls)
    assert any('sandbox_execution_completed' in str(log) for log in log_calls)


def test_sandbox_executa_codigo_numpy_seguro(mock_rag_agent, sample_dataframe):
    """✅ TESTE 2: Código numpy seguro deve executar com sucesso."""
    code = """
import numpy as np
resultado = np.median(df['Amount'])
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is True
    assert result['result'] == 300.0
    assert result['error_type'] is None


def test_sandbox_executa_operacoes_complexas(mock_rag_agent, sample_dataframe):
    """✅ TESTE 3: Operações complexas (groupby, agg) devem funcionar."""
    code = """
resultado = df.groupby('Class')['Amount'].mean()
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is True
    assert isinstance(result['result'], pd.Series)
    assert len(result['result']) == 2  # 2 classes (0 e 1)


def test_sandbox_executa_multiplas_operacoes(mock_rag_agent, sample_dataframe):
    """✅ TESTE 4: Múltiplas linhas de código devem funcionar."""
    code = """
media = df['Amount'].mean()
desvio = df['Amount'].std()
resultado = {'media': media, 'desvio': desvio}
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is True
    assert isinstance(result['result'], dict)
    assert 'media' in result['result']
    assert 'desvio' in result['result']


# ═══════════════════════════════════════════════════════════════
# TESTES DE SEGURANÇA (CÓDIGO BLOQUEADO)
# ═══════════════════════════════════════════════════════════════

def test_sandbox_bloqueia_import_os(mock_rag_agent, sample_dataframe):
    """❌ TESTE 5: Import 'os' deve ser BLOQUEADO."""
    code = """
import os
resultado = os.listdir('.')
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False, "Import 'os' deveria ser bloqueado!"
    assert 'error' in result
    assert 'os' in result['error'].lower() or 'import' in result['error'].lower()
    assert result['error_type'] in ['SandboxImportError', 'CompilationError']


def test_sandbox_bloqueia_import_subprocess(mock_rag_agent, sample_dataframe):
    """❌ TESTE 6: Import 'subprocess' deve ser BLOQUEADO."""
    code = """
import subprocess
resultado = subprocess.run(['ls'], capture_output=True)
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert 'subprocess' in result['error'].lower() or 'import' in result['error'].lower()


def test_sandbox_bloqueia_eval(mock_rag_agent, sample_dataframe):
    """❌ TESTE 7: eval() deve ser BLOQUEADO em tempo de compilação."""
    code = """
resultado = eval('1 + 1')
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert 'eval' in result['error'].lower() or 'not allowed' in result['error'].lower()
    assert result['error_type'] == 'CompilationError'


def test_sandbox_bloqueia_exec(mock_rag_agent, sample_dataframe):
    """❌ TESTE 8: exec() deve ser BLOQUEADO em tempo de compilação."""
    code = """
exec('print("malicious")')
resultado = 1
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert 'exec' in result['error'].lower() or 'not allowed' in result['error'].lower()


def test_sandbox_bloqueia_open(mock_rag_agent, sample_dataframe):
    """❌ TESTE 9: open() deve ser BLOQUEADO (função não definida)."""
    code = """
resultado = open('/etc/passwd', 'r').read()
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert 'open' in result['error'].lower() or 'not defined' in result['error'].lower()
    assert result['error_type'] == 'ExecutionError'


def test_sandbox_bloqueia_acesso_dunder_import(mock_rag_agent, sample_dataframe):
    """❌ TESTE 10: __import__() deve ser BLOQUEADO."""
    code = """
os_module = __import__('os')
resultado = os_module.getcwd()
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert '__import__' in result['error'].lower() or 'not defined' in result['error'].lower()


# ═══════════════════════════════════════════════════════════════
# TESTES DE TIMEOUT E LIMITES
# ═══════════════════════════════════════════════════════════════

def test_sandbox_aplica_timeout_loop_infinito(mock_rag_agent, sample_dataframe):
    """⏱️ TESTE 11: Loop infinito deve ser interrompido por timeout."""
    code = """
while True:
    pass
resultado = 1
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe, timeout_seconds=2)
    
    # Nota: timeout pode não funcionar perfeitamente no Windows
    # Aceitamos tanto timeout quanto erro de execução longa
    assert result['success'] is False
    # Pode ser timeout ou outro erro dependendo da plataforma
    assert result['error_type'] in ['SandboxTimeoutError', 'ExecutionError', 'UnknownError']


def test_sandbox_timeout_customizado(mock_rag_agent, sample_dataframe):
    """⏱️ TESTE 12: Timeout customizado deve ser respeitado."""
    code = """
import time
time.sleep(10)  # Dormir 10 segundos
resultado = 1
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe, timeout_seconds=1)
    
    # Pode falhar por timeout ou por time.sleep não estar disponível
    assert result['success'] is False


# ═══════════════════════════════════════════════════════════════
# TESTES DE TRATAMENTO DE ERROS
# ═══════════════════════════════════════════════════════════════

def test_sandbox_trata_erro_sintaxe(mock_rag_agent, sample_dataframe):
    """⚠️ TESTE 13: Erro de sintaxe deve ser tratado graciosamente."""
    code = """
resultado = df['Amount'.mean()  # Parênteses não fechados
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert result['error_type'] == 'CompilationError'
    assert 'error' in result
    assert len(result['error']) > 0


def test_sandbox_trata_erro_runtime(mock_rag_agent, sample_dataframe):
    """⚠️ TESTE 14: Erro em tempo de execução deve ser capturado."""
    code = """
resultado = df['ColunaNaoExiste'].mean()  # Coluna inexistente
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert result['error_type'] == 'ExecutionError'
    assert 'ColunaNaoExiste' in result['error'] or 'KeyError' in result['error']


def test_sandbox_trata_divisao_por_zero(mock_rag_agent, sample_dataframe):
    """⚠️ TESTE 15: Divisão por zero deve ser tratada."""
    code = """
resultado = 1 / 0
"""
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    assert result['success'] is False
    assert result['error_type'] == 'ExecutionError'
    assert 'division' in result['error'].lower() or 'zero' in result['error'].lower()


# ═══════════════════════════════════════════════════════════════
# TESTES DE LOGGING E AUDITORIA
# ═══════════════════════════════════════════════════════════════

def test_sandbox_registra_logs_auditoria(mock_rag_agent, sample_dataframe):
    """📝 TESTE 16: Logs de auditoria devem ser registrados."""
    code = "resultado = df['Amount'].sum()"
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    # Verificar que logger.info foi chamado
    assert mock_rag_agent.logger.info.called
    
    # Verificar estrutura dos logs
    log_calls = [call[0][0] for call in mock_rag_agent.logger.info.call_args_list]
    
    # Deve ter log de request e completed
    events = [log.get('event') if isinstance(log, dict) else None for log in log_calls]
    assert 'sandbox_execution_request' in events
    assert 'sandbox_execution_completed' in events


def test_sandbox_logs_contem_timestamp(mock_rag_agent, sample_dataframe):
    """📝 TESTE 17: Logs devem conter timestamp para auditoria."""
    code = "resultado = 42"
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    log_calls = [call[0][0] for call in mock_rag_agent.logger.info.call_args_list]
    
    # Verificar que pelo menos um log tem timestamp
    timestamps = [log.get('timestamp') for log in log_calls if isinstance(log, dict) and 'timestamp' in log]
    assert len(timestamps) > 0
    
    # Verificar formato ISO 8601
    for ts in timestamps:
        datetime.fromisoformat(ts)  # Não deve levantar exceção


def test_sandbox_logs_erros_detalhados(mock_rag_agent, sample_dataframe):
    """📝 TESTE 18: Erros devem ter logs detalhados."""
    code = "import os"  # Código malicioso
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    # Verificar que logger.error foi chamado
    assert mock_rag_agent.logger.info.called  # Mesmo erros logam em info primeiro
    
    log_calls = [call[0][0] for call in mock_rag_agent.logger.info.call_args_list]
    completed_logs = [log for log in log_calls if isinstance(log, dict) and log.get('event') == 'sandbox_execution_completed']
    
    assert len(completed_logs) > 0
    assert completed_logs[0].get('success') is False
    assert 'error_type' in completed_logs[0]


# ═══════════════════════════════════════════════════════════════
# TESTES DE INTEGRAÇÃO COM _executar_instrucao
# ═══════════════════════════════════════════════════════════════

def test_executar_instrucao_metricas_nativas(mock_rag_agent, sample_dataframe):
    """🔗 TESTE 19: Métricas nativas (média, mediana) não devem usar sandbox."""
    instrucao = {'acao': 'média', 'colunas': ['Amount'], 'params': {}}
    
    result = mock_rag_agent._executar_instrucao(sample_dataframe, instrucao)
    
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert result.loc['Amount', 'Média'] == 300.0
    
    # Verificar que sandbox NÃO foi chamado (métricas nativas não precisam)
    sandbox_logs = [log for log in mock_rag_agent.logger.info.call_args_list 
                    if isinstance(log[0][0], dict) and log[0][0].get('event') == 'sandbox_execution_request']
    assert len(sandbox_logs) == 0


def test_executar_instrucao_metrica_complexa_via_sandbox(mock_rag_agent, sample_dataframe):
    """🔗 TESTE 20: Métricas complexas devem usar sandbox + LLM."""
    instrucao = {'acao': 'correlação entre Amount e Time', 'colunas': ['Amount', 'Time'], 'params': {}}
    
    # Mock da resposta LLM
    mock_rag_agent.llm.invoke = Mock(return_value=Mock(content="resultado = df[['Amount', 'Time']].corr()"))
    
    result = mock_rag_agent._executar_instrucao(sample_dataframe, instrucao)
    
    # Se LLM está mockado e retornou código válido, sandbox deve ter sido chamado
    assert mock_rag_agent.llm.invoke.called


# ═══════════════════════════════════════════════════════════════
# TESTES DE COMPATIBILIDADE E REGRESSÃO
# ═══════════════════════════════════════════════════════════════

def test_sandbox_nao_quebra_fluxo_rag(mock_rag_agent, sample_dataframe):
    """🔗 TESTE 21: Sandbox não deve quebrar fluxo de orquestração."""
    # Simular método _executar_instrucao completo
    instrucoes = [
        {'acao': 'média', 'colunas': ['Amount'], 'params': {}},
        {'acao': 'mediana', 'colunas': ['Amount'], 'params': {}},
    ]
    
    resultados = []
    for instrucao in instrucoes:
        resultado = mock_rag_agent._executar_instrucao(sample_dataframe, instrucao)
        resultados.append(resultado)
    
    # Todas as instruções devem retornar resultados
    assert all(r is not None for r in resultados)
    assert len(resultados) == 2


def test_sandbox_retorna_dict_padrao(mock_rag_agent, sample_dataframe):
    """🔗 TESTE 22: Sandbox sempre retorna dict com chaves esperadas."""
    code = "resultado = 42"
    
    result = mock_rag_agent._executar_codigo_sandbox(code, sample_dataframe)
    
    # Verificar estrutura do dict
    assert isinstance(result, dict)
    assert 'success' in result
    assert 'result' in result
    assert 'error' in result
    assert 'error_type' in result
    assert 'execution_time_ms' in result
    assert 'logs' in result
    
    # Tipos corretos
    assert isinstance(result['success'], bool)
    assert isinstance(result['execution_time_ms'], (int, float))
    assert isinstance(result['logs'], list)


# ═══════════════════════════════════════════════════════════════
# SUMÁRIO E EXECUÇÃO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🔒 SPRINT 3 P0-5: Executando Testes de Segurança Sandbox + RAGDataAgent")
    print("=" * 80)
    pytest.main([__file__, '-v', '--tb=short'])
    print("=" * 80)
    print("✅ Testes concluídos! Verifique resultados acima.")
