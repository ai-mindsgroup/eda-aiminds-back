"""
Testes Automatizados de Respostas EDA - FASE 2
===============================================

Este módulo valida se o sistema responde corretamente às perguntas
padrão de Análise Exploratória de Dados (EDA), incluindo:

1. Descrição dos Dados
2. Identificação de Padrões e Tendências
3. Detecção de Anomalias (Outliers)
4. Relações entre Variáveis

Dataset: data/synthetic_eda_test.csv (100 transações sintéticas)
Agente: OrchestratorAgent com integração LLM
"""
import pytest
import pandas as pd
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Imports do projeto
try:
    from src.agent.orchestrator_agent import OrchestratorAgent
    from src.data.data_processor import DataProcessor
    from src.utils.logging_config import get_logger
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    print(f"⚠️ OrchestratorAgent não disponível: {str(e)}")

logger = get_logger(__name__)

# Configurações de teste
TEST_DATA_PATH = root_dir / "data" / "synthetic_eda_test.csv"
REPORTS_DIR = root_dir / "reports"
OUTPUTS_DIR = root_dir / "outputs"

# Garantir que diretórios existam
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)


class EDATestResult:
    """Representa o resultado de um teste EDA."""
    
    def __init__(self, question: str, category: str):
        self.question = question
        self.category = category
        self.response = None
        self.success = False
        self.error = None
        self.timestamp = datetime.now()
        self.execution_time = 0.0
        self.validation_results = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "category": self.category,
            "response": self.response,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_seconds": self.execution_time,
            "validations": self.validation_results
        }


@pytest.fixture(scope="session")
def test_dataset():
    """Carrega o dataset sintético para testes."""
    if not TEST_DATA_PATH.exists():
        pytest.skip(f"Dataset de teste não encontrado: {TEST_DATA_PATH}")
    
    try:
        df = pd.read_csv(TEST_DATA_PATH)
        logger.info(f"✅ Dataset carregado: {len(df)} linhas, {len(df.columns)} colunas")
        return df
    except Exception as e:
        pytest.fail(f"Erro ao carregar dataset: {str(e)}")


@pytest.fixture(scope="session")
def orchestrator():
    """Inicializa o OrchestratorAgent para testes."""
    if not ORCHESTRATOR_AVAILABLE:
        pytest.skip("OrchestratorAgent não disponível")
    
    try:
        agent = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=False,  # Desabilitar RAG para testes isolados
            enable_llm_manager=True,
            enable_data_processor=True
        )
        logger.info("✅ OrchestratorAgent inicializado")
        return agent
    except Exception as e:
        pytest.fail(f"Erro ao inicializar OrchestratorAgent: {str(e)}")


@pytest.fixture(scope="session")
def data_processor(test_dataset):
    """Inicializa o DataProcessor com dataset de teste."""
    try:
        # Autorizar test_system a acessar CSV
        processor = DataProcessor(caller_agent="test_system")
        processor.load_data_from_dataframe(test_dataset, source_name="synthetic_eda_test")
        logger.info("✅ DataProcessor inicializado")
        return processor
    except Exception as e:
        pytest.fail(f"Erro ao inicializar DataProcessor: {str(e)}")


