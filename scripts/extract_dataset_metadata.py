"""
Script para extrair metadados de datasets CSV.

Este script executa a Etapa 1 do pipeline de ingestão robusta.
Pode ser executado standalone ou importado como módulo.

Uso:
    python scripts/extract_dataset_metadata.py <arquivo_csv>
    python scripts/extract_dataset_metadata.py data/creditcard.csv

Autor: EDA AI Minds Backend Team
Data: 2025-01-20
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingest.metadata_extractor import (
    extract_dataset_metadata,
    print_metadata_summary
)
from src.utils.logging_config import get_logger
import json

logger = get_logger(__name__)


def main():
    """Função principal do script."""
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/extract_dataset_metadata.py <arquivo_csv>")
        print("\nExemplo:")
        print("  python scripts/extract_dataset_metadata.py data/creditcard.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Validar arquivo
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        sys.exit(1)
    
    print(f"🔍 Extraindo metadados de: {csv_file}\n")
    
    try:
        # Definir caminho de saída
        os.makedirs("outputs", exist_ok=True)
        output_json = f"outputs/metadata_{Path(csv_file).stem}.json"
        
        # Extrair metadados
        logger.info(f"Iniciando extração: {csv_file}")
        metadata = extract_dataset_metadata(csv_file, output_path=output_json)
        
        # Imprimir resumo formatado
        print_metadata_summary(metadata)
        
        # Salvar JSON adicional com pretty print
        json_output = json.dumps(metadata, indent=2, ensure_ascii=False)
        print("=" * 80)
        print("JSON COMPLETO:")
        print("=" * 80)
        print(json_output)
        print("=" * 80)
        
        print(f"\n✅ Extração concluída com sucesso!")
        print(f"📁 Metadados salvos em: {output_json}")
        
        logger.info(f"Extração concluída: {output_json}")
        
    except Exception as e:
        print(f"❌ Erro durante extração: {e}")
        logger.error(f"Erro: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
