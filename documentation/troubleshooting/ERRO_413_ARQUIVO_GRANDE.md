# 🚨 ERRO 413 - Arquivo CSV Muito Grande

**Data**: 02/10/2025  
**Erro**: `Request failed with status code 413`  
**Causa**: Arquivo CSV excede o limite de tamanho configurado

---

## 🎯 O Que Significa Erro 413?

**HTTP 413 - Payload Too Large (Request Entity Too Large)**

Significa que o arquivo que você está tentando fazer upload é **maior** que o limite configurado no servidor.

---

## 📊 Limites Configurados

### ✅ ANTES (Limitado)
- **Limite padrão FastAPI**: ~10MB
- **Resultado**: Erro 413 para arquivos grandes

### ✅ AGORA (Corrigido)
- **Novo limite**: **100MB**
- **Mensagem de erro melhorada**: Informa tamanho máximo e recebido

---

## 🔧 Correção Aplicada

### 1. Adicionadas Constantes de Limite

```python
# Configurações de limites
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100MB
```

### 2. Middleware para Verificação Antecipada

```python
@app.middleware("http")
async def check_request_size(request: Request, call_next):
    """Middleware para verificar tamanho do request."""
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request Too Large",
                    "message": f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB",
                    "max_size_mb": MAX_FILE_SIZE // (1024*1024),
                    "received_size_mb": int(content_length) // (1024*1024)
                }
            )
    response = await call_next(request)
    return response
```

### 3. Validação no Endpoint de Upload

```python
# Verificar tamanho após leitura
file_size = len(contents)
if file_size > MAX_FILE_SIZE:
    raise HTTPException(
        status_code=413,
        detail=f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
    )
```

---

## 🚀 Como Usar Agora

### Reinicie a API

```powershell
# Se estiver rodando, pare (Ctrl+C)
# Reinicie:
uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload
```

### Teste o Upload

```powershell
# Teste com arquivo pequeno (<100MB)
curl -X POST http://localhost:8000/csv/upload `
  -F "file=@data/creditcard_test_500.csv"

# ✅ Deve funcionar!
```

---

## 📏 Limites Por Tamanho de Arquivo

| Tamanho do Arquivo | Status | Ação |
|--------------------|--------|------|
| < 10MB | ✅ Rápido | Upload normal |
| 10-50MB | ✅ Ok | Pode demorar 5-10s |
| 50-100MB | ⚠️ Lento | Demora 20-60s |
| > 100MB | ❌ Erro 413 | Dividir arquivo ou aumentar limite |

---

## 🔧 Como Aumentar Limite (se necessário)

Se você precisar fazer upload de arquivos **maiores que 100MB**, edite `api_simple.py`:

```python
# Linha ~12-13
MAX_FILE_SIZE = 500 * 1024 * 1024  # Aumentar para 500MB
MAX_REQUEST_SIZE = 500 * 1024 * 1024  # Aumentar para 500MB
```

**Reinicie a API** após a mudança.

---

## 💡 Mensagem de Erro Melhorada

### ANTES (genérico):
```
Request failed with status code 413
```

### AGORA (informativo):
```json
{
  "error": "Request Too Large",
  "message": "Arquivo muito grande. Tamanho máximo permitido: 100MB",
  "max_size_mb": 100,
  "received_size_mb": 150
}
```

Agora você sabe **exatamente**:
- Qual o limite
- Qual o tamanho do seu arquivo
- O que fazer

---

## 🐛 Troubleshooting

### Erro Persiste Após Correção?

**1. Verificar se API foi reiniciada**
```powershell
# Pare a API (Ctrl+C)
# Reinicie
uvicorn api_simple:app --reload
```

**2. Limpar cache do navegador**
```
Ctrl+F5 (hard reload)
```

**3. Verificar tamanho real do arquivo**
```powershell
# PowerShell
(Get-Item "caminho\arquivo.csv").Length / 1MB
# Deve ser < 100
```

**4. Arquivo realmente é CSV?**
```powershell
# Verificar extensão
Get-Item "arquivo.csv" | Select-Object Name, Extension
```

---

## 📊 Frontend: Como Tratar o Erro

### Atualizar Código do Frontend

```typescript
// No serviço de upload
try {
  const response = await api.post('/csv/upload', formData);
  return response.data;
} catch (error) {
  if (error.response?.status === 413) {
    // Erro 413 - arquivo muito grande
    const errorData = error.response.data;
    throw new Error(
      `Arquivo muito grande! ` +
      `Máximo permitido: ${errorData.max_size_mb}MB. ` +
      `Arquivo enviado: ${errorData.received_size_mb}MB`
    );
  }
  throw error;
}
```

### Adicionar Validação no Frontend

```typescript
// Antes de enviar
const MAX_SIZE_MB = 100;
const fileSizeMB = file.size / (1024 * 1024);

if (fileSizeMB > MAX_SIZE_MB) {
  alert(`Arquivo muito grande (${fileSizeMB.toFixed(1)}MB). Máximo: ${MAX_SIZE_MB}MB`);
  return;
}

// Prosseguir com upload
```

---

## ✅ Checklist de Validação

- [ ] API foi atualizada com novo código
- [ ] API foi reiniciada
- [ ] Arquivo CSV é menor que 100MB
- [ ] Arquivo tem extensão .csv
- [ ] Frontend foi atualizado (hard reload Ctrl+F5)
- [ ] Testado upload com arquivo pequeno (funciona?)
- [ ] Testado upload com arquivo grande (erro informativo?)

---

## 🎯 Resultado Esperado

### Upload Bem-Sucedido (< 100MB)
```json
{
  "file_id": "csv_20251002_015600",
  "filename": "dados.csv",
  "rows": 50000,
  "columns": 25,
  "message": "CSV 'dados.csv' carregado com sucesso!",
  "columns_list": ["col1", "col2", ...],
  "preview": {...}
}
```

### Erro Informativo (> 100MB)
```json
{
  "error": "Request Too Large",
  "message": "Arquivo muito grande. Tamanho máximo permitido: 100MB",
  "max_size_mb": 100,
  "received_size_mb": 150
}
```

---

## 📞 Perguntas Frequentes

**Q: Por que 100MB e não mais?**  
R: Equilíbrio entre:
- Memória do servidor (evitar crash)
- Tempo de processamento (Pandas demora com arquivos grandes)
- Performance da aplicação

**Q: Posso aumentar para 500MB?**  
R: Sim, mas considere:
- Servidor precisa de mais RAM
- Upload demora mais
- Processamento Pandas mais lento
- Risco de timeout

**Q: Como processar CSV > 100MB?**  
R: Opções:
1. Dividir arquivo em partes menores
2. Processar em chunks (streaming)
3. Usar processamento assíncrono
4. Upload para S3/storage e processar depois

**Q: Erro continua mesmo com arquivo pequeno?**  
R: Verificar:
- API realmente foi reiniciada?
- Frontend não está enviando dados extras?
- Verificar Content-Length no DevTools Network tab

---

## 🚀 Próximos Passos

1. **Reinicie a API** com o código corrigido
2. **Teste** com um arquivo pequeno (~1-5MB)
3. **Valide** que recebe resposta correta
4. **Teste** com arquivo médio (~20-50MB)
5. **Implemente** validação no frontend

---

**Correção aplicada**: 02/10/2025  
**Limite atual**: 100MB  
**Status**: ✅ Corrigido e documentado
