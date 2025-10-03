# 📚 Documentação EDA AI Minds Backend

*Sistema multiagente para análise inteligente de dados CSV com LangChain, Supabase e vetorização.*

## 🗂️ Índice Geral

### 🚀 [Guias de Início Rápido](./guides/)
- **[Leia Primeiro](./guides/LEIA_PRIMEIRO.md)** - Visão geral do projeto
- **[Inicialização Rápida](./guides/API_QUICK_START.md)** - Como iniciar a API em minutos
- **[Comparativo de APIs](./guides/COMPARATIVO_APIS.md)** - Qual API usar em cada situação

### 🔧 [Documentação da API](./api/)
- **[Instruções Frontend](./api/FRONTEND_INSTRUÇÕES_TESTE.md)** - Como integrar com frontend
- **[Upload de Arquivos](./api/PROBLEMA_CORRIGIDO_UPLOAD_CSV.md)** - Configuração de upload
- **[LLMs Suportados](./api/LLMs_SUPORTADOS.md)** - Modelos disponíveis
- **[Suporte Gemini](./api/SUPORTE_GEMINI.md)** - Configuração Google Gemini

### 🛠️ [Desenvolvimento](./development/)
- **[Sessões de Desenvolvimento](../docs/)** - Histórico detalhado das implementações
- **[Relatório Final](../docs/relatorio-final.md)** - Status completo do projeto
- **[Análise de Memória](../docs/ANALISE_MEMORIA_SISTEMA_MULTIAGENTE.md)** - Otimizações ML

### ⚠️ [Solução de Problemas](./troubleshooting/)
- **[Erro 413 - Arquivo Grande](./troubleshooting/ERRO_413_ARQUIVO_GRANDE.md)** - Solução para uploads grandes
- **[Chat Corrigido](./troubleshooting/CHAT_CORRIGIDO_FINAL.md)** - Problemas de chat resolvidos
- **[Frontend Mock Detection](./troubleshooting/FRONTEND_DETECTANDO_MOCK.md)** - Correção detecção mock

## 🏗️ Estrutura do Projeto

```
eda-aiminds-back-1/
├── 📁 src/                    # Código fonte principal
│   ├── 📁 api/               # FastAPI e rotas
│   ├── 📁 agent/             # Agentes multiagente
│   ├── 📁 embeddings/        # Sistema vetorial
│   └── 📁 utils/             # Utilitários
├── 📁 tests/                 # Testes automatizados
├── 📁 docs/                  # Documentação histórica
├── 📁 documentation/         # Documentação organizada (ESTA PASTA)
├── 📁 examples/              # Exemplos e demos
├── 📁 configs/               # Configurações
├── 📁 data/                  # Dados de exemplo
└── 📁 scripts/               # Scripts utilitários
```

## 🚀 Quick Start

### 1. Instalação
```bash
# Clonar repositório
git clone https://github.com/ai-mindsgroup/eda-aiminds-back.git
cd eda-aiminds-back-1

# Criar ambiente virtual
python -m venv .venv
.venv\\Scripts\\Activate.ps1  # Windows
source .venv/bin/activate     # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração
```bash
# Copiar configurações
cp configs/.env.example configs/.env

# Editar variáveis de ambiente
# SUPABASE_URL=your_url
# SUPABASE_KEY=your_key
# GOOGLE_API_KEY=your_key
```

### 3. Executar
```bash
# API Simples (desenvolvimento)
python api_simple.py

# API Completa (produção)
python -m src.api.main
```

## 🔗 Links Rápidos

- **[Documentação API](http://localhost:8000/docs)** - Swagger UI
- **[Health Check](http://localhost:8000/health)** - Status da API
- **[Supabase Dashboard](https://supabase.com/dashboard)** - Banco de dados
- **[GitHub Repository](https://github.com/ai-mindsgroup/eda-aiminds-back)** - Código fonte

## 🆘 Precisa de Ajuda?

1. **Problemas de Startup**: Consulte [Solução de Problemas](./troubleshooting/)
2. **Integração Frontend**: Veja [Instruções Frontend](./api/FRONTEND_INSTRUÇÕES_TESTE.md)
3. **Desenvolvimento**: Acesse [Sessões de Desenvolvimento](../docs/)

---

**🏷️ Tags**: `multiagente` `llm` `rag` `supabase` `fastapi` `langchain` `embeddings`

**📅 Última Atualização**: October 2025  
**👥 Mantido por**: AI Minds Group