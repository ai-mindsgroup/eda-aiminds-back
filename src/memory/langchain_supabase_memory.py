"""
Camada de integração entre LangChain Memory e Supabase.

Permite que o fluxo de memória conversacional do LangChain seja persistido e recuperado diretamente do Supabase,
garantindo histórico, rastreabilidade e compatibilidade multiagente.
"""

from langchain.memory import ConversationBufferMemory
from src.memory.supabase_memory import SupabaseMemoryManager
from src.vectorstore.supabase_client import supabase

class LangChainSupabaseMemory(ConversationBufferMemory):
    """
    Extensão da ConversationBufferMemory do LangChain para persistência no Supabase.
    """
    def __init__(self, agent_name: str = None, session_id: str = None, **kwargs):
        # Inicializa ConversationBufferMemory primeiro
        super().__init__(**kwargs)
        # Define atributos personalizados após inicialização do pai
        object.__setattr__(self, 'agent_name', agent_name)
        object.__setattr__(self, 'session_id', session_id)
        object.__setattr__(self, 'supabase_manager', SupabaseMemoryManager(agent_name) if agent_name else None)

    def save_context(self, inputs, outputs):
        """
        Salva contexto no buffer e persiste no Supabase.
        """
        super().save_context(inputs, outputs)
        # Persiste no Supabase se manager disponível
        if self.supabase_manager and self.session_id:
            try:
                self.supabase_manager.save_message(
                    session_id=self.session_id,
                    message=inputs.get('input', ''),
                    response=outputs.get('output', ''),
                    metadata={}
                )
            except Exception as e:
                print(f"⚠️ Erro ao persistir no Supabase: {e}")

    def load_memory(self):
        """
        Carrega histórico do Supabase para o buffer do LangChain.
        """
        if self.supabase_manager and self.session_id:
            try:
                history = self.supabase_manager.get_session_history(self.session_id)
                for msg in history:
                    self.chat_memory.add_user_message(msg['message'])
                    self.chat_memory.add_ai_message(msg['response'])
            except Exception as e:
                print(f"⚠️ Erro ao carregar histórico do Supabase: {e}")

    def clear(self):
        """
        Limpa buffer e histórico no Supabase.
        """
        super().clear()
        if self.supabase_manager and self.session_id:
            try:
                self.supabase_manager.clear_session_history(self.session_id)
            except Exception as e:
                print(f"⚠️ Erro ao limpar histórico do Supabase: {e}")
