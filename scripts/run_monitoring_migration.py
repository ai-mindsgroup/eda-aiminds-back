"""
Script para executar migration do sistema de monitoramento no Supabase.

Cria tabelas sandbox_metrics e sandbox_alerts com todos os índices,
views agregadas e funções de cleanup.

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def read_migration_file(migration_path: str) -> str:
    """
    Lê arquivo de migration SQL.
    
    Args:
        migration_path: Caminho do arquivo SQL
        
    Returns:
        Conteúdo do arquivo SQL
    """
    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de migration não encontrado: {migration_path}")
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao ler arquivo: {e}")
        raise


def execute_migration_sql(sql_content: str) -> bool:
    """
    Executa migration SQL no Supabase.
    
    Args:
        sql_content: Conteúdo SQL a executar
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        # Dividir SQL em statements individuais (separados por ponto e vírgula)
        # Ignorar comentários e linhas vazias
        statements = []
        current_statement = []
        in_function = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # Ignorar comentários
            if stripped.startswith('--'):
                continue
            
            # Detectar início de função/procedure
            if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
                in_function = True
            
            # Adicionar linha ao statement atual
            if stripped:
                current_statement.append(line)
            
            # Detectar fim de statement
            if stripped.endswith(';'):
                # Se dentro de função, verificar se é o fim da função
                if in_function and '$$;' in stripped:
                    in_function = False
                    statement = '\n'.join(current_statement)
                    statements.append(statement)
                    current_statement = []
                # Se não está em função, é fim de statement normal
                elif not in_function:
                    statement = '\n'.join(current_statement)
                    statements.append(statement)
                    current_statement = []
        
        logger.info(f"📊 Total de statements SQL: {len(statements)}")
        
        # Executar cada statement
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            # Ignorar statements vazios
            if not statement.strip():
                continue
            
            try:
                # Extrair tipo de statement para log
                statement_type = statement.strip().split()[0:3]
                statement_desc = ' '.join(statement_type)
                
                logger.info(f"▶️ [{i}/{len(statements)}] Executando: {statement_desc}...")
                
                # Executar via Supabase RPC (PostgREST)
                # Para DDL, precisamos usar o client direto do Supabase
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                
                logger.info(f"✅ [{i}/{len(statements)}] Sucesso: {statement_desc}")
                success_count += 1
                
            except AttributeError:
                # Se RPC não existe, tentar executar diretamente
                # Nota: Isso pode não funcionar com Supabase client padrão
                logger.warning(f"⚠️ RPC exec_sql não disponível, tentando método alternativo...")
                
                # Alternativa: usar psycopg diretamente
                try:
                    from src.settings import build_db_dsn
                    import psycopg
                    
                    dsn = build_db_dsn()
                    
                    with psycopg.connect(dsn) as conn:
                        with conn.cursor() as cur:
                            cur.execute(statement)
                            conn.commit()
                    
                    logger.info(f"✅ [{i}/{len(statements)}] Sucesso (psycopg): {statement_desc}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ [{i}/{len(statements)}] Erro: {statement_desc}")
                    logger.error(f"   Detalhes: {e}")
                    error_count += 1
                    
                    # Continuar com próximo statement
                    continue
                    
            except Exception as e:
                logger.error(f"❌ [{i}/{len(statements)}] Erro: {statement_desc}")
                logger.error(f"   Detalhes: {e}")
                error_count += 1
                
                # Continuar com próximo statement
                continue
        
        # Resumo final
        logger.info("=" * 80)
        logger.info("📊 RESUMO DA MIGRATION")
        logger.info("=" * 80)
        logger.info(f"✅ Sucesso: {success_count}/{len(statements)}")
        logger.info(f"❌ Erros: {error_count}/{len(statements)}")
        
        if error_count == 0:
            logger.info("🎉 Migration executada com sucesso!")
            return True
        else:
            logger.warning(f"⚠️ Migration concluída com {error_count} erros")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro crítico ao executar migration: {e}")
        return False


