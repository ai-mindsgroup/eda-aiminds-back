"""
Módulo de extração de metadados de datasets CSV.

Este módulo implementa a Etapa 1 do pipeline de ingestão robusta:
- Leitura dinâmica de qualquer arquivo CSV
- Detecção automática de tipos de dados (dtype e semântico)
- Geração de JSON estruturado com metadados completos

Autor: EDA AI Minds Backend Team
Data: 2025-01-20
"""

import os
import json
import warnings
from typing import Dict, Any, Optional
from pathlib import Path

import pandas as pd
import numpy as np

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def detect_semantic_type(column_name: str, series: pd.Series) -> str:
    """
    Detecta o tipo semântico de uma coluna de forma inteligente.
    
    Analisa tanto o nome da coluna quanto os valores para determinar
    o tipo semântico mais apropriado.
    
    Args:
        column_name: Nome da coluna
        series: Série pandas com os dados da coluna
    
    Returns:
        Tipo semântico identificado:
        - "temporal": Dados de data/hora/timestamp
        - "categorical_binary": Categórico com exatamente 2 valores únicos
        - "categorical": Categórico com múltiplos valores
        - "numeric": Numérico (int, float)
        - "text": Texto livre
        - "unknown": Não foi possível determinar
    """
    try:
        # Normalizar nome da coluna
        col_lower = column_name.lower()
        
        # 1. Verificar indicadores temporais no nome
        temporal_keywords = [
            "time", "date", "timestamp", "datetime", "created", "updated",
            "modified", "year", "month", "day", "hour", "minute", "second",
            "data", "hora", "tempo", "dia", "mes", "ano"
        ]
        
        if any(keyword in col_lower for keyword in temporal_keywords):
            return "temporal"
        
        # 2. Verificar se é datetime pelo dtype
        if pd.api.types.is_datetime64_any_dtype(series):
            return "temporal"
        
        # 3. Tentar converter para datetime (sample para performance)
        if pd.api.types.is_object_dtype(series):
            sample = series.dropna().head(100)
            if len(sample) > 0:
                try:
                    pd.to_datetime(sample, errors='raise')
                    return "temporal"
                except (ValueError, TypeError):
                    pass
        
        # 4. Verificar categórico binário
        unique_count = series.nunique(dropna=True)
        if unique_count == 2:
            return "categorical_binary"
        
        # 5. Verificar numérico
        if pd.api.types.is_numeric_dtype(series):
            # Verificar se é ID (muitos valores únicos relativos ao total)
            if unique_count / len(series.dropna()) > 0.95:
                return "numeric_id"
            return "numeric"
        
        # 6. Verificar categórico (baixa cardinalidade)
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
            # Considerar categórico se < 50% de valores únicos ou < 100 categorias
            ratio = unique_count / len(series.dropna()) if len(series.dropna()) > 0 else 0
            if ratio < 0.5 or unique_count < 100:
                return "categorical"
            else:
                # Alta cardinalidade = texto livre
                return "text"
        
        # 7. Boolean
        if pd.api.types.is_bool_dtype(series):
            return "categorical_binary"
        
        return "unknown"
        
    except Exception as e:
        logger.warning(f"Erro ao detectar tipo semântico da coluna '{column_name}': {e}")
        return "unknown"


def extract_column_metadata(column_name: str, series: pd.Series) -> Dict[str, Any]:
    """
    Extrai metadados detalhados de uma coluna específica.
    
    Args:
        column_name: Nome da coluna
        series: Série pandas com os dados
    
    Returns:
        Dicionário com metadados da coluna
    """
    try:
        metadata = {
            "dtype": str(series.dtype),
            "semantic_type": detect_semantic_type(column_name, series),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float(round(series.isnull().sum() / len(series) * 100, 2)),
            "unique_values": int(series.nunique(dropna=True)),
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "mode": None,
            "top_values": None
        }
        
        # Estatísticas para numéricos
        if pd.api.types.is_numeric_dtype(series):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                metadata["min"] = float(series.min()) if not pd.isna(series.min()) else None
                metadata["max"] = float(series.max()) if not pd.isna(series.max()) else None
                metadata["mean"] = float(series.mean()) if not pd.isna(series.mean()) else None
                metadata["median"] = float(series.median()) if not pd.isna(series.median()) else None
                metadata["std"] = float(series.std()) if not pd.isna(series.std()) else None
        
        # Modo (valor mais frequente)
        try:
            mode_value = series.mode()
            if len(mode_value) > 0:
                metadata["mode"] = str(mode_value.iloc[0]) if not pd.isna(mode_value.iloc[0]) else None
        except Exception:
            pass
        
        # Top valores para categóricos
        if metadata["semantic_type"] in ["categorical", "categorical_binary", "text"]:
            try:
                top_values = series.value_counts(dropna=True).head(5)
                metadata["top_values"] = {
                    str(k): int(v) for k, v in top_values.items()
                }
            except Exception:
                pass
        
        return metadata
        
    except Exception as e:
        logger.error(f"Erro ao extrair metadados da coluna '{column_name}': {e}")
        return {
            "dtype": str(series.dtype),
            "semantic_type": "unknown",
            "null_count": 0,
            "null_percentage": 0.0,
            "unique_values": 0
        }


