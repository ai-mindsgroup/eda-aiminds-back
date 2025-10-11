"""Sistema de Gerenciamento de LLM com Abstração e Fallback Automático
=======================================================================

Este módulo fornece uma camada de abstração para diferentes provedores LLM:
- Groq (llama-3.1-8b-instant)
- Google Gemini (gemini-1.5-flash)
- OpenAI (gpt-3.5-turbo)
- Fallback automático quando um provedor falha

Uso:
    manager = LLMManager()
    response = manager.chat("Analise estes dados...")
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

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Provedores LLM disponíveis."""
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


class LLMManager:
    """Gerenciador centralizado para diferentes provedores LLM com fallback automático."""
    
    def __init__(self, preferred_providers: Optional[List[LLMProvider]] = None):
        """Inicializa o gerenciador LLM.
        
        Args:
            preferred_providers: Lista ordenada de provedores preferenciais
        """
        self.logger = logger
        self.preferred_providers = preferred_providers or [
            LLMProvider.GROQ,    # Primeiro: Groq (mais rápido)
            LLMProvider.GOOGLE,  # Segundo: Google (boa qualidade)
            LLMProvider.OPENAI   # Terceiro: OpenAI (fallback)
        ]
        
        # Cache de clientes inicializados
        self._clients = {}
        self._provider_status = {}
        
        # Verificar disponibilidade dos provedores
        self._check_provider_availability()
        
        # Encontrar primeiro provedor disponível
        self.active_provider = self._get_first_available_provider()
        if not self.active_provider:
            raise RuntimeError("❌ Nenhum provedor LLM disponível. Verifique as configurações de API keys.")
        
        self.logger.info(f"✅ LLM Manager inicializado com provedor ativo: {self.active_provider.value}")
    
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
                self.logger.warning(f"⚠️ {provider.value.upper()}: Erro na verificação - {str(e)}")
    
    def _check_single_provider(self, provider: LLMProvider) -> Tuple[bool, str]:
        """Verifica se um provedor específico está disponível.
        
        Returns:
            Tuple[bool, str]: (disponível, mensagem)
        """
        if provider == LLMProvider.GROQ:
            try:
                from groq import Groq
                if not GROQ_API_KEY:
                    return False, "API key não configurada"
                return True, "Groq disponível"
            except ImportError:
                return False, "Biblioteca groq não instalada (pip install groq)"
        
        elif provider == LLMProvider.GOOGLE:
            try:
                import google.generativeai as genai
                if not GOOGLE_API_KEY:
                    return False, "API key não configurada"
                return True, "Google Gemini disponível"
            except ImportError:
                return False, "Biblioteca google-generativeai não instalada"
        
        elif provider == LLMProvider.OPENAI:
            try:
                import openai
                if not OPENAI_API_KEY:
                    return False, "API key não configurada"
                return True, "OpenAI disponível"
            except ImportError:
                return False, "Biblioteca openai não instalada"
        
        return False, "Provedor desconhecido"
    
    def _get_first_available_provider(self) -> Optional[LLMProvider]:
        """Retorna o primeiro provedor disponível na ordem de preferência."""
        for provider in self.preferred_providers:
            if self._provider_status.get(provider, {}).get("available", False):
                return provider
        return None
    
    def _get_client(self, provider: LLMProvider):
        """Obtém ou cria cliente para o provedor especificado."""
        if provider in self._clients:
            return self._clients[provider]
        
        client = None
        if provider == LLMProvider.GROQ:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
        
        elif provider == LLMProvider.GOOGLE:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            client = genai.GenerativeModel('models/gemini-2.0-flash')
        
        elif provider == LLMProvider.OPENAI:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        if client:
            self._clients[provider] = client
        
        return client
    
    def _get_default_model(self, provider: LLMProvider) -> str:
        """Retorna o modelo padrão para cada provedor."""
        defaults = {
            LLMProvider.GROQ: "llama-3.1-8b-instant",
            LLMProvider.GOOGLE: "models/gemini-2.0-flash",
            LLMProvider.OPENAI: "gpt-3.5-turbo"
        }
        return defaults.get(provider, "unknown")
    
    def _call_groq(self, prompt: str, config: LLMConfig, system_prompt: Optional[str] = None) -> LLMResponse:
        """Chama a API do Groq."""
        start_time = time.time()
        client = self._get_client(LLMProvider.GROQ)
        model = config.model or self._get_default_model(LLMProvider.GROQ)
        
        # Construir mensagens com system prompt se fornecido
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p
        )
        
        processing_time = time.time() - start_time
        content = response.choices[0].message.content
        
        # Extrair tokens de forma segura
        tokens_used = None
        if hasattr(response, 'usage') and response.usage:
            tokens_used = getattr(response.usage, 'total_tokens', None)
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.GROQ,
            model=model,
            tokens_used=tokens_used,
            processing_time=processing_time
        )
    
    def _call_google(self, prompt: str, config: LLMConfig, system_prompt: Optional[str] = None) -> LLMResponse:
        """Chama a API do Google Gemini."""
        start_time = time.time()
        client = self._get_client(LLMProvider.GOOGLE)
        
        # Google Gemini não suporta system prompts diretamente, então combinamos
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\nUsuário: {prompt}"
        else:
            combined_prompt = prompt
        
        response = client.generate_content(
            combined_prompt,
            generation_config={
                'temperature': config.temperature,
                'max_output_tokens': config.max_tokens,
                'top_p': config.top_p,
            }
        )
        
        processing_time = time.time() - start_time
        content = response.text
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.GOOGLE,
            model="models/gemini-2.0-flash",
            processing_time=processing_time
        )
    
    def _call_openai(self, prompt: str, config: LLMConfig, system_prompt: Optional[str] = None) -> LLMResponse:
        """Chama a API da OpenAI."""
        start_time = time.time()
        client = self._get_client(LLMProvider.OPENAI)
        model = config.model or self._get_default_model(LLMProvider.OPENAI)
        
        # Construir mensagens com system prompt se fornecido
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p
        )
        
        processing_time = time.time() - start_time
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model=model,
            tokens_used=tokens_used,
            processing_time=processing_time
        )
    
    def chat(self, 
             prompt: str, 
             config: Optional[LLMConfig] = None,
             force_provider: Optional[LLMProvider] = None,
             system_prompt: Optional[str] = None) -> LLMResponse:
        """Envia prompt para LLM com fallback automático.
        
        Args:
            prompt: Texto do prompt
            config: Configurações para a chamada
            force_provider: Forçar uso de provedor específico
            system_prompt: Prompt de sistema para definir comportamento/personalidade
        
        Returns:
            LLMResponse com resultado ou erro
        """
        config = config or LLMConfig()
        
        # Determinar ordem de tentativa dos provedores
        if force_provider:
            providers_to_try = [force_provider]
        else:
            # Começar com o provedor ativo, depois tentar outros disponíveis
            available_providers = [
                p for p in self.preferred_providers 
                if self._provider_status.get(p, {}).get("available", False)
            ]
            
            if self.active_provider in available_providers:
                # Mover provedor ativo para o início
                available_providers.remove(self.active_provider)
                providers_to_try = [self.active_provider] + available_providers
            else:
                providers_to_try = available_providers
        
        last_error = None
        
        # Tentar cada provedor na ordem de preferência
        for provider in providers_to_try:
            try:
                self.logger.debug(f"Tentando provedor: {provider.value}")
                
                if provider == LLMProvider.GROQ:
                    response = self._call_groq(prompt, config, system_prompt)
                elif provider == LLMProvider.GOOGLE:
                    response = self._call_google(prompt, config, system_prompt)
                elif provider == LLMProvider.OPENAI:
                    response = self._call_openai(prompt, config, system_prompt)
                else:
                    continue
                
                # Sucesso! Atualizar provedor ativo se necessário
                if provider != self.active_provider:
                    self.logger.info(f"Mudando provedor ativo para: {provider.value}")
                    self.active_provider = provider
                
                self.logger.debug(f"✅ Resposta obtida via {provider.value} em {response.processing_time:.2f}s")
                return response
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"❌ Falha no provedor {provider.value}: {last_error}")
                
                # Marcar provedor como indisponível temporariamente
                if provider in self._provider_status:
                    self._provider_status[provider]["available"] = False
                    self._provider_status[provider]["message"] = f"Erro: {last_error}"
                
                continue
        
        # Todos os provedores falharam
        error_msg = f"Todos os provedores LLM falharam. Último erro: {last_error}"
        self.logger.error(error_msg)
        
        return LLMResponse(
            content="",
            provider=self.active_provider,
            model="unknown",
            error=error_msg,
            success=False
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status de todos os provedores."""
        return {
            "active_provider": self.active_provider.value if self.active_provider else None,
            "preferred_order": [p.value for p in self.preferred_providers],
            "provider_status": {
                p.value: status for p, status in self._provider_status.items()
            }
        }
    
    def refresh_providers(self) -> None:
        """Revalida a disponibilidade de todos os provedores."""
        self.logger.info("🔄 Revalidando disponibilidade dos provedores...")
        self._check_provider_availability()
        
        # Atualizar provedor ativo se necessário
        new_active = self._get_first_available_provider()
        if new_active and new_active != self.active_provider:
            self.logger.info(f"Provedor ativo alterado: {self.active_provider.value} -> {new_active.value}")
            self.active_provider = new_active
        elif not new_active:
            self.logger.error("❌ Nenhum provedor disponível após revalidação!")
            self.active_provider = None


# Instância global singleton para uso em todo o sistema
_llm_manager_instance = None

def get_llm_manager() -> LLMManager:
    """Retorna instância singleton do LLM Manager."""
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager()
    return _llm_manager_instance


def reset_llm_manager() -> None:
    """Reseta a instância global (útil para testes)."""
    global _llm_manager_instance
    _llm_manager_instance = None