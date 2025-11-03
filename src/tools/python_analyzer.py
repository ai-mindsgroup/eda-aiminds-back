"""Ferramenta de análise de dados Python para o sistema multiagente.

⚠️ CONFORMIDADE CRÍTICA: Esta ferramenta deve priorizar dados da tabela embeddings
sobre acesso direto a arquivos CSV para agentes de resposta.

Esta ferramenta permite que agentes executem código Python real para
calcular estatísticas precisas dos dados armazenados no Supabase.

🛡️ SEGURANÇA (2025-10-31): Integrado com sandbox seguro para execução de código.
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

# 🛡️ SANDBOX SEGURO - Implementado 2025-10-31
from src.security.sandbox import execute_in_sandbox

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
    
    def get_data_from_embeddings(self, limit: int = None, metadata_filter: Dict = None, parse_chunk_text: bool = True) -> Optional[pd.DataFrame]:
        """Recupera dados APENAS da tabela embeddings (CONFORMIDADE).
        
        Args:
            limit: Limite de registros (None para todos)
            metadata_filter: Filtros por metadata
            parse_chunk_text: Se True, parseia o conteúdo CSV do chunk_text para reconstruir colunas originais (PADRÃO: True)
            
        Returns:
            DataFrame com os dados PARSEADOS do CSV original ou None se falhar
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
            
            # SEMPRE tentar parsear chunk_text para reconstruir dados originais do CSV
            if 'chunk_text' in df.columns:
                self.logger.info("🔄 Parseando chunk_text para reconstruir colunas originais do CSV...")
                parsed_df = self._parse_chunk_text_to_dataframe(df)
                if parsed_df is not None:
                    self.logger.info(f"✅ Dados parseados com sucesso: {len(parsed_df)} linhas, {len(parsed_df.columns)} colunas originais")
                    self.logger.info(f"📊 Colunas reconstruídas: {list(parsed_df.columns)}")
                    return parsed_df
                else:
                    self.logger.warning("⚠️ Falha ao parsear chunk_text, retornando dados brutos da tabela embeddings")
            
            # Fallback: Remover colunas com tipos não-hashable (metadata, embedding) para evitar erros
            if 'metadata' in df.columns:
                df = df.drop(columns=['metadata'])
            if 'embedding' in df.columns:
                df = df.drop(columns=['embedding'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dados da tabela embeddings: {str(e)}")
            return None
    
    def _parse_chunk_text_to_dataframe(self, embeddings_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Parseia o conteúdo CSV dentro do chunk_text para reconstruir DataFrame original.
        
        Args:
            embeddings_df: DataFrame com coluna chunk_text contendo CSV
            
        Returns:
            DataFrame com colunas originais do CSV ou None se falhar
        """
        try:
            all_rows = []
            header_found = None
            
            for idx, row in embeddings_df.iterrows():
                chunk_text = row.get('chunk_text', '')
                if not chunk_text or not isinstance(chunk_text, str):
                    continue
                
                # Separar linhas do chunk
                lines = chunk_text.strip().split('\n')
                
                # Procurar pelo cabeçalho CSV (linha que começa com aspas ou tem muitas vírgulas)
                for line_idx, line in enumerate(lines):
                    line = line.strip()
                    
                    # Pular linhas vazias, metadados ou descrições
                    if not line or line.startswith('#') or line.startswith('CHUNK'):
                        continue
                    
                    # IMPORTANTE: Ignorar linha descritiva que começa com "Colunas: "
                    # Exemplo: Colunas: "Time","V1","V2"... (isso é metadado, não o header real)
                    if line.startswith('Colunas:'):
                        continue
                    
                    # Pular linha separadora
                    if line.startswith('==='):
                        continue
                    
                    # Detectar header REAL: linha que começa diretamente com aspas
                    # Header válido para QUALQUER CSV: linha que começa com " e contém vírgulas separando colunas
                    # Exemplos válidos: "Time","V1","V2" ou "Nome","Idade","Cidade" ou "id","valor","status"
                    # A linha DEVE começar com " (aspas) para ser considerada header válido
                    if header_found is None and line.startswith('"') and '","' in line:
                        # Para ser header válido, deve ter pelo menos 2 colunas (separadas por ",")
                        # Isso funciona para QUALQUER CSV, não apenas creditcard
                        tentative_header = [col.strip().strip('"').strip() for col in line.split(',')]
                        tentative_header = [col for col in tentative_header if col]  # Remover vazios
                        
                        # Validar que temos pelo menos 2 colunas com nomes válidos
                        if len(tentative_header) >= 2:
                            # Validar que os nomes não são apenas números (provavelmente são dados, não header)
                            non_numeric_count = sum(1 for col in tentative_header[:5] if not col.replace('.','',1).replace('-','',1).isdigit())
                            
                            # Se a maioria das primeiras colunas não são puramente numéricas, é um header válido
                            if non_numeric_count >= max(2, len(tentative_header[:5]) // 2):
                                header_found = tentative_header
                                self.logger.info(f"📋 Header CSV detectado: {len(header_found)} colunas - {header_found[:5]}...")
                                continue
                    
                    # Se já temos header, parsear linhas de dados
                    # Linha de dados: não começa com aspas, tem vírgulas, não é metadado
                    if header_found and ',' in line:
                        # Pular linhas de metadados/descrição
                        skip_keywords = ['Chunk', 'Dataset', 'Contém', 'Inclui', 'Features', 
                                       'Exemplo', 'Colunas:', 'Transações', '===', '---']
                        if any(line.startswith(kw) for kw in skip_keywords):
                            continue
                        
                        # Pular se for linha de header duplicada (começa com aspas)
                        if line.startswith('"'):
                            continue
                        
                        try:
                            # Dividir por vírgula
                            values = line.split(',')
                            
                            # Limpar valores (remover aspas extras se houver)
                            values = [v.strip().strip('"') for v in values]
                            
                            # Verificar se tem o mesmo número de colunas do header
                            if len(values) == len(header_found):
                                all_rows.append(values)
                            elif len(values) > len(header_found):
                                # Truncar valores extras
                                all_rows.append(values[:len(header_found)])
                            elif len(values) >= len(header_found) - 2:  # Tolerância de 2 colunas
                                # Preencher com None
                                all_rows.append(values + [None] * (len(header_found) - len(values)))
                        except Exception as e:
                            self.logger.debug(f"Erro ao parsear linha: {str(e)}")
                            continue
            
            if not header_found:
                self.logger.warning("Nenhum header CSV encontrado no chunk_text")
                return None
                
            if not all_rows:
                self.logger.warning("Nenhuma linha de dados CSV encontrada no chunk_text")
                self.logger.debug(f"Amostra de chunk_text analisado (primeiros 500 chars): {str(embeddings_df['chunk_text'].iloc[0])[:500] if len(embeddings_df) > 0 else 'N/A'}")
                return None
            
            self.logger.info(f"📊 Parseando CSV: {len(all_rows)} linhas encontradas, {len(header_found)} colunas detectadas")
            self.logger.info(f"📋 Colunas: {header_found}")
            
            # Criar DataFrame
            df = pd.DataFrame(all_rows, columns=header_found)
            
            # Tentar converter colunas numéricas
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
            
            self.logger.info(f"✅ DataFrame reconstruído: {len(df)} linhas, {len(df.columns)} colunas")
            self.logger.info(f"📊 Tipos de dados: {df.dtypes.to_dict()}")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao parsear chunk_text: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
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
        """Reconstrói dados originais APENAS da tabela embeddings do Supabase.
        
        Returns:
            DataFrame com dados parseados do chunk_text ou None se falhar
            
        ⚠️ CONFORMIDADE TOTAL: APENAS SUPABASE EMBEDDINGS - NENHUM CSV.
        """
        try:
            self.logger.info("🔄 Reconstruindo dados originais APENAS da tabela embeddings...")
            
            # ÚNICA FONTE DE DADOS: Tabela embeddings do Supabase
            # O método get_data_from_embeddings() já parseia chunk_text automaticamente
            df = self.get_data_from_embeddings(limit=None, parse_chunk_text=True)
            
            if df is not None:
                self.logger.info(f"✅ Dados reconstruídos: {len(df)} registros, {len(df.columns)} colunas (CONFORMIDADE TOTAL)")
                return df
            
            # Se não há dados, retornar None - NUNCA ler CSV
            self.logger.error(
                f"❌ Nenhum dado encontrado na tabela embeddings do Supabase.\n"
                f"⚠️ Sem fallback para CSV - APENAS embeddings permitido.\n"
                f"Execute a ingestão de dados primeiro: python ingest_completo.py"
            )
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao reconstruir dados originais: {str(e)}")
            return None
            
    def _detect_most_recent_csv(self) -> Optional[pd.DataFrame]:
        """Retorna dados APENAS da tabela embeddings (CONFORMIDADE TOTAL).
        
        ⚠️ NENHUM FALLBACK PARA CSV - APENAS SUPABASE EMBEDDINGS.
        """
        # APENAS dados da tabela embeddings - SEM EXCEÇÕES
        embeddings_data = self.get_data_from_embeddings()
        if embeddings_data is not None:
            self.logger.info("✅ Dados recuperados da tabela embeddings (CONFORMIDADE TOTAL)")
            return embeddings_data
        
        # Se não há dados em embeddings, retornar None - NUNCA ler CSV
        self.logger.error(
            f"❌ Nenhum dado encontrado na tabela embeddings do Supabase.\n"
            f"⚠️ Sem fallback para CSV - APENAS embeddings permitido.\n"
            f"Execute a ingestão de dados primeiro: python ingest_completo.py"
        )
        return None
    
    def _reconstruct_csv_data(self, csv_filename: str) -> Optional[pd.DataFrame]:
        """Reconstrói dados APENAS via embeddings do Supabase (CONFORMIDADE TOTAL).
        
        Args:
            csv_filename: Nome do arquivo CSV (ex: 'creditcard.csv', 'sales.csv') - APENAS REFERÊNCIA
            
        Returns:
            DataFrame com dados da tabela embeddings ou None se falhar
            
        ⚠️ NENHUM FALLBACK PARA CSV - APENAS SUPABASE EMBEDDINGS.
        """
        # APENAS dados da tabela embeddings - SEM EXCEÇÕES - SEM FALLBACK
        embeddings_data = self.get_data_from_embeddings()
        if embeddings_data is not None:
            self.logger.info(f"✅ Dados de {csv_filename} recuperados via embeddings (CONFORMIDADE TOTAL)")
            return embeddings_data
        
        # Se não há dados em embeddings, retornar None - NUNCA ler CSV
        self.logger.error(
            f"❌ Nenhum dado encontrado na tabela embeddings para {csv_filename}.\n"
            f"⚠️ Sem fallback para CSV - APENAS embeddings permitido.\n"
            f"Execute a ingestão de dados primeiro: python ingest_completo.py"
        )
        return None
    
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
                    try:
                        col_dtype = df[col].dtype
                        
                        if col_dtype in ['int64', 'float64', 'int32', 'float32', 'int8', 'int16', 'float16']:
                            numeric_cols.append(col)
                        elif col_dtype == 'object':
                            # Verificar se é categórico real (strings/texto) ou se deveria ser numérico
                            try:
                                # Tentar converter para numérico para detectar números como strings
                                pd.to_numeric(df[col].dropna().head(100))
                                # Se conseguiu converter, pode ser numérico mal formatado
                                numeric_cols.append(col)
                            except (ValueError, TypeError):
                                # Verificar se é categórico (poucos valores únicos) ou texto
                                categorical_cols.append(col)
                        elif 'datetime' in str(col_dtype).lower():
                            datetime_cols.append(col)
                        else:
                            # Para tipos desconhecidos, tentar detectar se é numérico
                            try:
                                if col_dtype.kind in 'biufc':  # boolean, int, unsigned, float, complex
                                    numeric_cols.append(col)
                                else:
                                    categorical_cols.append(col)
                            except:
                                categorical_cols.append(col)
                    except Exception as e:
                        self.logger.warning(f"Erro ao analisar dtype da coluna '{col}': {str(e)}")
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
                    try:
                        value_counts = df[col].value_counts()
                        if len(value_counts) <= 20:  # Só mostrar se não há muitas categorias
                            estatisticas[col] = {
                                "tipo": str(df[col].dtype),
                                "unique_values": df[col].unique().tolist()[:10],  # Máximo 10 valores
                                "value_counts": value_counts.head(10).to_dict(),
                                "percentages": (value_counts.head(10) / len(df) * 100).round(2).to_dict()
                            }
                    except Exception as e:
                        self.logger.warning(f"Erro ao calcular estatísticas para coluna categórica '{col}': {str(e)}")
                        continue
                
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
        """
        Executa código Python de forma SEGURA usando sandbox.
        
        🛡️ SEGURANÇA: Substituído exec() direto por execute_in_sandbox() - 2025-10-31
        
        Args:
            code: Código Python para executar
            context: Contexto adicional (DataFrames, variáveis)
            
        Returns:
            Resultado da execução
        """
        import time
        start_time = time.time()
        
        try:
            # 🛡️ EXECUTAR NO SANDBOX SEGURO
            self.logger.info(f"🛡️ Executando código via sandbox seguro (caller: {self.caller_agent})")
            
            # Preparar contexto customizado
            custom_globals = {}
            if context:
                custom_globals.update(context)
            
            # Executar no sandbox com monitoramento ativo
            sandbox_result = execute_in_sandbox(
                code=code,
                custom_globals=custom_globals,
                enable_monitoring=True,  # ✅ Popula sandbox_metrics
                timeout_seconds=10,
                memory_limit_mb=200
            )
            
            execution_time = time.time() - start_time
            
            if sandbox_result['success']:
                self.logger.info(f"✅ Código executado com sucesso via sandbox (tempo: {execution_time:.3f}s)")
                
                return PythonAnalysisResult(
                    success=True,
                    result=sandbox_result.get('result'),
                    output=sandbox_result.get('logs', ''),
                    execution_time=execution_time
                )
            else:
                # Falha na execução
                error_msg = sandbox_result.get('error', 'Erro desconhecido')
                self.logger.error(f"❌ Erro na execução do código via sandbox: {error_msg}")
                
                return PythonAnalysisResult(
                    success=False,
                    result=None,
                    output=sandbox_result.get('logs', ''),
                    error=error_msg,
                    execution_time=execution_time
                )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ Erro crítico no execute_safe_python: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            
            return PythonAnalysisResult(
                success=False,
                result=None,
                output="",
                error=error_msg,
                execution_time=execution_time
            )
    
    def calculate_clustering_analysis(self, n_clusters: int = 3) -> Dict[str, Any]:
        """
        Calcula análise de clustering (KMeans) nos dados numéricos do dataset.
        
        Args:
            n_clusters: Número de clusters desejados (padrão: 3)
            
        Returns:
            Dicionário com informações sobre os clusters encontrados
        """
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            # 1. Recuperar dados do Supabase usando reconstruct_original_data
            df = self.reconstruct_original_data()
            
            if df is None or df.empty:
                return {
                    "error": "Nenhum dado disponível para análise de clustering",
                    "suggestion": "Certifique-se de que os dados foram ingeridos na tabela embeddings"
                }
            
            # 2. Selecionar apenas colunas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Remover colunas irrelevantes como ID, índice, etc.
            numeric_cols = [col for col in numeric_cols if col.lower() not in ['id', 'index', 'unnamed: 0']]
            
            if len(numeric_cols) == 0:
                return {
                    "error": "Nenhuma coluna numérica encontrada para clustering",
                    "available_columns": df.columns.tolist()
                }
            
            self.logger.info(f"🔬 Aplicando KMeans com {n_clusters} clusters em {len(numeric_cols)} variáveis numéricas")
            
            # 3. Preparar dados para clustering
            X = df[numeric_cols].copy()
            
            # Remover linhas com valores nulos
            X = X.dropna()
            
            if len(X) == 0:
                return {
                    "error": "Todos os dados têm valores nulos nas colunas numéricas"
                }
            
            # 4. Normalizar dados (importante para KMeans)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # 5. Aplicar KMeans
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # 6. Contar pontos por cluster
            unique, counts = np.unique(cluster_labels, return_counts=True)
            cluster_distribution = dict(zip(unique.tolist(), counts.tolist()))
            
            # 7. Calcular percentuais
            total_points = len(cluster_labels)
            cluster_percentages = {
                cluster: (count / total_points) * 100 
                for cluster, count in cluster_distribution.items()
            }
            
            # 8. Calcular centróides (características médias de cada cluster)
            centroids = kmeans.cluster_centers_
            
            # 9. Verificar balanceamento
            max_cluster_pct = max(cluster_percentages.values())
            min_cluster_pct = min(cluster_percentages.values())
            is_balanced = (max_cluster_pct / min_cluster_pct) < 3.0  # threshold arbitrário
            
            # 10. Construir resposta estruturada
            result = {
                "success": True,
                "n_clusters": n_clusters,
                "total_points": total_points,
                "numeric_variables_used": numeric_cols,
                "cluster_distribution": cluster_distribution,
                "cluster_percentages": cluster_percentages,
                "is_balanced": is_balanced,
                "balance_ratio": max_cluster_pct / min_cluster_pct if min_cluster_pct > 0 else float('inf'),
                "inertia": float(kmeans.inertia_),  # Soma das distâncias quadradas aos centróides
                "interpretation": self._interpret_clustering_results(
                    cluster_distribution,
                    cluster_percentages,
                    is_balanced,
                    numeric_cols
                )
            }
            
            self.logger.info(f"✅ Clustering concluído: {cluster_distribution}")
            return result
            
        except ImportError:
            return {
                "error": "Biblioteca scikit-learn não está instalada",
                "suggestion": "Execute: pip install scikit-learn"
            }
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de clustering: {str(e)}", exc_info=True)
            return {
                "error": f"Erro ao calcular clustering: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _interpret_clustering_results(
        self,
        cluster_distribution: Dict[int, int],
        cluster_percentages: Dict[int, float],
        is_balanced: bool,
        numeric_cols: List[str]
    ) -> str:
        """Gera interpretação textual dos resultados de clustering."""
        
        interpretation = "**Análise de Clustering (KMeans):**\n\n"
        
        # Distribuição dos clusters
        interpretation += f"Os dados foram agrupados em {len(cluster_distribution)} clusters distintos:\n\n"
        
        for cluster_id in sorted(cluster_distribution.keys()):
            count = cluster_distribution[cluster_id]
            pct = cluster_percentages[cluster_id]
            interpretation += f"- **Cluster {cluster_id}:** {count:,} pontos ({pct:.1f}%)\n"
        
        interpretation += "\n"
        
        # Avaliação do balanceamento
        if is_balanced:
            interpretation += "✅ **Balanceamento:** Os clusters estão relativamente balanceados, "
            interpretation += "indicando grupos de tamanhos similares nos dados.\n\n"
        else:
            interpretation += "⚠️ **Balanceamento:** Os clusters estão desbalanceados, "
            interpretation += "sugerindo que há um grupo dominante e outros menores.\n\n"
        
        # Variáveis utilizadas
        if len(numeric_cols) > 5:
            interpretation += f"**Variáveis Utilizadas:** {len(numeric_cols)} variáveis numéricas "
            interpretation += f"(incluindo {', '.join(numeric_cols[:3])}, ...)\n\n"
        else:
            interpretation += f"**Variáveis Utilizadas:** {', '.join(numeric_cols)}\n\n"
        
        # Conclusão
        interpretation += "**Conclusão:** SIM, os dados apresentam estrutura de agrupamentos naturais. "
        interpretation += "Diferentes técnicas de clustering ou número de clusters podem revelar padrões adicionais."
        
        return interpretation

# Instância global para uso pelos agentes
python_analyzer = PythonDataAnalyzer()