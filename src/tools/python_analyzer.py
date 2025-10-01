"""Ferramenta de análise de dados Python para o sistema multiagente.

⚠️ CONFORMIDADE CRÍTICA: Esta ferramenta deve priorizar dados da tabela embeddings
sobre acesso direto a arquivos CSV para agentes de resposta.

Esta ferramenta permite que agentes executem código Python real para
calcular estatísticas precisas dos dados armazenados no Supabase.
"""
from __future__ import annotations
import sys
import os
import inspect
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import io
import traceback
import warnings

# Suprimir warnings desnecessários
warnings.filterwarnings('ignore')

from src.utils.logging_config import get_logger

# Import do cliente Supabase para recuperação de dados
try:
    from src.vectorstore.supabase_client import supabase
    SUPABASE_CLIENT_AVAILABLE = True
except ImportError as e:
    SUPABASE_CLIENT_AVAILABLE = False
    supabase = None


class UnauthorizedCSVAccessError(Exception):
    """Exceção lançada quando acesso não autorizado a CSV é detectado."""
    pass


@dataclass
class PythonAnalysisResult:
    """Resultado da execução de análise Python"""
    success: bool
    result: Any
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0


class PythonDataAnalyzer:
    """Ferramenta para execução de código Python para análise de dados.
    
    ⚠️ CONFORMIDADE: Prioriza dados da tabela embeddings sobre CSV direto.
    
    Esta classe permite que agentes executem código Python real para
    calcular estatísticas precisas dos dados, evitando alucinações do LLM.
    """
    
    def __init__(self, caller_agent: Optional[str] = None):
        self.logger = get_logger(__name__)
        
        # Detectar e validar caller_agent
        self.caller_agent = caller_agent or self._detect_caller_agent()
        
        self._setup_secure_environment()
        self.logger.info(f"PythonDataAnalyzer inicializado por: {self.caller_agent}")
    
    def _detect_caller_agent(self) -> str:
        """Detecta qual agente está chamando este analisador."""
        frame = inspect.currentframe()
        try:
            # Subir na stack para encontrar o caller
            for i in range(15):  # Limite de segurança
                frame = frame.f_back
                if frame is None:
                    break
                    
                filename = frame.f_code.co_filename
                
                # Verificar se é um agente conhecido
                if 'ingestion_agent' in filename:
                    return 'ingestion_agent'
                elif 'orchestrator_agent' in filename:
                    return 'orchestrator_agent'
                elif 'csv_analysis_agent' in filename or 'embeddings_analysis_agent' in filename:
                    return 'analysis_agent'
                elif 'rag_agent' in filename:
                    return 'rag_agent'
                elif 'test_' in filename or '_test' in filename:
                    return 'test_system'
                    
            return 'unknown_caller'
            
        finally:
            del frame
    
    def _validate_csv_access_authorization(self) -> None:
        """Valida se o caller tem autorização para acessar CSV diretamente."""
        authorized_agents = [
            'ingestion_agent',
            'test_system'  # Para testes
        ]
        
        if self.caller_agent not in authorized_agents:
            error_msg = (
                f"⚠️ VIOLAÇÃO DE CONFORMIDADE DETECTADA!\n"
                f"Agente '{self.caller_agent}' tentou usar PythonDataAnalyzer com potencial acesso CSV.\n"
                f"Apenas agentes autorizados podem acessar CSV: {authorized_agents}\n"
                f"Agentes de resposta devem usar APENAS a tabela embeddings."
            )
            self.logger.error(error_msg)
            raise UnauthorizedCSVAccessError(error_msg)
        
        self.logger.info(f"✅ PythonDataAnalyzer: Acesso autorizado para agente: {self.caller_agent}")
    
    def _setup_secure_environment(self):
        """Configura ambiente seguro para execução de código Python"""
        # Lista de módulos permitidos (segurança)
        self.allowed_modules = {
            'pandas', 'numpy', 'math', 'statistics', 'datetime', 'json',
            'collections', 're', 'itertools', 'functools'
        }
        
        # Namespaces seguros para execução
        self.safe_globals = {
            '__builtins__': {
                'len', 'sum', 'min', 'max', 'abs', 'round', 'sorted',
                'enumerate', 'zip', 'range', 'list', 'dict', 'tuple', 'set',
                'str', 'int', 'float', 'bool', 'print'
            },
            'pd': pd,
            'np': np,
        }
    
    def get_data_from_embeddings(self, limit: int = None, metadata_filter: Dict = None) -> Optional[pd.DataFrame]:
        """Recupera dados APENAS da tabela embeddings (CONFORMIDADE).
        
        Args:
            limit: Limite de registros (None para todos)
            metadata_filter: Filtros por metadata
            
        Returns:
            DataFrame com os dados ou None se falhar
        """
        if not SUPABASE_CLIENT_AVAILABLE or not supabase:
            self.logger.error("Cliente Supabase não disponível")
            return None
        
        try:
            self.logger.info("✅ Recuperando dados da tabela embeddings (CONFORMIDADE)")
            
            query = supabase.table('embeddings').select('*')
            
            # Aplicar filtros se especificados
            if metadata_filter:
                for key, value in metadata_filter.items():
                    query = query.eq(f'metadata->{key}', value)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            if not result.data:
                self.logger.warning("Nenhum dado encontrado na tabela embeddings")
                return None
            
            df = pd.DataFrame(result.data)
            self.logger.info(f"✅ Dados recuperados: {len(df)} registros da tabela embeddings")
            
            # Remover colunas com tipos não-hashable (metadata, embedding) para evitar erros
            if 'metadata' in df.columns:
                df = df.drop(columns=['metadata'])
            if 'embedding' in df.columns:
                df = df.drop(columns=['embedding'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dados da tabela embeddings: {str(e)}")
            return None
    
    def get_data_from_supabase(self, table: str = 'embeddings', limit: int = None) -> Optional[pd.DataFrame]:
        """Recupera dados do Supabase como DataFrame.
        
        ⚠️ CONFORMIDADE: Apenas tabela 'embeddings' para agentes de resposta.
        
        Args:
            table: Nome da tabela ('embeddings', 'chunks', etc.)
            limit: Limite de registros (None para todos)
            
        Returns:
            DataFrame com os dados ou None se falhar
        """
        # Validar conformidade para agentes de resposta
        if table != 'embeddings' and self.caller_agent not in ['ingestion_agent', 'test_system']:
            error_msg = (
                f"⚠️ VIOLAÇÃO DE CONFORMIDADE DETECTADA!\n"
                f"Agente '{self.caller_agent}' tentou acessar tabela '{table}' diretamente.\n"
                f"Agentes de resposta devem usar APENAS a tabela 'embeddings'."
            )
            self.logger.error(error_msg)
            raise UnauthorizedCSVAccessError(error_msg)
        
        if not SUPABASE_CLIENT_AVAILABLE or not supabase:
            self.logger.error("Cliente Supabase não disponível")
            return None
        
        try:
            self.logger.info(f"Recuperando dados da tabela {table}...")
            
            query = supabase.table(table).select('*')
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            if not result.data:
                self.logger.warning(f"Nenhum dado encontrado na tabela {table}")
                return None
            
            df = pd.DataFrame(result.data)
            self.logger.info(f"Dados recuperados: {len(df)} registros, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dados do Supabase: {str(e)}")
            return None
    
    def reconstruct_original_data(self) -> Optional[pd.DataFrame]:
        """Reconstrói dados originais do CSV a partir dos embeddings.
        
        Returns:
            DataFrame com dados originais ou None se falhar
        """
        try:
            # Estratégia 1: Tentar detectar arquivo CSV automaticamente
            self.logger.info("Tentando reconstruir dados originais...")
            
            embeddings_df = self.get_data_from_supabase('embeddings', limit=100)
            if embeddings_df is None or 'chunk_text' not in embeddings_df.columns:
                # Estratégia 2: Buscar arquivo CSV mais recente no diretório data/
                return self._detect_most_recent_csv()
            
            # Analisar chunk_text para extrair informações estruturadas
            sample_chunks = embeddings_df['chunk_text'].dropna().head(20)  # Aumentar amostra
            
            # Procurar por padrões nos chunks que indiquem arquivos CSV
            csv_files_found = set()
            
            for chunk in sample_chunks:
                # SISTEMA GENÉRICO: Buscar qualquer arquivo .csv mencionado
                import re
                csv_files = re.findall(r'(\w+\.csv)', chunk.lower())
                if csv_files:
                    csv_files_found.update(csv_files)
                    
                # Também procurar por nomes de arquivos sem extensão
                potential_files = re.findall(r'arquivo[:\s]+(\w+)', chunk.lower())
                for file in potential_files:
                    csv_files_found.add(f"{file}.csv")
            
            # Tentar carregar os arquivos encontrados
            if csv_files_found:
                self.logger.info(f"Arquivos CSV detectados: {list(csv_files_found)}")
                
                for csv_file in csv_files_found:
                    result = self._reconstruct_csv_data(csv_file)
                    if result is not None:
                        return result
            
            # Estratégia 3: Se nada foi encontrado, usar o arquivo mais recente
            return self._detect_most_recent_csv()
            
        except Exception as e:
            self.logger.error(f"Erro ao reconstruir dados originais: {str(e)}")
            return None
            
    def _detect_most_recent_csv(self) -> Optional[pd.DataFrame]:
        """Detecta dados via embeddings (CONFORMIDADE) ou fallback para ingestão."""
        # Priorizar dados da tabela embeddings
        embeddings_data = self.get_data_from_embeddings()
        if embeddings_data is not None:
            self.logger.info("✅ Usando dados da tabela embeddings (CONFORMIDADE)")
            return embeddings_data
        
        # Fallback apenas para agente de ingestão
        if self.caller_agent == 'ingestion_agent':
            try:
                from pathlib import Path
                import os
                
                self.logger.warning(f"🚨 FALLBACK CSV para agente de ingestão: {self.caller_agent}")
                
                data_dir = Path("data/")
                if not data_dir.exists():
                    self.logger.warning("Diretório data/ não encontrado")
                    return None
                
                # Buscar todos os arquivos .csv
                csv_files = list(data_dir.glob("*.csv"))
                
                if not csv_files:
                    self.logger.warning("Nenhum arquivo CSV encontrado em data/")
                    return None
                
                # Ordenar por data de modificação (mais recente primeiro)
                csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                most_recent = csv_files[0]
                
                self.logger.info(f"Usando arquivo CSV mais recente: {most_recent.name}")
                return pd.read_csv(most_recent)
                
            except Exception as e:
                self.logger.error(f"Erro ao detectar CSV mais recente: {str(e)}")
                return None
        else:
            # Bloquear acesso direto para outros agentes
            error_msg = (
                f"⚠️ VIOLAÇÃO DE CONFORMIDADE DETECTADA!\n"
                f"Agente '{self.caller_agent}' tentou acessar CSV diretamente via _detect_most_recent_csv().\n"
                f"Use get_data_from_embeddings() para acessar dados."
            )
            self.logger.error(error_msg)
            raise UnauthorizedCSVAccessError(error_msg)
    
    def _reconstruct_csv_data(self, csv_filename: str) -> Optional[pd.DataFrame]:
        """Reconstrói dados via embeddings (CONFORMIDADE) ou fallback para ingestão.
        
        Args:
            csv_filename: Nome do arquivo CSV (ex: 'creditcard.csv', 'sales.csv')
            
        Returns:
            DataFrame com dados da tabela embeddings ou None se falhar
        """
        # Priorizar dados da tabela embeddings
        embeddings_data = self.get_data_from_embeddings()
        if embeddings_data is not None:
            self.logger.info(f"✅ Dados de {csv_filename} recuperados via embeddings (CONFORMIDADE)")
            return embeddings_data
        
        # Fallback apenas para agente de ingestão
        if self.caller_agent == 'ingestion_agent':
            try:
                self.logger.warning(f"🚨 FALLBACK CSV para agente de ingestão: {csv_filename}")
                
                # Tentar carregar arquivo original se disponível
                csv_path = Path(f"data/{csv_filename}")
                if csv_path.exists():
                    self.logger.info(f"Carregando dados originais do {csv_filename}...")
                    df = pd.read_csv(csv_path)
                    return df
                else:
                    self.logger.warning(f"Arquivo {csv_filename} não encontrado em data/")
                    
                    # Estratégia alternativa: procurar na raiz do projeto
                    root_csv_path = Path(csv_filename)
                    if root_csv_path.exists():
                        self.logger.info(f"Carregando dados do {csv_filename} na raiz...")
                        df = pd.read_csv(root_csv_path)
                        return df
                    else:
                        self.logger.warning(f"Arquivo {csv_filename} não encontrado")
                        return None
                        
            except Exception as e:
                self.logger.error(f"Erro ao carregar {csv_filename}: {str(e)}")
                return None
        else:
            # Bloquear acesso direto para outros agentes
            error_msg = (
                f"⚠️ VIOLAÇÃO DE CONFORMIDADE DETECTADA!\n"
                f"Agente '{self.caller_agent}' tentou acessar CSV '{csv_filename}' diretamente.\n"
                f"Use get_data_from_embeddings() para acessar dados."
            )
            self.logger.error(error_msg)
            raise UnauthorizedCSVAccessError(error_msg)
    
    def calculate_real_statistics(self, query_type: str = "tipos_dados") -> Dict[str, Any]:
        """Calcula estatísticas reais dos dados usando Python.
        
        Args:
            query_type: Tipo de análise ('tipos_dados', 'estatisticas', 'distribuicao')
            
        Returns:
            Dicionário com estatísticas calculadas
        """
        try:
            # Obter dados reais
            df = self.reconstruct_original_data()
            if df is None:
                return {"error": "Não foi possível acessar dados reais"}
            
            self.logger.info(f"Calculando estatísticas reais para: {query_type}")
            
            # SISTEMA GENÉRICO: Analisar qualquer dataset
            result = {
                "data_source": "dataset genérico",
                "total_records": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns)
            }
            
            if query_type in ["tipos_dados", "all"]:
                # Análise genérica de tipos de dados
                numeric_cols = []
                categorical_cols = []
                datetime_cols = []
                
                for col in df.columns:
                    if df[col].dtype in ['int64', 'float64', 'int32', 'float32', 'int8', 'int16', 'float16']:
                        numeric_cols.append(col)
                    elif df[col].dtype == 'object':
                        # Verificar se é categórico real (strings/texto) ou se deveria ser numérico
                        try:
                            # Tentar converter para numérico para detectar números como strings
                            pd.to_numeric(df[col].dropna().head(100))
                            # Se conseguiu converter, pode ser numérico mal formatado
                            numeric_cols.append(col)
                        except (ValueError, TypeError):
                            # Verificar se é categórico (poucos valores únicos) ou texto
                            unique_ratio = df[col].nunique() / len(df)
                            categorical_cols.append(col)
                    elif 'datetime' in str(df[col].dtype).lower():
                        datetime_cols.append(col)
                    else:
                        # Para tipos desconhecidos, tentar detectar se é numérico
                        try:
                            if df[col].dtype.kind in 'biufc':  # boolean, int, unsigned, float, complex
                                numeric_cols.append(col)
                            else:
                                categorical_cols.append(col)
                        except:
                            categorical_cols.append(col)
                
                result.update({
                    "tipos_dados": {
                        "numericos": numeric_cols,
                        "categoricos": categorical_cols,
                        "datetime": datetime_cols,
                        "total_numericos": len(numeric_cols),
                        "total_categoricos": len(categorical_cols),
                        "total_datetime": len(datetime_cols)
                    }
                })
            
            if query_type in ["estatisticas", "all"]:
                # Estatísticas genéricas para colunas numéricas
                estatisticas = {}
                
                for col in df.select_dtypes(include=['number']).columns:
                    estatisticas[col] = {
                        "tipo": str(df[col].dtype),
                        "count": int(df[col].count()),
                        "mean": float(df[col].mean()),
                        "std": float(df[col].std()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "median": float(df[col].median()),
                        "q25": float(df[col].quantile(0.25)),
                        "q75": float(df[col].quantile(0.75))
                    }
                
                # Estatísticas para colunas categóricas
                for col in df.select_dtypes(include=['object']).columns:
                    value_counts = df[col].value_counts()
                    if len(value_counts) <= 20:  # Só mostrar se não há muitas categorias
                        estatisticas[col] = {
                            "tipo": str(df[col].dtype),
                            "unique_values": df[col].unique().tolist()[:10],  # Máximo 10 valores
                            "value_counts": value_counts.head(10).to_dict(),
                            "percentages": (value_counts.head(10) / len(df) * 100).round(2).to_dict()
                        }
                
                result.update({"estatisticas": estatisticas})
            
            if query_type in ["distribuicao", "all"]:
                # Distribuições genéricas
                distribuicao = {}
                
                # Para cada coluna categórica, calcular distribuição
                for col in df.select_dtypes(include=['object']).columns:
                    value_counts = df[col].value_counts()
                    if len(value_counts) <= 10:  # Só para colunas com poucas categorias
                        dist_dict = {}
                        for value, count in value_counts.items():
                            percentage = count / len(df) * 100
                            dist_dict[str(value)] = {
                                "count": int(count),
                                "percentage": float(percentage)
                            }
                        distribuicao[col] = dist_dict
                
                # Estatísticas de range para colunas numéricas
                numeric_ranges = {}
                for col in df.select_dtypes(include=['number']).columns:
                    numeric_ranges[col] = {
                        "range_min": float(df[col].min()),
                        "range_max": float(df[col].max()),
                        "range_amplitude": float(df[col].max() - df[col].min())
                    }
                
                result.update({
                    "distribuicao": distribuicao,
                    "ranges_numericos": numeric_ranges
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Erro ao calcular estatísticas: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def execute_safe_python(self, code: str, context: Dict[str, Any] = None) -> PythonAnalysisResult:
        """Executa código Python de forma segura.
        
        Args:
            code: Código Python para executar
            context: Contexto adicional (DataFrames, variáveis)
            
        Returns:
            Resultado da execução
        """
        import time
        start_time = time.time()
        
        # Capturar output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            # Preparar namespace seguro
            local_vars = self.safe_globals.copy()
            if context:
                local_vars.update(context)
            
            # Executar código
            exec(code, {"__builtins__": {}}, local_vars)
            
            # Capturar resultado
            output = captured_output.getvalue()
            execution_time = time.time() - start_time
            
            return PythonAnalysisResult(
                success=True,
                result=local_vars.get('result'),
                output=output,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Erro na execução: {str(e)}\n{traceback.format_exc()}"
            
            return PythonAnalysisResult(
                success=False,
                result=None,
                output=captured_output.getvalue(),
                error=error_msg,
                execution_time=execution_time
            )
        
        finally:
            sys.stdout = old_stdout

# Instância global para uso pelos agentes
python_analyzer = PythonDataAnalyzer()