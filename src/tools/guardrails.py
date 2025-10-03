"""Sistema de guardrails para validação de estatísticas e prevenção de alucinações.

Este módulo implementa validações automáticas para garantir que
as estatísticas fornecidas pelo LLM estejam dentro de ranges esperados.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import math

from src.utils.logging_config import get_logger

@dataclass
class ValidationResult:
    """Resultado da validação de guardrails"""
    is_valid: bool
    confidence_score: float
    issues: List[str]
    corrected_values: Optional[Dict[str, Any]] = None

class StatisticsGuardrails:
    """Sistema de guardrails para validação de estatísticas.
    
    Implementa validações automáticas para detectar e corrigir
    alucinações do LLM em estatísticas de dados.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # SISTEMA GENÉRICO: Ranges configuráveis por dataset
        self.dataset_ranges = {
            'creditcard': {
                'total_transactions': (280000, 290000),
                'total_columns': (30, 32),
                'amount_mean': (50, 150),
                'amount_std': (200, 300),
                'amount_min': (0, 1),
                'amount_max': (20000, 30000),
                'class_0_percentage': (99.0, 100.0),
                'class_1_percentage': (0.0, 1.0),
                'v_features_count': (28, 28),
            },
            'generic': {
                'total_transactions': (100, 10000000),  # Range muito amplo
                'total_columns': (2, 1000),
                'numeric_ranges': (-1000000, 1000000),  # Range genérico
                'percentage_ranges': (0.0, 100.0)
            }
        }
    
    def validate_response(self, response_content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Valida resposta do LLM para detectar alucinações GENÉRICAS.
        
        Args:
            response_content: Conteúdo da resposta do LLM
            context: Contexto adicional com dados conhecidos (ESSENCIAL)
            
        Returns:
            Resultado da validação com issues detectados
        """
        issues = []
        confidence_score = 1.0
        corrected_values = {}
        
        try:
            # VALIDAÇÃO GENÉRICA baseada no CONTEXTO real fornecido
            if context and 'csv_analysis' in context:
                return self._validate_against_real_data(response_content, context)
            else:
                # Se não tem contexto, fazer validação básica de consistência
                return self._validate_basic_consistency(response_content)
                
        except Exception as e:
            self.logger.error(f"Erro na validação de guardrails: {str(e)}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                issues=[f"Erro na validação: {str(e)}"]
            )
    
    def _validate_against_real_data(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Valida resposta comparando com dados REAIS do contexto.
        
        Args:
            content: Conteúdo da resposta do LLM
            context: Contexto com dados reais calculados
        """
        issues = []
        confidence_score = 1.0
        corrected_values = {}
        
        # 🛡️ GUARDRAIL: Validar que a resposta utiliza informações dos chunks
        if not self._validates_semantic_interpretation(content, context):
            issues.append("⚠️ Resposta não demonstra interpretação semântica adequada dos chunks fornecidos")
            confidence_score -= 0.3
        
        # Extrair dados reais do contexto
        real_data = context.get('csv_analysis', {})
        
        # 1. Validar contagens básicas
        self._validate_basic_counts(content, real_data, issues, corrected_values)
        
        # 2. Validar tipos de dados
        self._validate_data_types(content, real_data, issues, corrected_values)
        
        # 3. Validar estatísticas numéricas
        self._validate_statistics(content, real_data, issues, corrected_values)
        
        # 4. Validar distribuições
        self._validate_distributions(content, real_data, issues, corrected_values)
        
        # Calcular score de confiança
        if issues:
            confidence_score = max(0.1, 1.0 - (len(issues) * 0.2))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=confidence_score,
            issues=issues,
            corrected_values=corrected_values
        )
    
    def _validate_basic_counts(self, content: str, real_data: Dict, issues: list, corrected_values: Dict):
        """Valida contagens básicas (registros, colunas) com dados reais"""
        import re
        
        # Validar total de registros
        if 'total_records' in real_data:
            real_records = real_data['total_records']
            
            # Buscar números de registros na resposta
            record_patterns = [
                r'(\d{1,3}(?:[,.]?\d{3})*)\s*registros',
                r'Total.*?(\d{1,3}(?:[,.]?\d{3})*)',
                r'(\d{1,3}(?:[,.]?\d{3})*)\s*transações'
            ]
            
            for pattern in record_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    claimed_records = int(match.replace(',', '').replace('.', ''))
                    if abs(claimed_records - real_records) > 100:  # Tolerância de 100
                        issues.append(f"Registros incorretos: {claimed_records} (real: {real_records})")
                        corrected_values['total_records'] = real_records
        
        # Validar total de colunas
        if 'total_columns' in real_data:
            real_columns = real_data['total_columns']
            
            column_patterns = [
                r'(\d+)\s*colunas',
                r'Total.*?colunas.*?(\d+)',
                r'(\d+)\s*variáveis'
            ]
            
            for pattern in column_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    claimed_columns = int(match)
                    if claimed_columns != real_columns:
                        issues.append(f"Colunas incorretas: {claimed_columns} (real: {real_columns})")
                        corrected_values['total_columns'] = real_columns
    
    def _validate_data_types(self, content: str, real_data: Dict, issues: list, corrected_values: Dict):
        """Valida tipos de dados com dados reais"""
        if 'tipos_dados' in real_data:
            tipos_reais = real_data['tipos_dados']
            
            # Se todos são numéricos, não deveria mencionar categóricas
            if tipos_reais.get('total_categoricos', 0) == 0:
                categorical_mentions = [
                    'categóric', 'categoric', 'texto', 'string', 'object'
                ]
                
                for mention in categorical_mentions:
                    if mention in content.lower() and 'não' not in content.lower():
                        issues.append("Menciona colunas categóricas quando não existem")
                        corrected_values['categorical_error'] = "Todas as colunas são numéricas"
            
            # Verificar contagem de tipos
            if tipos_reais.get('total_numericos'):
                real_numeric = tipos_reais['total_numericos']
                import re
                numeric_pattern = r'(\d+)\s*(?:colunas?\s*)?(?:numéricas?|numéricos?)'
                matches = re.findall(numeric_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    claimed_numeric = int(match)
                    if claimed_numeric != real_numeric:
                        issues.append(f"Tipos incorretos: {claimed_numeric} numéricas (real: {real_numeric})")
                        corrected_values['numeric_count'] = real_numeric
    
    def _validate_statistics(self, content: str, real_data: Dict, issues: list, corrected_values: Dict):
        """Valida estatísticas numéricas com dados reais"""
        if 'estatisticas' in real_data:
            stats_reais = real_data['estatisticas']
            
            import re
            
            # Validar médias
            for col, stats in stats_reais.items():
                if 'mean' in stats:
                    real_mean = stats['mean']
                    
                    # Buscar menções da média desta coluna
                    patterns = [
                        rf'{col}.*?média.*?R?\$?\s*([\d,.]+)',
                        rf'média.*?{col}.*?R?\$?\s*([\d,.]+)',
                        rf'média.*?R?\$?\s*([\d,.]+)'  # Genérico
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            try:
                                claimed_mean = float(match.replace(',', '.'))
                                tolerance = abs(real_mean * 0.01)  # 1% de tolerância
                                
                                if abs(claimed_mean - real_mean) > tolerance:
                                    issues.append(f"Média {col} incorreta: {claimed_mean} (real: {real_mean:.2f})")
                                    corrected_values[f'{col}_mean'] = real_mean
                            except ValueError:
                                continue
    
    def _validate_distributions(self, content: str, real_data: Dict, issues: list, corrected_values: Dict):
        """Valida distribuições com dados reais"""
        if 'distribuicao' in real_data:
            dist_reais = real_data['distribuicao']
            
            import re
            
            # Validar percentuais
            for col, dist in dist_reais.items():
                if isinstance(dist, dict):
                    for value, count in dist.items():
                        total = real_data.get('total_records', 1)
                        real_percentage = (count / total) * 100
                        
                        # Buscar menções de percentuais
                        patterns = [
                            rf'{value}.*?(\d+(?:[,.]?\d+)?)%',
                            rf'(\d+(?:[,.]?\d+)?)%.*?{value}'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                try:
                                    claimed_percentage = float(match.replace(',', '.'))
                                    
                                    if abs(claimed_percentage - real_percentage) > 1.0:  # 1% tolerância
                                        issues.append(f"Percentual {col}={value} incorreto: {claimed_percentage}% (real: {real_percentage:.2f}%)")
                                        corrected_values[f'{col}_{value}_pct'] = real_percentage
                                except ValueError:
                                    continue
    
    def _validate_basic_consistency(self, content: str) -> ValidationResult:
        """Validação básica de consistência quando não há contexto"""
        issues = []
        
        # Verificações básicas de sanidade
        if len(content) < 10:
            issues.append("Resposta muito curta")
        
        if "erro" in content.lower() and "desculpe" not in content.lower():
            issues.append("Resposta indica erro sem explicação")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=0.8 if len(issues) == 0 else 0.3,
            issues=issues
        )
    
    def _validate_dataset_response(self, content: str, dataset_type: str = 'generic') -> ValidationResult:
        """Valida resposta para qualquer tipo de dataset.
        
        Args:
            content: Conteúdo da resposta
            dataset_type: Tipo do dataset ('creditcard', 'generic', etc.)
        """
        issues = []
        confidence_score = 1.0
        corrected_values = {}
        
        # Obter ranges para o dataset
        ranges = self.dataset_ranges.get(dataset_type, self.dataset_ranges['generic'])
        
        # Extrair valores numéricos da resposta
        extracted_values = self._extract_numerical_values(content)
        
        if dataset_type == 'creditcard':
            # Validações específicas para creditcard
            return self._validate_creditcard_specific(content, ranges, issues, confidence_score, corrected_values)
        else:
            # Validações genéricas
            return self._validate_generic_dataset(content, ranges, issues, confidence_score, corrected_values)
    
    def _validate_creditcard_specific(self, content: str, ranges: dict, issues: list, confidence_score: float, corrected_values: dict) -> ValidationResult:
        """Validações específicas para dataset creditcard"""
        
        # Validar total de transações
        total_match = re.search(r'(\d{1,3}(?:[,.]?\d{3})*)\s*(?:transações|registros|linhas)', content, re.IGNORECASE)
        if total_match:
            total = self._parse_number(total_match.group(1))
            if total and not (ranges['total_transactions'][0] <= total <= ranges['total_transactions'][1]):
                issues.append(f"Total de transações suspeito: {total:,} (esperado: ~284.807)")
                confidence_score -= 0.2
                corrected_values['total_transactions'] = 284807
        
        # Validar estatísticas Amount
        amount_mean = self._extract_amount_statistic(content, ['média', 'mean'])
        if amount_mean and not (ranges['amount_mean'][0] <= amount_mean <= ranges['amount_mean'][1]):
            issues.append(f"Média de Amount suspeita: R$ {amount_mean:.2f} (esperado: ~R$ 88)")
            confidence_score -= 0.3
            corrected_values['amount_mean'] = 88.35
        
        amount_std = self._extract_amount_statistic(content, ['desvio', 'std', 'standard'])
        if amount_std and not (ranges['amount_std'][0] <= amount_std <= ranges['amount_std'][1]):
            issues.append(f"Desvio padrão de Amount suspeito: R$ {amount_std:.2f} (esperado: ~R$ 250)")
            confidence_score -= 0.3
            corrected_values['amount_std'] = 250.12
        
        # Validar distribuição Class
        class_percentages = self._extract_class_percentages(content)
        if class_percentages:
            class_0_pct, class_1_pct = class_percentages
            
            if not (ranges['class_0_percentage'][0] <= class_0_pct <= ranges['class_0_percentage'][1]):
                issues.append(f"Porcentagem Class 0 suspeita: {class_0_pct:.1f}% (esperado: ~99.8%)")
                confidence_score -= 0.4
                corrected_values['class_0_percentage'] = 99.83
            
            if not (ranges['class_1_percentage'][0] <= class_1_pct <= ranges['class_1_percentage'][1]):
                issues.append(f"Porcentagem Class 1 suspeita: {class_1_pct:.1f}% (esperado: ~0.17%)")
                confidence_score -= 0.4
                corrected_values['class_1_percentage'] = 0.17
        
        # Validar features V1-V28
        v_features_count = len(re.findall(r'\bV\d+\b', content))
        if v_features_count > 0 and v_features_count != 28:
            issues.append(f"Número de features V suspeito: {v_features_count} (esperado: 28)")
            confidence_score -= 0.1
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=max(0.0, confidence_score),
            issues=issues,
            corrected_values=corrected_values if corrected_values else None
        )
    
    def _validate_generic_dataset(self, content: str, ranges: dict, issues: list, confidence_score: float, corrected_values: dict) -> ValidationResult:
        """Validações genéricas para qualquer dataset"""
        
        # Validar total de registros (range genérico)
        total_match = re.search(r'(\d{1,3}(?:[,.]?\d{3})*)\s*(?:transações|registros|linhas|rows)', content, re.IGNORECASE)
        if total_match:
            total = self._parse_number(total_match.group(1))
            if total and not (ranges['total_transactions'][0] <= total <= ranges['total_transactions'][1]):
                issues.append(f"Total de registros fora do range esperado: {total:,}")
                confidence_score -= 0.1
        
        # Validar percentuais genéricos
        percentages = re.findall(r'(\d+(?:[,.]\d+)?)\s*%', content)
        for pct_str in percentages:
            try:
                pct = float(pct_str.replace(',', '.'))
                if not (ranges['percentage_ranges'][0] <= pct <= ranges['percentage_ranges'][1]):
                    issues.append(f"Percentual impossível: {pct}%")
                    confidence_score -= 0.2
            except:
                continue
        
        # Validar números muito grandes ou pequenos
        numbers = re.findall(r'\b\d{1,3}(?:[,.]\d{3})*(?:[,.]\d+)?\b', content)
        for num_str in numbers:
            try:
                num = self._parse_number(num_str)
                if num and (num > 1000000000 or (num > 100 and num < 0.001)):
                    issues.append(f"Valor numérico suspeito: {num}")
                    confidence_score -= 0.1
            except:
                continue
        
        return ValidationResult(
            is_valid=len(issues) <= 2,  # Tolerar até 2 issues menores em datasets genéricos
            confidence_score=max(0.0, confidence_score),
            issues=issues,
            corrected_values=corrected_values if corrected_values else None
        )
    
    def _validate_generic_response(self, content: str) -> ValidationResult:
        """Validações genéricas para qualquer resposta (método mantido para compatibilidade)"""
        return self._validate_generic_dataset(content, self.dataset_ranges['generic'], [], 1.0, {})
    
    def _extract_numerical_values(self, content: str) -> Dict[str, float]:
        """Extrai valores numéricos da resposta"""
        values = {}
        
        # Padrões para extrair estatísticas comuns
        patterns = {
            'mean': r'média[:\s]*(?:R\$\s*)?(\d+(?:[,.]\d+)?)',
            'std': r'desvio[:\s]*(?:R\$\s*)?(\d+(?:[,.]\d+)?)',
            'min': r'mínimo[:\s]*(?:R\$\s*)?(\d+(?:[,.]\d+)?)',
            'max': r'máximo[:\s]*(?:R\$\s*)?(\d+(?:[,.]\d+)?)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                values[key] = self._parse_number(match.group(1))
        
        return values
    
    def _extract_amount_statistic(self, content: str, keywords: List[str]) -> Optional[float]:
        """Extrai estatística específica de Amount"""
        for keyword in keywords:
            pattern = f'{keyword}[:\s]*(?:R\$\s*)?(\d+(?:[,.]\d+)?)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return self._parse_number(match.group(1))
        return None
    
    def _extract_class_percentages(self, content: str) -> Optional[Tuple[float, float]]:
        """Extrai percentuais das classes 0 e 1"""
        class_0_match = re.search(r'(?:class\s*0|normal)[:\s]*(\d+(?:[,.]\d+)?)\s*%', content, re.IGNORECASE)
        class_1_match = re.search(r'(?:class\s*1|fraude)[:\s]*(\d+(?:[,.]\d+)?)\s*%', content, re.IGNORECASE)
        
        if class_0_match and class_1_match:
            class_0_pct = float(class_0_match.group(1).replace(',', '.'))
            class_1_pct = float(class_1_match.group(1).replace(',', '.'))
            return (class_0_pct, class_1_pct)
        
        return None
    
    def _parse_number(self, num_str: str) -> Optional[float]:
        """Parse seguro de números com diferentes formatos"""
        try:
            # Remover separadores de milhares e normalizar decimal
            clean_num = num_str.replace('.', '').replace(',', '.')
            
            # Se há mais de um ponto, assumir formato brasileiro (1.234,56)
            if '.' in num_str and ',' in num_str:
                # Formato brasileiro: 1.234,56
                clean_num = num_str.replace('.', '').replace(',', '.')
            elif ',' in num_str and num_str.count(',') == 1:
                # Pode ser decimal brasileiro (123,45) ou separador de milhares (1,234)
                parts = num_str.split(',')
                if len(parts[1]) <= 2:  # Provavelmente decimal
                    clean_num = num_str.replace(',', '.')
                else:  # Provavelmente separador de milhares
                    clean_num = num_str.replace(',', '')
            
            return float(clean_num)
        except:
            return None
    
    def generate_correction_prompt(self, validation_result: ValidationResult) -> str:
        """Gera prompt de correção baseado nos issues encontrados"""
        if validation_result.is_valid:
            return ""
        
        prompt = "\n⚠️ **CORREÇÕES NECESSÁRIAS:**\n"
        
        for issue in validation_result.issues:
            prompt += f"- {issue}\n"
        
        if validation_result.corrected_values:
            prompt += "\n✅ **Valores corretos:**\n"
            for key, value in validation_result.corrected_values.items():
                if 'percentage' in key:
                    prompt += f"- {key}: {value:.2f}%\n"
                elif 'amount' in key:
                    prompt += f"- {key}: R$ {value:.2f}\n"
                else:
                    prompt += f"- {key}: {value:,}\n"
    
    def _validates_semantic_interpretation(self, content: str, context: Dict[str, Any]) -> bool:
        """Valida se a resposta demonstra interpretação semântica dos chunks.
        
        Args:
            content: Conteúdo da resposta do LLM
            context: Contexto com dados dos chunks
            
        Returns:
            True se a resposta demonstra interpretação semântica adequada
        """
        # 🛡️ GUARDRAIL: Verificar se a resposta menciona informações específicas dos chunks
        content_lower = content.lower()
        
        # Verificar se há menção a elementos comuns em descrições de datasets
        semantic_indicators = [
            'features', 'colunas', 'columns', 'transações', 'dataset',
            'v1', 'v2', 'v3', 'pca', 'time', 'amount', 'class',
            'fraude', 'fraud', 'cartão', 'crédito', 'credit', 'card',
            'numérico', 'categórico', 'temporal', 'numeric', 'categorical'
        ]
        
        # Contar quantos indicadores semânticos estão presentes
        indicators_found = sum(1 for indicator in semantic_indicators if indicator in content_lower)
        
        # Resposta deve mencionar pelo menos 3 indicadores semânticos
        if indicators_found < 3:
            self.logger.warning(f"⚠️ Resposta não demonstra interpretação semântica adequada (apenas {indicators_found} indicadores encontrados)")
            return False
        
        # 🛡️ GUARDRAIL: Verificar se não é uma resposta genérica
        generic_phrases = [
            'não tenho informações suficientes',
            'não posso fornecer detalhes',
            'sem contexto adicional',
            'dados não disponíveis'
        ]
        
        for phrase in generic_phrases:
            if phrase in content_lower:
                self.logger.warning(f"⚠️ Resposta contém frase genérica: '{phrase}'")
                return False
        
        self.logger.info(f"✅ Resposta demonstra interpretação semântica adequada ({indicators_found} indicadores encontrados)")
        return True
        
        return prompt

# Instância global para uso pelos agentes
statistics_guardrails = StatisticsGuardrails()