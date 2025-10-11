# Sistema de Ingestão Automática de CSV - Google Drive

## 📋 Visão Geral

Sistema completo de ingestão automática de arquivos CSV do Google Drive para o EDA AI Minds, com gerenciamento de ciclo de vida dos arquivos e integração com o sistema de embeddings vetoriais.

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                      GOOGLE DRIVE                                │
│                 (Pasta Monitorada)                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Polling (5min)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Auto Ingest Service                                 │
│  (Orquestrador Central)                                          │
└──────┬──────────────────┬───────────────────┬───────────────────┘
       │                  │                   │
       │                  │                   │
       ▼                  ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Google Drive │   │  CSV File    │   │    Data      │
│   Client     │   │   Manager    │   │  Ingestor    │
└──────────────┘   └──────────────┘   └──────────────┘

Fluxo de Arquivos:
data/ → processando/ → [Ingestão] → processado/
```

## 🔧 Componentes

### 1. Google Drive Client (`src/integrations/google_drive_client.py`)
- **Autenticação OAuth2** com Google Drive API
- **Listagem de arquivos** na pasta monitorada
- **Download automático** de arquivos CSV
- **Gerenciamento de token** (renovação automática)
- **Tracking** de arquivos já processados

### 2. CSV File Manager (`src/data/csv_file_manager.py`)
- **Validação** de arquivos CSV
- **Movimentação** entre diretórios (data → processando → processado)
- **Limpeza automática** de arquivos antigos
- **Informações** de arquivos

### 3. Auto Ingest Service (`src/services/auto_ingest_service.py`)
- **Polling** configurável do Google Drive
- **Orquestração** do fluxo completo
- **Tratamento de erros** e retry
- **Estatísticas** e logging detalhado
- **Shutdown gracioso** (Ctrl+C)

### 4. Data Ingestor (Existente) (`src/agent/data_ingestor.py`)
- Análise descritiva do CSV
- Chunking inteligente
- Geração de embeddings
- Inserção no Supabase

## 📦 Instalação

### 1. Instalar Dependências

```powershell
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Ou adicione ao `requirements.txt`:
```
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
```

### 2. Configurar Google Drive API

#### a) Criar Projeto no Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto (ou use existente)
3. Habilite a **Google Drive API**:
   - APIs & Services → Library
   - Busque "Google Drive API"
   - Clique em "Enable"

#### b) Criar Credenciais OAuth 2.0

1. Acesse: https://console.cloud.google.com/apis/credentials
2. Clique em "Create Credentials" → "OAuth 2.0 Client ID"
3. Configure tela de consentimento (OAuth consent screen):
   - User Type: External (para testes)
   - App name: EDA AI Minds
   - User support email: seu email
   - Developer contact: seu email
4. Application type: **Desktop app**
5. Name: EDA AI Minds Auto Ingest
6. Clique em "Create"
7. **Baixe o arquivo JSON** de credenciais
8. Salve como: `configs/google_drive_credentials.json`

#### c) Obter ID da Pasta do Google Drive

1. Abra o Google Drive no navegador
2. Navegue até a pasta que deseja monitorar
3. Copie o ID da URL:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                           ^^^^^^^^^^^^^^^^^^^^
                                           Este é o ID da pasta
   ```

### 3. Configurar Variáveis de Ambiente

Edite `configs/.env` e adicione:

```env
# ========================================================================
# CONFIGURAÇÕES DE INGESTÃO AUTOMÁTICA DE CSV
# ========================================================================

# Diretórios locais
EDA_DATA_DIR=C:\\workstashion\\eda-aiminds-i2a2-rb\\data
EDA_DATA_DIR_PROCESSANDO=C:\\workstashion\\eda-aiminds-i2a2-rb\\data\\processando
EDA_DATA_DIR_PROCESSADO=C:\\workstashion\\eda-aiminds-i2a2-rb\\data\\processado

# Google Drive
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_FILE=configs/google_drive_token.json
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j

# Polling (segundos)
AUTO_INGEST_POLLING_INTERVAL=300

