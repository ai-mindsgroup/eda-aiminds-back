# 🎯 EDA AI Minds Backend - Sistema Multiagente

<div align="center">

![Version](https://img.shields.io/badge/Version-2.0.1-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3.27-1C3C3C?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Ready-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Sistema multiagente inteligente para análise exploratória de dados CSV**

*Análise contextual  Roteamento inteligente de LLM  Sistema de memória  RAG com embeddings*

[ Documentação](#-documentação) 
[ Quick Start](#-quick-start) 
[ Funcionalidades](#-funcionalidades) 
[ Changelog](CHANGELOG.md)

</div>

---

##  Sobre o Projeto

Sistema backend multiagente desenvolvido para análise inteligente e exploratória de dados em formato CSV. Utiliza LangChain, múltiplos LLMs (Google Gemini), embeddings vetoriais e sistema RAG para fornecer análises contextualizadas e insights automáticos.

> **Nota:** Este projeto é resultado de trabalho em grupo, sem menção a autores individuais.

###  Principais Características

-  **Sistema Multiagente** com coordenação inteligente via Orchestrator
-  **Roteamento Inteligente de LLM** baseado em complexidade (economia 60-70%)
-  **Suporte a qualquer CSV** com análise adaptativa
-  **Sistema de Memória** persistente com Supabase + LangChain
-  **RAG** com busca vetorial
-  **Sistema de file_id** para análise contextual
-  **Cache inteligente** para performance otimizada

---

##  Stack Tecnológica

### Core & Framework
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/_LangChain-0.3.27-1C3C3C?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Ready-009688?style=for-the-badge&logo=fastapi&logoColor=white)

### Data & Analysis
![Pandas](https://img.shields.io/badge/Pandas-2.2.3-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.3.2-013243?style=for-the-badge&logo=numpy&logoColor=white)

### AI & LLMs
![Google AI](https://img.shields.io/badge/Google_AI-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)

### Database
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)

---

##  Quick Start

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/ai-mindsgroup/eda-aiminds-back.git
cd eda-aiminds-back

# 2. Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env
cp configs/.env.example configs/.env
# Edite configs/.env com suas credenciais
```

### Executar API

```bash
# API completa (porta 8001)
python api_completa.py

# API simples (porta 8000)
python api_simple.py
```

---

##  Documentação

-  [**Índice Completo**](docs/INDEX.md) - Navegação estruturada
-  [**CHANGELOG**](CHANGELOG.md) - Histórico de versões
-  [**API Documentation**](docs/API_DOCUMENTATION.md) - Referência da API
-  [**Arquitetura**](docs/architecture/) - Documentação técnica
-  [**Troubleshooting**](docs/troubleshooting/) - Resolução de problemas
-  [**Guides**](docs/guides/) - Guias de configuração

---

##  Funcionalidades

### Agente Orquestrador Central
-  Coordenação inteligente de agentes especializados
-  Classificação automática de consultas (6 tipos)
-  Contexto persistente com memória
-  Interface unificada

### Sistema de Carregamento
-  Múltiplas fontes (arquivo, URL, base64)
-  Validação automática (score 0-100)
-  Limpeza inteligente de dados
-  Detecção automática de encoding

### Agentes Inteligentes
-  **OrchestratorAgent** - Coordenador central
-  **CSVAnalysisAgent** - Análise com Pandas + LLM
-  **RAGAgent** - Busca vetorial
-  **BaseAgent** - Framework base

---

##  Arquitetura

```

      OrchestratorAgent              
   Coordenador + LLM Router          

                       
        
      CSV          RAG   
     Agent        Agent  
        
                      
    
      MemoryManager        
      Supabase             
    
```

---

##  Performance

### LLM Router - Economia de Custos

| Complexidade | Modelo | Uso | Economia |
|--------------|--------|-----|----------|
| SIMPLE | gemini-1.5-flash | 60% | 70% |
| MEDIUM | gemini-1.5-flash | 25% | 50% |
| COMPLEX | gemini-1.5-pro | 10% | - |
| ADVANCED | gemini-2.0 | 5% | - |

**Economia total: 60-70% em custos**

### Cache
- Primeira requisição: 60-90s
- Subsequentes: 2-10s
- Timeout: 120s
- Limite CSV: 999MB

---

##  Limitações

-  Contexto LLM: ~1M tokens
-  CSV grandes: Performance reduzida >100k linhas
-  RAM: Requer 4GB+ disponível
-  Timeout primeira carga: 60-90s

**Detalhes:** [docs/troubleshooting/2025-10-04_0325_limitacoes-tecnicas.md](docs/troubleshooting/2025-10-04_0325_limitacoes-tecnicas.md)

---

##  Roadmap

###  v2.0 (Atual)
- [x] Sistema multiagente
- [x] LLM Router
- [x] Memória persistente
- [x] RAG com embeddings
- [x] API REST

###  v2.1 (Próxima)
- [ ] Interface web
- [ ] Suporte Excel/JSON
- [ ] Autenticação
- [ ] Dashboard

---

##  Contribuindo

1. Fork o projeto
2. Crie branch (`git checkout -b feature/MinhaFeature`)
3. Commit (`git commit -m 'feat: adiciona feature'`)
4. Push (`git push origin feature/MinhaFeature`)
5. Abra Pull Request

**Guia:** [docs/guides/2025-10-04_0315_guia-commits.md](docs/guides/2025-10-04_0315_guia-commits.md)

---

##  Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

##  Agradecimentos

- **LangChain** - Framework de orquestração
- **Supabase** - Backend e banco vetorial
- **Google** - Modelos Gemini
- **Comunidade Python** - Bibliotecas excepcionais

---

<div align="center">

** Se este projeto foi útil, considere dar uma estrela!**

[ Reportar Bug](https://github.com/ai-mindsgroup/eda-aiminds-back/issues) 
[ Solicitar Feature](https://github.com/ai-mindsgroup/eda-aiminds-back/issues) 
[ Documentação](docs/INDEX.md)

</div>
