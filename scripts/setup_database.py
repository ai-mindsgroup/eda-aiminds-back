"""Script para Setup de Banco de Dados
===================================

Executa apenas a configuração do banco de dados:
- Verifica conexão
- Aplica migrations
- Valida schema
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def setup_database():
    """Configura o banco de dados completo."""
    print("🗄️ SETUP DE BANCO DE DADOS - EDA AI MINDS")
    print("=" * 45)
    
    # Verificar se .env existe
    env_file = Path("configs/.env")
    if not env_file.exists():
        print("❌ Arquivo configs/.env não encontrado")
        print("   Copie configs/.env.example para configs/.env")
        print("   Configure as variáveis de banco de dados")
        return False
    
    # Testar conexão
    print("\n📋 Testando conexão com banco de dados...")
    try:
        from src.settings import build_db_dsn, DB_HOST
        
        if not DB_HOST:
            print("❌ DB_HOST não configurado em .env")
            return False
            
        dsn = build_db_dsn()
        print(f"✅ DSN construído: {dsn.split('@')[0]}@[HOST_OCULTO]")
        
        # Testar conexão real
        import psycopg
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ Conexão bem-sucedida")
                print(f"   PostgreSQL: {version.split(',')[0]}")
                
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("   Execute: pip install psycopg")
        return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique as configurações em configs/.env")
        return False
    
    # Aplicar migrations
    print(f"\n📋 Aplicando migrations...")
    try:
        import scripts.run_migrations as migrations
        result = migrations.main()
        
        if result == 0:
            print("✅ Migrations aplicadas com sucesso")
        else:
            print("❌ Erro ao aplicar migrations")
            return False
            
    except Exception as e:
        print(f"❌ Erro nas migrations: {e}")
        return False
    
    # Verificar schema
    print(f"\n📋 Verificando schema do banco...")
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                # Verificar se extensão pgvector está instalada
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                if cur.fetchone():
                    print("✅ Extensão pgvector instalada")
                else:
                    print("⚠️ Extensão pgvector não encontrada")
                
                # Verificar tabelas principais
                tables_to_check = ['embeddings', 'chunks', 'metadata']
                for table in tables_to_check:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        );
                    """, (table,))
                    
                    if cur.fetchone()[0]:
                        print(f"✅ Tabela '{table}' existe")
                    else:
                        print(f"⚠️ Tabela '{table}' não encontrada")
                
                # Verificar função de busca vetorial
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_proc 
                        WHERE proname = 'match_embeddings'
                    );
                """)
                
                if cur.fetchone()[0]:
                    print("✅ Função 'match_embeddings' disponível")
                else:
                    print("⚠️ Função 'match_embeddings' não encontrada")
                    
    except Exception as e:
        print(f"⚠️ Erro na verificação do schema: {e}")
        print("   O banco pode estar funcionando mesmo assim")
    
    print(f"\n🎉 SETUP DE BANCO CONCLUÍDO!")
    print("=" * 45)
    print("💡 TESTANDO CONEXÃO:")
    print("   python check_db.py")
    print("\n💡 TESTANDO SISTEMA COMPLETO:")
    print("   python examples/teste_groq_completo.py")
    
    return True


if __name__ == "__main__":
    try:
        success = setup_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup de banco interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erro durante setup de banco: {e}")
        sys.exit(1)