"""Classe base para agentes do sistema multiagente.

Esta classe fornece a estrutura comum para todos os agentes especializados:
- Logging centralizado
- Interface padronizada de comunicação
- Integração com LangChain
- Tratamento de erros
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.utils.logging_config import get_logger
from src.api.sonar_client import send_sonar_query


class BaseAgent(ABC):
    """Classe base abstrata para todos os agentes do sistema."""
    
    def __init__(self, name: str, description: str = ""):
        """Inicializa o agente base.
        
        Args:
            name: Nome único do agente
            description: Descrição das responsabilidades do agente
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"agent.{name}")
        self.logger.info(f"Agente {name} inicializado: {description}")
    
    @abstractmethod
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa uma consulta e retorna uma resposta.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (dados, histórico, etc.)
        
        Returns:
            Dict com resposta processada e metadados
        """
        pass
    
    def _call_llm(self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Chama o LLM via Sonar API com configurações padrão.
        
        Args:
            prompt: Prompt para o LLM
            context: Contexto adicional
            **kwargs: Parâmetros extras para send_sonar_query
        
        Returns:
            Resposta da API Sonar
        """
        try:
            # Configurações padrão para agentes
            default_params = {
                "temperature": 0.2,
                "max_tokens": 1024,
                "top_p": 0.9
            }
            default_params.update(kwargs)
            
            self.logger.debug(f"Chamando LLM para agente {self.name}")
            response = send_sonar_query(prompt, context, **default_params)
            return response
        
        except Exception as e:
            self.logger.error(f"Erro ao chamar LLM: {str(e)[:100]}")
            return {
                "error": True,
                "message": f"Falha na comunicação com LLM: {type(e).__name__}"
            }
    
    def _build_response(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Constrói resposta padronizada do agente.
        
        Args:
            content: Conteúdo principal da resposta
            metadata: Metadados adicionais
        
        Returns:
            Resposta estruturada
        """
        response = {
            "agent": self.name,
            "content": content,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }
        return response
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual em formato ISO."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"


class AgentError(Exception):
    """Exceção específica para erros de agentes."""
    
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"[{agent_name}] {message}")