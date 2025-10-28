"""
Testes complementares para o classificador semântico de intenção (IntentClassifier)
Valida robustez, fallback, acionamento de módulos e metadata.
"""
import pytest
from unittest.mock import MagicMock

# Importa o classificador e dependências reais do sistema
from src.analysis.intent_classifier import IntentClassifier, AnalysisIntent
from src.llm.langchain_manager import get_langchain_llm_manager

@pytest.fixture(scope="module")
def intent_classifier():
    llm_manager = get_langchain_llm_manager()
    llm = llm_manager.get_llm()
    return IntentClassifier(llm)

def test_statistical_intent(intent_classifier):
    pergunta = "Qual a média e desvio padrão da coluna valor?"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.STATISTICAL
    assert result.confidence > 0.5

def test_frequency_intent(intent_classifier):
    pergunta = "Quais são os valores mais comuns em categoria?"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.FREQUENCY
    assert result.confidence > 0.5

def test_correlation_intent(intent_classifier):
    pergunta = "Existe correlação entre idade e renda?"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.CORRELATION
    assert result.confidence > 0.5

def test_outliers_intent(intent_classifier):
    pergunta = "Há outliers em transações?"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.OUTLIERS
    assert result.confidence > 0.5

def test_clustering_intent(intent_classifier):
    pergunta = "Agrupe os dados por similaridade"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.CLUSTERING
    assert result.confidence > 0.5

def test_comparison_mixed_intent(intent_classifier):
    pergunta = "Compare a variabilidade entre clusters ao longo do tempo"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.COMPARISON
    # Deve identificar secundárias relevantes
    secundarias = [i.value for i in result.secondary_intents]
    assert "clustering" in secundarias or "temporal" in secundarias
    assert result.confidence > 0.5

def test_visualization_intent(intent_classifier):
    pergunta = "Mostre um gráfico de dispersão"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.VISUALIZATION
    assert result.confidence > 0.5

def test_general_intent(intent_classifier):
    pergunta = "O que há de interessante neste dataset?"
    result = intent_classifier.classify(pergunta)
    assert result.primary_intent == AnalysisIntent.GENERAL
    assert result.confidence > 0.5

def test_fallback_low_confidence(intent_classifier):
    pergunta = "asdfghjklqwertyuiopzxcvbnm"  # Pergunta sem sentido
    result = intent_classifier.classify(pergunta)
    assert result.confidence < 0.5
    assert result.primary_intent == AnalysisIntent.GENERAL

def test_metadata_fields(intent_classifier):
    pergunta = "Qual a média da coluna idade?"
    result = intent_classifier.classify(pergunta)
    # Metadata deve conter query, timestamp e resposta do LLM
    assert "query" in result.metadata
    assert "timestamp" in result.metadata
    assert "llm_response" in result.metadata
    assert result.metadata["query"] == pergunta


def test_parser_multiple_json_blocks():
    """Valida extração de múltiplos JSONs e ignora texto extra."""
    from src.analysis.intent_classifier import IntentClassifier
    parser = IntentClassifier(llm=MagicMock())
    resposta = '''
    Aqui está o resultado:
    {"primary_intent": "STATISTICAL", "secondary_intents": [], "confidence": 0.9}
    Algum texto extra
    {"primary_intent": "CLUSTERING", "secondary_intents": [], "confidence": 0.8}
    '''
    jsons = parser._extract_json_objects(resposta)
    assert len(jsons) == 2
    assert jsons[0]["primary_intent"] == "STATISTICAL"
    assert jsons[1]["primary_intent"] == "CLUSTERING"


def test_parser_invalid_json_ignored():
    """Valida que blocos inválidos são ignorados e apenas JSONs válidos são retornados."""
    from src.analysis.intent_classifier import IntentClassifier
    parser = IntentClassifier(llm=MagicMock())
    resposta = '{"primary_intent": "STATISTICAL", "secondary_intents": [], "confidence": 0.9} texto {invalid json}'
    jsons = parser._extract_json_objects(resposta)
    assert len(jsons) == 1
    assert jsons[0]["primary_intent"] == "STATISTICAL"


def test_reprompt_on_invalid_response(monkeypatch):
    """Valida que o re-prompt é acionado e retorna resposta válida após erro inicial."""
    from src.analysis.intent_classifier import IntentClassifier, AnalysisIntent
    # Simula LLM retornando resposta inválida na 1a chamada e válida na 2a
    class FakeLLM:
        def __init__(self):
            self.calls = 0
        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return type('Resp', (), {"content": "texto solto sem json"})()
            return type('Resp', (), {"content": '{"primary_intent": "FREQUENCY", "secondary_intents": [], "confidence": 0.8}'})()
    llm = FakeLLM()
    classifier = IntentClassifier(llm)
    result = classifier.classify("Quais são os valores mais comuns?", max_retries=1)
    assert result.primary_intent == AnalysisIntent.FREQUENCY
    assert result.confidence == 0.8
    assert llm.calls == 2
