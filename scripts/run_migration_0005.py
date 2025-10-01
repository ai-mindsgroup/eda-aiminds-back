"""Executa apenas a migration 0005 (Agent Memory Tables) no Supabase.

Este script executa somente a migration de memória dos agentes,
sem afetar as tabelas e dados existentes.

Uso:
    python scripts/run_migration_0005.py

Requisitos:
    - Variáveis definidas em configs/.env
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

MIGRATION_FILE = ROOT / "migrations" / "0005_agent_memory_tables.sql"


def run_migration_0005() -> int:
    """Executa a migration 0005 de forma segura."""
    
    if not MIGRATION_FILE.exists():
        print(f"❌ Erro: Arquivo de migration não encontrado: {MIGRATION_FILE}")
        return 1
    
    dsn = build_db_dsn()
    print(f"🔗 Conectando ao Supabase...")
    print(f"   DSN: {dsn.split('@')[0]}@... (credenciais ocultas)")
    
    try:
        with psycopg.connect(dsn) as conn:
            print(f"\n📄 Lendo migration: {MIGRATION_FILE.name}")
            sql = MIGRATION_FILE.read_text(encoding="utf-8")
            
            print(f"⚙️  Executando migration 0005 (Agent Memory Tables)...")
            print("   - Criando tabela: agent_sessions")
            print("   - Criando tabela: agent_conversations")
            print("   - Criando tabela: agent_memory_store")
            print("   - Criando índices e constraints...")
            
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            
            print("\n✅ Migration 0005 aplicada com sucesso!")
            print("   Tabelas de memória dos agentes criadas:")
            print("   - agent_sessions")
            print("   - agent_conversations")
            print("   - agent_memory_store")
            print("   - Índices e triggers configurados")
            
        return 0
        
    except psycopg.errors.DuplicateTable as e:
        print("\n⚠️  Aviso: Algumas tabelas já existem.")
        print(f"   Detalhes: {str(e)}")
        print("   As tabelas de memória podem já ter sido criadas anteriormente.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        return 1


if __name__ == "__main__":
    print("=" * 70)
    print("  EXECUÇÃO DA MIGRATION 0005 - AGENT MEMORY TABLES")
    print("=" * 70)
    exit_code = run_migration_0005()
    print("=" * 70)
    raise SystemExit(exit_code)
