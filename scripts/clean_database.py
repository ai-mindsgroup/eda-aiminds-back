"""Script para limpeza completa da base de embeddings no Supabase.

Executa limpeza em lotes para evitar timeouts em grandes volumes de dados.
"""
from __future__ import annotations

import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def clean_embeddings_table() -> int:
    """Limpa completamente a tabela embeddings em lotes."""
    total_deleted = 0
    batch_size = 1000
    
    print("🧹 Iniciando limpeza da base de embeddings...")
    
    while True:
        try:
            # Buscar IDs em lotes
            response = supabase.table('embeddings').select('id').limit(batch_size).execute()
            
            if not response.data or len(response.data) == 0:
                print("✅ Limpeza concluída - nenhum registro restante")
                break
            
            # Extrair IDs
            ids_to_delete = [row['id'] for row in response.data]
            batch_count = len(ids_to_delete)
            
            print(f"🗑️ Removendo lote de {batch_count} registros...")
            
            # Deletar por IDs específicos (mais eficiente)
            delete_response = supabase.table('embeddings').delete().in_('id', ids_to_delete).execute()
            
            if delete_response.data:
                deleted_count = len(delete_response.data)
                total_deleted += deleted_count
                print(f"   ✅ {deleted_count} registros removidos")
            else:
                print("   ⚠️ Nenhum registro foi removido neste lote")
            
            # Pausa entre lotes para evitar sobrecarga
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Erro durante limpeza: {e}")
            print(f"❌ Erro: {e}")
            # Continuar tentando com lotes menores
            batch_size = max(100, batch_size // 2)
            print(f"🔄 Reduzindo tamanho do lote para {batch_size}")
            continue
    
    return total_deleted

def verify_cleanup() -> int:
    """Verifica quantos registros restaram após limpeza."""
    try:
        response = supabase.table('embeddings').select('id', count='exact').execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        logger.error(f"Erro ao verificar limpeza: {e}")
        return -1

def main() -> int:
    print("=" * 60)
    print("🚀 Script de Limpeza da Base de Embeddings")
    print("=" * 60)
    
    # Verificar estado inicial
    initial_count = verify_cleanup()
    if initial_count == -1:
        print("❌ Erro ao verificar estado inicial da base")
        return 1
    
    print(f"📊 Registros iniciais: {initial_count}")
    
    if initial_count == 0:
        print("✅ Base já está limpa!")
        return 0
    
    # Executar limpeza
    deleted_count = clean_embeddings_table()
    
    # Verificar resultado final
    final_count = verify_cleanup()
    
    print("\n" + "=" * 60)
    print("📈 RESULTADO DA LIMPEZA")
    print("=" * 60)
    print(f"Registros iniciais: {initial_count}")
    print(f"Registros removidos: {deleted_count}")
    print(f"Registros finais: {final_count}")
    
    if final_count == 0:
        print("✅ Limpeza bem-sucedida! Base pronta para nova ingestão.")
        return 0
    else:
        print(f"⚠️ Ainda restam {final_count} registros na base")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())