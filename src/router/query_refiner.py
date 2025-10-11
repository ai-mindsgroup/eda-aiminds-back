"""
Pipeline de refinamento de queries para busca vetorial.

Funcionalidades:
- Recebe uma query, gera embedding
- Compara com embeddings de queries anteriores que tiveram sucesso (memória)
- **NOVO:** Gera paraphrases via LLM (LangChain) para aumentar recall
- Se similaridade abaixo do limiar, gera uma nova query refinada (simplesmente por heurística + ontologia)
- Repete até atingir qualidade mínima ou número máximo de iterações

Integra com: EmbeddingGenerator, Memory (Supabase), LLM Manager (LangChain) e Logging
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import time
import re

from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
from src.embeddings.vector_store import VectorStore
from src.utils.logging_config import get_logger
from src.router.semantic_ontology import StatisticalOntology

# Import LLM Manager para paraphrases
try:
    from src.llm.manager import LLMManager, LLMConfig
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMManager = None
    LLMConfig = None

logger = get_logger(__name__)


@dataclass
class RefinementResult:
    query: str
    embedding: List[float]
    similarity_to_best: float
    iterations: int
    success: bool
    # Métricas de paraphrase (novo)
    paraphrase_used: bool = False
    num_paraphrases_tested: int = 0
    best_paraphrase_similarity: float = 0.0
    llm_model_id: Optional[str] = None
    paraphrase_elapsed_time: float = 0.0
    paraphrases_generated: List[str] = field(default_factory=list)


class QueryRefiner:
    """Implementa loop de refinamento de queries baseado em embeddings históricos.

    Nota: essa implementação usa heurísticas simples (ontologia + pequenas substituições)
    e busca por queries históricas salvas na memória (SupabaseMemory) que tenham sido
    marcadas como bem-sucedidas.
    """

    def __init__(self,
                 embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                 memory: Optional[VectorStore] = None,
                 similarity_threshold: float = 0.72,
                 max_iterations: int = 3,
                 enable_paraphrase: bool = True,
                 num_paraphrases: int = 3):
        self.embedding_gen = EmbeddingGenerator(provider=embedding_provider)
        # usar VectorStore (síncrono) para histórico de queries/embeddings
        self.memory = memory or VectorStore()
        self.similarity_threshold = similarity_threshold
        self.max_iterations = max_iterations
        
        # Paraphrase via LLM (novo)
        self.enable_paraphrase = enable_paraphrase and LLM_AVAILABLE
        self.num_paraphrases = num_paraphrases
        self.llm_manager = None
        
        if self.enable_paraphrase:
            try:
                self.llm_manager = LLMManager()
                logger.info("🔤 QueryRefiner: Paraphrase via LLM habilitado (N=%d)", self.num_paraphrases)
            except Exception as e:
                logger.warning("⚠️ Falha ao inicializar LLM Manager para paraphrases: %s", str(e))
                self.enable_paraphrase = False
        else:
            if not LLM_AVAILABLE:
                logger.warning("⚠️ LLM Manager indisponível - paraphrases desabilitados")

    def _get_best_historical_similarity(self, query_emb: List[float]) -> float:
        """Consulta a memória por queries históricas e retorna a maior similaridade encontrada."""
        try:
            # VectorStore.search_similar retorna VectorSearchResult com similarity_score
            results = self.memory.search_similar(query_embedding=query_emb, similarity_threshold=0.0, limit=10)
            if not results:
                return 0.0
            best = max(r.similarity_score for r in results)
            return best
        except Exception as e:
            logger.warning("Falha ao buscar histórico de queries: %s", str(e))
            return 0.0

    def _heuristic_refine(self, query: str, iteration: int) -> str:
        """Gera uma refinamento simples da query usando a ontologia e regras básicas."""
        # usar ontologia para detectar intenção e acrescentar termos relevantes
        parts = StatisticalOntology.expand_query(query)
        refined = query
        # Em iterações posteriores, acrescentar termos explícitos
        if parts.get('variability'):
            refined = refined + ' desvio padrão variância'
        if parts.get('central_tendency'):
            refined = refined + ' média mediana'
        if parts.get('interval'):
            refined = refined + ' mínimo máximo range'

        # small change per iteration to diversify
        if iteration == 1:
            refined = refined + ' detalhes por variável'
        elif iteration >= 2:
            refined = refined + ' incluir exemplos e colunas específicas'

        return refined
    
    def _generate_paraphrases_via_llm(self, query: str) -> List[str]:
        """Gera N paraphrases da query usando LLM via LangChain.
        
        Args:
            query: Query original
            
        Returns:
            Lista de paraphrases (pode estar vazia se falhar)
        """
        if not self.enable_paraphrase or not self.llm_manager:
            return []
        
        try:
            # Prompt seguro para paraphrase
            system_prompt = (
                "Você é um especialista em reformulação de perguntas técnicas sobre análise de dados estatísticos. "
                "Sua tarefa é gerar variações linguísticas que mantenham fielmente a intenção original."
            )
            
            user_prompt = f"""Reformule a seguinte pergunta de análise de dados, mantendo fielmente a intenção original, mas usando palavras diferentes, sinônimos ou estruturas alternativas do domínio estatístico:

