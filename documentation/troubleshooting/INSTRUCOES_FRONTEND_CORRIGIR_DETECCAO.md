# 🎯 INSTRUÇÕES PARA TIME DE FRONTEND - Corrigir Detecção de Modo Mock

**Urgência**: Alta  
**Impacto**: UX (usuário vê aviso incorreto de modo demonstração)  
**Esforço**: Baixo (15-30 minutos)

---

## ❌ Problema Atual

Frontend mostra:
```
⚠️ Modo Demonstração Detectado
Este é um ambiente de demonstração com dados mockados.
```

**MAS O BACKEND ESTÁ EM PRODUÇÃO COM DADOS REAIS!**

---

## ✅ Solução Rápida (3 Passos)

### Passo 1: Adicionar Função de Verificação

Adicione esta função no componente principal ou em um hook:

```javascript
// src/hooks/useAPIMode.js (ou componente principal)
import { useState, useEffect } from 'react';

export const useAPIMode = () => {
  const [apiMode, setApiMode] = useState('loading');
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkMode = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config');
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Backend retorna: { mode: "production", features: {...} }
        setApiMode(data.mode || 'unknown');
        
      } catch (err) {
        console.error('Erro ao verificar modo da API:', err);
        setError(err.message);
        setApiMode('offline');
      }
    };

    checkMode();
    
    // Revalidar a cada 30 segundos
    const interval = setInterval(checkMode, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    isProduction: apiMode === 'production',
    isDemoMode: apiMode === 'demo',
    isOffline: apiMode === 'offline',
    isLoading: apiMode === 'loading',
    error
  };
};
```

### Passo 2: Usar no Componente

```javascript
// src/App.js ou componente principal
import { useAPIMode } from './hooks/useAPIMode';

function App() {
  const { isProduction, isDemoMode, isOffline, isLoading } = useAPIMode();

  return (
    <div className="App">
      {/* Avisos condicionais */}
      {isLoading && (
        <Alert severity="info">
          🔍 Verificando status da API...
        </Alert>
      )}
      
      {isOffline && (
        <Alert severity="error">
          ❌ Backend offline. Funcionalidades limitadas.
        </Alert>
      )}
      
      {isDemoMode && (
        <Alert severity="warning">
          ⚠️ Modo demonstração detectado. Dados não são reais.
        </Alert>
      )}
      
      {isProduction && (
        <Alert severity="success">
          ✅ Conectado ao backend em produção
        </Alert>
      )}
      
      {/* Resto do app */}
      <Dashboard />
    </div>
  );
}
```

### Passo 3: Remover Lógica Hardcoded

Procure e **DELETE** qualquer código como:

```javascript
// ❌ REMOVER ISTO:
const isDemoMode = true;
const isMockData = true;
const isTestEnvironment = true;

// ❌ REMOVER ISTO:
<Alert severity="warning">
  ⚠️ Modo Demonstração Detectado
</Alert>

// ❌ REMOVER ISTO:
if (true) { // sempre mostra aviso
  showDemoWarning();
}
```

---

## 🔍 Onde Procurar o Código Problemático

Busque nos arquivos por:

1. **Strings suspeitas**:
   ```
   "Modo Demonstração"
   "dados mockados"
   "ambiente de demonstração"
   "isDemoMode"
   "isMockData"
   ```

2. **Variáveis hardcoded**:
   ```javascript
   const isDemoMode = true;
   const mockMode = true;
   let demoDetected = true;
   ```

3. **Componentes de aviso**:
   ```jsx
   <Alert severity="warning">
     ⚠️ Modo Demonstração Detectado
   </Alert>
   ```

---

## 📋 Checklist de Implementação

- [ ] Criar hook `useAPIMode` (ou equivalente)
- [ ] Fazer request para `http://localhost:8000/api/config`
- [ ] Ler campo `mode` da resposta
- [ ] Atualizar estado baseado na resposta
- [ ] Remover todas as variáveis `isDemoMode = true`
- [ ] Remover avisos hardcoded de modo demo
- [ ] Tornar avisos condicionais ao modo real da API
- [ ] Testar com backend rodando
- [ ] Limpar cache do navegador (Ctrl+F5)
- [ ] Verificar Network tab no DevTools
- [ ] Confirmar que não há mais aviso de modo demo

