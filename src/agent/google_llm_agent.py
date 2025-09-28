"""Agente LLM usando Google Generative AI (Gemini)
===============================================

Este agente utiliza o Google Gemini para análises inteligentes e insights.
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

from src.agent.base_agent import BaseAgent, AgentError
from src.settings import GOOGLE_API_KEY
from src.utils.logging_config import get_logger

# Import condicional do Google Generative AI
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    genai = None

logger = get_logger(__name__)


@dataclass
class LLMRequest:
    """Request para o LLM."""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    temperature: float = 0.3
    max_tokens: int = 1000
    system_prompt: Optional[str] = None


@dataclass 
class LLMResponse:
    """Resposta do LLM."""
    content: str
    usage: Dict[str, Any]
    model: str
    success: bool = True
    error: Optional[str] = None


class GoogleLLMAgent(BaseAgent):
    """Agente que utiliza Google Generative AI (Gemini) para análises inteligentes."""
    
    def __init__(self, model: str = "gemini-pro"):
        super().__init__(
            name="google_llm",
            description="Agente LLM usando Google Gemini para análises inteligentes e insights"
        )
        
        self.model_name = model
        self.model = None
        
        # Verificar disponibilidade
        if not GOOGLE_AI_AVAILABLE:
            raise AgentError(
                self.name,
                "Google Generative AI não disponível. Execute: pip install google-generativeai"
            )
        
        if not GOOGLE_API_KEY:
            raise AgentError(
                self.name, 
                "GOOGLE_API_KEY não configurado. Configure em configs/.env"
            )
        
        # Configurar e inicializar
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(model)
            self.logger.info(f"Google LLM inicializado: {model}")
            
        except Exception as e:
            raise AgentError(self.name, f"Erro na inicialização do Google LLM: {e}")
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta usando Google Gemini.
        
        Args:
            query: Consulta/prompt para o LLM
            context: Contexto adicional (dados, configurações, etc.)
            
        Returns:
            Resposta estruturada do LLM
        """
        try:
            # Preparar request
            llm_request = self._prepare_request(query, context)
            
            # Enviar para Google Gemini
            response = self._call_gemini(llm_request)
            
            # Processar resposta
            return self._build_response(
                response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "llm_used": True,
                    "success": response.success
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erro no processamento LLM: {e}")
            return self._build_response(
                f"Erro no processamento: {str(e)}",
                metadata={"error": True, "llm_used": False}
            )
    
    def _prepare_request(self, query: str, context: Optional[Dict[str, Any]]) -> LLMRequest:
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
        
        return LLMRequest(
            prompt=full_prompt,
            context=context,
            temperature=0.3,  # Mais determinístico para análise de dados
            max_tokens=1000
        )
    
    def _call_gemini(self, request: LLMRequest) -> LLMResponse:
        """Chama Google Gemini API."""
        try:
            # Configurar parâmetros de geração
            generation_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
                "candidate_count": 1,
            }
            
            # Gerar resposta
            response = self.model.generate_content(
                request.prompt,
                generation_config=generation_config
            )
            
            # Extrair conteúdo
            content = response.text if response.text else "Sem resposta gerada"
            
            # Metadados de uso (Gemini não fornece tokens detalhados via API gratuita)
            usage = {
                "prompt_tokens": len(request.prompt.split()),  # Aproximado
                "completion_tokens": len(content.split()),     # Aproximado  
                "total_tokens": len(request.prompt.split()) + len(content.split())
            }
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model_name,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Erro na chamada Gemini: {e}")
            return LLMResponse(
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
        
        prompt = f"""Analise os padrões de fraude nos seguintes dados:

DADOS DE FRAUDE:
{json.dumps(fraud_data, indent=2, ensure_ascii=False)}

Forneça uma análise especializada incluindo:

1. **Análise de Risco**: Avalie o nível de risco atual
2. **Padrões de Fraude**: Identifique características comuns das fraudes
3. **Fatores de Risco**: Quais variáveis mais indicam fraude?
4. **Estratégias de Prevenção**: Como reduzir fraudes futuras?
5. **Alertas Críticos**: Situações que requerem atenção imediata

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