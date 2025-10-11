"""Testes para LangChain LLM Manager.

Valida:
- Inicialização com múltiplos provedores
- Fallback automático
- Configuração de parâmetros (temperatura, top_p, max_tokens)
- Respostas e metadados
"""

import pytest
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.llm.langchain_manager import (
    LangChainLLMManager,
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LANGCHAIN_AVAILABLE
)


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain não disponível")
class TestLangChainLLMManager:
    """Testes para o gerenciador LLM com LangChain."""
    
    def test_manager_initialization(self):
        """Testa inicialização do manager."""
        manager = LangChainLLMManager()
        
        assert manager is not None
        assert manager.active_provider is not None
        assert manager.active_provider in LLMProvider
    
    def test_provider_status(self):
        """Testa verificação de status dos provedores."""
        manager = LangChainLLMManager()
        status = manager.get_provider_status()
        
        assert "active_provider" in status
        assert "providers" in status
        assert len(status["providers"]) > 0
    
    def test_chat_basic(self):
        """Testa chamada básica de chat."""
        manager = LangChainLLMManager()
        
        response = manager.chat("Diga 'olá' em uma palavra")
        
        assert isinstance(response, LLMResponse)
        assert response.success
        assert len(response.content) > 0
        assert response.provider in LLMProvider
    
    def test_chat_with_config(self):
        """Testa chat com configuração personalizada."""
        manager = LangChainLLMManager()
        
        config = LLMConfig(
            temperature=0.1,
            max_tokens=50,
            top_p=0.8
        )
        
        response = manager.chat("Conte até 3", config=config)
        
        assert response.success
        assert len(response.content) > 0
    
    def test_chat_with_system_prompt(self):
        """Testa chat com system prompt."""
        manager = LangChainLLMManager()
        
        system_prompt = "Você é um assistente conciso que responde em uma única palavra."
        response = manager.chat("Qual a cor do céu?", system_prompt=system_prompt)
        
        assert response.success
        assert len(response.content) > 0
    
    def test_default_models(self):
        """Testa modelos padrão de cada provedor."""
        manager = LangChainLLMManager()
        
        groq_model = manager._get_default_model(LLMProvider.GROQ)
        google_model = manager._get_default_model(LLMProvider.GOOGLE)
        openai_model = manager._get_default_model(LLMProvider.OPENAI)
        
        assert groq_model == "llama-3.1-8b-instant"
        assert google_model == "models/gemini-2.0-flash"
        assert openai_model == "gpt-3.5-turbo"
    
    def test_response_metadata(self):
        """Testa presença de metadados na resposta."""
        manager = LangChainLLMManager()
        
        response = manager.chat("Teste")
        
        assert hasattr(response, 'content')
        assert hasattr(response, 'provider')
        assert hasattr(response, 'model')
        assert hasattr(response, 'processing_time')
        assert response.processing_time >= 0


@pytest.mark.integration
class TestLangChainLLMManagerIntegration:
    """Testes de integração com provedores reais."""
    
    def test_groq_provider(self):
        """Testa provedor Groq especificamente."""
        try:
            manager = LangChainLLMManager(preferred_providers=[LLMProvider.GROQ])
            response = manager.chat("Teste", provider=LLMProvider.GROQ)
            
            assert response.provider == LLMProvider.GROQ
            assert response.success
        except RuntimeError:
            pytest.skip("Groq não configurado")
    
    def test_google_provider(self):
        """Testa provedor Google especificamente."""
        try:
            manager = LangChainLLMManager(preferred_providers=[LLMProvider.GOOGLE])
            response = manager.chat("Teste", provider=LLMProvider.GOOGLE)
            
            assert response.provider == LLMProvider.GOOGLE
            assert response.success
        except RuntimeError:
            pytest.skip("Google não configurado")
    
    def test_openai_provider(self):
        """Testa provedor OpenAI especificamente."""
        try:
            manager = LangChainLLMManager(preferred_providers=[LLMProvider.OPENAI])
            response = manager.chat("Teste", provider=LLMProvider.OPENAI)
            
            assert response.provider == LLMProvider.OPENAI
            assert response.success
        except RuntimeError:
            pytest.skip("OpenAI não configurado")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
