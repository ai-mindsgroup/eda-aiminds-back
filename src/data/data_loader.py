"""Sistema de carregamento de dados CSV com múltiplas fontes e validações robustas.

Este módulo implementa o carregamento inteligente de dados CSV com suporte a:
- Arquivos locais com detecção automática de encoding
- URLs remotas (HTTP/HTTPS)
- DataFrames pandas existentes
- Dados sintéticos para testes
- Upload via base64
- Validação robusta de formato e conteúdo
"""
from __future__ import annotations
import io
import os
import base64
import requests
import chardet
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from urllib.parse import urlparse
import warnings
from datetime import datetime, timedelta

from src.utils.logging_config import get_logger


class DataLoaderError(Exception):
    """Exceção personalizada para erros de carregamento de dados."""
    pass


class DataLoader:
    """Carregador inteligente de dados CSV com múltiplas fontes e validações."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._last_loaded_info: Optional[Dict[str, Any]] = None
        
        # Configurações padrão
        self.default_encoding = 'utf-8'
        self.supported_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        self.max_file_size_mb = 500
        self.timeout_seconds = 30
        
        self.logger.info("DataLoader inicializado")
    
    def load_from_file(self, file_path: str, **pandas_kwargs) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Carrega dados de arquivo local com detecção automática de encoding.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **pandas_kwargs: Argumentos adicionais para pd.read_csv()
            
        Returns:
            Tuple com (DataFrame, informações do carregamento)
            
        Raises:
            DataLoaderError: Se houver erro no carregamento
        """
        try:
            file_path = Path(file_path).resolve()
            
            if not file_path.exists():
                raise DataLoaderError(f"Arquivo não encontrado: {file_path}")
            
            if not file_path.is_file():
                raise DataLoaderError(f"Caminho não é um arquivo: {file_path}")
            
            # Verificar tamanho do arquivo
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise DataLoaderError(f"Arquivo muito grande: {file_size_mb:.1f}MB (máximo: {self.max_file_size_mb}MB)")
            
            self.logger.info(f"Carregando arquivo: {file_path} ({file_size_mb:.1f}MB)")
            
            # Detectar encoding se não especificado
            encoding = pandas_kwargs.get('encoding')
            if not encoding:
                encoding = self._detect_encoding(file_path)
                pandas_kwargs['encoding'] = encoding
            
            # Configurações padrão
            default_kwargs = {
                'low_memory': False,
                'encoding': encoding
            }
            default_kwargs.update(pandas_kwargs)
            
            # Carregar dados
            df = pd.read_csv(file_path, **default_kwargs)
            
            # Informações do carregamento
            load_info = {
                'source_type': 'file',
                'source_path': str(file_path),
                'file_size_mb': file_size_mb,
                'encoding': encoding,
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'load_time': datetime.now().isoformat(),
                'pandas_kwargs': default_kwargs
            }
            
            self._last_loaded_info = load_info
            self.logger.info(f"✅ Arquivo carregado: {load_info['rows']} linhas, {load_info['columns']} colunas")
            
            return df, load_info
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise DataLoaderError(error_msg) from e
    
    def load_from_url(self, url: str, **pandas_kwargs) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Carrega dados de URL remota.
        
        Args:
            url: URL do arquivo CSV
            **pandas_kwargs: Argumentos adicionais para pd.read_csv()
            
        Returns:
            Tuple com (DataFrame, informações do carregamento)
            
        Raises:
            DataLoaderError: Se houver erro no carregamento
        """
        try:
            # Validar URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme in ['http', 'https']:
                raise DataLoaderError(f"URL deve usar HTTP ou HTTPS: {url}")
            
            self.logger.info(f"Baixando dados de: {url}")
            
            # Fazer request com timeout
            response = requests.get(url, timeout=self.timeout_seconds, stream=True)
            response.raise_for_status()
            
            # Verificar tamanho
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    raise DataLoaderError(f"Arquivo muito grande: {size_mb:.1f}MB (máximo: {self.max_file_size_mb}MB)")
            
            # Detectar encoding do conteúdo
            content = response.content
            encoding = pandas_kwargs.get('encoding')
            if not encoding:
                detected = chardet.detect(content)
                encoding = detected.get('encoding', 'utf-8')
                pandas_kwargs['encoding'] = encoding
            
            # Configurações padrão
            default_kwargs = {
                'low_memory': False,
                'encoding': encoding
            }
            default_kwargs.update(pandas_kwargs)
            
            # Carregar dados
            df = pd.read_csv(io.BytesIO(content), **default_kwargs)
            
            # Informações do carregamento
            load_info = {
                'source_type': 'url',
                'source_path': url,
                'file_size_mb': len(content) / (1024 * 1024),
                'encoding': encoding,
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'load_time': datetime.now().isoformat(),
                'pandas_kwargs': default_kwargs,
                'response_headers': dict(response.headers)
            }
            
            self._last_loaded_info = load_info
            self.logger.info(f"✅ URL carregada: {load_info['rows']} linhas, {load_info['columns']} colunas")
            
            return df, load_info
            
        except Exception as e:
            error_msg = f"Erro ao carregar URL {url}: {str(e)}"
            self.logger.error(error_msg)
            raise DataLoaderError(error_msg) from e
    
    def load_from_dataframe(self, df: pd.DataFrame, source_info: str = "dataframe") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Carrega dados de um DataFrame pandas existente.
        
        Args:
            df: DataFrame pandas
            source_info: Informação sobre a origem dos dados
            
        Returns:
            Tuple com (DataFrame, informações do carregamento)
        """
        if not isinstance(df, pd.DataFrame):
            raise DataLoaderError("Entrada deve ser um pandas DataFrame")
        
        if df.empty:
            raise DataLoaderError("DataFrame está vazio")
        
        # Fazer cópia para evitar modificações não intencionais
        df_copy = df.copy()
        
        # Informações do carregamento
        load_info = {
            'source_type': 'dataframe',
            'source_path': source_info,
            'rows': len(df_copy),
            'columns': len(df_copy.columns),
            'memory_usage_mb': df_copy.memory_usage(deep=True).sum() / (1024 * 1024),
            'load_time': datetime.now().isoformat(),
            'original_dtypes': df_copy.dtypes.to_dict()
        }
        
        self._last_loaded_info = load_info
        self.logger.info(f"✅ DataFrame carregado: {load_info['rows']} linhas, {load_info['columns']} colunas")
        
        return df_copy, load_info
    
    def load_from_base64(self, base64_content: str, filename: str = "upload.csv", **pandas_kwargs) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Carrega dados de string base64 (útil para upload de arquivos).
        
        Args:
            base64_content: Conteúdo CSV codificado em base64
            filename: Nome do arquivo para referência
            **pandas_kwargs: Argumentos adicionais para pd.read_csv()
            
        Returns:
            Tuple com (DataFrame, informações do carregamento)
            
        Raises:
            DataLoaderError: Se houver erro no carregamento
        """
        try:
            # Decodificar base64
            content = base64.b64decode(base64_content)
            
            # Verificar tamanho
            size_mb = len(content) / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                raise DataLoaderError(f"Arquivo muito grande: {size_mb:.1f}MB (máximo: {self.max_file_size_mb}MB)")
            
            self.logger.info(f"Processando upload: {filename} ({size_mb:.1f}MB)")
            
            # Detectar encoding
            encoding = pandas_kwargs.get('encoding')
            if not encoding:
                detected = chardet.detect(content)
                encoding = detected.get('encoding', 'utf-8')
                pandas_kwargs['encoding'] = encoding
            
            # Configurações padrão
            default_kwargs = {
                'low_memory': False,
                'encoding': encoding
            }
            default_kwargs.update(pandas_kwargs)
            
            # Carregar dados
            df = pd.read_csv(io.BytesIO(content), **default_kwargs)
            
            # Informações do carregamento
            load_info = {
                'source_type': 'base64_upload',
                'source_path': filename,
                'file_size_mb': size_mb,
                'encoding': encoding,
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'load_time': datetime.now().isoformat(),
                'pandas_kwargs': default_kwargs
            }
            
            self._last_loaded_info = load_info
            self.logger.info(f"✅ Upload processado: {load_info['rows']} linhas, {load_info['columns']} colunas")
            
            return df, load_info
            
        except Exception as e:
            error_msg = f"Erro ao processar upload {filename}: {str(e)}"
            self.logger.error(error_msg)
            raise DataLoaderError(error_msg) from e
    
    def create_synthetic_data(self, data_type: str = "fraud_detection", num_rows: int = 1000, **kwargs) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Cria dados sintéticos para testes e demonstrações.
        
        Args:
            data_type: Tipo de dados sintéticos ('fraud_detection', 'sales', 'customer', 'generic')
            num_rows: Número de linhas a gerar
            **kwargs: Argumentos específicos para cada tipo de dados
            
        Returns:
            Tuple com (DataFrame, informações do carregamento)
        """
        if num_rows <= 0:
            raise DataLoaderError("Número de linhas deve ser positivo")
        
        if num_rows > 100000:
            raise DataLoaderError("Número máximo de linhas para dados sintéticos: 100,000")
        
        self.logger.info(f"Gerando dados sintéticos: {data_type} ({num_rows} linhas)")
        
        # Seed para reprodutibilidade
        seed = kwargs.get('seed', 42)
        np.random.seed(seed)
        
        if data_type == "fraud_detection":
            df = self._create_fraud_data(num_rows, **kwargs)
        elif data_type == "sales":
            df = self._create_sales_data(num_rows, **kwargs)
        elif data_type == "customer":
            df = self._create_customer_data(num_rows, **kwargs)
        elif data_type == "generic":
            df = self._create_generic_data(num_rows, **kwargs)
        else:
            raise DataLoaderError(f"Tipo de dados sintéticos não suportado: {data_type}")
        
        # Informações do carregamento
        load_info = {
            'source_type': 'synthetic',
            'source_path': f"synthetic_{data_type}",
            'data_type': data_type,
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'load_time': datetime.now().isoformat(),
            'generation_params': {'num_rows': num_rows, 'seed': seed, **kwargs}
        }
        
        self._last_loaded_info = load_info
        self.logger.info(f"✅ Dados sintéticos gerados: {load_info['rows']} linhas, {load_info['columns']} colunas")
        
        return df, load_info
    
    def get_last_load_info(self) -> Optional[Dict[str, Any]]:
        """Retorna informações do último carregamento realizado."""
        return self._last_loaded_info
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detecta encoding de arquivo automaticamente."""
        try:
            # Ler amostra do arquivo
            with open(file_path, 'rb') as f:
                sample = f.read(10240)  # 10KB
            
            # Detectar encoding
            result = chardet.detect(sample)
            confidence = result.get('confidence', 0)
            detected_encoding = result.get('encoding', 'utf-8')
            
            self.logger.info(f"Encoding detectado: {detected_encoding} (confiança: {confidence:.2f})")
            
            # Se confiança baixa, tentar encodings comuns
            if confidence < 0.7:
                self.logger.warning(f"Baixa confiança na detecção de encoding ({confidence:.2f})")
                for encoding in self.supported_encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            f.read(1024)  # Teste de leitura
                        self.logger.info(f"Usando encoding alternativo: {encoding}")
                        return encoding
                    except UnicodeDecodeError:
                        continue
            
            return detected_encoding or 'utf-8'
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção de encoding: {str(e)}, usando utf-8")
            return 'utf-8'
    
    def _create_fraud_data(self, num_rows: int, **kwargs) -> pd.DataFrame:
        """Gera dados sintéticos para detecção de fraude."""
        fraud_rate = kwargs.get('fraud_rate', 0.05)  # 5% de fraude por padrão
        
        data = {
            'transaction_id': range(1, num_rows + 1),
            'amount': np.random.lognormal(4, 1.2, num_rows),
            'merchant_category': np.random.choice(['grocery', 'gas', 'restaurant', 'online', 'pharmacy', 'retail'], num_rows),
            'hour': np.random.randint(0, 24, num_rows),
            'day_of_week': np.random.randint(1, 8, num_rows),
            'customer_age': np.random.normal(40, 12, num_rows).astype(int).clip(18, 80),
            'account_balance': np.random.normal(3000, 1500, num_rows).clip(0, None),
            'transactions_today': np.random.poisson(2, num_rows),
            'is_weekend': np.random.choice([0, 1], num_rows, p=[0.71, 0.29]),
            'distance_from_home': np.random.exponential(5, num_rows),
        }
        
        # Lógica de fraude sofisticada
        fraud_prob = np.zeros(num_rows)
        fraud_prob += (data['amount'] > np.percentile(data['amount'], 95)) * 0.4
        fraud_prob += ((data['hour'] >= 2) & (data['hour'] <= 6)) * 0.3
        fraud_prob += (data['transactions_today'] > 8) * 0.5
        fraud_prob += (data['distance_from_home'] > 50) * 0.3
        
        # Aplicar taxa de fraude desejada
        fraud_prob = fraud_prob * (fraud_rate / fraud_prob.mean())
        data['is_fraud'] = np.random.binomial(1, np.clip(fraud_prob, 0, 1), num_rows)
        
        return pd.DataFrame(data)
    
    def _create_sales_data(self, num_rows: int, **kwargs) -> pd.DataFrame:
        """Gera dados sintéticos de vendas."""
        start_date = kwargs.get('start_date', '2023-01-01')
        
        # Gerar datas
        start = pd.to_datetime(start_date)
        dates = pd.date_range(start, periods=num_rows, freq='D')
        
        data = {
            'date': dates,
            'product_id': np.random.randint(1, 1000, num_rows),
            'category': np.random.choice(['electronics', 'clothing', 'books', 'home', 'sports'], num_rows),
            'price': np.random.uniform(10, 1000, num_rows),
            'quantity': np.random.randint(1, 10, num_rows),
            'sales_rep': np.random.choice([f'rep_{i:03d}' for i in range(1, 21)], num_rows),
            'region': np.random.choice(['North', 'South', 'East', 'West'], num_rows),
            'customer_type': np.random.choice(['new', 'returning', 'vip'], num_rows, p=[0.3, 0.6, 0.1])
        }
        
        data['total_amount'] = data['price'] * data['quantity']
        
        return pd.DataFrame(data)
    
    def _create_customer_data(self, num_rows: int, **kwargs) -> pd.DataFrame:
        """Gera dados sintéticos de clientes."""
        data = {
            'customer_id': range(1, num_rows + 1),
            'age': np.random.normal(35, 15, num_rows).astype(int).clip(18, 80),
            'income': np.random.lognormal(10, 0.5, num_rows).astype(int),
            'education': np.random.choice(['high_school', 'bachelor', 'master', 'phd'], num_rows, p=[0.3, 0.4, 0.2, 0.1]),
            'city_tier': np.random.choice([1, 2, 3], num_rows, p=[0.2, 0.3, 0.5]),
            'years_experience': np.random.exponential(5, num_rows).astype(int).clip(0, 40),
            'credit_score': np.random.normal(650, 100, num_rows).astype(int).clip(300, 850),
            'owns_home': np.random.choice([0, 1], num_rows, p=[0.4, 0.6]),
            'married': np.random.choice([0, 1], num_rows, p=[0.45, 0.55]),
        }
        
        # Correlações realistas
        # Converter education para Series primeiro para usar map
        education_series = pd.Series(data['education'])
        education_multiplier = education_series.map({'high_school': 0, 'bachelor': 0.3, 'master': 0.6, 'phd': 1.0})
        data['income'] = data['income'] * (1 + education_multiplier)
        data['credit_score'] = data['credit_score'] + (data['income'] / 10000 * 20)
        
        return pd.DataFrame(data)
    
    def _create_generic_data(self, num_rows: int, **kwargs) -> pd.DataFrame:
        """Gera dados sintéticos genéricos."""
        num_numeric = kwargs.get('num_numeric', 5)
        num_categorical = kwargs.get('num_categorical', 3)
        
        data = {}
        
        # Colunas numéricas
        for i in range(num_numeric):
            data[f'numeric_{i+1}'] = np.random.normal(100, 20, num_rows)
        
        # Colunas categóricas
        for i in range(num_categorical):
            categories = [f'cat_{j}' for j in range(1, np.random.randint(3, 8))]
            data[f'category_{i+1}'] = np.random.choice(categories, num_rows)
        
        # ID
        data['id'] = range(1, num_rows + 1)
        
        return pd.DataFrame(data)