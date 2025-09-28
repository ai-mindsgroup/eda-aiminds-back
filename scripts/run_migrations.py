"""Executa migrations SQL na ordem, conectando ao Postgres do Supabase.

Uso:
    ./.venv/Scripts/Activate.ps1  # Windows PowerShell
    python scripts/run_migrations.py

Requisitos:
    - Variáveis definidas em configs/.env (ou ambiente)
    - psycopg instalado
"""
from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
from dotenv import load_dotenv

# Carrega .env do projeto
ENV_PATH = ROOT / "configs" / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Importa settings depois de carregar .env
from src.settings import build_db_dsn  # noqa: E402

MIGRATIONS_DIR = ROOT / "migrations"


def run_sql(conn: psycopg.Connection, sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main() -> int:
    dsn = build_db_dsn()
    print(f"Conectando com DSN: {dsn.split('@')[0]}@... (oculto)")
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("Nenhum arquivo .sql encontrado em migrations/")
        return 0

    with psycopg.connect(dsn) as conn:
        for fp in files:
            sql = fp.read_text(encoding="utf-8")
            print(f"Aplicando migration: {fp.name}")
            run_sql(conn, sql)
        print("Migrations aplicadas com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
