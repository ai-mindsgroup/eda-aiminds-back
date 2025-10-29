"""
Módulo: code_generator.py
Responsável por gerar código Python (Pandas, Matplotlib) a partir da intenção detectada.

Interface principal:
- generate_code(intent: dict, context: dict) -> str

Exemplo de uso:
    intent = {"tipo": "frequencia_coluna", "coluna": "idade"}
    context = {"nome_arquivo": "dados.csv"}
    codigo = generate_code(intent, context)
    # código gerado pode ser executado pelo executor seguro
"""
from typing import Dict

class CodeGenerator:
    """
    Classe responsável por traduzir a intenção analítica em código Python executável.
    Suporta geração para Pandas e Matplotlib.
    """
    def generate_code(self, intent: Dict, context: Dict) -> str:
        """
        Gera código Python a partir da intenção e contexto.
        Args:
            intent (dict): Dicionário com a intenção detectada (ex: tipo, coluna, operação).
            context (dict): Contexto adicional (ex: nome do arquivo, filtros).
        Returns:
            str: Código Python gerado.
        """
        tipo = intent.get("tipo")
        coluna = intent.get("coluna")
        arquivo = context.get("nome_arquivo", "dados.csv")

        if tipo == "frequencia_coluna":
            return (
                f"import pandas as pd\n"
                f"df = pd.read_csv('{arquivo}')\n"
                f"frequencia = df['{coluna}'].value_counts()\n"
                f"print(frequencia)\n"
            )
        elif tipo == "histograma_coluna":
            return (
                f"import pandas as pd\nimport matplotlib.pyplot as plt\n"
                f"df = pd.read_csv('{arquivo}')\n"
                f"df['{coluna}'].hist()\n"
                f"plt.title('Histograma de {coluna}')\n"
                f"plt.xlabel('{coluna}')\n"
                f"plt.ylabel('Frequência')\n"
                f"plt.show()\n"
            )
        # Adicione outros tipos conforme necessário
        else:
            return "# Tipo de análise não suportado."

# Exemplo de uso
if __name__ == "__main__":
    generator = CodeGenerator()
    intent = {"tipo": "frequencia_coluna", "coluna": "idade"}
    context = {"nome_arquivo": "dados.csv"}
    codigo = generator.generate_code(intent, context)
    print("Código gerado:\n", codigo)
