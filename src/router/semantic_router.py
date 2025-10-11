"""
Módulo: semantic_router.py
Pipeline avançado de roteamento semântico para perguntas do backend multiagente EDA AI Minds.
Utiliza embeddings, consulta vetorial, fallback inteligente e validação Pydantic.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError

from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
from src.embeddings.vector_store import VectorStore
from src.utils.logging_config import get_logger
from src.router.semantic_ontology import StatisticalOntology
from src.router.query_refiner import QueryRefiner

logger = get_logger(__name__)

# Definição de entidades/intenção via Pydantic
class QuestionIntent(BaseModel):
    category: str
    entities: List[str]
    confidence: float

# Inicialização do generator e vectorstore usando provider do projeto
# VectorStore usa o cliente Supabase global já configurado
embedding_generator = EmbeddingGenerator(provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
vector_store = VectorStore()


class SemanticRouter:
    """
    Pipeline de roteamento semântico:
    1. Normaliza pergunta
    2. Gera embedding via provider Groq
    3. Consulta vetorial para identificar intenção/categoria
    4. Valida entidades com Pydantic
    5. Fallback contextual antes de LLM genérica
    6. Logging estruturado
    """
    def __init__(self):
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        self.logger = logger

    def normalize(self, question: str) -> str:
        """
        Normaliza a pergunta do usuário para processamento semântico.
        Remove espaços, converte para minúsculas e aplica limpeza básica.
        Args:
            question: Pergunta original do usuário
        Returns:
            Pergunta normalizada
        """
        return question.strip().lower()

    def embed_question(self, question: str) -> List[float]:
        """
        Gera embedding vetorial da pergunta usando o provider configurado.
        Args:
            question: Pergunta normalizada
        Returns:
            Vetor de embedding (List[float])
        """
        result = self.embedding_generator.generate_embedding(question)
        return result.embedding

    def search_with_expansion(self, question: str,
                              base_threshold: float = 0.7,
                              base_limit: int = 3) -> List["VectorSearchResult"]:
        """Tenta buscar no vector store usando a query original e variações geradas pela ontologia.

        Estratégia:
        1. Buscar com a query original (threshold/base_limit)
        2. Gerar variações simples via StatisticalOntology.generate_simple_expansions
        3. Para cada variação, gerar embedding e buscar com threshold reduzido e limit aumentado
        4. Agregar resultados ordenando por similaridade
        """
        # 1) search original
        embedding = self.embed_question(question)
        results = self.vector_store.search_similar(
            query_embedding=embedding,
            similarity_threshold=base_threshold,
            limit=base_limit
        )

        if results:
            return results

        # 2) tentar refinamento iterativo via QueryRefiner (histórico)
        try:
            refiner = QueryRefiner(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
            ref_result = refiner.refine_query(question)
            if ref_result and ref_result.success:
                emb = ref_result.embedding
                alt_results = self.vector_store.search_similar(
                    query_embedding=emb,
                    similarity_threshold=base_threshold,
                    limit=base_limit
                )
                if alt_results:
                    return alt_results
        except Exception as e:
            self.logger.warning(f"QueryRefiner falhou: {e}")

        # 3) expand queries and retry with relaxed params
        variations = StatisticalOntology.generate_simple_expansions(question)
        aggregated = []
        seen_ids = set()

        for var in variations:
            try:
                emb = self.embed_question(var)
                # relaxar threshold e aumentar limite
                alt_results = self.vector_store.search_similar(
                    query_embedding=emb,
                    similarity_threshold=max(0.5, base_threshold - 0.15),
                    limit=min(10, base_limit * 3)
                )

                for r in alt_results:
                    if r.embedding_id not in seen_ids:
                        aggregated.append(r)
                        seen_ids.add(r.embedding_id)
            except Exception:
                continue

        # ordenar por similaridade e retornar os top base_limit
        aggregated.sort(key=lambda x: x.similarity_score, reverse=True)
        return aggregated[:base_limit]

    def classify_intent(self, question: str) -> Optional[QuestionIntent]:
        """
        Classifica a intenção da pergunta via busca vetorial e validação Pydantic.
        Args:
            question: Pergunta normalizada
        Returns:
            Instância QuestionIntent ou None se não houver correspondência
        """
        # Usar busca com expansão para melhorar recall
        results = self.search_with_expansion(question, base_threshold=0.7, base_limit=3)
        if not results:
            self.logger.warning("Nenhuma correspondência semântica encontrada para a pergunta.")
            return None
        top = results[0]
        try:
            intent = QuestionIntent(
                category=top.metadata.get('category', 'unknown'),
                entities=top.metadata.get('entities', []),
                confidence=top.similarity_score
            )
            self.logger.info(f"Classificação semântica: {intent}")
            return intent
        except ValidationError as e:
            self.logger.error(f"Erro na validação Pydantic: {e}")
            return None

    def fallback_contextual(self, question: str) -> Optional[str]:
        """
        Busca resposta contextualizada via embeddings caso não haja classificação semântica.
        Args:
            question: Pergunta normalizada
        Returns:
            Texto da resposta contextual ou None
        """
        # tentar busca com expansão para melhorar recall
        results = self.search_with_expansion(question, base_threshold=0.6, base_limit=1)
        if results:
            resposta = results[0].chunk_text
            self.logger.info("Resposta contextualizada encontrada via embeddings.")
            return resposta
        self.logger.info("Nenhuma resposta contextualizada encontrada, encaminhando para LLM genérica.")
        return None

    def route(self, question: str) -> Dict[str, Any]:
        """
        Pipeline completo de roteamento semântico para perguntas do usuário.
        Executa normalização, classificação, fallback e logging.
        Args:
            question: Pergunta original do usuário
        Returns:
            Dicionário com rota, entidades, confiança e fonte
        """
        q_norm = self.normalize(question)
        intent = self.classify_intent(q_norm)
        if intent:
            return {
                "route": intent.category,
                "entities": intent.entities,
                "confidence": intent.confidence,
                "source": "semantic_router"
            }
        resposta = self.fallback_contextual(q_norm)
        if resposta:
            return {
                "route": "contextual_embedding",
                "response": resposta,
                "source": "semantic_router"
            }
        return {
            "route": "llm_generic",
            "response": None,
            "source": "semantic_router"
        }

# Exemplo básico de uso
def exemplo_roteamento():
    router = SemanticRouter()
    perguntas = [
        "Qual a média da variável Amount?",
        "Detecte fraudes no dataset.",
        "Qual a mediana de V1?",
        "Explique a distribuição de V2."
    ]
    for pergunta in perguntas:
        resultado = router.route(pergunta)
        print(f"Pergunta: {pergunta}\nRoteamento: {resultado}\n---")

if __name__ == "__main__":
    exemplo_roteamento()
