# 🔍 Auditoria Técnica: Rastreabilidade de Arquivos CSV entre Frontend e Backend

**Data:** 2025-10-10  
**Sistema:** EDA AI Minds - Sistema Multiagente  
**Objetivo:** Investigar identificação e rastreabilidade de arquivos CSV desde o upload até os embeddings

---

## 📋 Executive Summary

### Conclusão Principal
**❌ NÃO EXISTE** identificador único persistido no backend que correlacione com o `id` gerado pelo frontend (`csv_20251010_134412`).

### Situação Atual
O sistema armazena **apenas o path do arquivo** no campo `metadata.source`:
```json
{
  "source": "data\\processando\\creditcard.csv"
}
```

### Impacto
- ❌ Impossível correlacionar embeddings com arquivos específicos enviados pelo frontend
- ❌ Sem rastreabilidade entre múltiplos uploads do mesmo arquivo
- ❌ Sem histórico de versões ou diferentes uploads
- ❌ Dificuldade para deletar/atualizar embeddings de um arquivo específico

---

## 1️⃣ Análise Completa da Cadeia de Ingestão

### 🔄 Fluxo de Dados Identificado

```
FRONTEND                    BACKEND                         SUPABASE
════════                    ═══════                         ════════

1. Gera ID único            
   csv_20251010_134412
         │
         ├─> Upload via API ──────> 2. Recebe arquivo CSV
         │                              │
         │                              ├─> GoogleDriveClient.download()
         │                              │
         │                              ├─> DataIngestor.ingest_csv()
         │                              │   ou
         │                              │   RAGAgent.ingest_csv_file()
         │                              │
         │                              └─> Chunking + Embeddings
         │                                      │
         │                                      └─> VectorStore.store_embeddings()
         │                                              │
         └─ ID PERDIDO! ─────────────────────────────> 3. Persiste embeddings
                                                           └─> metadata: {"source": "path"}
                                                               ❌ SEM ID DO FRONTEND
```

---

## 2️⃣ Análise de Campos e Estruturas de Dados

### 2.1 Schema da Tabela `embeddings` (Supabase)

**Arquivo:** `migrations/0002_schema.sql`

```sql
create table if not exists public.embeddings (
    id uuid primary key default gen_random_uuid(),      -- UUID gerado pelo Supabase
    chunk_text text not null,                           -- Conteúdo textual do chunk
    embedding vector(1536) not null,                    -- Vetor 1536D (OpenAI dims)
    metadata jsonb default '{}'::jsonb,                 -- Metadados em formato JSON
    created_at timestamp with time zone default now()
);
```

**Campos Disponíveis:**
- ✅ `id` - UUID único do embedding (gerado pelo Supabase)
- ✅ `chunk_text` - Texto do chunk
- ✅ `embedding` - Vetor de embeddings
- ⚠️ `metadata` - **Campo JSONB onde o ID do frontend DEVE ser armazenado**
- ✅ `created_at` - Timestamp de criação

---

### 2.2 Estrutura do Campo `metadata` (Atual)

#### 📁 DataIngestor (Simplificado - 2 chunks)

**Arquivo:** `src/agent/data_ingestor.py` (Linha 186)

```python
self.supabase.table('embeddings').insert({
    'chunk_text': chunk,
    'embedding': embedding,
    'metadata': {'source': csv_path}  # ❌ APENAS O PATH DO ARQUIVO
}).execute()
```

**Metadata Resultante:**
```json
{
  "source": "data\\processando\\creditcard.csv"
}
```

**❌ Problemas:**
- Sem identificador único do arquivo
- Sem informações sobre upload
- Sem rastreabilidade de versões

---

#### 📊 RAGAgent (Completo - 633 chunks)

**Arquivo:** `src/embeddings/vector_store.py` (Linhas 168-179)

```python
metadata = {
    "provider": result.provider.value,           # Ex: "sentence_transformer"
    "model": result.model,                       # Ex: "all-MiniLM-L6-v2"
    "dimensions": result.dimensions,             # Ex: 384
    "raw_dimensions": result.raw_dimensions,     
    "processing_time": result.processing_time,   # Tempo de processamento
    "source_type": source_type,                  # Ex: "csv"
    "created_at": datetime.now().isoformat()     # Timestamp ISO
}

# Adicionar metadados do chunk se disponíveis
if result.chunk_metadata:
    metadata.update(result.chunk_metadata)
```

