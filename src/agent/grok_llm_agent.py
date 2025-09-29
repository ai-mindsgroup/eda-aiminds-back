"""Agente LLM usando Grok (xAI)
================================

Este agente utiliza o Grok da xAI para análises inteligentes e insights.
Integra com o sistema multiagente para fornecer capacidades avançadas de NLP.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from typing import Dict, Any, Optional, List
import json
from dataclasses import dataclass
import requests

from src.agent.base_agent import BaseAgent, AgentError
from src.settings import GROK_API_KEY
from src.utils.logging_config import get_logger

# Import condicional do sistema RAG
try:
    from src.embeddings.vector_store import VectorStore
    from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    VectorStore = None
    EmbeddingGenerator = None

logger = get_logger(__name__)


@dataclass
class GrokRequest:
    """Request para o Grok."""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    temperature: float = 0.3
    max_tokens: int = 1000
    system_prompt: Optional[str] = None


@dataclass 
class GrokResponse:
    """Resposta do Grok."""
    content: str
    usage: Dict[str, Any]
    model: str
    success: bool = True
    error: Optional[str] = None


class GrokLLMAgent(BaseAgent):
    """Agente que utiliza Grok (xAI) para análises inteligentes."""
    
    def __init__(self, model: str = "grok-3-mini"):
        super().__init__(
            name="grok_llm",
            description="Agente LLM usando Grok da xAI para análises inteligentes e insights"
        )
        
        self.model_name = model
        self.api_base = "https://api.x.ai/v1"
        
        # Verificar disponibilidade
        if not GROK_API_KEY:
            raise AgentError(
                self.name, 
                "GROK_API_KEY não configurado. Configure em configs/.env"
            )
        
        # Inicializar sistema RAG se disponível
        self.rag_enabled = False
        self.vector_store = None
        self.embedding_generator = None
        
        if RAG_AVAILABLE:
            try:
                self.vector_store = VectorStore()
                self.embedding_generator = EmbeddingGenerator(EmbeddingProvider.SENTENCE_TRANSFORMER)
                self.rag_enabled = True
                self.logger.info("RAG integrado ao Grok LLM Agent")
            except Exception as e:
                self.logger.warning(f"RAG não disponível: {e}")
        
        self.logger.info(f"Grok LLM inicializado: {model}")

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta usando busca RAG + Grok (sistema híbrido).
        
        Fluxo:
        1. Se RAG disponível, busca consultas similares no banco vetorial
        2. Se encontrar resposta relevante, usa ela (cache inteligente)  
        3. Se não encontrar, chama Grok
        4. Salva consulta + resposta LLM no banco vetorial
        
        Args:
            query: Consulta/prompt para o LLM
            context: Contexto adicional (dados, configurações, etc.)
            
        Returns:
            Resposta estruturada do LLM ou cache
        """
        try:
            # 1. BUSCAR NO CACHE VETORIAL (se disponível)
            if self.rag_enabled:
                cached_response = self._search_cached_response(query)
                if cached_response:
                    self.logger.info("💾 Usando resposta em cache (RAG)")
                    return self._build_response(
                        cached_response["content"],
                        metadata={
                            "model": "cache_rag", 
                            "llm_used": False,
                            "cache_used": True,
                            "similarity_score": cached_response.get("similarity", 0.0),
                            "success": True
                        }
                    )
            
            # 2. GERAR NOVA RESPOSTA COM GROK
            self.logger.info("🤖 Gerando nova resposta com Grok")
            
            # Preparar request
            grok_request = self._prepare_request(query, context)
            
            # Enviar para Grok
            response = self._call_grok(grok_request)
            
            # 3. SALVAR NO BANCO VETORIAL (se disponível)
            if self.rag_enabled and response.success:
                self._save_to_vector_store(query, response.content, context)
            
            # Processar resposta
            return self._build_response(
                response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "llm_used": True,
                    "cache_used": False,
                    "success": response.success
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erro no processamento LLM híbrido: {e}")
            return self._build_response(
                f"Erro no processamento: {str(e)}",
                metadata={"error": True, "llm_used": False, "cache_used": False}
            )

    def _prepare_request(self, query: str, context: Optional[Dict[str, Any]]) -> GrokRequest:
        """Prepara request para o LLM com contexto e system prompt."""
        
        # System prompt para análise de dados
        system_prompt = """Você é um especialista em análise de dados e detecção de fraudes.
        
Suas responsabilidades:
- Analisar dados CSV e identificar padrões
- Detectar anomalias e possíveis fraudes
- Fornecer insights estratégicos baseados em dados
- Explicar correlações e tendências
- Sugerir ações para melhorar segurança

Diretrizes:
- Seja preciso e baseie-se nos dados fornecidos
- Use linguagem técnica mas acessível
- Destaque descobertas importantes
- Forneça recomendações práticas
- Seja conciso mas completo
"""
        
        # Construir prompt com contexto
        if context:
            prompt_parts = [system_prompt, "\nContexto dos dados:"]
            
            # Adicionar informações do contexto
            if "file_path" in context:
                prompt_parts.append(f"Arquivo: {context['file_path']}")
            
            if "data_info" in context:
                data_info = context["data_info"]
                prompt_parts.append(f"Dimensões: {data_info.get('rows', 'N/A')} linhas × {data_info.get('columns', 'N/A')} colunas")
            
            if "fraud_data" in context:
                fraud_info = context["fraud_data"] 
                prompt_parts.append(f"Fraudes: {fraud_info.get('count', 0)} de {fraud_info.get('total', 0)} transações")
            
            # Adicionar consulta do usuário
            prompt_parts.extend(["\nConsulta do usuário:", query])
            
            full_prompt = "\n".join(prompt_parts)
        else:
            full_prompt = f"{system_prompt}\n\nConsulta: {query}"
        
        return GrokRequest(
            prompt=full_prompt,
            context=context,
            temperature=0.3,  # Mais determinístico para análise de dados
            max_tokens=1000
        )

    def _call_grok(self, request: GrokRequest) -> GrokResponse:
        """Chama Grok API."""
        try:
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "model": self.model_name,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extrair conteúdo
            content = data["choices"][0]["message"]["content"]
            
            # Metadados de uso
            usage = data.get("usage", {
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(request.prompt.split()) + len(content.split())
            })
            
            return GrokResponse(
                content=content,
                usage=usage,
                model=self.model_name,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Erro na chamada Grok: {e}")
            return GrokResponse(
                content=f"Erro na geração: {str(e)}",
                usage={},
                model=self.model_name,
                success=False,
                error=str(e)
            )

    def analyze_data_insights(self, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa dados e gera insights inteligentes."""
        
        # Construir prompt especializado para análise de dados
        prompt = f"""Analise os seguintes dados e forneça insights estratégicos:

RESUMO DOS DADOS:
{json.dumps(data_summary, indent=2, ensure_ascii=False)}

Por favor, forneça:
1. **Principais Descobertas**: 3-5 insights mais importantes
2. **Padrões Identificados**: Tendências ou correlações relevantes  
3. **Riscos Potenciais**: Possíveis problemas ou anomalias
4. **Recomendações**: 3-5 ações estratégicas específicas
5. **Próximos Passos**: Sugestões para análises adicionais

Formato: Use markdown para estruturar a resposta de forma clara."""
        
        context = {"analysis_type": "data_insights", "data_summary": data_summary}
        
        return self.process(prompt, context)

    def detect_fraud_patterns(self, fraud_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa padrões de fraude e fornece insights especializados."""
        
        prompt = f"""Analise os padrões de fraude encontrados nos dados:

DADOS DE FRAUDE:
{json.dumps(fraud_data, indent=2, ensure_ascii=False)}

Forneça uma análise detalhada incluindo:
1. **Padrões de Fraude**: Características principais das transações fraudulentas
2. **Indicadores de Risco**: Variáveis mais importantes para detecção
3. **Segmentação**: Grupos de risco identificados
4. **Prevenção**: Estratégias para reduzir fraudes
5. **Monitoramento**: KPIs e alertas recomendados

Use dados concretos e seja específico nas recomendações."""
        
        context = {"analysis_type": "fraud_detection", "fraud_data": fraud_data}
        
        return self.process(prompt, context)

    def explain_correlations(self, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explica correlações de forma acessível para negócios."""
        
        prompt = f"""Explique as correlações nos dados de forma acessível para stakeholders de negócio:

CORRELAÇÕES ENCONTRADAS:
{json.dumps(correlation_data, indent=2, ensure_ascii=False)}

Explique:
1. **O que significam** essas correlações em termos práticos
2. **Implicações de negócio** de cada correlação importante
3. **Oportunidades** identificadas através das correlações
4. **Riscos** potenciais revelados pelos dados
5. **Ações recomendadas** baseadas nessas descobertas

Use linguagem acessível e evite jargão estatístico excessivo."""
        
        context = {"analysis_type": "correlation_analysis", "correlation_data": correlation_data}
        
        return self.process(prompt, context)

    def _search_cached_response(self, query: str, similarity_threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """Busca respostas similares no cache vetorial.
        
        Args:
            query: Consulta para buscar
            similarity_threshold: Limite mínimo de similaridade (0-1)
            
        Returns:
            Resposta em cache se encontrada, senão None
        """
        if not self.rag_enabled:
            return None
            
        try:
            # Gerar embedding da consulta
            query_result = self.embedding_generator.generate_embedding(query)
            query_embedding = query_result.embedding  # Extrair lista de floats
            
            # Buscar consultas similares
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                limit=1,
                similarity_threshold=similarity_threshold
            )
            
            if results and len(results) > 0:
                best_match = results[0]
                self.logger.info(f"🎯 Cache hit! Similaridade: {best_match.similarity_score:.3f}")
                
                return {
                    "content": best_match.metadata.get("response", ""),
                    "similarity": best_match.similarity_score,
                    "original_query": best_match.chunk_text
                }
                
        except Exception as e:
            self.logger.warning(f"Erro na busca de cache: {e}")
            
        return None

    def _save_to_vector_store(self, query: str, response: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Salva consulta e resposta no banco vetorial para cache futuro."""
        if not self.rag_enabled:
            return False
            
        try:
            # Preparar metadados
            metadata = {
                "response": response,
                "model": self.model_name,
                "timestamp": self._get_timestamp(),
                "agent": self.name
            }
            
            if context and "source_file" in context:
                metadata["source_file"] = context["file_path"]
            
            # Gerar e salvar embedding
            query_result = self.embedding_generator.generate_embedding(query)
            query_embedding = query_result.embedding  # Extrair lista de floats
            
            result = self.vector_store.store_embedding(
                query=query,
                response=response,
                embedding=query_embedding
            )
            
            if result:
                self.logger.info(f"💾 Consulta salva no cache vetorial: {query[:50]}...")
                return True
            else:
                self.logger.warning("Falha ao salvar no cache vetorial")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar no cache: {e}")
            return False


if __name__ == "__main__":
    # Teste básico do agente
    try:
        agent = GrokLLMAgent()
        
        test_query = "Explique como detectar fraudes em transações de cartão de crédito"
        result = agent.process(test_query)
        
        print("🧪 TESTE DO GROK LLM AGENT")
        print("=" * 50)
        print(f"Query: {test_query}")
        print(f"Resposta: {result.get('content', 'Erro')[:200]}...")
        print(f"Metadata: {result.get('metadata', {})}")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")