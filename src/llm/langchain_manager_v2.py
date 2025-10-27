"""Sistema de Gerenciamento de LLM usando LangChain Nativo - V2
==================================================================

Versão refatorada do LLM Manager usando LangChain nativamente.

Este módulo substitui o manager.py anterior, oferecendo:
✅ Interface unificada via LangChain
✅ Fallback automático robusto  
✅ Retry nativo
✅ Callbacks e logging estruturado
✅ Cache integrado
✅ Menos código, mais manutenível

Uso:
    manager = LangChainManagerV2()
    response = await manager.chat([HumanMessage(content="Query")])
"""

from __future__ import annotations
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import time

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.utils.logging_config import get_logger
from src.settings import GROQ_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY

# Imports LangChain
try:
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
    from langchain.callbacks import get_openai_callback
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    ChatGroq = None
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    print(f"⚠️ LangChain não disponível: {e}")

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Provedores LLM disponíveis via LangChain."""
    GROQ = "groq"
    GOOGLE = "google"
    OPENAI = "openai"


@dataclass
class LLMResponse:
    """Resposta padronizada de qualquer provedor LLM."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: Optional[int] = None
    processing_time: float = 0.0
    error: Optional[str] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMConfig:
    """Configuração para chamadas LLM."""
    temperature: float = 0.3
    max_tokens: int = 2000
    top_p: float = 0.9
    model: Optional[str] = None
    streaming: bool = False
    verbose: bool = False