**Metadados do Chunk** (`ChunkMetadata` - `src/embeddings/chunker.py` linhas 27-38):

```python
@dataclass
class ChunkMetadata:
    """Metadados de um chunk."""
    source: str                      # ❌ Apenas o path do arquivo
    chunk_index: int                 # Índice do chunk
    strategy: ChunkStrategy          # Estratégia de chunking (CSV_ROW, FIXED_SIZE)
    char_count: int                  # Contagem de caracteres
    word_count: int                  # Contagem de palavras
    start_position: int              # Posição inicial no texto
    end_position: int                # Posição final no texto
    overlap_with_previous: int = 0   # Overlap com chunk anterior
    additional_info: Dict[str, Any] = None  # ⚠️ CAMPO EXTENSÍVEL!
```

**Metadata Consolidada (Exemplo Real):**
```json
{
  "provider": "sentence_transformer",
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "raw_dimensions": 384,
  "processing_time": 0.045,
  "source_type": "csv",
  "created_at": "2025-10-10T12:40:39.176000",
  "source": "data/creditcard.csv",       // ❌ Apenas path
  "chunk_index": 0,
  "strategy": "csv_row",
  "char_count": 1024,
  "word_count": 187,
  "start_position": 0,
  "end_position": 1024,
  "overlap_with_previous": 0,
  "additional_info": {                   // ⚠️ CAMPO EXTENSÍVEL!
    "chunk_type": "metadata_types",
    "topic": "data_types_structure"
  }
}
```

**✅ Campo Extensível Identificado:**
- `additional_info: Dict[str, Any]` - **Pode receber o ID do frontend!**

---

### 2.3 Análise do Fluxo `interface_interativa.py`

**Arquivo:** `interface_interativa.py` (Linhas 170-178)

```python
# Gerar session_id único para esta sessão de chat
session_id = str(uuid4())
safe_print(f"🔑 Sessão iniciada: {session_id[:8]}...\n")

# INTEGRAÇÃO: Executar ingestão do dataset antes de inicializar orchestrador
safe_print("🧹 Limpando base vetorial e carregando dataset...")
from src.agent.data_ingestor import DataIngestor
ingestor = DataIngestor()
ingestor.ingest_csv('data/creditcard.csv')  # ❌ SEM ID DE ARQUIVO
safe_print("✅ Dataset creditcard.csv carregado e base vetorial atualizada!\n")
```

**❌ Observação Crítica:**
- `interface_interativa.py` gera `session_id` (UUID da sessão de chat)
- **NÃO gera** `file_id` único para o arquivo CSV
- Chama `ingestor.ingest_csv()` **sem passar identificador**

---

### 2.4 Análise do Fluxo `auto_ingest_service.py`

**Arquivo:** `src/services/auto_ingest_service.py` (Linhas 265-280)

```python
# 2. Executa ingestão usando DataIngestor
logger.info("  → Executando ingestão no Supabase (DataIngestor)...")

# Executar ingestão (limpa base + analisa + chunking + embeddings)
self.data_ingestor.ingest_csv(str(download_path))  # ❌ SEM ID DE ARQUIVO
logger.info("  ✅ Ingestão concluída com sucesso")
```

**❌ Observação:**
- Recebe arquivo do Google Drive
- **NÃO gera** identificador único
- Chama `ingest_csv()` apenas com path

---

## 3️⃣ Resposta às Questões da Auditoria

### 3.1 Existe lógica de criação de identificador no backend?

**❌ NÃO.** O backend **não cria** identificador próprio para arquivos CSV.

**Evidências:**
1. `DataIngestor.ingest_csv()` recebe apenas `csv_path: str`
2. `RAGAgent.ingest_csv_file()` recebe `file_path` e `source_id`, mas `source_id` não é usado como ID único rastreável
3. Nenhum UUID ou hash é gerado para o arquivo

---

### 3.2 Algum campo armazena identificador correlacionável com o frontend?

**❌ NÃO.** Nenhum campo atual permite correlação direta.

