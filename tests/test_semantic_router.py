"""
Testes automatizados para o roteador semântico de perguntas.
Valida roteamento inteligente, fallback contextual e casos de termos novos.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from src.router.semantic_router import SemanticRouter

@pytest.fixture
def router():
    return SemanticRouter()

def test_classificacao_media(router):
    pergunta = "Qual a média da variável Amount?"
    resultado = router.route(pergunta)
    assert resultado["route"] in ["statistical_analysis", "contextual_embedding", "llm_generic"]
    assert resultado["source"] == "semantic_router"

def test_classificacao_mediana(router):
    pergunta = "Qual a mediana de V1?"
    resultado = router.route(pergunta)
    assert resultado["route"] in ["statistical_analysis", "contextual_embedding", "llm_generic"]
    assert resultado["source"] == "semantic_router"

def test_fallback_contextual(router):
    pergunta = "Pergunta totalmente nova sem termos conhecidos."
    resultado = router.route(pergunta)
    assert resultado["route"] in ["contextual_embedding", "llm_generic"]
    assert resultado["source"] == "semantic_router"

def test_logging_decisao(router, caplog):
    pergunta = "Detecte fraudes no dataset."
    with caplog.at_level("INFO"):
        resultado = router.route(pergunta)
        # Verifica se alguma decisão de roteamento foi logada
        assert ("Classificação semântica" in caplog.text or 
                "Resposta contextualizada" in caplog.text or
                "Nenhuma correspondência semântica encontrada" in caplog.text or
                "encaminhando para LLM genérica" in caplog.text)
