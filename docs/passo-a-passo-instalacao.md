# Passo a Passo de Instalação e Preparação do Ambiente

Este guia explica, de forma simples, como qualquer pessoa (mesmo júnior) pode preparar o ambiente do projeto.

> Ambiente alvo: Windows (PowerShell / pwsh). Se estiver em Linux ou macOS, apenas ajuste alguns comandos de ativação do ambiente virtual.

---
## 1. Pré-Requisitos
Certifique-se de ter instalado:
- Python 3.12 (ou 3.11+ se 3.12 não estiver disponível)
- Git
- Acesso à internet (para instalar dependências)

Verifique versões:
```powershell
python --version
git --version
```
Se o comando `python` não funcionar, tente `py --version`.

---
## 2. Clonar (ou Apontar) o Repositório
Se ainda não tiver o código local:
```powershell
git clone <URL_DO_REPOSITORIO>
cd eda-aiminds-back
```
Se já estiver dentro da pasta do projeto, apenas confirme:
```powershell
pwd   # mostra o diretório atual
```
Você deve ver algo como: `...\eda-aiminds-back`.

---
## 3. Criar Ambiente Virtual (Isolado)
Crie o ambiente virtual `.venv` dentro do projeto:
```powershell
python -m venv .venv
```
Ative o ambiente:
```powershell
.\.venv\Scripts\Activate.ps1
```
Você saberá que funcionou se o prompt mostrar algo como: `(.venv)` no início.

Atualize `pip` (boa prática):
```powershell
python -m pip install --upgrade pip
```

---
## 4. Instalar Dependências do Projeto
As bibliotecas estão listadas em `requirements.txt`.
```powershell
pip install -r requirements.txt
```
Principais pacotes instalados:
- `langchain` (orquestração LLM)
- `pandas` (manipulação de dados)
- `supabase` (cliente Supabase)
- `openai` (acesso a modelos GPT)
- `pytest` (testes)
- `python-dotenv` (carregar variáveis de ambiente)
- `psycopg[binary]` (conexão PostgreSQL)
- `requests` (chamadas HTTP gerais)

### 4.1 (Opcional) Instalar Dependências Individualmente
Se quiser instalar uma por uma (útil para diagnosticar algum erro específico):
```powershell
pip install langchain
pip install pandas
pip install supabase
pip install openai
pip install pytest
pip install python-dotenv
pip install "psycopg[binary]"
pip install requests
```

Ou em um único comando (PowerShell) separado por espaço:
```powershell
pip install langchain pandas supabase openai pytest python-dotenv "psycopg[binary]" requests
```

> Já realizamos essas instalações em iterações anteriores, mas você deve repetir localmente ao montar seu ambiente.

---
## 5. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo (se existir):
```powershell
copy .\configs\.env.example .\configs\.env
```
Abra `.\configs\.env` e preencha os valores:
```
SUPABASE_URL=...
SUPABASE_KEY=...
OPENAI_API_KEY=...
SONAR_API_KEY=...        # opcional se for usar Sonar
DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
LOG_LEVEL=INFO
```
Nunca faça commit do arquivo `.env` (já está no `.gitignore`).

---
## 6. Verificar Carregamento de Configurações
Teste rapidamente se as variáveis podem ser lidas:
```powershell
python - << 'PYCODE'
from src import settings
print('SUPABASE_URL ok?', bool(settings.SUPABASE_URL))
print('DB DSN:', settings.build_db_dsn())
PYCODE
```

---
## 7. Testar Conexão com o Banco (Opcional Rápido)
Apenas se já tiver o Postgres/Supabase configurado:
```powershell
python - << 'PYCODE'
import psycopg
from src import settings
try:
    with psycopg.connect(settings.build_db_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            print('Conexão OK')
except Exception as e:
    print('Falhou:', e)
PYCODE
```

---
## 8. Executar Migrations
O script aplica os arquivos SQL na pasta `migrations/`.
```powershell
python .\scripts\run_migrations.py
```
Se tudo certo, verá logs de cada migration aplicada (extensões + tabelas + índices vetoriais).

---
## 9. Smoke Test das Bibliotecas
Verifique se os imports básicos funcionam:
```powershell
python - << 'PYCODE'
import pandas, langchain, requests, psycopg, openai, supabase
print('Imports OK')
PYCODE
```

---
## 10. (Opcional) Criar Teste Rápido com Pytest
Crie arquivo `tests/test_smoke.py` (se ainda não existir) com conteúdo:
```python
# tests/test_smoke.py

def test_basic_math():
    assert 2 + 2 == 4
```
Execute:
```powershell
pytest -q
```

---
## 11. Uso de LLM (Exemplo Simples OpenAI)
Antes: certifique-se que `OPENAI_API_KEY` está no `.env`.
```powershell
python - << 'PYCODE'
import os, openai
from dotenv import load_dotenv
load_dotenv('configs/.env')
client = openai.OpenAI()
resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":"Diga 'olá'"}])
print(resp.choices[0].message.content)
PYCODE
```
(Se a API mudar para interface `Responses`, adapte conforme documentação.)

---
## 12. Organização do Código (Resumo)
- `src/settings.py`: carrega variáveis de ambiente.
- `src/utils/logging_config.py`: logging central.
- `src/vectorstore/`: cliente Supabase / vetores.
- `scripts/run_migrations.py`: aplica migrations SQL.
- `migrations/`: arquivos `.sql` ordenados numericamente.

---
## 13. Problemas Comuns
| Sintoma | Causa Provável | Solução |
|---------|----------------|---------|
| `ModuleNotFoundError` | Ambiente não ativado | Ativar `.venv` antes de rodar scripts |
| Erro ao conectar Postgres | Credenciais inválidas | Revisar `.env` e se banco está acessível |
| `ssl`/`crypto` erro no psycopg | Ambiente Windows incompleto | Atualizar Python e reinstalar dependências |
| API OpenAI 401 | Chave incorreta ou faltando | Revisar `OPENAI_API_KEY` no `.env` |

---
## 14. Limpeza / Atualizações
Atualizar dependências (eventual):
```powershell
pip install -U -r requirements.txt
```
Recriar ambiente (se corrompido):
```powershell
Remove-Item -Recurse -Force .\.venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---
## 15. Próximos Passos
Após ambiente pronto:
1. Implementar agentes (profiling, indexação, orquestração).
2. Gerar descrições e embeddings.
3. Integrar rota/CLI para fazer perguntas (RAG flow).
4. Adicionar testes de integração.

---
## 16. Checklist Rápido
| Etapa | Feito? |
|-------|--------|
| Python & Git instalados |  |
| Ambiente virtual criado |  |
| Dependências instaladas |  |
| `.env` configurado |  |
| Migrations aplicadas |  |
| Smoke tests passaram |  |

---
Se algo falhar, anote a mensagem de erro completa e investigue a causa antes de repetir o comando. Em dúvida, peça ajuda.

*Documento criado para orientar onboarding júnior.*