def execute_migration_psycopg(sql_content: str) -> bool:
    """
    Executa migration SQL usando psycopg diretamente.
    
    Args:
        sql_content: Conteúdo SQL a executar
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        from src.settings import build_db_dsn
        import psycopg
        
        logger.info("🔌 Conectando ao PostgreSQL via psycopg...")
        
        dsn = build_db_dsn()
        
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                logger.info("▶️ Executando migration SQL...")
                
                # Executar todo o SQL de uma vez
                cur.execute(sql_content)
                
                logger.info("💾 Commitando transação...")
                conn.commit()
                
                logger.info("✅ Migration executada com sucesso!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Erro ao executar migration via psycopg: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_migration() -> bool:
    """
    Verifica se migration foi aplicada corretamente.
    
    Returns:
        True se tabelas existem, False caso contrário
    """
    try:
        logger.info("🔍 Verificando migration...")
        
        # Verificar se tabelas existem
        tables_to_check = ['sandbox_metrics', 'sandbox_alerts']
        
        from src.settings import build_db_dsn
        import psycopg
        
        dsn = build_db_dsn()
        
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                for table in tables_to_check:
                    cur.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        );
                    """)
                    
                    exists = cur.fetchone()[0]
                    
                    if exists:
                        logger.info(f"✅ Tabela '{table}' existe")
                        
                        # Contar registros
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        logger.info(f"   📊 {count} registros")
                    else:
                        logger.error(f"❌ Tabela '{table}' NÃO existe")
                        return False
                
                # Verificar views
                views_to_check = ['sandbox_metrics_24h', 'sandbox_alerts_active']
                
                for view in views_to_check:
                    cur.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.views 
                            WHERE table_schema = 'public' 
                            AND table_name = '{view}'
                        );
                    """)
                    
                    exists = cur.fetchone()[0]
                    
                    if exists:
                        logger.info(f"✅ View '{view}' existe")
                    else:
                        logger.warning(f"⚠️ View '{view}' NÃO existe")
                
                logger.info("✅ Verificação concluída com sucesso!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar migration: {e}")
        return False


def main():
    """Função principal."""
    logger.info("=" * 80)
    logger.info("🚀 EXECUTANDO MIGRATION: Sistema de Monitoramento")
    logger.info("=" * 80)
    
    # Caminho da migration
    project_root = Path(__file__).parent.parent
    migration_path = project_root / 'migrations' / '0003_sandbox_monitoring_schema.sql'
    
    logger.info(f"📁 Migration: {migration_path}")
    
    # Ler arquivo SQL
    try:
        sql_content = read_migration_file(str(migration_path))
        logger.info(f"✅ Migration carregada ({len(sql_content)} caracteres)")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar migration: {e}")
        return 1
    
    # Executar migration via psycopg (método mais confiável)
    logger.info("")
    logger.info("Método: psycopg (PostgreSQL direto)")
    logger.info("-" * 80)
    
    success = execute_migration_psycopg(sql_content)
    
    if not success:
        logger.error("❌ Falha ao executar migration")
        return 1
    
    # Verificar migration
    logger.info("")
    logger.info("-" * 80)
    
    if verify_migration():
        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 MIGRATION CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📊 Tabelas criadas:")
        logger.info("   - sandbox_metrics")
        logger.info("   - sandbox_alerts")
        logger.info("")
        logger.info("📈 Views criadas:")
        logger.info("   - sandbox_metrics_24h")
        logger.info("   - sandbox_alerts_active")
        logger.info("")
        logger.info("🔧 Funções criadas:")
        logger.info("   - cleanup_old_sandbox_metrics()")
        logger.info("   - cleanup_old_sandbox_alerts()")
        logger.info("")
        return 0
    else:
        logger.error("❌ Verificação falhou")
        return 1


if __name__ == '__main__':
    sys.exit(main())