"{query}"

Produza exatamente {self.num_paraphrases} variações distintas, uma por linha, sem numeração ou marcadores."""
            
            # Configuração LLM: temperatura baixa para manter coerência
            config = LLMConfig(
                temperature=0.3,  # baixa para evitar criatividade excessiva
                max_tokens=512,
                top_p=0.9
            )
            
            logger.info("🔤 Gerando %d paraphrases via LLM...", self.num_paraphrases)
            start = time.time()
            
            response = self.llm_manager.chat(
                prompt=user_prompt,
                config=config,
                system_prompt=system_prompt
            )
            
            elapsed = time.time() - start
            
            if not response.success:
                logger.warning("⚠️ Falha ao gerar paraphrases: %s", response.error)
                return []
            
            # Parsear resposta: espera-se N linhas não-vazias
            paraphrases = []
            lines = response.content.strip().split('\n')
            for line in lines:
                # Remover numeração/marcadores se presentes (ex: "1.", "•", etc)
                cleaned = re.sub(r'^[\d\.\-\*•\s]+', '', line).strip()
                if cleaned and len(cleaned) > 10:  # filtrar linhas muito curtas
                    paraphrases.append(cleaned)
            
            # Limitar ao número solicitado
            paraphrases = paraphrases[:self.num_paraphrases]
            
            logger.info(
                "✅ Paraphrases geradas: %d variações em %.2fs usando modelo %s",
                len(paraphrases), elapsed, response.model
            )
            
            for i, p in enumerate(paraphrases, 1):
                logger.debug("  Paraphrase %d: %s", i, p[:80] + ('...' if len(p) > 80 else ''))
            
            return paraphrases
            
        except Exception as e:
            logger.error("❌ Erro ao gerar paraphrases via LLM: %s", str(e))
            return []
    
    def _test_paraphrases(self, paraphrases: List[str]) -> Dict[str, Any]:
        """Testa cada paraphrase na busca vetorial e retorna a melhor.
        
        Args:
            paraphrases: Lista de queries parafraseadas
            
        Returns:
            Dict com best_query, best_embedding, best_similarity, tested_count
        """
        if not paraphrases:
            return {
                'best_query': None,
                'best_embedding': None,
                'best_similarity': 0.0,
                'tested_count': 0
            }
        
        best_similarity = 0.0
        best_query = None
        best_embedding = None
        
        logger.info("🔍 Testando %d paraphrases na busca vetorial...", len(paraphrases))
        
        for i, paraphrase in enumerate(paraphrases, 1):
            try:
                # Gerar embedding para paraphrase
                emb_result = self.embedding_gen.generate_embedding(paraphrase)
                query_emb = emb_result.embedding
                
                # Buscar similaridade com histórico
                similarity = self._get_best_historical_similarity(query_emb)
                
                logger.debug(
                    "  Paraphrase %d: similarity=%.3f query='%s'",
                    i, similarity, paraphrase[:60] + ('...' if len(paraphrase) > 60 else '')
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_query = paraphrase
                    best_embedding = query_emb
                    
            except Exception as e:
                logger.warning("⚠️ Erro ao testar paraphrase %d: %s", i, str(e))
                continue
        
        if best_query:
            logger.info(
                "✅ Melhor paraphrase: similarity=%.3f query='%s'",
                best_similarity, best_query[:80] + ('...' if len(best_query) > 80 else '')
            )
        else:
            logger.warning("⚠️ Nenhuma paraphrase produziu resultado válido")
        
        return {
            'best_query': best_query,
            'best_embedding': best_embedding,
            'best_similarity': best_similarity,
            'tested_count': len(paraphrases)
        }

    def refine_query(self, original_query: str) -> RefinementResult:
        """Executa o loop de refinamento com paraphrases via LLM.
        
        Fluxo:
        1. Testa query original
        2. Se falhar E paraphrase habilitado: gera paraphrases via LLM e testa cada uma
        3. Se melhor paraphrase atingir limiar: retorna sucesso
        4. Se paraphrases falharem: continua com heurísticas (ontologia)
        5. Se tudo falhar: retorna última tentativa com success=False

        Retorna RefinementResult com dados da última iteração e métricas de paraphrase.
        """
        start = time.time()
        query = original_query
        iterations = 0
        success = False
        best_similarity = 0.0
        
        # Métricas de paraphrase
        paraphrase_used = False
        num_paraphrases_tested = 0
        best_paraphrase_similarity = 0.0
        llm_model_id = None
        paraphrase_elapsed_time = 0.0
        paraphrases_generated = []
        query_emb = []

        try:
            # === ETAPA 1: Testar query original ===
            iterations += 1
            emb_result = self.embedding_gen.generate_embedding(original_query)
            query_emb = emb_result.embedding
            best_similarity = self._get_best_historical_similarity(query_emb)
            
            logger.info(
                "[QueryRefiner] Iter %d (original): best_historical_similarity=%.3f for query='%s'",
                iterations, best_similarity, original_query
            )
            
            if best_similarity >= self.similarity_threshold:
                success = True
                elapsed = time.time() - start
                logger.info(
                    "[QueryRefiner] ✅ Query original atingiu limiar (%.3f >= %.3f) - sem necessidade de refinamento",
                    best_similarity, self.similarity_threshold
                )
                return RefinementResult(
                    query=original_query,
                    embedding=query_emb,
                    similarity_to_best=best_similarity,
                    iterations=iterations,
                    success=success
                )
            
            # === ETAPA 2: Tentar paraphrases via LLM ===
            if self.enable_paraphrase and self.llm_manager:
                logger.info("🔤 Query original não atingiu limiar - tentando paraphrases via LLM...")
                paraphrase_start = time.time()
                
                # Gerar paraphrases
                paraphrases_generated = self._generate_paraphrases_via_llm(original_query)
                
                if paraphrases_generated:
                    # Testar cada paraphrase
                    paraphrase_result = self._test_paraphrases(paraphrases_generated)
                    
                    num_paraphrases_tested = paraphrase_result['tested_count']
                    best_paraphrase_similarity = paraphrase_result['best_similarity']
                    
                    # Capturar modelo LLM usado
                    if self.llm_manager.active_provider:
                        llm_model_id = f"{self.llm_manager.active_provider.value}:{self.llm_manager._get_default_model(self.llm_manager.active_provider)}"
                    
                    paraphrase_elapsed_time = time.time() - paraphrase_start
                    
                    # Se melhor paraphrase atingiu limiar, usar
                    if best_paraphrase_similarity >= self.similarity_threshold:
                        query = paraphrase_result['best_query']
                        query_emb = paraphrase_result['best_embedding']
                        best_similarity = best_paraphrase_similarity
                        paraphrase_used = True
                        success = True
                        
                        logger.info(
                            "✅ Paraphrase bem-sucedida: similarity=%.3f (limiar=%.3f) em %.2fs",
                            best_similarity, self.similarity_threshold, paraphrase_elapsed_time
                        )
                        
                        elapsed = time.time() - start
                        return RefinementResult(
                            query=query,
                            embedding=query_emb,
                            similarity_to_best=best_similarity,
                            iterations=iterations,
                            success=success,
                            paraphrase_used=paraphrase_used,
                            num_paraphrases_tested=num_paraphrases_tested,
                            best_paraphrase_similarity=best_paraphrase_similarity,
                            llm_model_id=llm_model_id,
                            paraphrase_elapsed_time=paraphrase_elapsed_time,
                            paraphrases_generated=paraphrases_generated
                        )
                    else:
                        logger.warning(
                            "⚠️ Paraphrases falharam (melhor=%.3f < limiar=%.3f) - continuando com heurísticas",
                            best_paraphrase_similarity, self.similarity_threshold
                        )
                else:
                    logger.warning("⚠️ Nenhuma paraphrase gerada - continuando com heurísticas")
            
            # === ETAPA 3: Heurísticas (ontologia) ===
            logger.info("🔄 Tentando refinamento heurístico (ontologia + termos)...")
            
            while iterations < self.max_iterations:
                iterations += 1
                
                # Refinar query usando heurísticas
                query = self._heuristic_refine(original_query, iterations)
                
                # Gerar embedding
                emb_result = self.embedding_gen.generate_embedding(query)
                query_emb = emb_result.embedding

                # Comparar com histórico
                best_similarity = self._get_best_historical_similarity(query_emb)
                logger.info(
                    "[QueryRefiner] Iter %d (heuristic): best_historical_similarity=%.3f for query='%s'",
                    iterations, best_similarity, query
                )

                if best_similarity >= self.similarity_threshold:
                    success = True
                    break

            elapsed = time.time() - start
            logger.info(
                "[QueryRefiner] refine_query completed: success=%s iterations=%d elapsed=%.2fs paraphrase_used=%s",
                success, iterations, elapsed, paraphrase_used
            )
            
            return RefinementResult(
                query=query,
                embedding=query_emb,
                similarity_to_best=best_similarity,
                iterations=iterations,
                success=success,
                paraphrase_used=paraphrase_used,
                num_paraphrases_tested=num_paraphrases_tested,
                best_paraphrase_similarity=best_paraphrase_similarity,
                llm_model_id=llm_model_id,
                paraphrase_elapsed_time=paraphrase_elapsed_time,
                paraphrases_generated=paraphrases_generated
            )

        except Exception as e:
            logger.error("[QueryRefiner] erro durante refine_query: %s", str(e))
            return RefinementResult(
                query=original_query,
                embedding=[],
                similarity_to_best=0.0,
                iterations=iterations,
                success=False,
                paraphrase_used=paraphrase_used,
                num_paraphrases_tested=num_paraphrases_tested,
                best_paraphrase_similarity=best_paraphrase_similarity,
                llm_model_id=llm_model_id,
                paraphrase_elapsed_time=paraphrase_elapsed_time,
                paraphrases_generated=paraphrases_generated
            )
