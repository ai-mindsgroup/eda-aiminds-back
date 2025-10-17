"""
🔒 SPRINT 3 - TESTES AUTOMATIZADOS: Edge Cases

Testes para casos extremos e situações inesperadas.

Autor: GitHub Copilot Sonnet 4.5
Data: 2025-10-17
"""

import pytest


class TestEdgeCases:
    """Testes de casos extremos."""
    
    def test_empty_code(self, execute_sandbox_helper, assert_success):
        """✅ Teste 66: Código vazio é permitido (retorna namespace vazio)."""
        result = execute_sandbox_helper(code="")
        assert_success(result, expected_result={})
    
    def test_whitespace_only(self, execute_sandbox_helper, assert_success):
        """✅ Teste 67: Apenas espaços em branco (comportamento similar ao vazio)."""
        result = execute_sandbox_helper(code="   \n\n   \t  ")
        assert_success(result, expected_result={})

    
    def test_syntax_error(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 68: Erro de sintaxe."""
        code = '''
def foo(
    # Sintaxe inválida
resultado = 42
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
        assert 'Syntax' in result['error'] or 'syntax' in result['error'].lower()
    
    def test_missing_result_variable(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 69: Variável 'resultado' ausente."""
        code = '''
x = 10
y = 20
z = x + y
# Não definiu 'resultado'
'''
        result = execute_sandbox_helper(code)
        # Deve falhar porque 'resultado' não foi definido
        assert result['success'] is False or result['result'] is None
    
    def test_custom_return_variable(self, execute_sandbox_helper, assert_success):
        """✅ Teste 70: Variável de retorno customizada."""
        code = '''
output = 42
'''
        result = execute_sandbox_helper(code, return_variable='output')
        assert_success(result, expected_result=42)
    
    def test_custom_globals_dataframe(self, execute_sandbox_helper, assert_success, small_dataframe):
        """✅ Teste 71: Custom globals com DataFrame."""
        code = '''
resultado = len(df) + 10
'''
        result = execute_sandbox_helper(code, custom_globals={'df': small_dataframe})
        assert_success(result, expected_result=20)  # 10 rows + 10
    
    def test_none_result(self, execute_sandbox_helper, assert_success):
        """✅ Teste 72: Resultado None é válido."""
        code = '''
resultado = None
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=None)
    
    def test_large_string_result(self, execute_sandbox_helper, assert_success):
        """✅ Teste 73: Resultado com string grande."""
        code = '''
resultado = "x" * 10000
'''
        result = execute_sandbox_helper(code)
        assert_success(result)
        assert len(result['result']) == 10000
    
    def test_unicode_in_code(self, execute_sandbox_helper, assert_success):
        """✅ Teste 74: Código com caracteres Unicode."""
        code = '''
# Comentário em português: cálculo
texto = "Olá mundo! 你好 🌍"
resultado = len(texto)
'''
        result = execute_sandbox_helper(code)
        assert_success(result)
    
    def test_multiline_string_result(self, execute_sandbox_helper, assert_success):
        """✅ Teste 75: Resultado com string multi-linha."""
        code = '''
resultado = """
Linha 1
Linha 2
Linha 3
"""
'''
        result = execute_sandbox_helper(code)
        assert_success(result)
        assert 'Linha 1' in result['result']


"""
TOTAL: 10 testes edge cases
Cobertura esperada: ~10% (casos extremos)
"""
