import pytest
from unittest.mock import Mock, MagicMock
from src.router.query_refiner import QueryRefiner, RefinementResult
from typing import List


class FakeEmbeddingResult:
    def __init__(self, embedding: List[float]):
        self.embedding = embedding


class FakeGenerator:
    """Gera embeddings sintéticos que codificam a query em embedding[0]."""
    def generate_embedding(self, text: str):
        # Determine marker based on heuristics used by QueryRefiner._heuristic_refine
        # Make queries containing 'média' produce a higher base marker so immediate success is possible
        if 'incluir exemplos' in text:
            marker = 2.0
        elif 'detalhes por variável' in text:
            marker = 1.0
        elif 'média' in text or 'media' in text:
            marker = 1.0
        elif 'paraphrase' in text.lower():
            # Paraphrases get higher marker to simulate success
            marker = 2.5
        else:
            marker = 0.0
        emb = [marker] + [0.0] * 383
        return FakeEmbeddingResult(emb)


class DummyVectorStore:
    """Retorna similarities based on embedding[0]."""
    class R:
        def __init__(self, score):
            self.similarity_score = score

    def search_similar(self, query_embedding, similarity_threshold=0.0, limit=10):
        marker = query_embedding[0]
        if marker == 0.0:
            score = 0.3
        elif marker == 1.0:
            score = 0.6
        elif marker == 2.0:
            score = 0.75
        elif marker == 2.5:
            # Paraphrases get high similarity
            score = 0.85
        else:
            score = 0.0
        return [DummyVectorStore.R(score)]


class FakeLLMResponse:
    """Mock LLM response for paraphrases."""
    def __init__(self, content: str, model: str = "fake-model"):
        self.content = content
        self.model = model
        self.success = True
        self.error = None
        self.tokens_used = 100
        self.processing_time = 0.5


class FakeLLMManager:
    """Mock LLM Manager for testing paraphrases."""
    def __init__(self):
        from src.llm.manager import LLMProvider
        self.active_provider = LLMProvider.GROQ
        
    def chat(self, prompt: str, config=None, system_prompt=None):
        # Gera paraphrases fake baseadas no prompt
        paraphrases = [
            "PARAPHRASE 1: Como está a distribuição das variáveis? (histogramas)",
            "PARAPHRASE 2: Mostre a dispersão de cada coluna através de gráficos",
            "PARAPHRASE 3: Qual o comportamento de distribuição por variável?"
        ]
        content = "\n".join(paraphrases)
        return FakeLLMResponse(content, model="groq:llama-3.1-8b-instant")
    
    def _get_default_model(self, provider):
        return "llama-3.1-8b-instant"


def test_refiner_success_immediate():
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=False)  # Desabilitar paraphrase para teste simples
    # inject fakes
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.5

    result: RefinementResult = refiner.refine_query('Qual a média?')
    assert result.success is True
    assert result.iterations == 1
    assert result.similarity_to_best >= 0.5
    assert result.paraphrase_used is False


def test_refiner_refines_until_success():
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=False)  # Desabilitar paraphrase
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.72
    refiner.max_iterations = 3

    result: RefinementResult = refiner.refine_query('Qual a variabilidade dos dados?')
    assert result.success is True
    assert result.iterations <= 3
    assert result.similarity_to_best >= 0.72
    assert result.paraphrase_used is False


def test_refiner_with_paraphrases_success():
    """Testa que paraphrases via LLM aumentam recall."""
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=True, num_paraphrases=3)
    
    # Inject fakes
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.72
    refiner.llm_manager = FakeLLMManager()
    
    # Query original tem baixa similaridade (0.3)
    result: RefinementResult = refiner.refine_query('Qual a distribuição dos dados?')
    
    # Deve ter usado paraphrase para atingir sucesso
    assert result.paraphrase_used is True
    assert result.num_paraphrases_tested == 3
    assert result.best_paraphrase_similarity >= 0.72
    assert result.llm_model_id is not None
    assert result.success is True
    assert len(result.paraphrases_generated) == 3


def test_refiner_paraphrases_fallback_to_heuristics():
    """Testa que se paraphrases falharem, continua com heurísticas."""
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=True, num_paraphrases=3)
    
    # Inject fakes
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.95  # Limiar muito alto para paraphrases
    refiner.max_iterations = 3
    
    # Mock LLM que gera paraphrases ruins
    class BadLLMManager:
        def __init__(self):
            from src.llm.manager import LLMProvider
            self.active_provider = LLMProvider.GROQ
        def chat(self, prompt, config=None, system_prompt=None):
            # Paraphrases sem marcador especial (baixa similarity)
            return FakeLLMResponse("Bad paraphrase 1\nBad paraphrase 2\nBad paraphrase 3")
        def _get_default_model(self, provider):
            return "fake-model"
    
    refiner.llm_manager = BadLLMManager()
    
    result: RefinementResult = refiner.refine_query('Qual a distribuição?')
    
    # Paraphrases testadas mas falharam
    assert result.num_paraphrases_tested == 3
    assert result.best_paraphrase_similarity < 0.95
    # Deve ter continuado com heurísticas (iterations > 1)
    assert result.iterations > 1
    # Paraphrase não foi usado (não atingiu limiar)
    assert result.paraphrase_used is False


def test_refiner_paraphrases_disabled():
    """Testa que com enable_paraphrase=False, nunca usa LLM."""
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=False)
    
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.72
    
    result: RefinementResult = refiner.refine_query('Qual a distribuição?')
    
    # Nunca deve usar paraphrase
    assert result.paraphrase_used is False
    assert result.num_paraphrases_tested == 0
    assert result.llm_model_id is None
    assert len(result.paraphrases_generated) == 0


def test_refiner_no_infinite_loop():
    """Testa que refiner nunca entra em loop infinito."""
    store = DummyVectorStore()
    refiner = QueryRefiner(enable_paraphrase=True, max_iterations=3)
    
    refiner.embedding_gen = FakeGenerator()
    refiner.memory = store
    refiner.similarity_threshold = 0.99  # Impossível de atingir
    refiner.llm_manager = FakeLLMManager()
    
    result: RefinementResult = refiner.refine_query('Query impossível')
    
    # Deve terminar mesmo sem sucesso
    assert result.iterations <= 3
    assert result.success is False  # Não conseguiu atingir limiar

