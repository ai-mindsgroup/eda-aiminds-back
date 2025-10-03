# 🔧 Solução: Frontend Mostrando Mensagens Mockadas

## 🎯 Problema

Frontend detecta a API como "mock" e mostra mensagens simuladas.

---

## 🔍 Causa Provável

O frontend provavelmente está verificando um dos seguintes campos:

1. **Campo `mode` no health check**
2. **Endpoint `/api/config` retornando `demo: true`**
3. **Respostas sem dados reais**
4. **Falta de algum campo específico**

---

## ✅ Solução Backend (Já Implementada)

### **1. Health Check Atualizado**
```json
GET /health
{
  "status": "healthy",
  "timestamp": "2025-10-01T23:55:00",
  "version": "1.0.0",
  "message": "API funcionando perfeitamente!",
  "mode": "production"  // ← NÃO é demo!
}
```

### **2. Endpoint de Configuração**
```json
GET /api/config
{
  "mode": "production",  // ← Indica produção
  "features": {
    "csv_upload": true,
    "csv_analysis": true,
    "chat": true,
    "dashboard": true,
    "llm_analysis": false,
    "rag_search": false
  },
  "version": "1.0.0",
  "status": "operational"
}
```

---

## 🧪 O Que o Frontend Deve Verificar

### **Opção 1: Verificar campo `mode`**
```typescript
// src/services/api/client.ts ou similar

const checkIfDemo = async () => {
  try {
    const response = await apiClient.get('/health')
    return response.data.mode === 'demo'  // false = produção
  } catch {
    return true  // Se falhar, assume demo
  }
}
```

### **Opção 2: Verificar endpoint `/api/config`**
```typescript
const checkIfDemo = async () => {
  try {
    const response = await apiClient.get('/api/config')
    return response.data.mode === 'demo'
  } catch {
    return true
  }
}
```

### **Opção 3: Verificar se há dados reais**
```typescript
const checkIfDemo = async () => {
  try {
    // Tenta fazer uma operação real
    const response = await apiClient.get('/dashboard/metrics')
    
    // Se retornar dados válidos, não é demo
    return !response.data || response.data.status === 'demo'
  } catch {
    return true
  }
}
```

---

## 🔧 Correção no Frontend

### **Arquivo**: `src/services/api/client.ts` ou similar

#### **ANTES (Provavelmente)**:
```typescript
// Detecta se é demo baseado em algum critério errado
const isDemo = () => {
  // Sempre retorna true ou verifica campo errado
  return true
}
```

#### **DEPOIS (Correto)**:
```typescript
export const checkApiMode = async (): Promise<'production' | 'demo'> => {
  try {
    const response = await apiClient.get('/health')
    return response.data.mode || 'demo'
  } catch (error) {
    console.error('Erro ao verificar modo da API:', error)
    return 'demo'
  }
}

// Ou mais simples:
export const isProduction = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/api/config')
    return response.data.mode === 'production'
  } catch {
    return false
  }
}
```

---

## 🚀 Como Testar

### **1. Verificar Health Check**:
```powershell
curl http://localhost:8000/health
```

**Deve retornar**:
```json
{
  "status": "healthy",
  "mode": "production"  ← Verifique este campo!
}
```

### **2. Verificar Config**:
```powershell
curl http://localhost:8000/api/config
```

**Deve retornar**:
```json
{
  "mode": "production"  ← Verifique este campo!
}
```

### **3. Testar Upload Real**:
```powershell
curl -X POST "http://localhost:8000/csv/upload" `
  -F "file=@data/creditcard_test_500.csv"
```

**Deve retornar dados reais do CSV**, não mock!

---

## 📊 Checklist de Verificação Frontend

### **No código do frontend, verifique**:

- [ ] Como está detectando se é demo/mock?
- [ ] Qual endpoint está usando para verificar?
- [ ] Qual campo está verificando?
- [ ] Está fazendo a verificação no momento certo?
- [ ] Está cacheando o resultado?

### **Locais comuns para verificar**:
```
src/
  services/
    api/
      client.ts          ← Verificar aqui
      config.ts          ← Ou aqui
  utils/
    api.ts               ← Ou aqui
  config/
    api.config.ts        ← Ou aqui
  App.tsx                ← Ou na raiz
