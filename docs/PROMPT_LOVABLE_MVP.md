# Prompt Lovable - Frontend MVP para EDA AI Minds

## 🎯 Objetivo: MVP Simples e Funcional

Criar um frontend **minimalista e eficiente** para o sistema EDA AI Minds, priorizando **simplicidade**, **manutenibilidade** e **entrega rápida**. O foco é um MVP funcional que demonstre as capacidades da API sem complexidade desnecessária.

## 🔌 API Integration - SUPER SIMPLES

### **Base URL**
```
http://localhost:8000
```

### **Endpoints Essenciais (apenas 5)**
```typescript
// 1. Health Check
GET /health
// Response: { status: "healthy", timestamp: "...", message: "..." }

// 2. Chat com IA
POST /chat
// Body: { message: string, session_id?: string }
// Response: { response: string, session_id: string, timestamp: string }

// 3. Upload CSV
POST /csv/upload
// Form-data: file
// Response: { file_id: string, filename: string, rows: number, columns: number, message: string, columns_list: string[], preview: {...} }

// 4. Lista arquivos
GET /csv/files
// Response: { total: number, files: Array<{file_id, filename, rows, columns}> }

// 5. Métricas dashboard
GET /dashboard/metrics
// Response: { total_files: number, total_rows: number, total_columns: number, status: string }
```

## 🎨 Design: Clean & Minimal

### **Paleta de Cores SIMPLES**
- **Primária**: `#3B82F6` (Azul)
- **Sucesso**: `#10B981` (Verde)
- **Erro**: `#EF4444` (Vermelho)
- **Neutro**: `#6B7280` (Cinza)
- **Background**: `#F9FAFB` (Branco sujo)

### **Tipografia SIMPLES**
- **Font**: System default (`-apple-system, BlinkMacSystemFont, "Segoe UI"`)
- **Tamanhos**: `text-sm` (14px), `text-base` (16px), `text-lg` (18px), `text-xl` (20px)

## 📱 Stack Tecnológica MINIMALISTA

### **Core Essencial**
- ✅ **React 18** (sem TypeScript para simplicidade)
- ✅ **Vite** (setup rápido)
- ✅ **TailwindCSS** (styling sem CSS customizado)
- ❌ ~~React Router~~ (SPA simples, sem roteamento)
- ❌ ~~Redux/Zustand~~ (useState + useEffect apenas)

### **Bibliotecas Mínimas**
- ✅ **Axios** (HTTP requests)
- ✅ **React Dropzone** (upload drag&drop)
- ❌ ~~Chart.js~~ (usar CSS puro para visualizações simples)
- ❌ ~~Component Libraries~~ (componentes customizados simples)

### **Package.json Enxuto**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-dropzone": "^14.2.3"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.0"
  }
}
```

## 🖥️ Interface: Uma Página, Três Seções

### **Layout Único (Single Page App)**
```
┌─────────────────────────────────────────────────────────┐
│ 🏠 EDA AI Minds - Análise de Dados CSV                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📊 MÉTRICAS RÁPIDAS                                    │
│ [12 arquivos] [245K linhas] [156 colunas] [✅ Online]  │
│                                                         │
│ 📤 UPLOAD DE CSV                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │     Arraste seu arquivo CSV aqui                   │ │
│ │              ou clique para selecionar             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 💬 CHAT COM IA                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🤖: Olá! Envie um CSV e faça perguntas sobre os    │ │
│ │     dados. Posso ajudar com análises e insights.   │ │
│ │                                                     │ │
│ │ 👤: [Digite sua mensagem...]              [Enviar] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 📋 ARQUIVOS ENVIADOS                                   │
│ • transactions.csv (1.2K linhas, 8 colunas)           │
│ • customers.csv (890 linhas, 12 colunas)               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🧩 Componentes Simples (apenas 5)

### **1. MetricsBar.jsx**
```jsx
function MetricsBar() {
  const [metrics, setMetrics] = useState(null);
  
  useEffect(() => {
    axios.get('/dashboard/metrics').then(res => setMetrics(res.data));
  }, []);

  if (!metrics) return <div>Carregando...</div>;

  return (
    <div className="bg-white p-4 rounded shadow">
      <div className="grid grid-cols-4 gap-4 text-center">
        <div>📁 {metrics.total_files} arquivos</div>
        <div>📊 {metrics.total_rows} linhas</div>
        <div>🏷️ {metrics.total_columns} colunas</div>
        <div>✅ {metrics.status}</div>
      </div>
    </div>
  );
}
```

### **2. FileUploader.jsx**
```jsx
import { useDropzone } from 'react-dropzone';

function FileUploader({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);

  const onDrop = async (files) => {
    const file = files[0];
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('/csv/upload', formData);
      onUploadSuccess(response.data);
    } catch (error) {
      alert('Erro no upload: ' + error.message);
    }
    setUploading(false);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop, 
    accept: { 'text/csv': ['.csv'] }
  });

  return (
    <div 
      {...getRootProps()} 
      className={`border-2 border-dashed p-8 text-center cursor-pointer rounded
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        ${uploading ? 'opacity-50' : ''}`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <div>📤 Enviando arquivo...</div>
      ) : (
        <div>
          <div className="text-4xl mb-2">📊</div>
          <div>Arraste seu arquivo CSV aqui ou clique para selecionar</div>
        </div>
      )}
    </div>
  );
}
```