**Campos Analisados:**
- ✅ `embeddings.id` - UUID do embedding (gerado pelo Supabase, não relacionado ao arquivo)
- ❌ `embeddings.chunk_text` - Apenas conteúdo textual
- ⚠️ `embeddings.metadata` - **Campo JSON extensível, mas atualmente só tem path**
- ❌ `embeddings.created_at` - Timestamp de criação

---

### 3.3 Sugestão de Extensão: Onde adicionar o ID do frontend?

### ✅ SOLUÇÃO RECOMENDADA

**Campo Alvo:** `embeddings.metadata` (JSONB)

**Proposta de Estrutura:**
```json
{
  // ====== IDENTIFICAÇÃO DO ARQUIVO (NOVO) ======
  "file_id": "csv_20251010_134412",              // ✅ ID do frontend
  "file_name": "creditcard.csv",                 // ✅ Nome original
  "file_hash": "sha256:abc123...",               // ✅ Hash para deduplicação
  "upload_timestamp": "2025-10-10T13:44:12Z",    // ✅ Timestamp do upload
  "upload_source": "google_drive",               // ✅ Origem (drive/local/api)
  
  // ====== METADADOS DE PROCESSAMENTO (EXISTENTES) ======
  "provider": "sentence_transformer",
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "processing_time": 0.045,
  "source_type": "csv",
  "created_at": "2025-10-10T12:40:39.176000",
  
  // ====== METADADOS DO CHUNK (EXISTENTES) ======
  "source": "data/creditcard.csv",               // Path local
  "chunk_index": 0,
  "strategy": "csv_row",
  "char_count": 1024,
  "word_count": 187,
  "additional_info": {
    "chunk_type": "metadata_types",
    "topic": "data_types_structure"
  }
}
```

---

## 4️⃣ Implementação Recomendada

### 4.1 Onde Gerar o ID?

#### ✅ Opção 1: Gerar no Frontend (Recomendado)

**Vantagens:**
- ✅ Frontend já gera IDs (`csv_20251010_134412`)
- ✅ ID disponível desde o início do upload
- ✅ Facilita tracking na UI
- ✅ Permite retry com mesmo ID

**Fluxo:**
```typescript
// Frontend (TypeScript/JavaScript)
const fileId = `csv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Upload via API
await uploadCSV({
  file: csvFile,
  fileId: fileId,          // ✅ Envia ID para backend
  fileName: csvFile.name,
  uploadSource: 'web_ui'
});
```

---

#### ⚠️ Opção 2: Gerar no Backend

**Vantagens:**
- ✅ Backend controla unicidade
- ✅ Pode usar hash do conteúdo

**Desvantagens:**
- ❌ Frontend não conhece o ID imediatamente
- ❌ Requer API para retornar o ID gerado

**Fluxo:**
```python
# Backend (Python)
import hashlib
from datetime import datetime