class TestEDADescricaoDados:
    """1. CATEGORIA: Descrição dos Dados"""
    
    def test_tipos_de_dados(self, orchestrator, data_processor):
        """Quais são os tipos de dados (numéricos, categóricos)?"""
        result = EDATestResult(
            question="Quais são os tipos de dados (numéricos, categóricos)?",
            category="Descrição dos Dados"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_numeric"] = any(
                keyword in result.response.lower() 
                for keyword in ["numérico", "numeric", "int", "float", "número"]
            )
            result.validation_results["mentions_categorical"] = any(
                keyword in result.response.lower() 
                for keyword in ["categórico", "categorical", "texto", "string", "categoria"]
            )
            result.validation_results["response_length"] = len(result.response)
            result.validation_results["is_humanized"] = len(result.response) > 50  # Não hardcoded
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_numeric"] and
                result.validation_results["mentions_categorical"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_distribuicao_variaveis(self, orchestrator, data_processor):
        """Qual a distribuição de cada variável (histogramas)?"""
        result = EDATestResult(
            question="Qual a distribuição de cada variável? Mostre histogramas.",
            category="Descrição dos Dados"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_distribution"] = any(
                keyword in result.response.lower() 
                for keyword in ["distribuição", "distribution", "histograma", "histogram"]
            )
            result.validation_results["mentions_visualization"] = any(
                keyword in result.response.lower() 
                for keyword in ["gráfico", "plot", "chart", "visualização", "figura"]
            )
            result.validation_results["response_length"] = len(result.response)
            
            result.success = (
                result.validation_results["has_response"] and
                (result.validation_results["mentions_distribution"] or 
                 result.validation_results["mentions_visualization"])
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_intervalo_dados(self, orchestrator, data_processor):
        """Qual o intervalo (mínimo, máximo)?"""
        result = EDATestResult(
            question="Qual o intervalo dos dados (mínimo e máximo) para as variáveis numéricas?",
            category="Descrição dos Dados"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_min_max"] = any(
                keyword in result.response.lower() 
                for keyword in ["mínimo", "máximo", "minimum", "maximum", "min", "max", "intervalo"]
            )
            result.validation_results["has_numeric_values"] = any(
                char.isdigit() for char in result.response
            )
            result.validation_results["response_length"] = len(result.response)
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_min_max"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_tendencia_central(self, orchestrator, data_processor):
        """Quais as medidas de tendência central (média, mediana)?"""
        result = EDATestResult(
            question="Quais as medidas de tendência central (média e mediana) dos dados?",
            category="Descrição dos Dados"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_mean"] = any(
                keyword in result.response.lower() 
                for keyword in ["média", "mean", "average"]
            )
            result.validation_results["mentions_median"] = any(
                keyword in result.response.lower() 
                for keyword in ["mediana", "median"]
            )
            result.validation_results["has_numeric_values"] = any(
                char.isdigit() for char in result.response
            )
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_mean"] and
                result.validation_results["mentions_median"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_variabilidade(self, orchestrator, data_processor):
        """Qual a variabilidade (desvio padrão, variância)?"""
        result = EDATestResult(
            question="Qual a variabilidade dos dados (desvio padrão e variância)?",
            category="Descrição dos Dados"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_std"] = any(
                keyword in result.response.lower() 
                for keyword in ["desvio padrão", "standard deviation", "std", "desvio"]
            )
            result.validation_results["mentions_variance"] = any(
                keyword in result.response.lower() 
                for keyword in ["variância", "variance", "var"]
            )
            result.validation_results["has_numeric_values"] = any(
                char.isdigit() for char in result.response
            )
            
            result.success = (
                result.validation_results["has_response"] and
                (result.validation_results["mentions_std"] or 
                 result.validation_results["mentions_variance"])
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"


class TestEDAPadroesETendencias:
    """2. CATEGORIA: Identificação de Padrões e Tendências"""
    
    def test_padroes_temporais(self, orchestrator, data_processor):
        """Existem padrões ou tendências temporais?"""
        result = EDATestResult(
            question="Existem padrões ou tendências temporais nas transações? Analise por hora do dia.",
            category="Padrões e Tendências"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_temporal"] = any(
                keyword in result.response.lower() 
                for keyword in ["temporal", "tempo", "hora", "tendência", "padrão", "time"]
            )
            result.validation_results["mentions_hour"] = any(
                keyword in result.response.lower() 
                for keyword in ["hora", "hour", "transaction_hour"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 100
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_temporal"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_valores_frequentes(self, orchestrator, data_processor):
        """Quais os valores mais e menos frequentes?"""
        result = EDATestResult(
            question="Quais são os valores mais e menos frequentes nas variáveis categóricas?",
            category="Padrões e Tendências"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_frequency"] = any(
                keyword in result.response.lower() 
                for keyword in ["frequente", "frequency", "comum", "raro", "contagem"]
            )
            result.validation_results["mentions_categorical"] = any(
                keyword in result.response.lower() 
                for keyword in ["categoria", "category", "payment_method", "pagamento"]
            )
            result.validation_results["has_specific_values"] = any(
                keyword in result.response 
                for keyword in ["Credit Card", "Debit Card", "PayPal", "Cash", "Wire Transfer"]
            )
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_frequency"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_agrupamentos(self, orchestrator, data_processor):
        """Existem agrupamentos (clusters)?"""
        result = EDATestResult(
            question="Existem agrupamentos (clusters) nos dados? Analise customer_age vs transaction_amount.",
            category="Padrões e Tendências"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_clustering"] = any(
                keyword in result.response.lower() 
                for keyword in ["cluster", "agrupamento", "grupo", "segmento"]
            )
            result.validation_results["mentions_variables"] = any(
                keyword in result.response.lower() 
                for keyword in ["age", "idade", "amount", "valor"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 80
            
            result.success = (
                result.validation_results["has_response"] and
                len(result.response) > 50  # Resposta substantiva
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"


class TestEDADeteccaoAnomalias:
    """3. CATEGORIA: Detecção de Anomalias (Outliers)"""
    
    def test_valores_atipicos(self, orchestrator, data_processor):
        """Existem valores atípicos?"""
        result = EDATestResult(
            question="Existem valores atípicos (outliers) nos dados? Analise transaction_amount.",
            category="Detecção de Anomalias"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_outliers"] = any(
                keyword in result.response.lower() 
                for keyword in ["outlier", "atípico", "anômalo", "anomalia", "discrepante"]
            )
            result.validation_results["mentions_amount"] = any(
                keyword in result.response.lower() 
                for keyword in ["amount", "valor", "transaction"]
            )
            result.validation_results["has_numeric_values"] = any(
                char.isdigit() for char in result.response
            )
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_outliers"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_impacto_anomalias(self, orchestrator, data_processor):
        """Como afetam a análise?"""
        result = EDATestResult(
            question="Como os valores atípicos afetam a análise estatística dos dados?",
            category="Detecção de Anomalias"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_impact"] = any(
                keyword in result.response.lower() 
                for keyword in ["afeta", "impacto", "influência", "efeito", "impact", "affect"]
            )
            result.validation_results["mentions_statistics"] = any(
                keyword in result.response.lower() 
                for keyword in ["média", "mediana", "estatística", "análise", "mean", "median"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 100
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_impact"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_tratamento_anomalias(self, orchestrator, data_processor):
        """Podem ser removidos, transformados ou investigados?"""
        result = EDATestResult(
            question="Os outliers detectados devem ser removidos, transformados ou investigados? Justifique.",
            category="Detecção de Anomalias"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_treatment"] = any(
                keyword in result.response.lower() 
                for keyword in ["remover", "transformar", "investigar", "remove", "transform", "investigate"]
            )
            result.validation_results["has_justification"] = any(
                keyword in result.response.lower() 
                for keyword in ["porque", "pois", "justifica", "razão", "motivo", "because", "since"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 120
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_treatment"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"


class TestEDARelacoesVariaveis:
    """4. CATEGORIA: Relações entre Variáveis"""
    
    def test_relacoes_variaveis(self, orchestrator, data_processor):
        """Como as variáveis estão relacionadas?"""
        result = EDATestResult(
            question="Como as variáveis estão relacionadas entre si? Analise transaction_amount e customer_age.",
            category="Relações entre Variáveis"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_relationship"] = any(
                keyword in result.response.lower() 
                for keyword in ["relação", "relacionada", "relationship", "correlação", "correlation"]
            )
            result.validation_results["mentions_variables"] = any(
                keyword in result.response.lower() 
                for keyword in ["amount", "age", "valor", "idade"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 80
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_relationship"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_correlacao(self, orchestrator, data_processor):
        """Existe correlação entre elas?"""
        result = EDATestResult(
            question="Existe correlação entre as variáveis numéricas? Calcule e interprete.",
            category="Relações entre Variáveis"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_correlation"] = any(
                keyword in result.response.lower() 
                for keyword in ["correlação", "correlation", "coef", "pearson"]
            )
            result.validation_results["has_numeric_values"] = any(
                char.isdigit() or char == '-' or char == '.' for char in result.response
            )
            result.validation_results["is_interpretative"] = len(result.response) > 80
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_correlation"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"
    
    def test_influencia_variaveis(self, orchestrator, data_processor):
        """Quais variáveis parecem ter maior ou menor influência?"""
        result = EDATestResult(
            question="Quais variáveis parecem ter maior influência na detecção de fraude (is_fraud)?",
            category="Relações entre Variáveis"
        )
        
        try:
            import time
            start = time.time()
            
            response = orchestrator.process({
                "query": result.question,
                "context": {"data_processor": data_processor}
            })
            
            result.execution_time = time.time() - start
            result.response = response.get("content", str(response))
            
            # Validações
            result.validation_results["has_response"] = bool(result.response)
            result.validation_results["mentions_influence"] = any(
                keyword in result.response.lower() 
                for keyword in ["influência", "influence", "importância", "relevante", "importance"]
            )
            result.validation_results["mentions_fraud"] = any(
                keyword in result.response.lower() 
                for keyword in ["fraude", "fraud", "is_fraud"]
            )
            result.validation_results["mentions_variables"] = any(
                keyword in result.response.lower() 
                for keyword in ["amount", "age", "score", "hour", "purchase"]
            )
            result.validation_results["is_interpretative"] = len(result.response) > 100
            
            result.success = (
                result.validation_results["has_response"] and
                result.validation_results["mentions_influence"]
            )
            
        except Exception as e:
            result.error = e
            result.success = False
        
        logger.info(f"{'✅' if result.success else '❌'} {result.question}: {result.success}")
        assert result.success, f"Falhou: {result.error}"


# Fixture para coletar resultados
@pytest.fixture(scope="session", autouse=True)
def test_results_collector():
    """Coleta resultados de todos os testes para geração do sumário."""
    results = []
    
    yield results
    
    # Gerar sumário ao final de todos os testes
    generate_test_summary(results)


def generate_test_summary(results: List[EDATestResult]):
    """Gera sumário consolidado dos testes."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    summary_path = REPORTS_DIR / "test_eda_summary.md"
    
    # Calcular estatísticas
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Agrupar por categoria
    by_category = {}
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = []
        by_category[result.category].append(result)
    
    # Gerar relatório Markdown
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Sumário de Testes EDA - FASE 2
Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Resumo Executivo

- **Total de Testes**: {total_tests}
- **Testes Aprovados**: {passed_tests} ✅
- **Testes Falhados**: {failed_tests} ❌
- **Taxa de Sucesso**: {success_rate:.1f}%

## Resultados por Categoria

""")
        
        for category, category_results in by_category.items():
            passed = sum(1 for r in category_results if r.success)
            total = len(category_results)
            rate = (passed / total * 100) if total > 0 else 0
            
            f.write(f"""### {category}
- Testes: {total}
- Aprovados: {passed} ({rate:.1f}%)

""")
            
            for result in category_results:
                status = "✅" if result.success else "❌"
                f.write(f"""#### {status} {result.question}
- **Status**: {'APROVADO' if result.success else 'FALHOU'}
- **Tempo de Execução**: {result.execution_time:.2f}s
- **Validações**:
""")
                for key, value in result.validation_results.items():
                    f.write(f"  - {key}: {value}\n")
                
                if result.error:
                    f.write(f"- **Erro**: {result.error}\n")
                
                f.write("\n")
        
        f.write(f"""
## Detalhes Técnicos

- **Dataset**: data/synthetic_eda_test.csv
- **Linhas**: 100
- **Colunas**: 10 (6 numéricas, 4 categóricas)
- **Timestamp**: {timestamp}

## Conclusão

{'✅ TODOS OS TESTES PASSARAM!' if failed_tests == 0 else f'⚠️ {failed_tests} teste(s) falharam. Revisar logs para detalhes.'}
""")
    
    logger.info(f"📊 Sumário gerado: {summary_path}")
    logger.info(f"✅ Taxa de sucesso: {success_rate:.1f}% ({passed_tests}/{total_tests})")


if __name__ == "__main__":
    # Executar testes com pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])