# Filtro de arquivos (regex)
AUTO_INGEST_FILE_PATTERN=.*\.csv$
```

## 🚀 Uso

### Modo Contínuo (Recomendado para VPS)

```powershell
python run_auto_ingest.py
```

O serviço ficará rodando continuamente, verificando novos arquivos a cada 5 minutos (ou intervalo configurado).

### Modo Single-Run (Testes)

```powershell
python run_auto_ingest.py --once
```

Executa apenas um ciclo de verificação e processamento.

### Com Intervalo Customizado

```powershell
python run_auto_ingest.py --interval 60
```

Define intervalo de 60 segundos entre verificações.

### Modo Debug

```powershell
python run_auto_ingest.py --debug
```

Habilita logging verbose para troubleshooting.

## 📁 Estrutura de Diretórios

```
data/
├── processando/      # Arquivos sendo processados
├── processado/       # Arquivos já processados
└── *.csv             # Arquivos baixados do Drive
```

### Ciclo de Vida dos Arquivos

1. **Download**: `Google Drive` → `data/arquivo.csv`
2. **Processamento**: `data/arquivo.csv` → `data/processando/arquivo.csv`
3. **Ingestão**: Análise + Embeddings + Supabase
4. **Conclusão**: `data/processando/arquivo.csv` → `data/processado/arquivo.csv`

## 🔐 Autenticação

### Primeira Execução

Na primeira vez que o serviço rodar, será necessário autorizar via navegador:

1. O serviço abrirá automaticamente seu navegador
2. Faça login com sua conta Google
3. Autorize o acesso à pasta do Google Drive
4. O token será salvo em `configs/google_drive_token.json`
5. Nas próximas execuções, usará o token salvo

### Renovação Automática

O token expira após um tempo, mas o serviço renova automaticamente quando necessário.

## 📊 Monitoramento

### Logs

Os logs são salvos em:
- **Console**: Output em tempo real
- **Arquivo**: `logs/auto_ingest.log`

### Estatísticas

O serviço rastreia:
- Total de arquivos processados
- Total de arquivos com erro
- Último sucesso
- Último erro
- Tempo de execução (uptime)

Pressione `Ctrl+C` para ver estatísticas finais.

## 🛠️ Integração com RAG Agents

### Referência Centralizada

O agente RAG sempre busca o arquivo mais recente em:
```python
from src.settings import EDA_DATA_DIR_PROCESSADO
from src.data.csv_file_manager import create_csv_file_manager

file_manager = create_csv_file_manager()
latest_csv = file_manager.get_latest_processed_file()
```

### Atualização Automática

Após cada ingestão bem-sucedida:
1. Arquivo é movido para `data/processado/`
2. Embeddings estão no Supabase
3. RAG Agents consultam embeddings (não CSV diretamente)

## 🔧 Troubleshooting

### Erro: "Bibliotecas do Google Drive não instaladas"

```powershell
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Erro: "Arquivo de credenciais não encontrado"

Verifique se `configs/google_drive_credentials.json` existe e o caminho em `.env` está correto.

### Erro: "GOOGLE_DRIVE_FOLDER_ID não configurado"

Configure a variável no `.env` com o ID da pasta do Google Drive.

### Erro de Autenticação

Delete `configs/google_drive_token.json` e execute novamente para reautorizar.

### Arquivos não sendo processados

1. Verifique `GOOGLE_DRIVE_ENABLED=true` no `.env`
2. Verifique se o padrão `AUTO_INGEST_FILE_PATTERN` está correto
3. Execute em modo `--debug` para ver logs detalhados

## 🖥️ Executar como Serviço no Windows (VPS)

### Opção 1: Task Scheduler

1. Abra Task Scheduler
2. Create Task
3. **General**:
   - Name: EDA Auto Ingest
   - Run whether user is logged on or not
4. **Triggers**:
   - Begin the task: At startup
5. **Actions**:
   - Program: `C:\Python312\python.exe`
   - Arguments: `run_auto_ingest.py`
   - Start in: `C:\workstashion\eda-aiminds-i2a2-rb`
6. **Conditions**:
   - Uncheck "Start the task only if the computer is on AC power"

### Opção 2: NSSM (Non-Sucking Service Manager)

```powershell
# Instalar NSSM
choco install nssm

# Registrar serviço
nssm install EDAAutoIngest "C:\Python312\python.exe"
nssm set EDAAutoIngest AppDirectory "C:\workstashion\eda-aiminds-i2a2-rb"
nssm set EDAAutoIngest AppParameters "run_auto_ingest.py"
nssm set EDAAutoIngest DisplayName "EDA AI Minds Auto Ingest"
nssm set EDAAutoIngest Description "Ingestão automática de CSV do Google Drive"

# Iniciar serviço
nssm start EDAAutoIngest

# Status
nssm status EDAAutoIngest

# Logs
nssm set EDAAutoIngest AppStdout "C:\workstashion\eda-aiminds-i2a2-rb\logs\service-stdout.log"
nssm set EDAAutoIngest AppStderr "C:\workstashion\eda-aiminds-i2a2-rb\logs\service-stderr.log"
```

## 🧪 Testes

### Teste Manual (Sem Google Drive)

1. Coloque um arquivo CSV manualmente em `data/`
2. Execute: `python run_auto_ingest.py --once`
3. Verifique que o arquivo foi processado e está em `data/processado/`

### Teste com Google Drive

1. Configure tudo conforme documentação
2. Coloque um arquivo CSV na pasta monitorada do Drive
3. Execute: `python run_auto_ingest.py --once --debug`
4. Verifique logs para confirmar download e processamento

## 📝 Próximos Passos

- [ ] Adicionar suporte para outros formatos (Excel, JSON)
- [ ] Implementar webhooks do Google Drive (tempo real ao invés de polling)
- [ ] Dashboard web para monitoramento
- [ ] Notificações (email/Slack) em caso de erros
- [ ] Backup automático de arquivos processados

## 🤝 Contribuindo

Este módulo foi desenvolvido seguindo os padrões do EDA AI Minds:
- Logging estruturado
- Tratamento robusto de erros
- Configuração via variáveis de ambiente
- Documentação completa
- Compatibilidade com Windows VPS

## 📄 Licença

Este módulo faz parte do projeto EDA AI Minds.
