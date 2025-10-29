"""
Módulo: output_formatter.py
Responsável por formatar o resultado das análises em texto, tabelas markdown e gráficos.

Interface principal:
- format_output(result: any, output_type: str = 'auto') -> str | bytes

Exemplo de uso:
    formatter = OutputFormatter()
    texto = formatter.format_output(resultado, output_type='text')
    tabela = formatter.format_output(resultado, output_type='markdown')
    grafico = formatter.format_output(resultado, output_type='plot')
"""
from typing import Any
import pandas as pd
import matplotlib.pyplot as plt
import io

class OutputFormatter:
    """
    Formata resultados analíticos em texto, markdown ou gráficos.
    """
    def format_output(self, result: Any, output_type: str = 'auto') -> str:
        """
        Formata o resultado conforme o tipo desejado.
        Args:
            result: Resultado da análise (DataFrame, Series, valor escalar, figura)
            output_type: 'auto', 'text', 'markdown', 'plot'
        Returns:
            str: Saída formatada (texto ou markdown)
        """
        if output_type == 'auto':
            if isinstance(result, pd.DataFrame):
                output_type = 'markdown'
            elif isinstance(result, pd.Series):
                output_type = 'markdown'
            elif hasattr(result, 'figure') or hasattr(result, 'savefig'):
                output_type = 'plot'
            else:
                output_type = 'text'

        if output_type == 'markdown':
            if isinstance(result, (pd.DataFrame, pd.Series)):
                return result.to_markdown(index=True)
            else:
                return str(result)
        elif output_type == 'text':
            return str(result)
        elif output_type == 'plot':
            buf = io.BytesIO()
            plt.figure()
            if isinstance(result, pd.Series):
                result.plot(kind='bar')
            elif isinstance(result, pd.DataFrame):
                result.plot()
            else:
                return "[Gráfico não suportado para este tipo de resultado]"
            plt.tight_layout()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            return buf.read()  # Retorna bytes PNG
        else:
            return str(result)

# Exemplo de uso
if __name__ == "__main__":
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    formatter = OutputFormatter()
    print(formatter.format_output(df, output_type='markdown'))
    print(formatter.format_output(df["A"], output_type='text'))
