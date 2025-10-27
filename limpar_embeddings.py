"""Script para limpar a tabela embeddings antes de uma nova carga completa.

Este script remove todos os dados da tabela embeddings de forma segura,
mantendo a estrutura da tabela intacta.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def contar_registros() -> int:
    """Conta o número de registros na tabela embeddings."""
    try:
        response = supabase.table('embeddings').select('id', count='exact').execute()
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        logger.error(f"Erro ao contar registros: {e}")
        return 0


def limpar_tabela_embeddings(confirmar: bool = True) -> bool:
    """
    Limpa todos os registros da tabela embeddings.
    
    Args:
        confirmar: Se True, solicita confirmação antes de deletar
        
    Returns:
        True se a limpeza foi bem-sucedida, False caso contrário
    """
    print("\n" + "="*70)
    print("🗑️  LIMPEZA DA TABELA EMBEDDINGS")
    print("="*70 + "\n")
    
    # Contar registros atuais
    total_registros = contar_registros()
    
    if total_registros == 0:
        print("ℹ️  A tabela embeddings já está vazia.")
        return True
    
    print(f"📊 Registros atuais na tabela: {total_registros:,}")
    
    # Solicitar confirmação
    if confirmar:
        print("\n⚠️  ATENÇÃO: Esta operação irá DELETAR TODOS os registros da tabela embeddings!")
        print("   Esta ação NÃO pode ser desfeita.\n")
        
        resposta = input("Deseja continuar? Digite 'SIM' para confirmar: ").strip().upper()
        
        if resposta != "SIM":
            print("\n❌ Operação cancelada pelo usuário.")
            return False
    
    print("\n🔄 Deletando registros em lotes...")
    
    try:
        # Deletar em lotes pequenos para evitar timeout
        batch_size = 100
        total_deletados = 0
        
        while True:
            # Buscar IDs em lote pequeno
            response = supabase.table('embeddings').select('id').limit(batch_size).execute()
            
            if not response.data or len(response.data) == 0:
                break
            
            ids_to_delete = [row['id'] for row in response.data]
            
            # Deletar por ID específico em batch
            for row_id in ids_to_delete:
                try:
                    supabase.table('embeddings').delete().eq('id', row_id).execute()
                    total_deletados += 1
                    if total_deletados % 50 == 0:
                        print(f"  ⏳ Deletados {total_deletados}/{total_registros}...")
                except Exception as e:
                    logger.warning(f"Erro ao deletar {row_id}: {e}")
            
            if len(response.data) < batch_size:
                break
        
        # Verificar se a deleção foi bem-sucedida
        registros_restantes = contar_registros()
        
        print("\n" + "="*70)
        
        if registros_restantes == 0:
            print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print(f"   • Registros deletados: {total_registros:,}")
            print(f"   • Registros restantes: 0")
            logger.info(f"Tabela embeddings limpa: {total_registros} registros deletados")
            return True
        else:
            print("⚠️  LIMPEZA PARCIAL")
            print(f"   • Registros deletados: {total_registros - registros_restantes:,}")
            print(f"   • Registros restantes: {registros_restantes:,}")
            logger.warning(f"Limpeza parcial: {registros_restantes} registros não foram deletados")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO durante a limpeza: {e}")
        logger.error(f"Erro ao limpar tabela embeddings: {e}")
        return False
    
    finally:
        print("="*70 + "\n")


def limpar_por_source_id(source_id: str) -> bool:
    """
    Limpa registros de um source_id específico.
    
    Args:
        source_id: ID da fonte a ser removida
        
    Returns:
        True se a limpeza foi bem-sucedida, False caso contrário
    """
    print(f"\n🔄 Deletando registros do source_id: {source_id}...")
    
    try:
        # Contar registros antes
        response_before = supabase.table('embeddings')\
            .select('id', count='exact')\
            .eq('metadata->>source', source_id)\
            .execute()
        
        count_before = response_before.count if hasattr(response_before, 'count') else 0
        
        if count_before == 0:
            print(f"ℹ️  Nenhum registro encontrado para source_id: {source_id}")
            return True
        
        # Deletar
        supabase.table('embeddings')\
            .delete()\
            .eq('metadata->>source', source_id)\
            .execute()
        
        # Contar registros depois
        response_after = supabase.table('embeddings')\
            .select('id', count='exact')\
            .eq('metadata->>source', source_id)\
            .execute()
        
        count_after = response_after.count if hasattr(response_after, 'count') else 0
        deletados = count_before - count_after
        
        print(f"✅ Registros deletados: {deletados:,}")
        
        if count_after > 0:
            print(f"⚠️  {count_after:,} registros não foram deletados")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao deletar por source_id: {e}")
        logger.error(f"Erro ao deletar source_id {source_id}: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Limpa a tabela embeddings antes de uma nova carga"
    )
    parser.add_argument(
        '--source-id',
        type=str,
        help='Limpar apenas registros de um source_id específico'
    )
    parser.add_argument(
        '--sim',
        action='store_true',
        help='Confirmar automaticamente (não solicitar confirmação)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.source_id:
            # Limpar source_id específico
            sucesso = limpar_por_source_id(args.source_id)
        else:
            # Limpar toda a tabela
            sucesso = limpar_tabela_embeddings(confirmar=not args.sim)
        
        exit(0 if sucesso else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
        exit(130)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        print(f"\n❌ Erro inesperado: {e}")
        exit(1)
