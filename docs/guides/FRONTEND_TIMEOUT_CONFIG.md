# 🚀 Guia Rápido: Configuração de Timeout no Frontend

**Problema:** Timeout de 30s ao fazer requisições ao backend multiagente  
**Solução:** Configurar timeout de **120 segundos (120000ms)** no cliente HTTP

---

## ⚡ Configuração Rápida por Framework

### React com Axios

```javascript
// src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8001',
  timeout: 120000  // ⏰ 120 segundos
});

export default api;
```

**Uso:**
```javascript
import api from './services/api';

const response = await api.post('/chat', {
  message: 'Analise o dataset',
  file_id: 'csv_123456'
});
```

---

### Fetch API (Vanilla JS / React / Next.js)

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 120000);

try {
  const response = await fetch('http://localhost:8001/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, file_id }),
    signal: controller.signal
  });
  
  clearTimeout(timeoutId);
  
  if (!response.ok) throw new Error('Erro na requisição');
  return await response.json();
  
} catch (error) {
  if (error.name === 'AbortError') {
    console.error('⏰ Timeout de 120s excedido');
  }
  throw error;
}
```

---

### Angular HttpClient

```typescript
// app.module.ts
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { TimeoutInterceptor } from './interceptors/timeout.interceptor';

@NgModule({
  imports: [HttpClientModule],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TimeoutInterceptor,
      multi: true
    }
  ]
})
export class AppModule {}
```

```typescript
// interceptors/timeout.interceptor.ts
import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler } from '@angular/common/http';
import { timeout } from 'rxjs/operators';

@Injectable()
export class TimeoutInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler) {
    return next.handle(req).pipe(
      timeout(120000)  // ⏰ 120 segundos
    );
  }
}
```

---

### Vue.js com Axios

```javascript
// src/plugins/axios.js
import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:8001',
  timeout: 120000  // ⏰ 120 segundos
});

export default instance;
```

```javascript
// main.js
import axios from './plugins/axios';

app.config.globalProperties.$axios = axios;
```

---

## 🎨 Feedback Visual de Carregamento

### Componente React com Feedback

```jsx
import { useState } from 'react';
import api from './services/api';

function ChatComponent() {
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const sendMessage = async (message, fileId) => {
    setLoading(true);
    
    // Mensagem baseada no estado
    if (firstLoad) {
      setLoadingMessage('⏳ Primeira requisição: carregando sistema (60-90s)...');
    } else {
      setLoadingMessage('🤔 Processando com IA (2-10s)...');
    }

    try {
      const response = await api.post('/chat', {
        message,
        file_id: fileId,
        session_id: 'user-123'
      });
      
      setFirstLoad(false);  // Próximas requisições são mais rápidas
      return response.data;
      
    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        alert('⏰ Operação demorou mais de 120s. Tente novamente.');
      } else {
        console.error('Erro:', error);
      }
      throw error;
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  return (
    <div className="chat-container">
      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <p>{loadingMessage}</p>
          {firstLoad && (
            <small style={{ color: '#666' }}>
              Esta é a primeira requisição e pode demorar mais. 
              Próximas serão instantâneas!
            </small>
          )}
        </div>
      )}
      
      {/* Resto do componente de chat */}
    </div>
  );
}
```

---

### CSS para Loading Overlay

```css
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  color: white;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  margin-top: 20px;
  font-size: 18px;
  font-weight: 500;
}

.loading-overlay small {
  margin-top: 10px;
  max-width: 400px;
  text-align: center;
  line-height: 1.5;
}
```

---

## 🔍 Verificar Status do Backend

### Health Check Antes de Enviar Requisição

```javascript
async function checkBackendStatus() {
  try {
    const response = await fetch('http://localhost:8001/health/detailed');
    const data = await response.json();
    
    return {
      ready: data.components.multiagent_system,
      firstLoad: !data.components.orchestrator_loaded,
      recommendedTimeout: parseInt(data.performance.recommended_timeout_frontend),
      estimatedTime: data.components.orchestrator_loaded 
        ? data.performance.subsequent_requests 
        : data.performance.first_load_time
    };
  } catch (error) {
    console.error('Erro ao verificar status do backend:', error);
    return { ready: false };
  }
}

// Uso no componente
useEffect(() => {
  checkBackendStatus().then(status => {
    if (status.ready && status.firstLoad) {
      showNotification(
        '⚠️ Primeira requisição pode demorar 60-90s (carregando sistema multiagente)',
        'info',
        { duration: 10000 }
      );
    }
  });
}, []);
```

---

## 📊 Métricas de Performance

| Requisição | Tempo Esperado | Observação |
|-----------|----------------|------------|
| **Primeira** | 60-90 segundos | Carrega todos os agentes |
| **Segunda em diante** | 2-10 segundos | Cache de agentes |
| **Health Check** | < 1 segundo | Não carrega agentes |

---

## ⚠️ Troubleshooting

### Problema: Ainda dá timeout

**Solução 1: Verificar se API está configurada**
```bash
curl http://localhost:8001/health/detailed
```

Deve retornar `"timeout_config": 120`

**Solução 2: Aumentar timeout no frontend para 180s**
```javascript
const api = axios.create({
  timeout: 180000  // 3 minutos
});
```

---

### Problema: Backend demora muito mesmo depois de carregado

**Possíveis causas:**
1. Dataset muito grande (>500k linhas)
2. Query complexa (#advanced)
3. Múltiplos agentes sendo chamados

**Solução:** Usar streaming (implementação futura)

---

### Problema: Memory leak no frontend

**Causa:** AbortController não está sendo limpo

**Solução:**
```javascript
useEffect(() => {
  const controller = new AbortController();
  
  // Sua requisição aqui...
  
  return () => {
    controller.abort();  // Cleanup
  };
}, []);
```

---

## 🎯 Checklist de Implementação

- [ ] Configurar timeout de 120000ms no cliente HTTP
- [ ] Adicionar feedback visual de carregamento
- [ ] Implementar mensagem diferente para primeira requisição
- [ ] Verificar status com `/health/detailed` antes de enviar
- [ ] Adicionar tratamento de erro de timeout
- [ ] Testar com dataset real (>100k linhas)
- [ ] Adicionar logging de performance no console

---

## 📚 Exemplos Completos

### Exemplo 1: Componente React Completo

Veja: `examples/frontend-timeout-config/ReactChatComponent.jsx`

### Exemplo 2: Vue.js Composition API

Veja: `examples/frontend-timeout-config/VueChatComponent.vue`

### Exemplo 3: Angular Service

Veja: `examples/frontend-timeout-config/chat.service.ts`

---

## 🆘 Suporte

Se continuar com problemas de timeout:

1. Verifique logs do backend: `tail -f logs/api.log`
2. Teste requisição direta: `curl -X POST http://localhost:8001/chat ...`
3. Verifique se orquestrador carregou: `curl http://localhost:8001/health/detailed`

---

**Atualizado em:** 2025-10-04  
**Versão da API:** 2.0.0  
**Timeout Recomendado:** 120000ms (120s)
