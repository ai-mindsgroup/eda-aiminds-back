# Guia de Recarga Completa - Tabela Embeddings

**Data:** 03 de outubro de 2025  
**Objetivo:** Reprocessar o arquivo `creditcard.csv` completo (284,807 registros)

---

## 📋 Passo a Passo

### 1️⃣ Verificar Carga Atual

```powershell
python verificar_carga_completa.py
```

**Resultado esperado:**
```
❌ CARGA INCOMPLETA! Faltam 254,807 registros (89.47%).
   Recomenda-se reprocessar o arquivo CSV.
```

---

### 2️⃣ Limpar Tabela Embeddings

**Opção A: Limpeza Interativa (recomendado)**
```powershell
python limpar_embeddings.py
```

Será solicitada confirmação:
```
⚠️  ATENÇÃO: Esta operação irá DELETAR TODOS os registros da tabela embeddings!
Deseja continuar? Digite 'SIM' para confirmar:
```

**Opção B: Limpeza Automática (sem confirmação)**
```powershell
python limpar_embeddings.py --sim
```

**Opção C: Limpar Apenas um Source ID Específico**
```powershell
python limpar_embeddings.py --source-id creditcard_test_v1
```

**Resultado esperado:**
```
✅ LIMPEZA CONCLUÍDA COM SUCESSO!
   • Registros deletados: 30,000
   • Registros restantes: 0
```

---

### 3️⃣ Executar Carga Completa

```powershell
python scripts/ingest_completo.py
```

**O que você verá:**

```
🚀 INGESTÃO COMPLETA - creditcard.csv (284,807 registros)

✅ CONFIGURAÇÕES OTIMIZADAS PARA CARGA COMPLETA:
   • Linhas por chunk: 500 (máxima eficiência)
   • Overlap: 50 linhas (10% - preserva contexto)
   • Provider: Sentence Transformer (rápido e local)
   
📊 ESTIMATIVAS:
   • Total de linhas: 284,807
   • Chunks estimados: ~633
   • Tempo estimado: 1-3 horas (depende do hardware)

🔄 Iniciando processamento completo...
```

**Durante o processamento:**
- Progresso detalhado de chunks/embeddings
- Velocidade em tempo real
- Estimativa de tempo restante

---

### 4️⃣ Validar Carga Completa

Após a conclusão, o script executará validação automática:

```
🔍 VALIDANDO CARGA...

✅ Registros no arquivo CSV:        284,807
📦 Registros extraídos dos chunks:  284,807
📈 Percentual carregado:            100.00%

🎉 VALIDAÇÃO CONCLUÍDA: Carga 100% completa!
```

**Validação manual (se necessário):**
```powershell
python verificar_carga_completa.py
```

---

## 🔧 Scripts Criados

### 1. `verificar_carga_completa.py`
**Função:** Compara registros do CSV com chunks na tabela embeddings

**Uso:**
```powershell
python verificar_carga_completa.py
```

**Saída:**
- Total de registros no CSV
- Total de registros nos chunks
- Percentual carregado
- Diferença e status da carga

---

### 2. `limpar_embeddings.py`
**Função:** Limpa a tabela embeddings antes de nova carga

**Opções:**
```powershell
# Limpeza interativa (com confirmação)
python limpar_embeddings.py

# Limpeza automática (sem confirmação)
python limpar_embeddings.py --sim

# Limpar apenas um source_id específico
python limpar_embeddings.py --source-id nome_do_source
```

---

### 3. `scripts/ingest_completo.py`
**Função:** Processa o arquivo CSV completo com configurações otimizadas

**Configurações:**
- 500 linhas por chunk
- 50 linhas de overlap (10%)
- Sentence Transformer (local, rápido)
- Processamento assíncrono

**Uso:**
```powershell
python scripts/ingest_completo.py
```

**Características:**
- Monitoramento de progresso em tempo real
- Validação automática ao final
- Estatísticas detalhadas de performance
- Tratamento de interrupções (Ctrl+C)

---

## 📊 Análise Técnica

### Conclusão da Auditoria

✅ **Sistema SEM limitações técnicas** para carga completa

**Componentes verificados:**
- ✅ Chunker: Processa todas as linhas fornecidas
- ✅ RAGAgent: Lê arquivo completo
- ✅ EmbeddingGenerator: Processa todos os chunks
- ✅ VectorStore: Armazena todos os embeddings

**Causa da carga parcial anterior:**
- Possível uso do script de teste (`test_corrected_ingestion.py`) que limita a 1,000 linhas
- Interrupção manual do processo
- Timeout ou erro de conexão não detectado

### Capacidades do Sistema

- ✅ Processar 284,807 registros
- ✅ Criar ~633 chunks (500 linhas cada)
- ✅ Gerar embeddings em batches
- ✅ Armazenar no Supabase em batches

---

## ⏱️ Estimativas de Tempo

### Configuração Otimizada (500 linhas/chunk)

**Hardware típico:**
- CPU moderna: 1-2 horas
- CPU médio: 2-3 horas
- CPU lento: 3-5 horas

**Fatores que influenciam:**
- Velocidade do CPU (Sentence Transformer é local)
- Velocidade da conexão com Supabase
- Carga do sistema

### Durante o Processamento

O script exibirá:
- Chunks/segundo processados
- Tempo decorrido
- Estimativa de tempo restante baseada em performance real

---

## 🚨 Resolução de Problemas

### Erro: "Conexão com Supabase falhou"
**Solução:** Verificar credenciais em `configs/.env`
```powershell
python check_db.py
```

### Erro: "Sentence Transformer não disponível"
**Solução:** Instalar dependências
```powershell
pip install sentence-transformers
```

### Processo muito lento
**Solução:** Ajustar configurações no script `ingest_completo.py`
```python
# Aumentar tamanho dos chunks
csv_chunk_size_rows=1000,  # De 500 para 1000
csv_overlap_rows=100,      # De 50 para 100
```

### Interrupção acidental (Ctrl+C)
**O que fazer:**
1. Limpar registros parciais: `python limpar_embeddings.py`
2. Reiniciar carga: `python scripts/ingest_completo.py`

---

## 📈 Métricas de Sucesso

### Carga Completa
- ✅ 284,807 registros processados
- ✅ ~633 chunks criados
- ✅ Taxa de sucesso: 100%
- ✅ Validação: 100.00% carregado

### Qualidade dos Dados
- ✅ Chunks com contexto preservado
- ✅ Overlap de 10% entre chunks
- ✅ Metadados completos
- ✅ Embeddings de alta qualidade

---

## 📝 Próximos Passos Após Carga Completa

1. **Testar consultas RAG:**
   ```powershell
   python interface_interativa.py
   ```

2. **Verificar qualidade dos chunks:**
   ```powershell
   python scripts/view_chunk_example.py
   ```

3. **Executar análises:**
   ```powershell
   python examples/fraud_detection_llm_advanced.py
   ```

---

## 📚 Documentação Adicional

- `docs/analise-limitacao-carga.md` - Análise técnica completa
- `docs/STATUS-COMPLETO-PROJETO.md` - Status geral do projeto
- `.github/copilot-instructions.md` - Instruções do sistema

---

**Documento criado automaticamente pelo sistema EDA AI Minds**  
**Última atualização:** 03 de outubro de 2025
