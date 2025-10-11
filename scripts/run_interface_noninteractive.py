import asyncio
import sys
from pathlib import Path

# Garantir import do pacote src
root_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root_dir))

import builtins
import interface_interativa

# Sequência de inputs que a interface receberá: pergunta, depois 'sair'
inputs = iter([
    "Qual a distribuição de cada variável (histogramas, distribuições)?",
    "sair"
])

original_input = builtins.input

def fake_input(prompt=""):
    try:
        value = next(inputs)
        print(prompt + value)
        return value
    except StopIteration:
        return original_input(prompt)

builtins.input = fake_input

if __name__ == '__main__':
    try:
        asyncio.run(interface_interativa.main())
    finally:
        builtins.input = original_input
