"""LLM Manager integrado com LangChain para gerenciamento de múltiplos provedores.

Este módulo fornece uma camada de abstração usando LangChain para:
- ChatOpenAI (OpenAI GPT)
- ChatGoogleGenerativeAI (Google Gemini)
- ChatGroq (Groq)
- Fallback automático quando um provedor falha
- Configuração de temperatura, top_p, max_tokens

Integração incremental mantendo compatibilidade com sistema legado.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
import time

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.utils.logging_config import get_logger
from src.settings import GROQ_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY

# Imports LangChain
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    ChatGroq = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None
    print(f"⚠️ LangChain não disponível: {str(e)}")

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


@dataclass
class LLMConfig:
    """Configuração para chamadas LLM."""
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9
    model: Optional[str] = None  # Se None, usa modelo padrão do provedor


class LangChainLLMManager:
    """Gerenciador LLM usando LangChain como backend principal.
    
    Integração incremental mantendo fallback para sistema legado.
    """
    
    def __init__(self, preferred_providers: Optional[List[LLMProvider]] = None):
        """Inicializa o gerenciador LLM com LangChain.
        
        Args:
            preferred_providers: Lista ordenada de provedores preferenciais
        """
        self.logger = logger
        
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("❌ LangChain não está disponível. Execute: pip install langchain langchain-openai langchain-google-genai langchain-groq")
        
        self.preferred_providers = preferred_providers or [
            LLMProvider.GROQ,    # Primeiro: Groq (mais rápido)
            LLMProvider.GOOGLE,  # Segundo: Google (boa qualidade)
            LLMProvider.OPENAI   # Terceiro: OpenAI (fallback)
        ]
        
        # Cache de clientes LangChain
        self._clients = {}
        self._provider_status = {}
        
        # Verificar disponibilidade dos provedores
        self._check_provider_availability()
        
        # Encontrar primeiro provedor disponível
        self.active_provider = self._get_first_available_provider()
        if not self.active_provider:
            raise RuntimeError("❌ Nenhum provedor LLM disponível. Verifique as configurações de API keys.")
        
        self.logger.info(f"✅ LangChain LLM Manager inicializado com provedor ativo: {self.active_provider.value}")
    
    def _check_provider_availability(self) -> None:
        """Verifica quais provedores estão disponíveis."""
        for provider in LLMProvider:
            try:
                is_available, message = self._check_single_provider(provider)
                self._provider_status[provider] = {
                    "available": is_available,
                    "message": message,
                    "last_check": time.time()
                }
                
                if is_available:
                    self.logger.info(f"✅ {provider.value.upper()}: {message}")
                else:
                    self.logger.warning(f"⚠️ {provider.value.upper()}: {message}")
                    
            except Exception as e:
                self._provider_status[provider] = {
                    "available": False,
                    "message": f"Erro na verificação: {str(e)}",
                    "last_check": time.time()
                }
                self.logger.warning(f"⚠️ {provider.value.upper()}: Erro - {str(e)}")
    
    def _check_single_provider(self, provider: LLMProvider) -> Tuple[bool, str]:
        """Verifica se um provedor específico está disponível.
        
        Returns:
            Tuple[bool, str]: (disponível, mensagem)
        """
        if provider == LLMProvider.GROQ:
            if not GROQ_API_KEY:
                return False, "API key não configurada"
            return True, "Groq disponível via LangChain"
        
        elif provider == LLMProvider.GOOGLE:
            if not GOOGLE_API_KEY:
                return False, "API key não configurada"
            return True, "Google Gemini disponível via LangChain"
        
        elif provider == LLMProvider.OPENAI:
            if not OPENAI_API_KEY:
                return False, "API key não configurada"
            return True, "OpenAI disponível via LangChain"
        
        return False, "Provedor desconhecido"
    
    def _get_first_available_provider(self) -> Optional[LLMProvider]:
        """Retorna o primeiro provedor disponível na ordem de preferência."""
        for provider in self.preferred_providers:
            if self._provider_status.get(provider, {}).get("available", False):
                return provider
        return None
    
    def _get_client(self, provider: LLMProvider, config: LLMConfig):
        """Obtém ou cria cliente LangChain para o provedor especificado."""
        cache_key = f"{provider.value}_{config.temperature}_{config.max_tokens}"
        
        if cache_key in self._clients:
            return self._clients[cache_key]
        
        client = None
        model = config.model or self._get_default_model(provider)
        
        if provider == LLMProvider.GROQ:
            client = ChatGroq(
                api_key=GROQ_API_KEY,
                model=model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p
            )
        
        elif provider == LLMProvider.GOOGLE:
            client = ChatGoogleGenerativeAI(
                google_api_key=GOOGLE_API_KEY,
                model=model,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p
            )
        
        elif provider == LLMProvider.OPENAI:
            client = ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model=model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p
            )
        
        if client:
            self._clients[cache_key] = client
        
        return client
    
    def _get_default_model(self, provider: LLMProvider) -> str:
        """Retorna o modelo padrão para cada provedor."""
        defaults = {
            LLMProvider.GROQ: "llama-3.1-8b-instant",
            LLMProvider.GOOGLE: "gemini-pro",
            LLMProvider.OPENAI: "gpt-3.5-turbo"
        }
        return defaults.get(provider, "unknown")
    
    def chat(self, prompt: str, config: Optional[LLMConfig] = None, 
             system_prompt: Optional[str] = None, provider: Optional[LLMProvider] = None) -> LLMResponse:
        """Envia mensagem para o LLM e retorna resposta.
        
        Args:
            prompt: Mensagem do usuário
            config: Configuração LLM (temperatura, max_tokens, etc)
            system_prompt: Prompt de sistema opcional
            provider: Provedor específico (se None, usa ativo)
        
        Returns:
            LLMResponse com conteúdo e metadados
        """
        if config is None:
            config = LLMConfig()
        
        target_provider = provider or self.active_provider
        
        try:
            return self._call_provider(target_provider, prompt, config, system_prompt)
        except Exception as e:
            self.logger.error(f"Erro com {target_provider.value}: {str(e)}")
            
            # Tentar fallback
            for fallback_provider in self.preferred_providers:
                if fallback_provider == target_provider:
                    continue
                
                if self._provider_status.get(fallback_provider, {}).get("available"):
                    self.logger.warning(f"Tentando fallback para {fallback_provider.value}")
                    try:
                        return self._call_provider(fallback_provider, prompt, config, system_prompt)
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback {fallback_provider.value} falhou: {str(fallback_error)}")
            
            # Todos falharam
            return LLMResponse(
                content="",
                provider=target_provider,
                model="unknown",
                error=f"Todos os provedores falharam. Último erro: {str(e)}",
                success=False
            )
    
    def _call_provider(self, provider: LLMProvider, prompt: str, 
                      config: LLMConfig, system_prompt: Optional[str]) -> LLMResponse:
        """Chama um provedor específico via LangChain."""
        start_time = time.time()
        
        client = self._get_client(provider, config)
        model = config.model or self._get_default_model(provider)
        
        # Construir mensagens
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        # Invocar LLM via LangChain
        response = client.invoke(messages)
        
        processing_time = time.time() - start_time
        
        # Extrair tokens se disponível
        tokens_used = None
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            tokens_used = metadata.get('token_usage', {}).get('total_tokens')
        
        return LLMResponse(
            content=response.content,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            processing_time=processing_time,
            success=True
        )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Retorna status de todos os provedores."""
        return {
            "active_provider": self.active_provider.value if self.active_provider else None,
            "providers": {
                provider.value: status 
                for provider, status in self._provider_status.items()
            }
        }


# Singleton para acesso global
_langchain_manager: Optional[LangChainLLMManager] = None

def get_langchain_llm_manager() -> LangChainLLMManager:
    """Retorna instância singleton do LangChain LLM Manager."""
    global _langchain_manager
    if _langchain_manager is None:
        _langchain_manager = LangChainLLMManager()
    return _langchain_manager
