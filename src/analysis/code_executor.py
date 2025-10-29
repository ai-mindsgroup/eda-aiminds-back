"""
Módulo: code_executor.py
Responsável por executar código Python gerado dinamicamente em ambiente seguro (sandbox).

Interface principal:
- execute_code(code: str, context: dict = None) -> dict

O executor utiliza RestrictedPython para isolar a execução, limitando acesso a recursos perigosos.

Exemplo de uso:
    code = "resultado = df['idade'].mean()"
    context = {"df": df}
    exec_result = execute_code(code, context)
    if exec_result["success"]:
        print(exec_result["result"])
    else:
        print("Erro:", exec_result["error"])
"""
from typing import Dict, Any

class CodeExecutor:
    """
    Executor seguro de código Python usando sandbox (RestrictedPython).
    """
    def execute_code(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa código Python em ambiente restrito, com custom guards para DataFrame.
        Permite acesso seguro a df['coluna'] e operações analíticas comuns.
        Args:
            code (str): Código Python a ser executado.
            context (dict): Variáveis de contexto (ex: df).
        Returns:
            dict: {
                'success': bool,
                'result': valor retornado (se sucesso),
                'error': mensagem de erro (se falha),
                'traceback': traceback completo (se erro),
                'logs': lista de eventos para auditoria
            }
        """
        import sys
        import traceback
        from RestrictedPython import compile_restricted
        from RestrictedPython.Guards import safe_builtins
        import pandas as pd

        logs = []

        # Custom guard para liberar __getitem__ seguro em DataFrame/Series
        def guard_getitem(obj, key):
            # Permite apenas DataFrame/Series e chaves string/int
            if isinstance(obj, (pd.DataFrame, pd.Series)) and isinstance(key, (str, int)):
                logs.append(f"Acesso permitido: {type(obj).__name__}[{repr(key)}]")
                return obj[key]
            raise PermissionError(f"Acesso negado a {type(obj).__name__}[{repr(key)}]")

        # Custom builtins
        custom_builtins = dict(safe_builtins)
        # Permite funções matemáticas básicas
        for fn in ['abs', 'min', 'max', 'sum', 'len', 'round', 'range', 'enumerate', 'zip', 'sorted', 'list', 'dict', 'set', 'float', 'int', 'str', 'bool']:
            custom_builtins[fn] = __builtins__[fn]

        exec_globals = {
            "__builtins__": custom_builtins,
            "_getitem_": guard_getitem,  # RestrictedPython usa _getitem_ para []
        }
        if context:
            exec_globals.update(context)
        exec_locals = {}
        try:
            byte_code = compile_restricted(code, '<string>', 'exec')
            exec(byte_code, exec_globals, exec_locals)
            result = exec_locals.get('resultado', None)
            logs.append("Execução concluída com sucesso.")
            return {"success": True, "result": result, "logs": logs}
        except Exception as e:
            tb = traceback.format_exc()
            logs.append(f"Erro: {str(e)}")
            return {"success": False, "error": str(e), "traceback": tb, "logs": logs}

# Exemplo de uso
if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame({"idade": [20, 30, 40]})
    code = "resultado = df['idade'].mean()"
    executor = CodeExecutor()
    res = executor.execute_code(code, {"df": df})
    print(res)

    # Exemplo de acesso negado:
    code2 = "resultado = df.__class__"
    res2 = executor.execute_code(code2, {"df": df})
    print(res2)
