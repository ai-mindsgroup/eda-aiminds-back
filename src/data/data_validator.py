"""Módulo de validação e limpeza de dados CSV.

Este módulo fornece funcionalidades avançadas para:
- Validação da estrutura e conteúdo de dados CSV
- Detecção de anomalias e problemas de qualidade
- Limpeza automática de dados
- Sugestões de correção de problemas comuns
- Relatórios detalhados de qualidade dos dados
"""
from __future__ import annotations
import re
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime
import warnings

from src.utils.logging_config import get_logger


class DataValidationError(Exception):
    """Exceção personalizada para erros de validação de dados."""
    pass


class DataValidator:
    """Validador e limpador avançado de dados CSV."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._validation_results: Optional[Dict[str, Any]] = None
        
        # Configurações de validação
        self.max_missing_percentage = 90  # % máximo de valores faltantes por coluna
        self.min_unique_values = 2  # Mínimo de valores únicos por coluna
        self.suspicious_patterns = [
            r'^\s*$',  # Strings vazias ou só espaços
            r'^(null|NULL|nil|NIL|n/a|N/A|na|NA|#N/A|#NULL!)$',  # Valores nulos variados
            r'^-{1,}$',  # Sequências de traços
            r'^\?+$',   # Pontos de interrogação
            r'^\.+$',   # Pontos
        ]
        
        self.logger.info("DataValidator inicializado")
    
    def validate_dataframe(self, df: pd.DataFrame, strict: bool = False) -> Dict[str, Any]:
        """Valida um DataFrame e retorna relatório completo de qualidade.
        
        Args:
            df: DataFrame para validar
            strict: Se True, aplica validações mais rigorosas
            
        Returns:
            Dicionário com resultados detalhados da validação
        """
        if df is None or df.empty:
            raise DataValidationError("DataFrame está vazio ou é None")
        
        self.logger.info(f"Iniciando validação de DataFrame: {len(df)} linhas, {len(df.columns)} colunas")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'basic_info': self._get_basic_info(df),
            'structure_validation': self._validate_structure(df, strict),
            'content_validation': self._validate_content(df, strict),
            'data_quality': self._analyze_data_quality(df),
            'recommendations': [],
            'warnings': [],
            'errors': [],
            'overall_score': 0.0
        }
        
        # Compilar recomendações e calcular score
        validation_results = self._compile_recommendations(validation_results)
        
        self._validation_results = validation_results
        self.logger.info(f"Validação concluída. Score: {validation_results['overall_score']:.1f}/100")
        
        return validation_results
    
    def clean_dataframe(self, df: pd.DataFrame, auto_fix: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Limpa e corrige problemas comuns em DataFrame.
        
        Args:
            df: DataFrame para limpar
            auto_fix: Se True, aplica correções automaticamente
            
        Returns:
            Tuple com (DataFrame limpo, relatório de limpeza)
        """
        if df is None or df.empty:
            raise DataValidationError("DataFrame está vazio ou é None")
        
        self.logger.info(f"Iniciando limpeza de dados: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Fazer cópia para não modificar original
        df_clean = df.copy()
        
        cleaning_report = {
            'timestamp': datetime.now().isoformat(),
            'original_shape': df.shape,
            'actions_taken': [],
            'removed_rows': 0,
            'modified_columns': [],
            'warnings': []
        }
        
        if auto_fix:
            # 1. Limpar nomes de colunas
            df_clean, report = self._clean_column_names(df_clean)
            cleaning_report['actions_taken'].extend(report.get('actions', []))
            
            # 2. Tratar valores faltantes
            df_clean, report = self._handle_missing_values(df_clean)
            cleaning_report['actions_taken'].extend(report.get('actions', []))
            
            # 3. Normalizar tipos de dados
            df_clean, report = self._normalize_data_types(df_clean)
            cleaning_report['actions_taken'].extend(report.get('actions', []))
            
            # 4. Remover duplicatas
            df_clean, report = self._remove_duplicates(df_clean)
            cleaning_report['actions_taken'].extend(report.get('actions', []))
            cleaning_report['removed_rows'] += report.get('removed_rows', 0)
            
            # 5. Limpar valores suspeitos
            df_clean, report = self._clean_suspicious_values(df_clean)
            cleaning_report['actions_taken'].extend(report.get('actions', []))
        
        cleaning_report['final_shape'] = df_clean.shape
        cleaning_report['rows_removed'] = df.shape[0] - df_clean.shape[0]
        cleaning_report['columns_modified'] = len(set(df.columns) ^ set(df_clean.columns))
        
        self.logger.info(f"Limpeza concluída: {len(cleaning_report['actions_taken'])} ações realizadas")
        
        return df_clean, cleaning_report
    
    def suggest_improvements(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sugere melhorias para o DataFrame baseado na análise.
        
        Args:
            df: DataFrame para analisar
            
        Returns:
            Lista de sugestões de melhoria
        """
        if self._validation_results is None:
            self.validate_dataframe(df)
        
        suggestions = []
        
        # Análise de colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].std() == 0:
                suggestions.append({
                    'type': 'remove_constant',
                    'column': col,
                    'description': f"Coluna '{col}' tem valor constante, considere remover",
                    'priority': 'medium'
                })
        
        # Análise de correlações altas
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().abs()
            high_corr = np.where((corr_matrix > 0.9) & (corr_matrix < 1.0))
            if len(high_corr[0]) > 0:
                suggestions.append({
                    'type': 'high_correlation',
                    'description': "Algumas colunas numéricas têm correlação muito alta (>0.9)",
                    'priority': 'low'
                })
        
        # Análise de valores faltantes
        missing_pct = (df.isnull().sum() / len(df)) * 100
        for col, pct in missing_pct.items():
            if pct > 50:
                suggestions.append({
                    'type': 'high_missing',
                    'column': col,
                    'description': f"Coluna '{col}' tem {pct:.1f}% de valores faltantes",
                    'priority': 'high'
                })
        
        return suggestions
    
    def get_validation_summary(self) -> Optional[Dict[str, Any]]:
        """Retorna resumo da última validação realizada."""
        if self._validation_results is None:
            return None
        
        return {
            'overall_score': self._validation_results['overall_score'],
            'total_errors': len(self._validation_results['errors']),
            'total_warnings': len(self._validation_results['warnings']),
            'total_recommendations': len(self._validation_results['recommendations']),
            'data_shape': self._validation_results['basic_info']['shape'],
            'timestamp': self._validation_results['timestamp']
        }
    
    def _get_basic_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extrai informações básicas do DataFrame."""
        return {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum()
        }
    
    def _validate_structure(self, df: pd.DataFrame, strict: bool) -> Dict[str, Any]:
        """Valida a estrutura do DataFrame."""
        issues = []
        warnings = []
        
        # Verificar nomes de colunas
        for col in df.columns:
            # Nomes vazios ou só espaços
            if not col or str(col).strip() == '':
                issues.append(f"Coluna com nome vazio encontrada")
            
            # Caracteres suspeitos
            if re.search(r'[^\w\s_-]', str(col)):
                warnings.append(f"Coluna '{col}' contém caracteres especiais")
            
            # Nomes muito longos
            if len(str(col)) > 50:
                warnings.append(f"Nome da coluna '{col}' é muito longo ({len(str(col))} caracteres)")
        
        # Verificar duplicatas de nomes
        duplicated_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicated_cols:
            issues.append(f"Colunas com nomes duplicados: {duplicated_cols}")
        
        # Verificar se há colunas vazias
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            warnings.append(f"Colunas completamente vazias: {empty_cols}")
        
        return {
            'issues': issues,
            'warnings': warnings,
            'column_names_clean': len(issues) == 0,
            'has_duplicated_columns': len(duplicated_cols) > 0,
            'empty_columns': empty_cols
        }
    
    def _validate_content(self, df: pd.DataFrame, strict: bool) -> Dict[str, Any]:
        """Valida o conteúdo do DataFrame."""
        issues = []
        warnings = []
        column_analysis = {}
        
        for col in df.columns:
            col_analysis = {
                'unique_values': df[col].nunique(),
                'missing_percentage': (df[col].isna().sum() / len(df)) * 100,
                'data_type_consistent': True,
                'suspicious_values': []
            }
            
            # Verificar alta porcentagem de valores faltantes
            if col_analysis['missing_percentage'] > self.max_missing_percentage:
                issues.append(f"Coluna '{col}' tem {col_analysis['missing_percentage']:.1f}% de valores faltantes")
            
            # Verificar poucos valores únicos para dados não-categóricos
            if col_analysis['unique_values'] < self.min_unique_values and len(df) > 10:
                warnings.append(f"Coluna '{col}' tem apenas {col_analysis['unique_values']} valores únicos")
            
            # Verificar valores suspeitos
            if df[col].dtype == 'object':
                suspicious = self._find_suspicious_values(df[col])
                if suspicious:
                    col_analysis['suspicious_values'] = suspicious
                    warnings.append(f"Coluna '{col}' contém {len(suspicious)} valores suspeitos")
            
            column_analysis[col] = col_analysis
        
        return {
            'issues': issues,
            'warnings': warnings,
            'column_analysis': column_analysis,
            'content_quality_score': self._calculate_content_score(column_analysis)
        }
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise avançada da qualidade dos dados."""
        quality_metrics = {
            'completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'uniqueness': (1 - df.duplicated().sum() / len(df)) * 100,
            'consistency': 100.0,  # Placeholder - poderia verificar formatos consistentes
            'validity': 100.0      # Placeholder - poderia verificar valores em ranges válidos
        }
        
        # Análise de outliers para colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_analysis = {}
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
            outlier_analysis[col] = {
                'count': len(outliers),
                'percentage': (len(outliers) / len(df)) * 100,
                'bounds': {'lower': lower_bound, 'upper': upper_bound}
            }
        
        return {
            'quality_metrics': quality_metrics,
            'outlier_analysis': outlier_analysis,
            'data_distribution': self._analyze_distributions(df),
            'correlation_strength': self._analyze_correlations(df)
        }
    
    def _find_suspicious_values(self, series: pd.Series) -> List[str]:
        """Encontra valores suspeitos em uma série."""
        suspicious = []
        
        for pattern in self.suspicious_patterns:
            matches = series.astype(str).str.match(pattern, na=False)
            if matches.any():
                suspicious_values = series[matches].unique().tolist()
                suspicious.extend(suspicious_values)
        
        return list(set(suspicious))
    
    def _clean_column_names(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Limpa nomes de colunas."""
        original_cols = df.columns.tolist()
        new_cols = []
        actions = []
        
        for col in df.columns:
            new_col = str(col).strip()
            
            # Remover caracteres especiais
            new_col = re.sub(r'[^\w\s_-]', '_', new_col)
            
            # Substituir espaços por underscores
            new_col = re.sub(r'\s+', '_', new_col)
            
            # Remover underscores múltiplos
            new_col = re.sub(r'_+', '_', new_col)
            
            # Remover underscores no início/fim
            new_col = new_col.strip('_')
            
            # Se ficou vazio, gerar nome padrão
            if not new_col:
                new_col = f'column_{len(new_cols)}'
            
            # Garantir unicidade
            original_new_col = new_col
            counter = 1
            while new_col in new_cols:
                new_col = f"{original_new_col}_{counter}"
                counter += 1
            
            new_cols.append(new_col)
            
            if new_col != col:
                actions.append(f"Renomeada coluna '{col}' para '{new_col}'")
        
        df.columns = new_cols
        
        return df, {'actions': actions}
    
    def _handle_missing_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Trata valores faltantes."""
        actions = []
        
        # Identificar colunas com muitos valores faltantes
        missing_pct = (df.isnull().sum() / len(df)) * 100
        cols_to_drop = missing_pct[missing_pct > 80].index.tolist()
        
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            actions.append(f"Removidas colunas com >80% valores faltantes: {cols_to_drop}")
        
        # Para colunas numéricas, preencher com mediana
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                actions.append(f"Preenchida coluna '{col}' com mediana ({median_val:.2f})")
        
        # Para colunas categóricas, preencher com moda ou 'Unknown'
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().any():
                if df[col].mode().empty:
                    fill_value = 'Unknown'
                else:
                    fill_value = df[col].mode().iloc[0]
                df[col].fillna(fill_value, inplace=True)
                actions.append(f"Preenchida coluna '{col}' com '{fill_value}'")
        
        return df, {'actions': actions}
    
    def _normalize_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Normaliza tipos de dados."""
        actions = []
        
        for col in df.columns:
            # Tentar converter strings numéricas
            if df[col].dtype == 'object':
                # Verificar se pode ser numérico
                try:
                    # Remover espaços e caracteres comuns
                    cleaned = df[col].astype(str).str.replace(r'[,\s$%]', '', regex=True)
                    numeric_series = pd.to_numeric(cleaned, errors='coerce')
                    
                    # Se >=80% dos valores são numéricos, converter
                    if (numeric_series.notna().sum() / len(df)) >= 0.8:
                        df[col] = numeric_series
                        actions.append(f"Convertida coluna '{col}' para numérica")
                        continue
                except:
                    pass
                
                # Verificar se pode ser data/hora
                try:
                    datetime_series = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
                    if (datetime_series.notna().sum() / len(df)) >= 0.8:
                        df[col] = datetime_series
                        actions.append(f"Convertida coluna '{col}' para datetime")
                        continue
                except:
                    pass
        
        return df, {'actions': actions}
    
    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Remove linhas duplicadas."""
        initial_rows = len(df)
        df_clean = df.drop_duplicates()
        removed_rows = initial_rows - len(df_clean)
        
        actions = []
        if removed_rows > 0:
            actions.append(f"Removidas {removed_rows} linhas duplicadas")
        
        return df_clean, {'actions': actions, 'removed_rows': removed_rows}
    
    def _clean_suspicious_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Limpa valores suspeitos."""
        actions = []
        
        for col in df.select_dtypes(include=['object']).columns:
            for pattern in self.suspicious_patterns:
                mask = df[col].astype(str).str.match(pattern, na=False)
                if mask.any():
                    df.loc[mask, col] = np.nan
                    count = mask.sum()
                    actions.append(f"Removidos {count} valores suspeitos da coluna '{col}'")
        
        return df, {'actions': actions}
    
    def _calculate_content_score(self, column_analysis: Dict[str, Any]) -> float:
        """Calcula score de qualidade do conteúdo."""
        scores = []
        
        for col, analysis in column_analysis.items():
            col_score = 100.0
            
            # Penalizar alta porcentagem de faltantes
            col_score -= analysis['missing_percentage']
            
            # Penalizar valores suspeitos
            if analysis['suspicious_values']:
                col_score -= len(analysis['suspicious_values']) * 5
            
            col_score = max(col_score, 0)
            scores.append(col_score)
        
        return np.mean(scores) if scores else 0.0
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa distribuições dos dados."""
        distributions = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            distributions[col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'skewness': df[col].skew(),
                'kurtosis': df[col].kurtosis()
            }
        
        return distributions
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa correlações entre variáveis numéricas."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {'message': 'Insufficient numeric columns for correlation analysis'}
        
        corr_matrix = df[numeric_cols].corr()
        
        # Encontrar correlações mais fortes
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if not pd.isna(corr_value):
                    corr_pairs.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': corr_value
                    })
        
        # Ordenar por correlação absoluta
        corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'top_correlations': corr_pairs[:10],
            'high_correlations': [p for p in corr_pairs if abs(p['correlation']) > 0.7]
        }
    
    def _compile_recommendations(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compila recomendações finais e calcula score geral."""
        recommendations = []
        
        # Baseado nos erros estruturais
        if validation_results['structure_validation']['issues']:
            recommendations.append({
                'category': 'structure',
                'priority': 'high',
                'description': 'Corrigir problemas estruturais do DataFrame'
            })
        
        # Baseado na qualidade do conteúdo
        content_score = validation_results['content_validation']['content_quality_score']
        if content_score < 80:
            recommendations.append({
                'category': 'content_quality',
                'priority': 'medium',
                'description': 'Melhorar qualidade do conteúdo dos dados'
            })
        
        # Calcular score geral
        structure_score = 100 if not validation_results['structure_validation']['issues'] else 70
        quality_metrics = validation_results['data_quality']['quality_metrics']
        overall_score = np.mean([
            structure_score,
            content_score,
            quality_metrics['completeness'],
            quality_metrics['uniqueness']
        ])
        
        validation_results['recommendations'] = recommendations
        validation_results['overall_score'] = overall_score
        
        return validation_results