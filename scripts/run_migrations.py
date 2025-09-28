"""Script de execução de migrations SQL com modos online e offline.

Funcionalidades:
    1. Execução idempotente: cria e usa tabela schema_migrations para registrar arquivos aplicados.
    2. Modo offline (--offline): concatena as migrations na ordem e gera um arquivo único para colar no SQL Editor do Supabase (sem abrir conexão).
    3. Dry-run (--dry-run): mostra a ordem e quais seriam aplicadas (online) sem executar.
    4. Safe logs: não imprime credenciais.

Uso rápido:
    # Executar normalmente (apenas novas migrations)
    python scripts/run_migrations.py

    # Ver ordem / status sem aplicar
    python scripts/run_migrations.py --dry-run

    # Gerar arquivo único (migrations_combined.sql) para colar manualmente
    python scripts/run_migrations.py --offline

Pré-requisitos:
    - Variáveis em configs/.env (ou exportadas) para modo online
    - psycopg instalado
"""
from __future__ import annotations
import sys
import argparse
import datetime as _dt
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Carrega .env do projeto
ROOT = Path(__file__).resolve().parents[1]
# Garante que o diretório raiz esteja no sys.path para importar `src.*`
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENV_PATH = ROOT / "configs" / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Importa settings depois de carregar .env
from src.settings import build_db_dsn  # noqa: E402

MIGRATIONS_DIR = ROOT / "migrations"
COMBINED_FILENAME = ROOT / "migrations_combined.sql"

SCHEMA_MIGRATIONS_SQL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations (\n"
    "  filename TEXT PRIMARY KEY,\n"
    "  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
    ");"
)


def run_sql(conn: psycopg.Connection, sql: str) -> None:
    """Executa um bloco SQL (pode conter múltiplos statements)."""
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def ensure_schema_migrations(conn: psycopg.Connection) -> None:
    run_sql(conn, SCHEMA_MIGRATIONS_SQL)


def get_applied(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations")
        rows = cur.fetchall()
    return {r[0] for r in rows}


def register_applied(conn: psycopg.Connection, filename: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO schema_migrations (filename, applied_at) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (filename, _dt.datetime.utcnow()),
        )
    conn.commit()


def collect_migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def build_offline_file(files: list[Path]) -> Path:
    if not files:
        raise SystemExit("Nenhuma migration .sql encontrada para gerar offline.")
    lines: list[str] = ["-- Arquivo combinado gerado em " + _dt.datetime.utcnow().isoformat() + "Z", "-- Ordem: "]
    lines += ["--   " + f.name for f in files]
    lines.append("")
    for f in files:
        lines.append(f"-- >>> BEGIN {f.name} >>>")
        lines.append(f.read_text(encoding="utf-8"))
        lines.append(f"-- <<< END {f.name} <<<")
        lines.append("")
    COMBINED_FILENAME.write_text("\n".join(lines), encoding="utf-8")
    return COMBINED_FILENAME


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Executor de migrations SQL")
    p.add_argument("--offline", action="store_true", help="Gera arquivo combinado sem conectar")
    p.add_argument("--dry-run", action="store_true", help="Lista ordem e status sem aplicar")
    p.add_argument("--force", action="store_true", help="Força reaplicação (ignora registro). USE COM CAUTELA")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    files = collect_migration_files()
    if args.offline:
        out = build_offline_file(files)
        print(f"Arquivo offline gerado: {out}")
        return 0

    if not files:
        print("Nenhuma migration .sql encontrada em migrations/")
        return 0

    dsn = build_db_dsn()
    safe_dsn_prefix = dsn.split("@")[0]
    print(f"Conectando com DSN: {safe_dsn_prefix}@... (oculto)")

    with psycopg.connect(dsn) as conn:
        ensure_schema_migrations(conn)
        applied = get_applied(conn)
        print(f"{len(applied)} migrations já registradas.")

        plan: list[Path] = []
        for f in files:
            if args.force or (f.name not in applied):
                plan.append(f)
        if args.dry_run:
            print("Dry-run: ordem de aplicação ->")
            for f in plan:
                marker = "(NOVA)" if f.name not in applied else "(FORCE)"
                print(f" - {f.name} {marker}")
            print(f"Total a aplicar: {len(plan)}")
            return 0

        if not plan:
            print("Nenhuma nova migration para aplicar.")
            return 0

        for fp in plan:
            print(f"Aplicando migration: {fp.name}")
            sql = fp.read_text(encoding="utf-8")
            run_sql(conn, sql)
            register_applied(conn, fp.name)
        print("Migrations aplicadas com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
