"""
Script para verificar se a carga completa do CSV foi realizada na tabela embeddings.

Agora a verificação considera apenas os chunks do tipo CSV_ROW do "source_id" mais
recente relativo ao arquivo informado, somando csv_rows e descontando overlap_rows
para evitar contagem duplicada devido ao overlap entre chunks.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger
import re

logger = get_logger(__name__)


def contar_registros_csv(file_path: str) -> int:
    """
    Conta o número de registros (linhas) no arquivo CSV, excluindo o cabeçalho.
    
    Args:
        file_path: Caminho do arquivo CSV
        
    Returns:
        Número total de registros no CSV
    """
    try:
        df = pd.read_csv(file_path)
        total = len(df)
        logger.info(f"📊 Total de registros no CSV: {total:,}")
        return total
    except Exception as e:
        logger.error(f"❌ Erro ao ler CSV: {e}")
        raise


def _parse_iso(dt: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def _encontrar_source_id_recente(base_name: str) -> str | None:
    """Encontra o source_id mais recente no Supabase para um prefixo de arquivo.

    Procura por metadata->>source LIKE "{base_name}_%" e escolhe o que tiver
    maior metadata->>created_at. Se não houver created_at, retorna o primeiro encontrado.
    """
    try:
        pattern = f"{base_name}_%"
        resp = supabase.table('embeddings').select('metadata').like('metadata->>source', pattern).execute()
        rows = resp.data or []
        if not rows:
            return None
        # Mapear por source e pegar o created_at mais recente
        latest_by_source: dict[str, tuple[datetime | None, str]] = {}
        for r in rows:
            md = r.get('metadata') or {}
            src = md.get('source')
            created_at = _parse_iso(md.get('created_at', '')) if isinstance(md.get('created_at', ''), str) else None
            if not src:
                continue
            cur = latest_by_source.get(src)
            if cur is None or (created_at and (cur[0] is None or created_at > cur[0])):
                latest_by_source[src] = (created_at, src)
        # Escolher o mais recente entre os sources encontrados
        if not latest_by_source:
            return None
        selected = sorted(latest_by_source.values(), key=lambda x: (x[0] is not None, x[0]), reverse=True)[0][1]
        return selected
    except Exception as e:
        logger.error(f"❌ Erro ao localizar source_id: {e}")
        return None


def contar_registros_chunks(source_id: str) -> int:
    """
    Conta o número de registros distintos representados pelos chunks CSV_ROW
    do source_id informado. Para evitar dupla contagem devido ao overlap entre
    chunks, soma-se csv_rows e subtraem-se overlap_rows (dos chunks com index > 0).

    Args:
        source_id: Identificador do dataset na coluna metadata->>source

    Returns:
        Número total de registros representados pelos chunks CSV_ROW do source_id
    """
    try:
        # Buscar apenas chunks de LINHA (CSV_ROW) do source_id
        response = (
            supabase
            .table('embeddings')
            .select('metadata')
            .eq('metadata->>strategy', 'csv_row')
            .eq('metadata->>source', source_id)
            .execute()
        )
        
        if not response.data:
            logger.warning("⚠️ Nenhum chunk CSV_ROW encontrado para o source_id informado")
            return 0
        
        total_chunks = len(response.data)
        logger.info(f"📦 Total de chunks CSV_ROW do source '{source_id}': {total_chunks:,}")

        total_csv_rows = 0
        total_overlap_rows = 0

        for idx, row in enumerate(response.data, 1):
            md = row.get('metadata') or {}
            csv_rows = int(md.get('csv_rows', 0))
            overlap = int(md.get('overlap_rows', 0))
            chunk_index = int(md.get('chunk_index', 0))

            total_csv_rows += csv_rows
            # Descontar overlap apenas para chunks com índice > 0
            if chunk_index > 0:
                total_overlap_rows += overlap

            if idx <= 3:
                logger.debug(
                    f"Chunk {idx}: csv_rows={csv_rows}, overlap_rows={overlap}, chunk_index={chunk_index}"
                )

        total_distintos = max(0, total_csv_rows - total_overlap_rows)
        logger.info(
            f"📊 Total de registros distintos (ajustado por overlap): {total_distintos:,}"
        )
        return total_distintos
        
    except Exception as e:
        logger.error(f"❌ Erro ao contar registros dos chunks: {e}")
        raise


def verificar_carga_completa(csv_path: str):
    """
    Verifica se a carga do CSV foi completa comparando os totais.
    
    Args:
        csv_path: Caminho do arquivo CSV original
    """
    print("\n" + "="*70)
    print("🔍 VERIFICAÇÃO DE CARGA COMPLETA - EMBEDDINGS")
    print("="*70 + "\n")
    
    try:
        # Contar registros no CSV
        print("📁 Analisando arquivo CSV...")
        total_csv = contar_registros_csv(csv_path)
        
        # Determinar base e localizar source_id mais recente
        print("\n🔎 Analisando chunks na tabela embeddings...")
        base_name = Path(csv_path).stem
        source_id = _encontrar_source_id_recente(base_name)
        if not source_id:
            print(f"⚠️ Não foi possível localizar source_id para prefixo '{base_name}_%'.")
            print("   Verifique se a ingestão foi executada e tente novamente.")
            return {
                'csv_total': total_csv,
                'chunks_total': 0,
                'diferenca': total_csv,
                'percentual': 0.0,
                'completo': False
            }

        logger.info(f"🔎 Source ID identificado para verificação: {source_id}")

        # Contar registros distintos representados pelos chunks CSV_ROW
        total_chunks = contar_registros_chunks(source_id)
        
        # Comparar totais
        print("\n" + "="*70)
        print("📊 RESULTADO DA VERIFICAÇÃO")
        print("="*70)
        print(f"✅ Registros no arquivo CSV:        {total_csv:>10,}")
        print(f"📦 Registros representados pelos chunks CSV_ROW ({source_id}): {total_chunks:>10,}")
        print("-"*70)
        
        diferenca = total_csv - total_chunks
        percentual = (total_chunks / total_csv * 100) if total_csv > 0 else 0
        
        print(f"📈 Percentual carregado:            {percentual:>9.2f}%")
        print(f"📉 Diferença:                       {diferenca:>10,}")
        print("="*70)
        
        if total_chunks == total_csv:
            print("\n✅ CARGA COMPLETA! Todos os registros foram carregados com sucesso.")
        elif total_chunks > total_csv:
            print(f"\n⚠️ ATENÇÃO! Há {diferenca * -1:,} registros A MAIS nos chunks.")
            print("   Pode haver duplicação ou linhas extras no processamento.")
        else:
            print(f"\n❌ CARGA INCOMPLETA! Faltam {diferenca:,} registros ({100-percentual:.2f}%).")
            print("   Recomenda-se reprocessar o arquivo CSV.")
        
        print("\n" + "="*70 + "\n")
        
        return {
            'csv_total': total_csv,
            'chunks_total': total_chunks,
            'diferenca': diferenca,
            'percentual': percentual,
            'completo': total_chunks == total_csv
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        print(f"\n❌ Erro ao verificar carga: {e}\n")
        raise


if __name__ == "__main__":
    import sys
    from src.settings import EDA_DATA_DIR_PROCESSADO
    
    # Validar argumentos CLI
    if len(sys.argv) < 2:
        print("❌ Uso: python verificar_carga_completa.py <nome_arquivo.csv>")
        print("\nExemplo:")
        print("  python verificar_carga_completa.py creditcard.csv")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    csv_file = EDA_DATA_DIR_PROCESSADO / csv_filename
    
    # Validar existência do arquivo
    if not csv_file.exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        print(f"\nVerifique se o arquivo está em: {EDA_DATA_DIR_PROCESSADO}")
        sys.exit(1)
    
    # Executar verificação
    resultado = verificar_carga_completa(str(csv_file))
    
    # Retornar código de saída apropriado
    exit(0 if resultado['completo'] else 1)
