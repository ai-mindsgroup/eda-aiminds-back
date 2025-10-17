"""
🔒 SPRINT 3 P0-4: Exemplo de Integração Sandbox + RAGDataAgent

Script de teste manual para validar rapidamente a integração do sandbox seguro
no RAGDataAgent, sem necessidade de conexões reais com Supabase ou APIs.

Execução:
    python examples/test_rag_sandbox_integration.py

Autor: GitHub Copilot GPT-4 (Sprint 3)
Data: 2025-10-17
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from agent.rag_data_agent import RAGDataAgent
from security.sandbox import execute_in_sandbox


def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_result(test_name, result):
    """Imprime resultado de teste formatado."""
    status = "✅ SUCESSO" if result.get('success') else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    print(f"  Tempo: {result.get('execution_time_ms', 0):.2f}ms")
    if result.get('success'):
        print(f"  Resultado: {result.get('result')}")
    else:
        print(f"  Erro: {result.get('error')}")
        print(f"  Tipo: {result.get('error_type')}")


def main():
    print_header("🔒 TESTE DE INTEGRAÇÃO: SANDBOX + RAGDataAgent")
    
    # ═══════════════════════════════════════════════════════════════
    # 1. CRIAR DATAFRAME DE TESTE
    # ═══════════════════════════════════════════════════════════════
    print("\n📊 Criando DataFrame de teste (fraudes de cartão de crédito)...")
    df = pd.DataFrame({
        'Time': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'Amount': [100.50, 200.00, 150.75, 300.00, 250.25, 180.00, 220.50, 190.00, 280.00, 310.00],
        'Class': [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
        'V1': [1.2, -0.5, 0.8, 2.1, -1.3, 0.4, 1.8, -0.9, 0.6, 2.5],
        'V2': [0.3, 1.1, -0.7, 1.5, 0.2, -1.0, 1.3, 0.5, -0.4, 1.7]
    })
    print(f"✅ DataFrame criado: {df.shape[0]} linhas × {df.shape[1]} colunas")
    print(f"   Colunas: {list(df.columns)}")
    print(f"   Tipos: {df.dtypes.to_dict()}")
    
    # ═══════════════════════════════════════════════════════════════
    # 2. CRIAR INSTÂNCIA DO AGENTE (SEM CONEXÕES REAIS)
    # ═══════════════════════════════════════════════════════════════
    print("\n🤖 Inicializando RAGDataAgent (mock mode)...")
    
    # Mock das dependências para evitar conexões reais
    from unittest.mock import Mock, patch
    
    with patch('agent.rag_data_agent.supabase'), \
         patch('agent.rag_data_agent.EmbeddingGenerator'), \
         patch('agent.rag_data_agent.get_logger') as mock_logger:
        
        mock_logger.return_value = Mock()
        agent = RAGDataAgent()  # RAGDataAgent não aceita parâmetro 'name'
        agent.logger = Mock()  # Logger mockado
        
        print("✅ RAGDataAgent inicializado (sem conexões externas)")
    
    # ═══════════════════════════════════════════════════════════════
    # 3. TESTE 1: CÓDIGO SEGURO (PANDAS MEAN)
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 1: Código Seguro - Média com Pandas")
    
    code_safe_1 = "resultado = df['Amount'].mean()"
    result_1 = agent._executar_codigo_sandbox(code_safe_1, df)
    print_result("Cálculo de média", result_1)
    
    if result_1.get('success'):
        assert abs(result_1.get('result') - 218.1) < 0.1, "Média incorreta!"
        print("  ✅ Validação: Média correta (218.1)")
    
    # ═══════════════════════════════════════════════════════════════
    # 4. TESTE 2: CÓDIGO SEGURO (NUMPY + OPERAÇÕES COMPLEXAS)
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 2: Código Seguro - Estatísticas com NumPy")
    
    code_safe_2 = """
import numpy as np
media = df['Amount'].mean()
desvio = df['Amount'].std()
mediana = df['Amount'].median()
resultado = {
    'media': media,
    'desvio_padrao': desvio,
    'mediana': mediana
}
"""
    result_2 = agent._executar_codigo_sandbox(code_safe_2, df)
    print_result("Estatísticas descritivas", result_2)
    
    if result_2.get('success'):
        stats = result_2.get('result')
        print(f"  ✅ Validação: Estatísticas calculadas")
        print(f"     - Média: {stats['media']:.2f}")
        print(f"     - Desvio: {stats['desvio_padrao']:.2f}")
        print(f"     - Mediana: {stats['mediana']:.2f}")
    
    # ═══════════════════════════════════════════════════════════════
    # 5. TESTE 3: CÓDIGO SEGURO (GROUPBY + AGGREGATION)
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 3: Código Seguro - Agregação por Grupo")
    
    code_safe_3 = "resultado = df.groupby('Class')['Amount'].mean()"
    result_3 = agent._executar_codigo_sandbox(code_safe_3, df)
    print_result("GroupBy + Média", result_3)
    
    if result_3.get('success'):
        print(f"  ✅ Validação: Agregação por classe")
        print(f"     - Classe 0 (legítimo): {result_3.get('result')[0]:.2f}")
        print(f"     - Classe 1 (fraude): {result_3.get('result')[1]:.2f}")
    
    # ═══════════════════════════════════════════════════════════════
    # 6. TESTE 4: CÓDIGO MALICIOSO (IMPORT OS) - DEVE SER BLOQUEADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 4: Código Malicioso - Import OS (DEVE BLOQUEAR)")
    
    code_malicious_1 = """