---

## 🧪 Como Testar

### 1. Verificar Network Tab

Abra DevTools (F12) → Network tab

**Deve haver request para**:
```
GET http://localhost:8000/api/config
```

**Resposta esperada**:
```json
{
  "mode": "production",
  "features": {
    "csv_upload": true,
    "chat": true,
    "dashboard": true,
    "data_analysis": true
  }
}
```

### 2. Verificar Console

Não deve haver erros tipo:
```
❌ Failed to fetch
❌ TypeError: Cannot read property 'mode' of undefined
❌ CORS error
```

### 3. Verificar Comportamento

| Backend Status | Frontend Deve Mostrar |
|----------------|------------------------|
| Rodando (production) | ✅ "Conectado ao backend em produção" |
| Rodando (demo) | ⚠️ "Modo demonstração detectado" |
| Parado | ❌ "Backend offline" |

---

## 🐛 Problemas Comuns

### Problema 1: CORS Error

**Erro**: `Access to fetch at 'http://localhost:8000/api/config' from origin 'http://localhost:3000' has been blocked by CORS`

**Solução**: Backend já tem CORS configurado. Verifique se API está rodando.

### Problema 2: Failed to Fetch

**Erro**: `TypeError: Failed to fetch`

**Causa**: API não está rodando

**Solução**: Iniciar API com `uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload`

### Problema 3: Response é undefined

**Erro**: `Cannot read property 'mode' of undefined`

**Causa**: Response não foi parseada corretamente

**Solução**:
```javascript
// ✅ Correto
const response = await fetch('...');
const data = await response.json();  // ← NÃO ESQUECER!
console.log(data.mode);

// ❌ Errado
const response = await fetch('...');
console.log(response.mode);  // undefined!
```

### Problema 4: Ainda Mostra Demo Após Correção

**Causa**: Cache do navegador

**Solução**: 
1. Limpar cache: Ctrl+Shift+Delete
2. Hard reload: Ctrl+F5
3. Fechar e reabrir navegador

---

## 📊 Validação Final

Após implementar, verifique:

✅ **Request é feito**: Network tab mostra `GET /api/config`  
✅ **Response é correta**: `{mode: "production", ...}`  
✅ **Estado atualiza**: Console mostra novo estado  
✅ **UI atualiza**: Aviso de demo desaparece  
✅ **Funcionalidades funcionam**: Upload CSV, chat, etc.  

---

## 💡 Alternativa: Usar /health Endpoint

Se preferir, pode usar `/health` em vez de `/api/config`:

```javascript
const response = await fetch('http://localhost:8000/health');
const data = await response.json();

// Estrutura da resposta:
// {
//   status: "ok",
//   mode: "production",
//   timestamp: "2025-01-28T..."
// }

setApiMode(data.mode);
```

**Ambos os endpoints retornam o campo `mode` corretamente.**

---

## 📞 Suporte

**Se ainda tiver problemas**:

1. Verifique se API está rodando: `curl http://localhost:8000/health`
2. Veja logs da API no terminal
3. Verifique Network tab no DevTools
4. Leia documentação completa: `FRONTEND_DETECTANDO_MOCK.md`

**Evidências de que backend está OK**:
- Ver: `CONFIRMACAO_FINAL_BACKEND_PRODUCAO.md`
- Ver: `COMPROVACAO_BACKEND_PRODUÇÃO.md`

---

## ⏱️ Estimativa de Tempo

- Criar hook `useAPIMode`: **10 minutos**
- Integrar no componente: **5 minutos**
- Remover código hardcoded: **5 minutos**
- Testar e validar: **10 minutos**

**Total**: ~30 minutos

---

## 🎯 Resultado Esperado

**ANTES** (estado atual - incorreto):
```
⚠️ Modo Demonstração Detectado
Este é um ambiente de demonstração com dados mockados.
```

**DEPOIS** (estado esperado - correto):
```
✅ Conectado ao backend em produção
Todos os dados são reais e processados em tempo real.
```

---

**Última atualização**: 28/01/2025 05:55  
**Prioridade**: Alta  
**Responsável**: Time de Frontend
