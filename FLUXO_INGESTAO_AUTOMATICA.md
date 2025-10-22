# Fluxo de Ingestão Automática de CSV do Google Drive

## 🔄 Fluxo Completo Implementado

### **Visão Geral do Processo**

```
┌─────────────────────┐
│  Google Drive       │
│  (Pasta Monitorada) │
│                     │
│  📄 arquivo.csv     │
└──────────┬──────────┘
           │
           │ 1. Detecta novo arquivo (polling)
           │
           ▼
┌─────────────────────┐
│  Download           │
│  ⬇️ Baixa arquivo   │
└──────────┬──────────┘
           │
           │ 2. Salva em: data/processando/
           │
           ▼
┌─────────────────────┐
│  Processamento      │
│  🔄 RAGAgent        │
│                     │
│  - Limpeza base     │
│  - Análise EDA      │
│  - Chunking         │
│  - Embeddings       │
│  - Upload Supabase  │
└──────────┬──────────┘
           │
           │ 3. Se SUCESSO
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌─────────────────────┐  ┌─────────────────────┐
│  Move Local         │  │  Deleta do Drive    │
│  📁 → processado/   │  │  🗑️ Limpa pasta     │
└─────────────────────┘  └─────────────────────┘
```

---

## 📋 **Detalhamento Passo a Passo**

### **Passo 1: Monitoramento (Polling)**
- ⏱️ A cada `AUTO_INGEST_POLLING_INTERVAL` segundos (padrão: 300s = 5min)
- 🔍 Verifica pasta do Google Drive por novos arquivos CSV
- 📝 Ignora arquivos já processados (histórico em memória)

### **Passo 2: Download**
- ⬇️ Baixa arquivo do Google Drive
- 📁 Salva diretamente em: `data/processando/arquivo.csv`
- ✅ Cria diretório automaticamente se não existir

### **Passo 3: Processamento (RAGAgent)**
1. **Limpeza da Base Vetorial:**
   - 🧹 Remove embeddings antigos do mesmo arquivo
   - 🗑️ Limpa chunks anteriores
   - 📊 Prepara para dados novos

2. **Análise Exploratória (EDA):**
   - 📈 Estatísticas descritivas
   - 📊 Distribuições
   - 🔍 Detecção de outliers
   - 📉 Correlações

3. **Chunking:**
   - ✂️ Divide dados em pedaços menores
   - 📏 Tamanho configurável
   - 🔗 Mantém contexto entre chunks

4. **Geração de Embeddings:**
   - 🧠 Vetorização com modelo de linguagem
   - 📐 Embeddings de 1536 dimensões
   - 💾 Armazena no Supabase (pgvector)

### **Passo 4: Movimentação Local**
- 📁 Move de `data/processando/` → `data/processado/`
- 🏷️ Mantém nome original do arquivo
- ⏰ Timestamp de processamento registrado

### **Passo 5: Limpeza do Google Drive**
- 🗑️ **DELETA** o arquivo da pasta do Google Drive
- ✅ Libera espaço na pasta monitorada
- 🔒 Operação irreversível (arquivo vai para lixeira do Drive)

---

## ⚙️ **Configuração**

### **Variáveis de Ambiente (.env)**

```bash
# Google Drive
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=10sw4srFutRGzNfhpf04la39fzMsG7Pmk
GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_FILE=configs/google_drive_token.json

# Diretórios Locais (caminhos relativos)
EDA_DATA_DIR=data
EDA_DATA_DIR_PROCESSANDO=data/processando
EDA_DATA_DIR_PROCESSADO=data/processado

# Polling
AUTO_INGEST_POLLING_INTERVAL=300  # 5 minutos
AUTO_INGEST_FILE_PATTERN=.*\.csv$  # Apenas CSVs
```

---

## 🚀 **Como Executar**

### **Modo Teste (Único Ciclo)**
```powershell
python run_auto_ingest.py --once
```
- Executa um único ciclo de verificação
- Processa arquivos encontrados
- Termina automaticamente
- Ideal para testes

### **Modo Produção (Contínuo)**
```powershell
python run_auto_ingest.py
```
- Loop infinito de polling
- Verifica a cada 5 minutos (configurável)
- Processa automaticamente novos arquivos
- Pressione `Ctrl+C` para parar

### **Modo Debug**
```powershell
python run_auto_ingest.py --debug
```
- Logging detalhado
- Mostra cada operação
- Útil para troubleshooting

### **Personalizar Intervalo**
```powershell
python run_auto_ingest.py --interval 60
```
- Define intervalo customizado (segundos)
- Exemplo: `--interval 60` = verifica a cada 1 minuto

---

## 📊 **Logs e Monitoramento**

### **Estrutura de Logs**
```
logs/
└── auto_ingest_YYYYMMDD.log
```

