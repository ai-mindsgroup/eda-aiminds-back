"""
Sistema de Roteamento Inteligente de LLMs (LLM Router)
======================================================

Estratégia de cascata: começa com modelo rápido/barato e escala conforme complexidade.

Níveis de Complexidade:
- SIMPLE: Perguntas básicas, saudações, status
- MEDIUM: Análise de dados simples, estatísticas básicas
- COMPLEX: Detecção de fraude, análise profunda, múltiplos agentes
- ADVANCED: Análise massiva, correlações complexas, ML

Modelos Disponíveis (ordem de custo/capacidade):
1. gemini-1.5-flash (rápido/barato) -> SIMPLE/MEDIUM
2. gemini-1.5-pro (balanceado) -> MEDIUM/COMPLEX
3. gemini-2.0-flash-exp (experimental avançado) -> COMPLEX/ADVANCED
"""

from enum import Enum
from typing import Dict, Any, Optional
import re

class ComplexityLevel(Enum):
    """Níveis de complexidade de consulta"""
    SIMPLE = 1      # Perguntas básicas, saudações
    MEDIUM = 2      # Análise de dados simples
    COMPLEX = 3     # Detecção fraude, análise profunda
    ADVANCED = 4    # Análise massiva, ML, correlações

class LLMModel(Enum):
    """Modelos LLM disponíveis"""
    GEMINI_FLASH = "gemini-1.5-flash"           # Rápido e barato
    GEMINI_PRO = "gemini-1.5-pro"               # Balanceado
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"     # Experimental avançado