### **3. ChatInterface.jsx**
```jsx
function ChatInterface() {
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Olá! Envie um CSV e faça perguntas sobre os dados.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('/chat', { message: input });
      const botMessage = { type: 'bot', text: response.data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { type: 'bot', text: 'Erro: ' + error.message };
      setMessages(prev => [...prev, errorMessage]);
    }
    setLoading(false);
  };

  return (
    <div className="bg-white rounded shadow">
      <div className="h-64 overflow-y-auto p-4 border-b">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-2 ${msg.type === 'user' ? 'text-right' : ''}`}>
            <div className={`inline-block p-2 rounded max-w-xs ${
              msg.type === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {loading && <div className="text-gray-500">🤖 Pensando...</div>}
      </div>
      <div className="p-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Digite sua mensagem..."
          className="flex-1 border rounded px-3 py-2"
          disabled={loading}
        />
        <button 
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
```

### **4. FilesList.jsx**
```jsx
function FilesList() {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await axios.get('/csv/files');
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Erro ao carregar arquivos:', error);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-bold mb-3">📋 Arquivos Enviados</h3>
      {files.length === 0 ? (
        <div className="text-gray-500">Nenhum arquivo enviado ainda</div>
      ) : (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <div>
                <span className="font-medium">📄 {file.filename}</span>
              </div>
              <div className="text-sm text-gray-600">
                {file.rows} linhas • {file.columns} colunas
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### **5. App.jsx (Componente Principal)**
```jsx
import { useState } from 'react';
import MetricsBar from './components/MetricsBar';
import FileUploader from './components/FileUploader';
import ChatInterface from './components/ChatInterface';
import FilesList from './components/FilesList';

// Configurar base URL do axios
axios.defaults.baseURL = 'http://localhost:8000';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = (uploadData) => {
    alert(`✅ ${uploadData.filename} enviado com sucesso! ${uploadData.rows} linhas processadas.`);
    setRefreshKey(prev => prev + 1); // Força refresh das métricas e lista
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800">🏠 EDA AI Minds</h1>
          <p className="text-gray-600">Análise Inteligente de Dados CSV</p>
        </div>

        {/* Métricas */}
        <MetricsBar key={`metrics-${refreshKey}`} />

        {/* Upload */}
        <div>
          <h2 className="text-xl font-bold mb-3">📤 Upload de CSV</h2>
          <FileUploader onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Chat */}
        <div>
          <h2 className="text-xl font-bold mb-3">💬 Chat com IA</h2>
          <ChatInterface />
        </div>

        {/* Lista de Arquivos */}
        <FilesList key={`files-${refreshKey}`} />

      </div>
    </div>
  );
}

export default App;
```

## ⚙️ Configuração Mínima

### **vite.config.js**
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### **tailwind.config.js**
```js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### **src/main.jsx**
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### **src/index.css**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}
```

## 🚀 Scripts de Desenvolvimento

### **package.json scripts**
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### **Comandos para executar**
```bash
# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build para produção
npm run build
```

## 📋 Funcionalidades do MVP

### ✅ **O que DEVE ter (essencial)**
- [x] Upload de CSV drag & drop
- [x] Chat funcional com a IA
- [x] Visualização de métricas básicas
- [x] Lista de arquivos enviados
- [x] Status da API (online/offline)
- [x] Tratamento básico de erros
- [x] Interface responsiva simples

### ❌ **O que NÃO precisa (v2)**
- ❌ Roteamento entre páginas
- ❌ Estado global complexo
- ❌ Gráficos elaborados
- ❌ Autenticação/login
- ❌ Temas dark/light
- ❌ Testes automatizados
- ❌ PWA/offline
- ❌ Internacionalização

## 🎯 Resultado Esperado

### **Timeline de Desenvolvimento**
- **Dia 1**: Setup inicial + componentes básicos
- **Dia 2**: Integração com API + upload
- **Dia 3**: Chat interface + polish final

### **Entregável Final**
- ✅ SPA funcional em uma única página
- ✅ Integração completa com `api_simple.py`
- ✅ Interface limpa e responsiva
- ✅ Código simples e manutenível
- ✅ Pronto para demo/apresentação

## 💡 Princípios de Desenvolvimento

### **KISS (Keep It Simple, Stupid)**
- 1 página, 5 componentes, 3 dependências
- CSS via Tailwind (sem CSS customizado)
- Estado local (sem Redux/Context)
- Sem over-engineering

### **Foco no MVP**
- Funcionalidade antes de estética
- Código legível antes de otimização
- Entrega rápida antes de perfeição
- Demonstração antes de escalabilidade

### **Manutenibilidade**
- Componentes pequenos e focados
- Lógica simples e direta
- Sem abstrações desnecessárias
- Código auto-explicativo

---

Este prompt está otimizado para criar um MVP funcional e simples, perfeito para demonstrar as capacidades da API sem complexidade desnecessária. O resultado será um frontend limpo, rápido de desenvolver e fácil de manter! 🚀