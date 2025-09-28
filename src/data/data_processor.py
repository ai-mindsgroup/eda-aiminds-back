"""Interface unificada para carregamento e processamento de dados CSV.

Este módulo fornece uma interface simples e poderosa que integra:
- DataLoader: carregamento de múltiplas fontes
- DataValidator: validação e limpeza
- CSVAnalysisAgent: análise inteligente
- Suporte a diferentes formatos e fontes de dados
"""
from __future__ import annotations
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import pandas as pd

from src.data.data_loader import DataLoader, DataLoaderError  
from src.data.data_validator import DataValidator, DataValidationError
from src.agent.csv_analysis_agent import CSVAnalysisAgent
from src.utils.logging_config import get_logger


class DataProcessor:
    """Interface unificada para carregamento, validação e análise de dados CSV."""
    
    def __init__(self, auto_validate: bool = True, auto_clean: bool = True):
        """Inicializa o processador de dados.
        
        Args:
            auto_validate: Se True, valida automaticamente dados carregados
            auto_clean: Se True, limpa automaticamente problemas detectados
        """
        self.logger = get_logger(__name__)
        
        # Componentes principais
        self.loader = DataLoader()
        self.validator = DataValidator()
        self.analyzer = CSVAnalysisAgent()
        
        # Configurações
        self.auto_validate = auto_validate
        self.auto_clean = auto_clean
        
        # Estado atual
        self.current_df: Optional[pd.DataFrame] = None
        self.load_info: Optional[Dict[str, Any]] = None
        self.validation_results: Optional[Dict[str, Any]] = None
        self.cleaning_results: Optional[Dict[str, Any]] = None
        
        self.logger.info("DataProcessor inicializado")
    
    def load_from_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Carrega dados de arquivo local.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **kwargs: Argumentos para pd.read_csv()
            
        Returns:
            Resultado do processamento completo
        """
        try:
            # Carregar dados
            df, load_info = self.loader.load_from_file(file_path, **kwargs)
            
            # Processar dados carregados
            return self._process_loaded_data(df, load_info)
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def load_from_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Carrega dados de URL remota.
        
        Args:
            url: URL do arquivo CSV
            **kwargs: Argumentos para pd.read_csv()
            
        Returns:
            Resultado do processamento completo
        """
        try:
            # Carregar dados
            df, load_info = self.loader.load_from_url(url, **kwargs)
            
            # Processar dados carregados
            return self._process_loaded_data(df, load_info)
            
        except Exception as e:
            error_msg = f"Erro ao carregar URL {url}: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def load_from_upload(self, base64_content: str, filename: str = "upload.csv", **kwargs) -> Dict[str, Any]:
        """Carrega dados de upload base64.
        
        Args:
            base64_content: Conteúdo CSV em base64
            filename: Nome do arquivo para referência
            **kwargs: Argumentos para pd.read_csv()
            
        Returns:
            Resultado do processamento completo
        """
        try:
            # Carregar dados
            df, load_info = self.loader.load_from_base64(base64_content, filename, **kwargs)
            
            # Processar dados carregados
            return self._process_loaded_data(df, load_info)
            
        except Exception as e:
            error_msg = f"Erro ao processar upload {filename}: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def load_synthetic_data(self, data_type: str = "fraud_detection", num_rows: int = 1000, **kwargs) -> Dict[str, Any]:
        """Carrega dados sintéticos para testes.
        
        Args:
            data_type: Tipo de dados sintéticos
            num_rows: Número de linhas
            **kwargs: Parâmetros específicos do tipo de dados
            
        Returns:
            Resultado do processamento completo
        """
        try:
            # Carregar dados
            df, load_info = self.loader.create_synthetic_data(data_type, num_rows, **kwargs)
            
            # Processar dados carregados
            return self._process_loaded_data(df, load_info)
            
        except Exception as e:
            error_msg = f"Erro ao gerar dados sintéticos {data_type}: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def load_from_dataframe(self, df: pd.DataFrame, source_info: str = "external_dataframe") -> Dict[str, Any]:
        """Carrega dados de DataFrame pandas existente.
        
        Args:
            df: DataFrame pandas
            source_info: Informação sobre a origem
            
        Returns:
            Resultado do processamento completo
        """
        try:
            # Carregar dados
            df_copy, load_info = self.loader.load_from_dataframe(df, source_info)
            
            # Processar dados carregados
            return self._process_loaded_data(df_copy, load_info)
            
        except Exception as e:
            error_msg = f"Erro ao processar DataFrame {source_info}: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Executa análise no dataset atual.
        
        Args:
            query: Consulta ou comando de análise
            
        Returns:
            Resultado da análise
        """
        if self.current_df is None:
            return self._build_error_response("Nenhum dataset carregado. Use load_* methods primeiro.")
        
        try:
            result = self.analyzer.process(query)
            return result
            
        except Exception as e:
            error_msg = f"Erro na análise: {str(e)}"
            self.logger.error(error_msg)
            return self._build_error_response(error_msg)
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """Retorna resumo completo do dataset atual."""
        if self.current_df is None:
            return {"error": "Nenhum dataset carregado"}
        
        summary = {
            'load_info': self.load_info,
            'basic_info': {
                'shape': self.current_df.shape,
                'columns': self.current_df.columns.tolist(),
                'dtypes': self.current_df.dtypes.to_dict(),
                'memory_usage_mb': self.current_df.memory_usage(deep=True).sum() / (1024 * 1024),
                'missing_values': self.current_df.isnull().sum().to_dict(),
                'duplicates': self.current_df.duplicated().sum()
            }
        }
        
        if self.validation_results:
            summary['validation'] = {
                'overall_score': self.validation_results['overall_score'],
                'errors': len(self.validation_results['errors']),
                'warnings': len(self.validation_results['warnings'])
            }
        
        if self.cleaning_results:
            summary['cleaning'] = {
                'actions_taken': len(self.cleaning_results['actions_taken']),
                'rows_removed': self.cleaning_results.get('rows_removed', 0)
            }
        
        return summary
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Retorna relatório detalhado de qualidade dos dados."""
        if self.validation_results is None:
            if self.current_df is not None:
                self.validation_results = self.validator.validate_dataframe(self.current_df)
            else:
                return {"error": "Nenhum dataset carregado"}
        
        return self.validation_results
    
    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """Retorna sugestões de melhoria para o dataset."""
        if self.current_df is None:
            return []
        
        return self.validator.suggest_improvements(self.current_df)
    
    def export_to_csv(self, file_path: str, **kwargs) -> bool:
        """Exporta dataset atual para arquivo CSV.
        
        Args:
            file_path: Caminho do arquivo de destino
            **kwargs: Argumentos para pd.to_csv()
            
        Returns:
            True se exportação foi bem-sucedida
        """
        if self.current_df is None:
            self.logger.error("Nenhum dataset para exportar")
            return False
        
        try:
            # Configurações padrão
            default_kwargs = {'index': False, 'encoding': 'utf-8'}
            default_kwargs.update(kwargs)
            
            self.current_df.to_csv(file_path, **default_kwargs)
            
            self.logger.info(f"Dataset exportado para: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar para {file_path}: {str(e)}")
            return False
    
    def quick_analysis(self) -> Dict[str, Any]:
        """Executa análise rápida automática do dataset."""
        if self.current_df is None:
            return {"error": "Nenhum dataset carregado"}
        
        results = {}
        
        # Análises básicas
        try:
            results['basic_stats'] = self.analyze("Faça um resumo básico dos dados")
        except:
            results['basic_stats'] = {"error": "Falha na análise básica"}
        
        try:
            results['correlations'] = self.analyze("Analise as correlações entre variáveis")
        except:
            results['correlations'] = {"error": "Falha na análise de correlação"}
        
        # Detecção de fraude se houver colunas apropriadas
        fraud_cols = ['is_fraud', 'eh_fraude', 'fraud', 'fraude']
        if any(col in self.current_df.columns for col in fraud_cols):
            try:
                results['fraud_analysis'] = self.analyze("Analise os padrões de fraude")
            except:
                results['fraud_analysis'] = {"error": "Falha na análise de fraude"}
        
        # Qualidade dos dados
        results['data_quality'] = self.get_data_quality_report()
        
        return results
    
    def _process_loaded_data(self, df: pd.DataFrame, load_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados recém-carregados."""
        self.current_df = df
        self.load_info = load_info
        
        result = {
            'success': True,
            'load_info': load_info,
            'message': f"Dados carregados com sucesso: {load_info['rows']} linhas, {load_info['columns']} colunas"
        }
        
        # Validação automática
        if self.auto_validate:
            try:
                self.validation_results = self.validator.validate_dataframe(df)
                result['validation'] = {
                    'score': self.validation_results['overall_score'],
                    'errors': len(self.validation_results['errors']),
                    'warnings': len(self.validation_results['warnings'])
                }
                
                self.logger.info(f"Validação automática: score {self.validation_results['overall_score']:.1f}/100")
                
            except Exception as e:
                self.logger.warning(f"Falha na validação automática: {str(e)}")
                result['validation'] = {"error": str(e)}
        
        # Limpeza automática
        if self.auto_clean and self.validation_results and self.validation_results['overall_score'] < 80:
            try:
                df_clean, cleaning_results = self.validator.clean_dataframe(df, auto_fix=True)
                
                if len(cleaning_results['actions_taken']) > 0:
                    self.current_df = df_clean
                    self.cleaning_results = cleaning_results
                    
                    result['cleaning'] = {
                        'actions_taken': len(cleaning_results['actions_taken']),
                        'rows_removed': cleaning_results.get('rows_removed', 0)
                    }
                    
                    self.logger.info(f"Limpeza automática: {len(cleaning_results['actions_taken'])} ações realizadas")
                
            except Exception as e:
                self.logger.warning(f"Falha na limpeza automática: {str(e)}")
                result['cleaning'] = {"error": str(e)}
        
        # Conectar com CSVAnalysisAgent
        try:
            # Salvar temporariamente para o agente
            temp_file = None
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                temp_file = f.name
                self.current_df.to_csv(f, index=False)
            
            # Carregar no agente
            agent_result = self.analyzer.load_csv(temp_file)
            
            # Limpar arquivo temporário
            os.unlink(temp_file)
            
            result['agent_ready'] = agent_result.get('success', True)
            
        except Exception as e:
            self.logger.warning(f"Falha ao conectar com CSVAnalysisAgent: {str(e)}")
            result['agent_ready'] = False
        
        return result
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Constrói resposta de erro padronizada."""
        return {
            'success': False,
            'error': error_msg,
            'message': error_msg
        }


# Funções de conveniência para uso direto
def load_csv_file(file_path: str, **kwargs) -> DataProcessor:
    """Função de conveniência para carregar arquivo CSV rapidamente.
    
    Args:
        file_path: Caminho para o arquivo CSV
        **kwargs: Argumentos para pd.read_csv()
        
    Returns:
        DataProcessor com dados carregados
    """
    processor = DataProcessor()
    result = processor.load_from_file(file_path, **kwargs)
    
    if not result['success']:
        raise DataLoaderError(result['error'])
    
    return processor


def load_csv_url(url: str, **kwargs) -> DataProcessor:
    """Função de conveniência para carregar CSV de URL.
    
    Args:
        url: URL do arquivo CSV
        **kwargs: Argumentos para pd.read_csv()
        
    Returns:
        DataProcessor com dados carregados
    """
    processor = DataProcessor()
    result = processor.load_from_url(url, **kwargs)
    
    if not result['success']:
        raise DataLoaderError(result['error'])
    
    return processor


def create_demo_data(data_type: str = "fraud_detection", num_rows: int = 1000, **kwargs) -> DataProcessor:
    """Função de conveniência para criar dados de demonstração.
    
    Args:
        data_type: Tipo de dados sintéticos
        num_rows: Número de linhas
        **kwargs: Parâmetros específicos
        
    Returns:
        DataProcessor com dados sintéticos carregados
    """
    processor = DataProcessor()
    result = processor.load_synthetic_data(data_type, num_rows, **kwargs)
    
    if not result['success']:
        raise DataLoaderError(result['error'])
    
    return processor