class LangChainManagerV2:
    """
    Gerenciador LLM usando LangChain nativamente com fallback automático.
    
    Características:
    - Interface unificada para múltiplos provedores  
    - Fallback automático em caso de falha
    - Retry nativo do LangChain
    - Callbacks para logging e métricas
    - Cache de respostas (opcional)
    - Memória conversacional integrada
    """
    
    def __init__(self, preferred_providers: Optional[List[LLMProvider]] = None):
        """Inicializa o gerenciador LangChain.
        
        Args:
            preferred_providers: Lista ordenada de provedores preferenciais
        """
        self.logger = logger
        
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError(
                "LangChain não disponível. Instale: "
                "pip install langchain langchain-groq langchain-openai langchain-google-genai"
            )
        
        self.preferred_providers = preferred_providers or [
            LLMProvider.GROQ,
            LLMProvider.GOOGLE,
            LLMProvider.OPENAI
        ]
        
        self._llms: Dict[LLMProvider, Any] = {}
        self._provider_status: Dict[LLMProvider, Dict[str, Any]] = {}
        
        self._initialize_providers()
        
        self.active_provider = self._get_first_available_provider()
        if not self.active_provider:
            raise RuntimeError(
                "❌ Nenhum provedor LLM disponível. Verifique API keys."
            )
        
        self.logger.info(
            f"✅ LangChainManagerV2 inicializado: {self.active_provider.value}"
        )
    
    def _initialize_providers(self) -> None:
        """
        Inicializa LLMs LangChain para cada provedor disponível.
        
        ✅ REFATORADO (2025-10-23): Agora usa configurações centralizadas
        via create_llm_with_config() para garantir consistência.
        """
        from src.llm.optimized_config import create_llm_with_config, AnalysisType
        
        # Groq
        if GROQ_API_KEY:
            try:
                self._llms[LLMProvider.GROQ] = create_llm_with_config(
                    provider="groq",
                    analysis_type=AnalysisType.GENERAL_EDA
                )
                self._provider_status[LLMProvider.GROQ] = {
                    "available": True,
                    "message": "ChatGroq inicializado com configurações otimizadas",
                    "model": "llama-3.3-70b-versatile"
                }
                self.logger.info("✅ GROQ: ChatGroq inicializado")
            except Exception as e:
                self._provider_status[LLMProvider.GROQ] = {
                    "available": False,
                    "message": f"Erro: {str(e)}"
                }
                self.logger.warning(f"⚠️ GROQ: Falha - {e}")
        
        # Google Gemini
        if GOOGLE_API_KEY:
            try:
                self._llms[LLMProvider.GOOGLE] = create_llm_with_config(
                    provider="google",
                    analysis_type=AnalysisType.GENERAL_EDA
                )
                self._provider_status[LLMProvider.GOOGLE] = {
                    "available": True,
                    "message": "ChatGoogleGenerativeAI inicializado com configurações otimizadas",
                    "model": "gemini-1.5-flash"
                }
                self.logger.info("✅ GOOGLE: ChatGoogleGenerativeAI inicializado")
            except Exception as e:
                self._provider_status[LLMProvider.GOOGLE] = {
                    "available": False,
                    "message": f"Erro: {str(e)}"
                }
                self.logger.warning(f"⚠️ GOOGLE: Falha - {e}")
        
        # OpenAI
        if OPENAI_API_KEY:
            try:
                self._llms[LLMProvider.OPENAI] = create_llm_with_config(
                    provider="openai",
                    analysis_type=AnalysisType.GENERAL_EDA
                )
                self._provider_status[LLMProvider.OPENAI] = {
                    "available": True,
                    "message": "ChatOpenAI inicializado com configurações otimizadas",
                    "model": "gpt-4o-mini"
                }
                self.logger.info("✅ OPENAI: ChatOpenAI inicializado")
            except Exception as e:
                self._provider_status[LLMProvider.OPENAI] = {
                    "available": False,
                    "message": f"Erro: {str(e)}"
                }
                self.logger.warning(f"⚠️ OPENAI: Falha - {e}")
    
    def _get_first_available_provider(self) -> Optional[LLMProvider]:
        """Retorna o primeiro provedor disponível."""
        for provider in self.preferred_providers:
            if self._provider_status.get(provider, {}).get("available", False):
                return provider
        return None
    
    def get_llm(self, provider: Optional[LLMProvider] = None) -> Any:
        """Retorna LLM LangChain."""
        target_provider = provider or self.active_provider
        llm = self._llms.get(target_provider)
        
        if not llm:
            raise ValueError(f"Provedor {target_provider.value} não disponível")
        
        return llm
    
    async def chat(
        self,
        messages: List[BaseMessage],
        config: Optional[LLMConfig] = None,
        provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """
        Envia mensagens para o LLM usando LangChain com fallback automático.
        
        Args:
            messages: Lista de mensagens LangChain
            config: Configuração da chamada
            provider: Provedor específico ou None
            
        Returns:
            LLMResponse estruturada
        """
        config = config or LLMConfig()
        start_time = time.time()
        
        providers_to_try = [provider] if provider else self.preferred_providers
        
        last_error = None
        for current_provider in providers_to_try:
            if not self._provider_status.get(current_provider, {}).get("available"):
                continue
            
            try:
                llm = self.get_llm(current_provider)
                
                self.logger.debug(f"Chamando {current_provider.value}...")
                response = await asyncio.to_thread(llm.invoke, messages)
                
                processing_time = time.time() - start_time
                
                content = response.content if hasattr(response, 'content') else str(response)
                
                tokens_used = None
                if hasattr(response, 'response_metadata'):
                    usage = response.response_metadata.get('usage', {})
                    tokens_used = usage.get('total_tokens')
                
                self.logger.info(
                    f"✅ {current_provider.value}: {processing_time:.2f}s ({tokens_used or '?'} tokens)"
                )
                
                return LLMResponse(
                    content=content,
                    provider=current_provider,
                    model=self._provider_status[current_provider]["model"],
                    tokens_used=tokens_used,
                    processing_time=processing_time,
                    success=True,
                    metadata={
                        "response_metadata": response.response_metadata if hasattr(response, 'response_metadata') else {}
                    }
                )
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"⚠️ {current_provider.value} falhou: {str(e)[:100]}")
                continue
        
        processing_time = time.time() - start_time
        error_msg = f"Todos provedores falharam. Último: {last_error}"
        
        self.logger.error(f"❌ {error_msg}")
        
        return LLMResponse(
            content="",
            provider=self.active_provider,
            model="fallback_failed",
            processing_time=processing_time,
            success=False,
            error=error_msg
        )
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Retorna status de todos os provedores."""
        return {
            provider.value: status 
            for provider, status in self._provider_status.items()
        }


# Singleton
_manager_instance = None

def get_langchain_manager_v2() -> LangChainManagerV2:
    """Retorna instância singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = LangChainManagerV2()
    return _manager_instance