class LLMRouter:
    """Roteador inteligente de LLMs baseado em complexidade"""
    
    # Mapeamento: Complexidade -> Modelo
    COMPLEXITY_TO_MODEL = {
        ComplexityLevel.SIMPLE: LLMModel.GEMINI_FLASH,
        ComplexityLevel.MEDIUM: LLMModel.GEMINI_FLASH,
        ComplexityLevel.COMPLEX: LLMModel.GEMINI_PRO,
        ComplexityLevel.ADVANCED: LLMModel.GEMINI_2_FLASH,
    }
    
    # Palavras-chave que indicam complexidade
    SIMPLE_KEYWORDS = [
        "olá", "oi", "hello", "hey", "status", "help", "ajuda",
        "como funciona", "o que é", "tchau", "obrigado"
    ]
    
    MEDIUM_KEYWORDS = [
        "quantas linhas", "quantas colunas", "mostre", "exiba",
        "lista", "dados", "estatísticas básicas", "resumo"
    ]
    
    COMPLEX_KEYWORDS = [
        "fraude", "fraud", "detecção", "detectar", "anômalo", "outlier",
        "correlação", "padrões", "análise profunda", "machine learning",
        "predição", "classificação", "clustering"
    ]
    
    ADVANCED_KEYWORDS = [
        "análise completa", "todos os agentes", "análise massiva",
        "correlações complexas", "múltiplos modelos", "ensemble",
        "deep learning", "análise avançada", "otimização"
    ]
    
    @classmethod
    def detect_complexity(cls, query: str, context: Optional[Dict[str, Any]] = None) -> ComplexityLevel:
        """
        Detecta a complexidade da consulta baseado em:
        - Palavras-chave
        - Tamanho do dataset (se disponível no contexto)
        - Histórico de conversação
        - Flags explícitas
        """
        query_lower = query.lower()
        
        # 1. Verifica flags explícitas de complexidade
        if context and context.get("force_complexity"):
            return context["force_complexity"]
        
        # 2. Análise por palavras-chave (ordem reversa - mais complexo primeiro)
        if any(keyword in query_lower for keyword in cls.ADVANCED_KEYWORDS):
            return ComplexityLevel.ADVANCED
        
        if any(keyword in query_lower for keyword in cls.COMPLEX_KEYWORDS):
            return ComplexityLevel.COMPLEX
        
        if any(keyword in query_lower for keyword in cls.MEDIUM_KEYWORDS):
            return ComplexityLevel.MEDIUM
        
        if any(keyword in query_lower for keyword in cls.SIMPLE_KEYWORDS):
            return ComplexityLevel.SIMPLE
        
        # 3. Análise de tamanho do dataset (se disponível)
        if context and context.get("dataset_size"):
            rows = context["dataset_size"].get("rows", 0)
            columns = context["dataset_size"].get("columns", 0)
            
            # Dataset grande = complexidade maior
            if rows > 100000 or columns > 50:
                return ComplexityLevel.COMPLEX
            elif rows > 10000 or columns > 20:
                return ComplexityLevel.MEDIUM
        
        # 4. Análise de comprimento da query
        if len(query_lower) > 200:
            return ComplexityLevel.COMPLEX
        elif len(query_lower) > 100:
            return ComplexityLevel.MEDIUM
        
        # 5. Padrão: MEDIUM (balanceado)
        return ComplexityLevel.MEDIUM
    
    @classmethod
    def get_model(cls, complexity: ComplexityLevel) -> LLMModel:
        """Retorna o modelo apropriado para a complexidade"""
        return cls.COMPLEXITY_TO_MODEL.get(complexity, LLMModel.GEMINI_PRO)
    
    @classmethod
    def route_query(cls, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Roteador principal: analisa query e retorna modelo + configurações
        
        Returns:
            {
                "model": LLMModel,
                "complexity": ComplexityLevel,
                "temperature": float,
                "max_tokens": int,
                "reasoning": str
            }
        """
        complexity = cls.detect_complexity(query, context)
        model = cls.get_model(complexity)
        
        # Configurações por complexidade
        configs = {
            ComplexityLevel.SIMPLE: {
                "temperature": 0.3,
                "max_tokens": 500,
                "reasoning": "Resposta direta e concisa"
            },
            ComplexityLevel.MEDIUM: {
                "temperature": 0.5,
                "max_tokens": 1500,
                "reasoning": "Análise balanceada com dados"
            },
            ComplexityLevel.COMPLEX: {
                "temperature": 0.7,
                "max_tokens": 3000,
                "reasoning": "Análise profunda multi-agente"
            },
            ComplexityLevel.ADVANCED: {
                "temperature": 0.8,
                "max_tokens": 4000,
                "reasoning": "Análise massiva com todos os recursos"
            }
        }
        
        config = configs.get(complexity, configs[ComplexityLevel.MEDIUM])
        
        return {
            "model": model,
            "model_name": model.value,
            "complexity": complexity,
            "complexity_name": complexity.name,
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "reasoning": config["reasoning"]
        }
    
    @classmethod
    def escalate_complexity(cls, current_complexity: ComplexityLevel) -> ComplexityLevel:
        """
        Escala para o próximo nível de complexidade
        Útil quando o modelo atual falha ou precisa de mais capacidade
        """
        escalation = {
            ComplexityLevel.SIMPLE: ComplexityLevel.MEDIUM,
            ComplexityLevel.MEDIUM: ComplexityLevel.COMPLEX,
            ComplexityLevel.COMPLEX: ComplexityLevel.ADVANCED,
            ComplexityLevel.ADVANCED: ComplexityLevel.ADVANCED  # Já no máximo
        }
        return escalation.get(current_complexity, ComplexityLevel.MEDIUM)


def create_llm_with_routing(query: str, context: Optional[Dict[str, Any]] = None):
    """
    Factory function para criar LLM com roteamento automático
    
    Uso:
        llm_config = create_llm_with_routing(
            "Analise este dataset para fraude",
            context={"dataset_size": {"rows": 1000000, "columns": 50}}
        )
        
        # Retorna configuração para usar com LangChain
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=llm_config["model_name"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"]
        )
    """
    from src.settings import GOOGLE_API_KEY
    
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não configurada")
    
    routing = LLMRouter.route_query(query, context)
    
    return {
        **routing,
        "api_key": GOOGLE_API_KEY,
        "provider": "google",
    }


# Exemplo de uso
if __name__ == "__main__":
    # Testes
    queries = [
        ("Olá, como você está?", None),
        ("Quantas linhas tem o arquivo?", {"dataset_size": {"rows": 1000, "columns": 10}}),
        ("Analise este dataset para fraude", {"dataset_size": {"rows": 100000, "columns": 30}}),
        ("Faça uma análise completa com todos os agentes disponíveis", {"dataset_size": {"rows": 1000000, "columns": 50}}),
    ]
    
    for query, context in queries:
        result = LLMRouter.route_query(query, context)
        print(f"\n📝 Query: {query}")
        print(f"🧠 Modelo: {result['model_name']}")
        print(f"📊 Complexidade: {result['complexity_name']}")
        print(f"🌡️ Temperature: {result['temperature']}")
        print(f"💭 Reasoning: {result['reasoning']}")