```

---

## 🔍 Debug no Frontend

### **Adicione logs**:
```typescript
// No componente principal ou cliente API
useEffect(() => {
  const checkMode = async () => {
    try {
      const health = await apiClient.get('/health')
      console.log('🔍 Health Response:', health.data)
      console.log('🔍 Mode:', health.data.mode)
      
      const config = await apiClient.get('/api/config')
      console.log('🔍 Config Response:', config.data)
      console.log('🔍 Mode:', config.data.mode)
      
      // Verificar o que está causando detecção de mock
      if (health.data.mode === 'production') {
        console.log('✅ API em modo PRODUÇÃO')
      } else {
        console.log('⚠️ API em modo DEMO/MOCK')
      }
    } catch (error) {
      console.error('❌ Erro ao verificar modo:', error)
    }
  }
  
  checkMode()
}, [])
```

---

## 🎯 Possíveis Problemas no Frontend

### **1. Verificação Hardcoded**:
```typescript
// ERRADO ❌
const isDemoMode = true  // Sempre demo!

// CORRETO ✅
const isDemoMode = await checkIfDemoFromAPI()
```

### **2. Verificação do Campo Errado**:
```typescript
// ERRADO ❌
const isDemo = response.data.demo === true

// CORRETO ✅
const isDemo = response.data.mode === 'demo'
```

### **3. Fallback Sempre para Demo**:
```typescript
// ERRADO ❌
try {
  // verifica API
} catch {
  return 'demo'  // Sempre cai aqui se API não responder
}

// CORRETO ✅
try {
  const response = await apiClient.get('/health')
  return response.data.mode
} catch (error) {
  console.error('Erro ao verificar API:', error)
  throw error  // Deixa o erro propagar
}
```

### **4. Cache Incorreto**:
```typescript
// ERRADO ❌
const API_MODE = 'demo'  // Definido uma vez

// CORRETO ✅
const [apiMode, setApiMode] = useState<'production' | 'demo'>('demo')

useEffect(() => {
  checkApiMode().then(setApiMode)
}, [])
```

---

## 📝 Exemplo Completo para Frontend

### **Criar: `src/hooks/useApiMode.ts`**:
```typescript
import { useState, useEffect } from 'react'
import { apiClient } from '@/services/api/client'

export type ApiMode = 'production' | 'demo' | 'loading'

export const useApiMode = () => {
  const [mode, setMode] = useState<ApiMode>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkMode = async () => {
      try {
        const response = await apiClient.get('/api/config')
        const detectedMode = response.data.mode as 'production' | 'demo'
        
        console.log('🔍 API Mode detectado:', detectedMode)
        setMode(detectedMode)
        setError(null)
      } catch (err) {
        console.error('❌ Erro ao verificar modo da API:', err)
        setError('Não foi possível conectar à API')
        setMode('demo')  // Fallback para demo apenas se falhar
      }
    }

    checkMode()
  }, [])

  return { mode, error, isProduction: mode === 'production' }
}
```

### **Usar no componente**:
```typescript
import { useApiMode } from '@/hooks/useApiMode'

const MyComponent = () => {
  const { mode, isProduction } = useApiMode()

  if (mode === 'loading') {
    return <div>Verificando API...</div>
  }

  return (
    <div>
      {!isProduction && (
        <Alert severity="warning">
          ⚠️ Modo Demonstração Detectado
        </Alert>
      )}
      
      {isProduction && (
        <Alert severity="success">
          ✅ API em Modo Produção
        </Alert>
      )}
    </div>
  )
}
```

---

## 🚀 Iniciar API Corretamente

```powershell
# Certifique-se que a API está rodando
uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload
```

Ou use o script:
```powershell
.\iniciar_api.ps1
```

---

## ✅ Resultado Esperado

Após a correção no frontend:

### **ANTES** ❌:
```
⚠️ Modo Demonstração Detectado
O backend está retornando respostas simuladas...
```

### **DEPOIS** ✅:
```
✅ API Operacional
Sistema funcionando normalmente
[Sem avisos de mock/demo]
```

---

## 📚 Próximos Passos

1. **Identifique onde o frontend verifica se é demo**
2. **Atualize para verificar `/api/config` ou `/health`**
3. **Verifique o campo `mode`**
4. **Teste e confirme**

---

## 🔗 Endpoints para Verificar

| Endpoint | O Que Retorna |
|----------|---------------|
| `GET /health` | `{ "mode": "production", ... }` |
| `GET /api/config` | `{ "mode": "production", ... }` |
| `POST /csv/upload` | Dados reais do CSV |
| `GET /dashboard/metrics` | Métricas reais |
| `POST /chat` | Respostas reais (não mock) |

---

**💡 Dica**: Compartilhe este arquivo com quem está desenvolvendo o frontend para implementar a verificação correta!

*Última atualização: 01/10/2025 23:55*