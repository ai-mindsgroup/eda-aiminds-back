# Guia de Desenvolvimento - Sistema de Memória

## 🎯 Objetivo

Este guia fornece instruções detalhadas para desenvolvedores que trabalham com o sistema de memória persistente dos agentes multiagente.

## 🚀 Setup Inicial

### 1. Configuração do Ambiente

```bash
# Clonar o repositório
git clone <repository-url>
cd eda-aiminds-i2a2-rb

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração do Banco de Dados

```bash
# Configurar .env
cp configs/.env.example configs/.env

# Editar configs/.env com suas credenciais
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_anon_key
DB_HOST=db.xyz.supabase.co
DB_PASSWORD=your_db_password
```

### 3. Executar Migrations

```bash
# Executar todas as migrations
python scripts/run_migrations.py

# Verificar conexão
python check_db.py  # Deve retornar "Conexão OK"
```

## 🏗️ Arquitetura do Código

### Estrutura de Diretórios

```
src/
├── memory/                    # 🧠 Sistema de memória
│   ├── __init__.py           # Exports principais
│   ├── base_memory.py        # Interface abstrata
│   ├── supabase_memory.py    # Implementação Supabase
│   ├── memory_types.py       # Tipos de dados
│   └── memory_utils.py       # Utilitários
├── agent/                    # 🤖 Agentes multiagente
│   ├── base_agent.py         # Classe base com memória
│   ├── orchestrator_agent.py # Orquestrador principal
│   ├── csv_analysis_agent.py # Análise de CSV
│   └── rag_agent.py          # Busca RAG
└── vectorstore/              # 🗃️ Armazenamento vetorial
    └── supabase_client.py    # Cliente Supabase
```

### Imports Essenciais

```python
# Sistema de memória
from src.memory import (
    SupabaseMemoryManager,
    MemoryMixin,
    SessionInfo,
    ConversationMessage,
    AgentContext,
    MemoryEmbedding,
    MessageType,
    ContextType
)

# Agentes com memória
from src.agent.base_agent import BaseAgent
from src.agent.orchestrator_agent import OrchestratorAgent

# Configurações
from src.settings import SUPABASE_URL, SUPABASE_KEY
```

## 🧩 Implementação Básica

### 1. Criando um Novo Agente com Memória

```python
from src.agent.base_agent import BaseAgent
from src.memory import SupabaseMemoryManager, MessageType
from typing import Dict, Any, Optional

class CustomAnalysisAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        # Memória é inicializada automaticamente pela classe base
        
    async def analyze_data(self, data: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """Analisar dados com memória persistente."""
        
        # 1. Verificar se análise similar já foi feita (cache)
        cache_key = self._generate_cache_key(data, user_query)
        cached_result = await self._get_cached_analysis(cache_key)
        
        if cached_result:
            await self.remember_response(
                f"Resultado do cache: {cached_result['summary']}",
                metadata={"from_cache": True}
            )
            return cached_result
            
        # 2. Lembrar a query do usuário
        await self.remember_query(user_query)
        
        # 3. Executar análise
        analysis_result = await self._perform_analysis(data, user_query)
        
        # 4. Salvar resultado no cache
        await self._cache_analysis(cache_key, analysis_result)
        
        # 5. Lembrar a resposta
        await self.remember_response(
            f"Análise concluída: {analysis_result['summary']}",
            processing_time_ms=analysis_result.get('processing_time'),
            confidence=analysis_result.get('confidence', 0.8)
        )
        
        return analysis_result
    
    def _generate_cache_key(self, data: Dict[str, Any], query: str) -> str:
        """Gerar chave de cache baseada nos dados e query."""
        import hashlib
        
        # Criar hash dos dados (simplificado)
        data_str = str(sorted(data.items()))
        combined = f"{data_str}:{query}"
        
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Recuperar análise do cache."""
        if not self.has_memory:
            return None
            
        try:
            context = await self.memory_manager.get_context(
                session_id=self.current_session,
                context_type=ContextType.ANALYSIS_CACHE,
                context_key=cache_key
            )
            return context.context_data if context else None
        except Exception as e:
            self.logger.warning(f"Erro ao acessar cache: {e}")
            return None
    
    async def _cache_analysis(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Salvar análise no cache."""
        if not self.has_memory:
            return
            
        try:
            await self.memory_manager.save_context(
                session_id=self.current_session,
                context_type=ContextType.ANALYSIS_CACHE,
                context_key=cache_key,
                context_data=result,
                expires_in_hours=24  # Cache por 24 horas
            )
        except Exception as e:
            self.logger.warning(f"Erro ao salvar cache: {e}")
    
    async def _perform_analysis(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Executar análise real dos dados."""
        # Implementar lógica de análise específica
        import time
        start_time = time.time()
        
        # Simular análise
        await asyncio.sleep(0.1)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "summary": f"Análise de {len(data)} campos completada",
            "insights": ["Insight 1", "Insight 2"],
            "processing_time": processing_time,
            "confidence": 0.85
        }
```

### 2. Usando Memória em Agentes Existentes

```python
# Exemplo: Adicionar funcionalidade de memória a função existente
async def enhanced_process_query(self, query: str, context: Optional[Dict] = None) -> str:
    """Processar query com contexto de memória."""
    
    # 1. Inicializar memória se não estiver ativa
    if not self.current_session:
        await self.init_memory()
    
    # 2. Recuperar contexto da conversa anterior
    conversation_context = await self.recall_context(hours_back=24)
    
    # 3. Combinar contexto atual com histórico
    full_context = {
        **(context or {}),
        **conversation_context
    }
    
    # 4. Lembrar query do usuário
    await self.remember_query(query)
    
    # 5. Processar com contexto completo
    result = await self._process_with_llm(query, full_context)
    
    # 6. Lembrar resposta
    await self.remember_response(result)
    
    return result
```

### 3. Implementando Cache Inteligente

```python
class SmartCacheManager:
    """Gerenciador de cache inteligente com TTL e LRU."""
    
    def __init__(self, memory_manager: SupabaseMemoryManager):
        self.memory_manager = memory_manager
        self._local_cache = {}  # Cache em memória para acesso rápido
        self._access_times = {}  # Para implementar LRU
        self.max_local_cache_size = 100
        
    async def get_or_compute(
        self, 
        cache_key: str, 
        compute_func: Callable,
        ttl_hours: int = 24
    ) -> Any:
        """Obter do cache ou computar se não existir."""
        
        # 1. Verificar cache local primeiro
        if cache_key in self._local_cache:
            self._access_times[cache_key] = time.time()
            return self._local_cache[cache_key]
        
        # 2. Verificar cache persistente
        cached_context = await self.memory_manager.get_context(
            session_id=self.memory_manager.current_session,
            context_type=ContextType.ANALYSIS_CACHE,
            context_key=cache_key
        )
        
        if cached_context and not cached_context.is_expired():
            # Carregar no cache local
            self._local_cache[cache_key] = cached_context.context_data
            self._access_times[cache_key] = time.time()
            return cached_context.context_data
        
        # 3. Computar novo resultado
        result = await compute_func()
        
        # 4. Salvar em ambos os caches
        await self._save_to_caches(cache_key, result, ttl_hours)
        
        return result
    
    async def _save_to_caches(self, cache_key: str, data: Any, ttl_hours: int):
        """Salvar em cache local e persistente."""
        
        # Cache local com LRU
        if len(self._local_cache) >= self.max_local_cache_size:
            self._evict_lru()
        
        self._local_cache[cache_key] = data
        self._access_times[cache_key] = time.time()
        
        # Cache persistente
        await self.memory_manager.save_context(
            session_id=self.memory_manager.current_session,
            context_type=ContextType.ANALYSIS_CACHE,
            context_key=cache_key,
            context_data=data,
            expires_in_hours=ttl_hours
        )
    
    def _evict_lru(self):
        """Remover item menos recentemente usado."""
        if not self._access_times:
            return
            
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._local_cache[lru_key]
        del self._access_times[lru_key]
```

## 🔧 Patterns e Melhores Práticas

### 1. Pattern: Session Initialization

```python
async def ensure_memory_session(self) -> str:
    """Garantir que sessão de memória está ativa."""
    if not self.current_session:
        session_id = await self.init_memory()
        self.logger.info(f"Nova sessão de memória criada: {session_id}")
        return session_id
    return self.current_session
```

### 2. Pattern: Context Enrichment

```python
async def enrich_context_with_memory(self, base_context: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquecer contexto com dados da memória."""
    
    memory_context = await self.recall_context(hours_back=24)
    
    enriched_context = {
        **base_context,
        "conversation_history": memory_context.get("recent_conversations", []),
        "user_preferences": memory_context.get("user_preferences", {}),
        "previous_analyses": memory_context.get("analysis_history", []),
        "learned_patterns": memory_context.get("learned_patterns", {})
    }
    
    return enriched_context
```

### 3. Pattern: Error Recovery

```python
async def safe_memory_operation(self, operation: Callable) -> Any:
    """Executar operação de memória com fallback."""
    try:
        return await operation()
    except Exception as e:
        self.logger.warning(f"Operação de memória falhou: {e}")
        
        # Fallback: continuar sem memória
        if hasattr(self, '_fallback_mode'):
            self._fallback_mode = True
        
        return None
```

### 4. Pattern: Adaptive Learning

```python
async def learn_from_interaction(self, query: str, response: str, user_feedback: Optional[float] = None):
    """Aprender com interação para melhorar respostas futuras."""
    
    # Extrair padrões da query
    query_patterns = self._extract_patterns(query)
    
    # Salvar padrão aprendido
    for pattern in query_patterns:
        await self.memory_manager.save_context(
            session_id=self.current_session,
            context_type=ContextType.LEARNING_PATTERN,
            context_key=f"pattern_{pattern}",
            context_data={
                "pattern": pattern,
                "query": query,
                "response": response,
                "feedback": user_feedback,
                "confidence": self._calculate_confidence(query, response),
                "timestamp": datetime.now().isoformat()
            }
        )
```

## 🧪 Testing e Debugging

### 1. Testes Unitários

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestCustomAnalysisAgent:
    
    @pytest.fixture
    def mock_memory_manager(self):
        mock_manager = AsyncMock()
        mock_manager.initialize_session = AsyncMock(return_value="test_session")
        mock_manager.add_user_query = AsyncMock()
        mock_manager.add_agent_response = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def agent(self, mock_memory_manager):
        with patch('src.agent.base_agent.SupabaseMemoryManager') as mock_class:
            mock_class.return_value = mock_memory_manager
            agent = CustomAnalysisAgent("test_agent")
            agent.memory_manager = mock_memory_manager
            return agent
    
    @pytest.mark.asyncio
    async def test_analyze_data_with_cache(self, agent, mock_memory_manager):
        # Mock cache hit
        mock_memory_manager.get_context.return_value = Mock(
            context_data={"summary": "Cached analysis", "from_cache": True}
        )
        
        result = await agent.analyze_data(
            {"col1": [1, 2, 3]}, 
            "Analyze this data"
        )
        
        assert result["from_cache"] is True
        assert "Cached analysis" in result["summary"]
```

### 2. Debugging

```python
# Habilitar logs detalhados
import logging
logging.getLogger('src.memory').setLevel(logging.DEBUG)

# Verificar estado da memória
async def debug_memory_state(agent):
    """Debug do estado atual da memória."""
    
    print(f"Sessão ativa: {agent.current_session}")
    print(f"Tem memória: {agent.has_memory}")
    
    if agent.has_memory:
        context = await agent.recall_context()
        print(f"Contexto: {len(context)} itens")
        
        for key, value in context.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} itens")
            else:
                print(f"  {key}: {type(value)}")
```

### 3. Performance Monitoring

```python
import time
import functools

def monitor_memory_performance(func):
    """Decorator para monitorar performance de operações de memória."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            # Log performance
            logger = logging.getLogger('memory.performance')
            logger.info(f"{func.__name__}: {duration:.2f}ms")
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    
    return wrapper

# Uso
@monitor_memory_performance
async def expensive_memory_operation(self):
    # Operação custosa
    pass
```

## 🔍 Troubleshooting Comum

### 1. Problema: Sessão não Inicializada

```python
# ❌ Erro comum
async def process_query(self, query: str):
    await self.remember_query(query)  # Pode falhar se sessão não existe

# ✅ Solução
async def process_query(self, query: str):
    await self.ensure_memory_session()
    await self.remember_query(query)
```

### 2. Problema: Memory Leak

```python
# ❌ Cache cresce indefinidamente
self._cache[key] = large_data

# ✅ Cache com TTL e limpeza
self._cache[key] = {
    'data': large_data,
    'timestamp': time.time(),
    'ttl': 3600  # 1 hora
}

# Limpeza periódica
await self._cleanup_expired_cache()
```

### 3. Problema: Dados Grandes

```python
# ❌ Armazenar dataframe completo
await self.store_context("dataframe", df.to_dict())

# ✅ Armazenar resumo + hash
summary = {
    'shape': df.shape,
    'columns': df.columns.tolist(),
    'dtypes': df.dtypes.to_dict(),
    'sample': df.head().to_dict(),
    'hash': hashlib.md5(df.to_string().encode()).hexdigest()
}
await self.store_context("dataframe_summary", summary)
```

## 📚 Referências Rápidas

### Métodos Principais do MemoryMixin

```python
# Inicialização
session_id = await agent.init_memory()

# Lembrança
await agent.remember_query("Como analisar dados?")
await agent.remember_response("Aqui está a análise...", processing_time_ms=1500)

# Recuperação
context = await agent.recall_context(hours_back=24)

# Verificação
if agent.has_memory:
    # Operações com memória
    pass
```

### Tipos de Contexto Comuns

```python
ContextType.DATA                # Dados/datasets carregados
ContextType.USER_PREFERENCE     # Preferências do usuário
ContextType.ANALYSIS_CACHE      # Cache de análises
ContextType.SEARCH_CACHE        # Cache de buscas
ContextType.LEARNING_PATTERN    # Padrões aprendidos
```

### Configurações de Performance

```python
# Configurar TTL do cache
cache_config = {
    'analysis_cache_ttl': 24,      # 24 horas
    'search_cache_ttl': 12,        # 12 horas  
    'session_ttl': 48,             # 48 horas
    'max_context_size': 1024*1024  # 1MB
}
```

---

## 🎓 Próximos Passos

1. **Estudar** os exemplos nos arquivos de teste
2. **Experimentar** com agentes simples primeiro
3. **Implementar** cache inteligente gradualmente
4. **Monitorar** performance e ajustar conforme necessário
5. **Contribuir** com melhorias e patterns descobertos

Para dúvidas específicas, consulte os testes em `tests/memory/` ou a documentação de arquitetura em `docs/sistema-memoria-arquitetura.md`.