def extract_dataset_metadata(file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrai metadados completos de um dataset CSV de forma 100% dinâmica.
    
    Esta função implementa a Etapa 1 do pipeline de ingestão robusta:
    - Lê qualquer arquivo CSV fornecido
    - Detecta tipos de dados reais e semânticos coluna por coluna
    - Gera JSON estruturado com metadados completos
    - Salva JSON em arquivo (opcional)
    
    Args:
        file_path: Caminho para o arquivo CSV
        output_path: Caminho para salvar o JSON (opcional)
    
    Returns:
        Dicionário com metadados completos do dataset
    
    Raises:
        FileNotFoundError: Se o arquivo CSV não existir
        ValueError: Se o arquivo não puder ser lido como CSV
    
    Example:
        >>> metadata = extract_dataset_metadata("data/creditcard.csv")
        >>> print(json.dumps(metadata, indent=2))
    """
    # Validar entrada
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    logger.info(f"Iniciando extração de metadados: {file_path}")
    
    try:
        # Ler CSV de forma robusta
        df = pd.read_csv(file_path, low_memory=False)
        logger.info(f"CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")
        
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo CSV: {e}")
    
    # Nome do dataset (sem extensão)
    dataset_name = Path(file_path).stem
    
    # Estrutura principal de metadados
    dataset_metadata = {
        "dataset_name": dataset_name,
        "file_path": str(file_path),
        "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
        "shape": {
            "rows": len(df),
            "cols": len(df.columns)
        },
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        "columns": {}
    }
    
    # Extrair metadados de cada coluna dinamicamente
    logger.info("Extraindo metadados coluna por coluna...")
    for col in df.columns:
        logger.debug(f"Processando coluna: {col}")
        dataset_metadata["columns"][col] = extract_column_metadata(col, df[col])
    
    # Estatísticas gerais do dataset
    dataset_metadata["statistics"] = {
        "total_null_cells": int(df.isnull().sum().sum()),
        "null_percentage": float(round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2)),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_percentage": float(round(df.duplicated().sum() / len(df) * 100, 2))
    }
    
    # Análise de tipos semânticos
    semantic_summary = {}
    for col, meta in dataset_metadata["columns"].items():
        sem_type = meta["semantic_type"]
        semantic_summary[sem_type] = semantic_summary.get(sem_type, 0) + 1
    
    dataset_metadata["semantic_summary"] = semantic_summary
    
    logger.info(f"Metadados extraídos com sucesso: {len(dataset_metadata['columns'])} colunas")
    
    # Salvar JSON se solicitado
    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadados salvos em: {output_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar JSON: {e}")
    
    return dataset_metadata


def print_metadata_summary(metadata: Dict[str, Any]) -> None:
    """
    Imprime um resumo legível dos metadados extraídos.
    
    Args:
        metadata: Dicionário de metadados retornado por extract_dataset_metadata
    """
    print("\n" + "=" * 80)
    print(f"DATASET: {metadata['dataset_name']}")
    print("=" * 80)
    print(f"Arquivo: {metadata['file_path']}")
    print(f"Tamanho: {metadata['file_size_mb']} MB")
    print(f"Dimensões: {metadata['shape']['rows']} linhas × {metadata['shape']['cols']} colunas")
    print(f"Memória: {metadata['memory_usage_mb']} MB")
    print()
    
    print("ESTATÍSTICAS GERAIS:")
    print(f"  • Células nulas: {metadata['statistics']['total_null_cells']} ({metadata['statistics']['null_percentage']}%)")
    print(f"  • Linhas duplicadas: {metadata['statistics']['duplicate_rows']} ({metadata['statistics']['duplicate_percentage']}%)")
    print()
    
    print("DISTRIBUIÇÃO DE TIPOS SEMÂNTICOS:")
    for sem_type, count in metadata['semantic_summary'].items():
        print(f"  • {sem_type}: {count} colunas")
    print()
    
    print("COLUNAS:")
    print("-" * 80)
    for col_name, col_meta in metadata['columns'].items():
        print(f"  {col_name}")
        print(f"    - Tipo: {col_meta['dtype']} ({col_meta['semantic_type']})")
        print(f"    - Nulos: {col_meta['null_count']} ({col_meta['null_percentage']}%)")
        print(f"    - Valores únicos: {col_meta['unique_values']}")
        
        if col_meta.get('mean') is not None:
            print(f"    - Média: {col_meta['mean']:.2f} | Mediana: {col_meta['median']:.2f}")
        
        if col_meta.get('top_values'):
            top_3 = list(col_meta['top_values'].items())[:3]
            print(f"    - Top valores: {', '.join([f'{k}({v})' for k, v in top_3])}")
        
        print()
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    """
    Exemplo de uso do módulo.
    
    Execute:
        python -m src.ingest.metadata_extractor
    """
    import sys
    
    # Verificar se foi passado um arquivo CSV
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Tentar encontrar CSV de exemplo
        sample_files = [
            "data/creditcard.csv",
            "data/sample.csv",
            "temp_convert.csv"
        ]
        
        csv_file = None
        for file in sample_files:
            if os.path.exists(file):
                csv_file = file
                break
        
        if not csv_file:
            print("❌ Nenhum arquivo CSV encontrado.")
            print("Uso: python -m src.ingest.metadata_extractor <caminho_csv>")
            sys.exit(1)
    
    print(f"🔍 Extraindo metadados de: {csv_file}\n")
    
    # Extrair metadados
    try:
        output_json = f"outputs/metadata_{Path(csv_file).stem}.json"
        metadata = extract_dataset_metadata(csv_file, output_path=output_json)
        
        # Imprimir resumo
        print_metadata_summary(metadata)
        
        # Imprimir JSON completo
        print("JSON COMPLETO:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        print(f"\n✅ Metadados salvos em: {output_json}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