import os
resultado = os.listdir('.')
"""
    result_4 = agent._executar_codigo_sandbox(code_malicious_1, df)
    print_result("Tentativa de import 'os'", result_4)
    
    if not result_4.get('success'):
        print("  ✅ SEGURANÇA: Import 'os' foi BLOQUEADO como esperado")
    else:
        print("  ❌ VULNERABILIDADE: Import 'os' NÃO foi bloqueado!")
    
    # ═══════════════════════════════════════════════════════════════
    # 7. TESTE 5: CÓDIGO MALICIOSO (SUBPROCESS) - DEVE SER BLOQUEADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 5: Código Malicioso - Subprocess (DEVE BLOQUEAR)")
    
    code_malicious_2 = """
import subprocess
resultado = subprocess.run(['ls'], capture_output=True)
"""
    result_5 = agent._executar_codigo_sandbox(code_malicious_2, df)
    print_result("Tentativa de subprocess", result_5)
    
    if not result_5.get('success'):
        print("  ✅ SEGURANÇA: Import 'subprocess' foi BLOQUEADO como esperado")
    else:
        print("  ❌ VULNERABILIDADE: Subprocess NÃO foi bloqueado!")
    
    # ═══════════════════════════════════════════════════════════════
    # 8. TESTE 6: CÓDIGO MALICIOSO (EVAL) - DEVE SER BLOQUEADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 6: Código Malicioso - eval() (DEVE BLOQUEAR)")
    
    code_malicious_3 = """
resultado = eval('__import__("os").system("whoami")')
"""
    result_6 = agent._executar_codigo_sandbox(code_malicious_3, df)
    print_result("Tentativa de eval()", result_6)
    
    if not result_6.get('success'):
        print("  ✅ SEGURANÇA: eval() foi BLOQUEADO como esperado")
    else:
        print("  ❌ VULNERABILIDADE: eval() NÃO foi bloqueado!")
    
    # ═══════════════════════════════════════════════════════════════
    # 9. TESTE 7: CÓDIGO MALICIOSO (OPEN FILE) - DEVE SER BLOQUEADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 7: Código Malicioso - open() (DEVE BLOQUEAR)")
    
    code_malicious_4 = """
resultado = open('/etc/passwd', 'r').read()
"""
    result_7 = agent._executar_codigo_sandbox(code_malicious_4, df)
    print_result("Tentativa de open() file", result_7)
    
    if not result_7.get('success'):
        print("  ✅ SEGURANÇA: open() foi BLOQUEADO como esperado")
    else:
        print("  ❌ VULNERABILIDADE: open() NÃO foi bloqueado!")
    
    # ═══════════════════════════════════════════════════════════════
    # 10. TESTE 8: ERRO DE SINTAXE - DEVE SER TRATADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 8: Erro de Sintaxe (DEVE SER TRATADO)")
    
    code_syntax_error = """
resultado = df['Amount'.mean()  # Parênteses não fechados
"""
    result_8 = agent._executar_codigo_sandbox(code_syntax_error, df)
    print_result("Código com erro de sintaxe", result_8)
    
    if not result_8.get('success') and result_8.get('error_type') == 'CompilationError':
        print("  ✅ TRATAMENTO: Erro de sintaxe capturado graciosamente")
    else:
        print("  ⚠️ ATENÇÃO: Erro de sintaxe não tratado adequadamente")
    
    # ═══════════════════════════════════════════════════════════════
    # 11. TESTE 9: ERRO RUNTIME - DEVE SER TRATADO
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 9: Erro Runtime - Coluna Inexistente (DEVE SER TRATADO)")
    
    code_runtime_error = """
resultado = df['ColunaQueNaoExiste'].mean()
"""
    result_9 = agent._executar_codigo_sandbox(code_runtime_error, df)
    print_result("Código com erro runtime", result_9)
    
    if not result_9.get('success') and result_9.get('error_type') == 'ExecutionError':
        print("  ✅ TRATAMENTO: Erro runtime capturado graciosamente")
    else:
        print("  ⚠️ ATENÇÃO: Erro runtime não tratado adequadamente")
    
    # ═══════════════════════════════════════════════════════════════
    # SUMÁRIO FINAL
    # ═══════════════════════════════════════════════════════════════
    print_header("📊 SUMÁRIO DOS TESTES")
    
    all_results = [result_1, result_2, result_3, result_4, result_5, result_6, result_7, result_8, result_9]
    
    # Contar sucessos esperados
    safe_tests = [result_1, result_2, result_3]  # Devem ter success=True
    malicious_tests = [result_4, result_5, result_6, result_7]  # Devem ter success=False (bloqueados)
    error_tests = [result_8, result_9]  # Devem ter success=False (tratados)
    
    safe_passed = sum(1 for r in safe_tests if r.get('success'))
    malicious_blocked = sum(1 for r in malicious_tests if not r.get('success'))
    errors_handled = sum(1 for r in error_tests if not r.get('success'))
    
    print(f"\n✅ Código Seguro Executado: {safe_passed}/{len(safe_tests)} testes")
    print(f"🔒 Código Malicioso Bloqueado: {malicious_blocked}/{len(malicious_tests)} testes")
    print(f"⚠️ Erros Tratados: {errors_handled}/{len(error_tests)} testes")
    
    total_passed = safe_passed + malicious_blocked + errors_handled
    total_tests = len(all_results)
    
    print(f"\n📊 RESULTADO GERAL: {total_passed}/{total_tests} testes passaram ({total_passed/total_tests*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 SUCESSO TOTAL! Integração sandbox + RAGDataAgent está funcionando perfeitamente!")
        print("✅ Sprint 3 P0-4 validado com sucesso")
        return 0
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM! Revisar integração sandbox + RAGDataAgent")
        print(f"❌ {total_tests - total_passed} teste(s) falharam")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
