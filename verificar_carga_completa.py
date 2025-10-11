"""
Script para verificar se a carga completa do CSV foi realizada na tabela embeddings.
Compara o número de registros do arquivo CSV com o total de registros nos chunks.
"""

import pandas as pd
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


def contar_registros_chunks() -> int:
    """
    Conta o número de registros extraídos dos chunks na tabela embeddings.
    Cada chunk contém múltiplas linhas do CSV original.
    
    Returns:
        Número total de registros nos chunks
    """
    try:
        # Buscar todos os chunks
        response = supabase.table('embeddings').select('chunk_text').execute()
        
        if not response.data:
            logger.warning("⚠️ Nenhum chunk encontrado na tabela embeddings")
            return 0
        
        total_chunks = len(response.data)
        logger.info(f"📦 Total de chunks na tabela: {total_chunks:,}")
        
        # Contar registros em cada chunk
        total_registros = 0
        
        for idx, row in enumerate(response.data, 1):
            chunk_text = row.get('chunk_text', '')
            
            if not chunk_text:
                continue
            
            # Contar linhas no chunk (cada linha representa um registro)
            # Considerando que cada registro está em uma linha separada
            linhas = chunk_text.strip().split('\n')
            
            # Filtrar linhas vazias
            linhas_validas = [linha for linha in linhas if linha.strip()]
            
            num_registros = len(linhas_validas)
            total_registros += num_registros
            
            if idx <= 5:  # Log dos primeiros 5 chunks para debug
                logger.debug(f"Chunk {idx}: {num_registros} registros")
        
        logger.info(f"📊 Total de registros extraídos dos chunks: {total_registros:,}")
        return total_registros
        
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
        
        # Contar registros nos chunks
        print("\n🔎 Analisando chunks na tabela embeddings...")
        total_chunks = contar_registros_chunks()
        
        # Comparar totais
        print("\n" + "="*70)
        print("📊 RESULTADO DA VERIFICAÇÃO")
        print("="*70)
        print(f"✅ Registros no arquivo CSV:        {total_csv:>10,}")
        print(f"📦 Registros extraídos dos chunks:  {total_chunks:>10,}")
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
    # Caminho do arquivo CSV
    csv_file = r"C:\workstashion\eda-aiminds-i2a2-rb\data\creditcard.csv"
    
    # Executar verificação
    resultado = verificar_carga_completa(csv_file)
    
    # Retornar código de saída apropriado
    exit(0 if resultado['completo'] else 1)
