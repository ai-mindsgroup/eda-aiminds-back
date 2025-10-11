"""
Modelos Pydantic para tabelas de memória conversacional Supabase.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class AgentContext(BaseModel):
    id: Optional[str]
    agent_id: str
    session_id: str
    context: Dict[str, str]
    created_at: Optional[datetime] = None

class AgentConversation(BaseModel):
    id: Optional[str]
    agent_id: str
    session_id: str
    user_message: str
    agent_response: str
    timestamp: Optional[datetime] = None

class AgentMemoryEmbedding(BaseModel):
    id: Optional[str]
    agent_id: str
    session_id: str
    embedding: List[float]
    metadata: Dict[str, str]
    created_at: Optional[datetime] = None

class AgentSession(BaseModel):
    id: Optional[str]
    session_id: str
    user_id: Optional[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = "active"