def generate_file_id(file_path: str, content: bytes = None) -> str:
    """Gera ID único para arquivo CSV."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if content:
        # Usar hash do conteúdo para deduplicação
        file_hash = hashlib.sha256(content).hexdigest()[:12]
        return f"csv_{timestamp}_{file_hash}"
    else:
        # Fallback para UUID
        import uuid
        return f"csv_{timestamp}_{uuid.uuid4().hex[:12]}"
```

---

### 4.2 Modificações no Código Backend

#### 📝 Modificação 1: `DataIngestor.ingest_csv()`

**Arquivo:** `src/agent/data_ingestor.py`

**Estado Atual (Linha 173-189):**
```python
def ingest_csv(self, csv_path):
    self.clean_vector_db()
    logger.info(f"Processando CSV: {csv_path}")
    md_text = self.analyze_csv(csv_path)
    chunks = self.chunk_text(md_text)
    logger.info(f"Gerando embeddings e inserindo {len(chunks)} chunks...")
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        self.supabase.table('embeddings').insert({
            'chunk_text': chunk,
            'embedding': embedding,
            'metadata': {'source': csv_path}  # ❌ PROBLEMA AQUI
        }).execute()
    logger.info("Ingestão concluída com sucesso.")
```

**✅ Proposta de Modificação:**
```python
def ingest_csv(self, 
               csv_path: str, 
               file_id: Optional[str] = None,
               file_name: Optional[str] = None,
               upload_source: str = "local",
               file_hash: Optional[str] = None):
    """Ingesta CSV com rastreabilidade completa.
    
    Args:
        csv_path: Path do arquivo CSV
        file_id: ID único do frontend (ex: csv_20251010_134412)
        file_name: Nome original do arquivo
        upload_source: Origem do upload (google_drive, web_ui, local)
        file_hash: Hash SHA256 do conteúdo (opcional)
    """
    self.clean_vector_db()
    logger.info(f"Processando CSV: {csv_path} (ID: {file_id})")
    
    # Gerar file_id se não fornecido
    if not file_id:
        from datetime import datetime
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"csv_{timestamp}_{uuid.uuid4().hex[:8]}"
        logger.warning(f"file_id não fornecido, gerando: {file_id}")
    
    # Extrair nome do arquivo se não fornecido
    if not file_name:
        from pathlib import Path
        file_name = Path(csv_path).name
    
    # Calcular hash se não fornecido
    if not file_hash:
        import hashlib
        with open(csv_path, 'rb') as f:
            file_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()[:16]}"
    
    md_text = self.analyze_csv(csv_path)
    chunks = self.chunk_text(md_text)
    
    logger.info(f"Gerando embeddings e inserindo {len(chunks)} chunks...")
    upload_timestamp = datetime.now().isoformat()
    
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        
        # ✅ METADATA ENRIQUECIDA COM RASTREABILIDADE
        metadata = {
            # Identificação do arquivo
            'file_id': file_id,
            'file_name': file_name,
            'file_hash': file_hash,
            'upload_timestamp': upload_timestamp,
            'upload_source': upload_source,
            
            # Path local (mantido para compatibilidade)
            'source': csv_path,
            
            # Tipo de processamento
            'ingestor_type': 'DataIngestor',
            'ingestor_version': '1.0-deprecated'
        }
        
        self.supabase.table('embeddings').insert({
            'chunk_text': chunk,
            'embedding': embedding,
            'metadata': metadata
        }).execute()
    
    logger.info(f"Ingestão concluída: {len(chunks)} chunks com file_id={file_id}")
```

---

#### 📝 Modificação 2: `RAGAgent.ingest_csv_file()`

**Arquivo:** `src/agent/rag_agent.py`

**Estado Atual (Linhas 179-216):**
```python
def ingest_csv_file(self,
                   file_path: str,
                   source_id: str,
                   encoding: str = "utf-8") -> Dict[str, Any]:
    """Ingesta arquivo CSV usando estratégia otimizada CSV_ROW."""
    # ... (código atual sem file_id)
```

**✅ Proposta de Modificação:**
```python
def ingest_csv_file(self,
                   file_path: str,
                   source_id: str,
                   encoding: str = "utf-8",
                   file_id: Optional[str] = None,
                   file_name: Optional[str] = None,
                   upload_source: str = "local",
                   file_hash: Optional[str] = None) -> Dict[str, Any]:
    """Ingesta arquivo CSV usando estratégia otimizada CSV_ROW com rastreabilidade.
    
    Args:
        file_path: Path do arquivo CSV
        source_id: Identificador da fonte (usado como prefixo)
        encoding: Encoding do arquivo
        file_id: ID único do frontend (ex: csv_20251010_134412)
        file_name: Nome original do arquivo
        upload_source: Origem do upload (google_drive, web_ui, local)
        file_hash: Hash SHA256 do conteúdo (opcional)
    """
    # Gerar file_id se não fornecido
    if not file_id:
        from datetime import datetime
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"csv_{timestamp}_{uuid.uuid4().hex[:8]}"
        self.logger.warning(f"file_id não fornecido, gerando: {file_id}")
    
    # Extrair nome do arquivo se não fornecido
    if not file_name:
        from pathlib import Path
        file_name = Path(file_path).name
    
    # Calcular hash se não fornecido
    if not file_hash:
        import hashlib
        with open(file_path, 'rb') as f:
            file_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()[:16]}"
    
    self.logger.info(f"🔄 Ingestão CSV: {file_path} (file_id={file_id})")
    
    # ... (resto do código de ingestão)
    
    # Ao criar chunks, adicionar metadados do arquivo
    # Modificar ChunkMetadata.additional_info
    for chunk in chunks:
        if chunk.metadata.additional_info is None:
            chunk.metadata.additional_info = {}
        
        # ✅ ADICIONAR RASTREABILIDADE
        chunk.metadata.additional_info.update({
            'file_id': file_id,
            'file_name': file_name,
            'file_hash': file_hash,
            'upload_timestamp': datetime.now().isoformat(),
            'upload_source': upload_source
        })
    
    # ... (continuar com embedding e armazenamento)
```

---

#### 📝 Modificação 3: `auto_ingest_service.py`

**Arquivo:** `src/services/auto_ingest_service.py` (Linhas 265-280)

**Estado Atual:**
```python
# Executar ingestão (limpa base + analisa + chunking + embeddings)
self.data_ingestor.ingest_csv(str(download_path))
```

**✅ Proposta de Modificação:**
```python
# Gerar file_id único para este arquivo
from datetime import datetime
import hashlib

file_name = file['name']
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Calcular hash do arquivo para deduplicação
with open(download_path, 'rb') as f:
    content_hash = hashlib.sha256(f.read()).hexdigest()[:12]

file_id = f"csv_{timestamp}_{content_hash}"

logger.info(f"  📌 file_id gerado: {file_id}")

# Executar ingestão com rastreabilidade
self.data_ingestor.ingest_csv(
    csv_path=str(download_path),
    file_id=file_id,
    file_name=file_name,
    upload_source="google_drive",
    file_hash=f"sha256:{content_hash}"
)
```

---

#### 📝 Modificação 4: Endpoint da API (se houver upload direto)

**Arquivo Hipotético:** `src/api/upload_endpoint.py`

```python
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

router = APIRouter()

@router.post("/api/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    file_id: Optional[str] = Form(None),  # ✅ Recebe ID do frontend
    upload_source: str = Form("web_ui")
):
    """Endpoint para upload de CSV com rastreabilidade."""
    
    # Salvar arquivo temporariamente
    temp_path = f"data/processando/{file.filename}"
    content = await file.read()
    
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    # Gerar file_id se não fornecido pelo frontend
    if not file_id:
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.sha256(content).hexdigest()[:12]
        file_id = f"csv_{timestamp}_{content_hash}"
    
    # Calcular hash
    import hashlib
    file_hash = f"sha256:{hashlib.sha256(content).hexdigest()[:16]}"
    
    # Executar ingestão
    from src.agent.data_ingestor import DataIngestor
    ingestor = DataIngestor()
    
    ingestor.ingest_csv(
        csv_path=temp_path,
        file_id=file_id,
        file_name=file.filename,
        upload_source=upload_source,
        file_hash=file_hash
    )
    
    return {
        "status": "success",
        "file_id": file_id,          # ✅ Retorna ID para o frontend
        "file_name": file.filename,
        "file_hash": file_hash,
        "message": "CSV ingerido com sucesso"
    }
```

---

### 4.3 Consultas e Operações com `file_id`

#### 🔍 Buscar Embeddings por `file_id`

```python
def get_embeddings_by_file_id(file_id: str) -> List[Dict]:
    """Busca todos embeddings de um arquivo específico."""
    from src.vectorstore.supabase_client import supabase
    
    response = supabase.table('embeddings') \
        .select('*') \
        .filter('metadata->>file_id', 'eq', file_id) \
        .execute()
    
    return response.data
```

#### 🗑️ Deletar Embeddings por `file_id`

```python
def delete_embeddings_by_file_id(file_id: str) -> int:
    """Deleta todos embeddings de um arquivo específico."""
    from src.vectorstore.supabase_client import supabase
    
    # Buscar IDs dos embeddings
    response = supabase.table('embeddings') \
        .select('id') \
        .filter('metadata->>file_id', 'eq', file_id) \
        .execute()
    
    embedding_ids = [row['id'] for row in response.data]
    
    # Deletar em batch
    for embedding_id in embedding_ids:
        supabase.table('embeddings').delete().eq('id', embedding_id).execute()
    
    return len(embedding_ids)
```

#### 📊 Listar Arquivos Ingeridos

```python
def list_ingested_files() -> List[Dict]:
    """Lista todos arquivos CSV ingeridos com estatísticas."""
    from src.vectorstore.supabase_client import supabase
    
    # Buscar embeddings únicos por file_id
    response = supabase.table('embeddings') \
        .select('metadata') \
        .execute()
    
    files = {}
    for row in response.data:
        metadata = row['metadata']
        file_id = metadata.get('file_id')
        
        if file_id and file_id not in files:
            files[file_id] = {
                'file_id': file_id,
                'file_name': metadata.get('file_name'),
                'file_hash': metadata.get('file_hash'),
                'upload_timestamp': metadata.get('upload_timestamp'),
                'upload_source': metadata.get('upload_source'),
                'chunk_count': 0
            }
        
        if file_id:
            files[file_id]['chunk_count'] += 1
    
    return list(files.values())
```

---

## 5️⃣ Exemplos Práticos de Uso

### Exemplo 1: Upload pelo Frontend com ID

```typescript
// Frontend (React/TypeScript)
async function handleCSVUpload(file: File) {
  // Gerar ID único
  const fileId = `csv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_id', fileId);
  formData.append('upload_source', 'web_ui');
  
  const response = await fetch('/api/upload-csv', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  console.log('Arquivo ingerido:', result.file_id);
  
  // Salvar file_id no estado da aplicação
  setUploadedFiles(prev => [...prev, {
    id: result.file_id,
    name: result.file_name,
    hash: result.file_hash,
    uploadedAt: new Date()
  }]);
}
```

### Exemplo 2: Consulta de Embeddings por Arquivo

```python
# Backend - Consultar embeddings de arquivo específico
from src.vectorstore.supabase_client import supabase

file_id = "csv_20251010_134412"

# Buscar todos chunks deste arquivo
response = supabase.table('embeddings') \
    .select('chunk_text, metadata') \
    .filter('metadata->>file_id', 'eq', file_id) \
    .execute()

print(f"Encontrados {len(response.data)} chunks para file_id={file_id}")

for chunk in response.data:
    print(f"Chunk {chunk['metadata']['chunk_index']}: {chunk['chunk_text'][:100]}...")
```

### Exemplo 3: Deletar Arquivo e Seus Embeddings

```python
# Backend - Deletar todos embeddings de um arquivo
from src.vectorstore.supabase_client import supabase

file_id = "csv_20251010_134412"

# Contar embeddings antes
count_before = supabase.table('embeddings') \
    .select('id', count='exact') \
    .filter('metadata->>file_id', 'eq', file_id) \
    .execute()

print(f"Encontrados {count_before.count} embeddings para deletar")

# Deletar (PostgreSQL suporta delete com filtro JSONB)
delete_response = supabase.table('embeddings') \
    .delete() \
    .filter('metadata->>file_id', 'eq', file_id) \
    .execute()

print(f"Deletados com sucesso")
```

---

## 6️⃣ Benefícios da Implementação

### ✅ Rastreabilidade Total
- Correlação direta entre frontend e backend
- Histórico completo de uploads
- Auditoria de processamentos

### ✅ Gestão de Arquivos
- Deletar embeddings de arquivos específicos
- Atualizar versões sem conflitos
- Detectar duplicatas via hash

### ✅ Debugging e Monitoramento
- Identificar origem de embeddings problemáticos
- Logs mais informativos
- Métricas por arquivo

### ✅ Features Futuras
- Versionamento de arquivos
- Comparação entre versões
- Rollback de ingestões

---

## 7️⃣ Checklist de Implementação

### Fase 1: Backend (Obrigatório)
- [ ] Modificar `DataIngestor.ingest_csv()` para aceitar `file_id`
- [ ] Modificar `RAGAgent.ingest_csv_file()` para aceitar `file_id`
- [ ] Atualizar `auto_ingest_service.py` para gerar `file_id`
- [ ] Criar funções auxiliares (get/delete by file_id)
- [ ] Atualizar testes unitários

### Fase 2: API (se houver upload direto)
- [ ] Criar/atualizar endpoint `/api/upload-csv`
- [ ] Adicionar parâmetro `file_id` no endpoint
- [ ] Retornar `file_id` na resposta
- [ ] Documentar API (Swagger/OpenAPI)

### Fase 3: Frontend (se houver)
- [ ] Gerar `file_id` antes do upload
- [ ] Enviar `file_id` na requisição
- [ ] Armazenar `file_id` no estado local
- [ ] Implementar listagem de arquivos
- [ ] Implementar delete de arquivos

### Fase 4: Documentação
- [ ] Atualizar README com novo fluxo
- [ ] Documentar estrutura do metadata
- [ ] Criar guia de migração para dados existentes
- [ ] Adicionar exemplos de uso

---

## 8️⃣ Migração de Dados Existentes

### Problema: Embeddings sem `file_id`

Embeddings já armazenados **não têm** `file_id`. Como migrar?

### Opção 1: Inferir file_id a partir do path

```python
from src.vectorstore.supabase_client import supabase
from datetime import datetime
import hashlib

# Buscar todos embeddings sem file_id
response = supabase.table('embeddings') \
    .select('id, metadata') \
    .execute()

for row in response.data:
    metadata = row['metadata']
    
    # Se já tem file_id, pular
    if 'file_id' in metadata:
        continue
    
    # Inferir file_id a partir do source path
    source_path = metadata.get('source', '')
    
    if source_path:
        # Gerar file_id baseado no path + timestamp
        path_hash = hashlib.md5(source_path.encode()).hexdigest()[:8]
        file_id = f"csv_migrated_{path_hash}"
        
        # Atualizar metadata
        metadata['file_id'] = file_id
        metadata['file_name'] = source_path.split('/')[-1]
        metadata['upload_source'] = 'migration'
        metadata['migration_timestamp'] = datetime.now().isoformat()
        
        # Atualizar no banco
        supabase.table('embeddings') \
            .update({'metadata': metadata}) \
            .eq('id', row['id']) \
            .execute()
        
        print(f"Migrado: {row['id']} -> {file_id}")
```

### Opção 2: Agrupar por created_at

```python
# Agrupar embeddings por created_at próximos (mesmo upload)
from datetime import timedelta

response = supabase.table('embeddings') \
    .select('id, created_at, metadata') \
    .order('created_at') \
    .execute()

# Agrupar por janelas de 1 minuto
groups = {}
for row in response.data:
    created_at = datetime.fromisoformat(row['created_at'])
    # Truncar para minuto
    minute_key = created_at.replace(second=0, microsecond=0)
    
    if minute_key not in groups:
        groups[minute_key] = []
    
    groups[minute_key].append(row)

# Atribuir file_id por grupo
for minute_key, rows in groups.items():
    file_id = f"csv_batch_{minute_key.strftime('%Y%m%d_%H%M')}"
    
    for row in rows:
        metadata = row['metadata']
        metadata['file_id'] = file_id
        metadata['upload_source'] = 'migration_batch'
        
        supabase.table('embeddings') \
            .update({'metadata': metadata}) \
            .eq('id', row['id']) \
            .execute()
```

---

## 9️⃣ Conclusões e Recomendações

### ❌ Situação Atual: Crítica
- **Sem rastreabilidade** entre frontend e backend
- **Impossível** correlacionar embeddings com uploads
- **Difícil** deletar ou atualizar dados de arquivo específico

### ✅ Solução Proposta: Robusta e Escalável

1. **Campo `file_id` no metadata** - Simples e eficaz
2. **Geração no frontend** - Rastreamento desde o início
3. **Backend compatível** - Aceita e propaga o ID
4. **Funções auxiliares** - Get/Delete by file_id

### 🎯 Prioridades de Implementação

1. **Alta Prioridade (Imediato)**
   - Modificar `DataIngestor` e `RAGAgent` para aceitar `file_id`
   - Atualizar `auto_ingest_service.py`

2. **Média Prioridade (Curto Prazo)**
   - Criar endpoint de upload com `file_id`
   - Implementar funções de consulta/delete

3. **Baixa Prioridade (Longo Prazo)**
   - Migrar dados existentes
   - Dashboard de arquivos ingeridos

### 📚 Referências de Código

- `src/agent/data_ingestor.py` - Ingestão simplificada
- `src/agent/rag_agent.py` - Ingestão completa
- `src/embeddings/vector_store.py` - Persistência
- `src/embeddings/chunker.py` - Estrutura de metadados
- `src/services/auto_ingest_service.py` - Auto-ingestão
- `migrations/0002_schema.sql` - Schema do banco

---

**Auditoria concluída em:** 2025-10-10  
**Autor:** GitHub Copilot (GPT-4.1)  
**Status:** ✅ Análise Completa com Proposta de Solução