### **Exemplo de Log de Sucesso**
```
[INFO] 🔍 Iniciando ciclo de verificação (14:30:00)
[INFO] 📥 Encontrados 1 novos arquivos CSV
[INFO]   ⬇️ Baixando: transactions_2025.csv
[INFO]   ✅ Arquivo baixado para: data\processando\transactions_2025.csv
[INFO]   🔄 Iniciando processamento...
[INFO]   → Executando ingestão no Supabase...
[INFO]   ✅ Ingestão concluída com sucesso
[INFO]   → Movendo para pasta 'processado'...
[INFO]   ✅ Movido para: data\processado\transactions_2025.csv
[INFO]   🗑️ Removendo arquivo do Google Drive: transactions_2025.csv
[INFO]   ✅ Arquivo removido do Google Drive com sucesso
[INFO] ✅ Arquivo processado completamente: transactions_2025.csv
[INFO] ✅ Ciclo concluído: 1 arquivos processados
```

---

## 🎯 **Casos de Uso**

### **1. Upload Manual no Google Drive**
1. Usuário faz upload de `dados.csv` na pasta monitorada
2. Sistema detecta no próximo ciclo (até 5 min)
3. Baixa automaticamente
4. Processa e ingere no Supabase
5. Move para `processado/`
6. **Deleta do Google Drive**

### **2. Múltiplos Arquivos**
1. Usuário faz upload de 5 CSVs
2. Sistema detecta todos
3. Processa um por vez (sequencial)
4. Cada sucesso deleta do Drive
5. Relatório no log de quantos foram processados

### **3. Erro de Processamento**
1. Arquivo com erro é baixado
2. Processamento falha
3. Arquivo **NÃO é deletado** do Drive
4. Arquivo **permanece** em `processando/`
5. Próximo ciclo tenta novamente
6. Log registra erro para análise

---

## 🛡️ **Segurança e Robustez**

### **Tratamento de Erros**
- ✅ Falha no download → Não deleta do Drive
- ✅ Falha na ingestão → Não deleta do Drive
- ✅ Falha ao mover → Não deleta do Drive
- ✅ **Só deleta do Drive se TUDO der certo**

### **Retry Automático**
- 🔄 Arquivos com erro permanecem no Drive
- 🔄 Próximo ciclo tenta novamente
- 🔄 Histórico de erros no log

### **Limpeza Automática**
- 🧹 A cada 10 ciclos, limpa arquivos antigos
- 📅 Remove arquivos em `processado/` com mais de 30 dias
- 💾 Libera espaço em disco

---

## ⚠️ **Importante: Deleção é Permanente!**

### **O Arquivo é Deletado do Google Drive Após Sucesso**

- 🗑️ Arquivo vai para **lixeira do Google Drive**
- ⏰ Lixeira mantém por **30 dias**
- 🔄 Pode ser restaurado manualmente se necessário
- ⚠️ Após 30 dias, **deletado permanentemente**

### **Como Recuperar se Necessário**
1. Acesse: https://drive.google.com/drive/trash
2. Localize o arquivo
3. Clique com botão direito → "Restaurar"
4. Arquivo volta para a pasta original

---

## 🎛️ **Comandos Úteis**

### **Verificar Status**
```powershell
# Ver últimos logs
Get-Content logs\auto_ingest_*.log -Tail 50
```

### **Limpar Histórico de Downloads**
```python
from src.integrations.google_drive_client import create_google_drive_client
client = create_google_drive_client()
client.reset_download_history()
```

### **Testar Conexão Google Drive**
```powershell
python test_auto_ingest.py
```

---

## 📈 **Estatísticas Disponíveis**

O serviço mantém estatísticas em tempo real:

```python
{
    "total_files_processed": 15,
    "total_files_failed": 2,
    "last_check": "2025-10-09T14:30:00",
    "last_success": "2025-10-09T14:29:45",
    "last_error": "Timeout na conexão Supabase",
    "uptime_start": "2025-10-09T10:00:00"
}
```

---

## 🔧 **Troubleshooting**

### **Arquivo não foi deletado do Drive**
**Causa:** Processamento falhou em alguma etapa
**Solução:** Verifique logs para identificar erro

### **Arquivo baixado mas não processado**
**Causa:** Erro no pipeline de ingestão ou Supabase
**Solução:** 
1. Verifique conexão Supabase
2. Verifique credenciais
3. Arquivo fica em `processando/` para retry manual

### **"Permissão negada" ao deletar**
**Causa:** Credenciais OAuth sem permissão de escrita
**Solução:** 
1. Deletar `configs/google_drive_token.json`
2. Executar novamente (vai pedir nova autenticação)
3. Aceitar **todas** as permissões

---

## 📚 **Documentação Adicional**

- `SETUP_GOOGLE_DRIVE.md` - Setup completo do Google Drive API
- `docs/AUTO_INGEST_SETUP.md` - Guia detalhado de ingestão
- `QUICKSTART_AUTO_INGEST.md` - Referência rápida

---

**Sistema Pronto para Produção! 🚀**
