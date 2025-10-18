"""
Configuração do pytest para o projeto EDA AI Minds.

Adiciona o diretório src/ ao sys.path para permitir imports absolutos
dos módulos do projeto durante a execução dos testes.

Autor: EDA AI Minds Team
Data: 2025-10-16
"""

import sys
from pathlib import Path

# Adicionar diretório src/ ao Python path
repo_root = Path(__file__).parent.parent
src_dir = repo_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print(f"[OK] conftest.py: Adicionado {src_dir} ao sys.path")
