import os
import sys
from pathlib import Path


# Garante que o diretório raiz do projeto esteja no PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_addoption(parser):
    parser.addoption(
        "--run-supabase", action="store_true", default=False,
        help="Executa testes de integração com Supabase (requer SUPABASE_URL e SUPABASE_KEY)"
    )


def pytest_configure(config):
    # Definições mínimas seguras para rodar testes sem quebrar ambiente externo
    os.environ.setdefault("LOG_LEVEL", "INFO")
    # Não definir chaves de LLM aqui; testes que usam LLM devem mockar o manager
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
