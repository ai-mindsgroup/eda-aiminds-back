# 🚀 GUIA DEFINITIVO: Configurar Google Drive API do ZERO

**Projeto:** EDA AI Minds - Sistema de Ingestão Automática  
**Data:** 09/10/2025  
**Objetivo:** Configurar autenticação OAuth para script Python local

---

## 📋 PASSO A PASSO COMPLETO

### 1️⃣ ACESSE O GOOGLE CLOUD CONSOLE

```
🔗 URL: https://console.cloud.google.com/
📧 Login: aldenir.gil@gmail.com
```

### 2️⃣ SELECIONE/CRIE O PROJETO

- No topo da página, clique no seletor de projeto
- Se já tem projeto "EDA_AI_Minds-CSV-Upload", selecione-o
- Se não tem, clique em **"NOVO PROJETO"**:
  - Nome: `EDA AI Minds - CSV Upload`
  - Clique em **"CRIAR"**

### 3️⃣ ATIVE A API DO GOOGLE DRIVE

```
Menu lateral → APIs e Serviços → Biblioteca
```

1. Na barra de pesquisa, digite: **"Google Drive API"**
2. Clique em **"Google Drive API"**
3. Clique em **"ATIVAR"** (se já estiver ativada, pule)

### 4️⃣ CONFIGURE A TELA DE CONSENTIMENTO OAUTH

```
Menu lateral → APIs e Serviços → Tela de consentimento OAuth
```

1. Escolha: **"Externo"** (para testes)
2. Clique em **"CRIAR"**
3. Preencha:
   - **Nome do app:** `EDA AI Minds - CSV Upload`
   - **E-mail de suporte:** `aldenir.gil@gmail.com`
   - **E-mail do desenvolvedor:** `aldenir.gil@gmail.com`
4. Clique em **"SALVAR E CONTINUAR"**
5. Em "Escopos", clique em **"ADICIONAR OU REMOVER ESCOPOS"**:
   - Marque: `https://www.googleapis.com/auth/drive`
   - Clique em **"ATUALIZAR"**
6. Clique em **"SALVAR E CONTINUAR"**
7. Em "Usuários de teste", clique em **"+ ADICIONAR USUÁRIOS"**:
   - Adicione: `aldenir.gil@gmail.com`
   - Clique em **"ADICIONAR"**
8. Clique em **"SALVAR E CONTINUAR"**
9. Clique em **"VOLTAR PARA O PAINEL"**

### 5️⃣ CRIE CREDENCIAIS OAUTH 2.0 (TIPO DESKTOP) ⭐

```
Menu lateral → APIs e Serviços → Credenciais
```

1. Clique em **"+ CRIAR CREDENCIAIS"**
2. Selecione: **"ID do cliente OAuth 2.0"**
3. **IMPORTANTE:** Em "Tipo de aplicativo", escolha:
   ```
   ✅ Aplicativo para computador
   ```
   ⚠️ **NÃO escolha "Aplicativo da Web"!**
   
4. Nome: `EDA AI Minds - Desktop Client`
5. Clique em **"CRIAR"**
6. Janela aparecerá com:
   - Client ID
   - Client Secret
7. Clique em **"FAZER DOWNLOAD DO JSON"**

### 6️⃣ SALVE O ARQUIVO JSON

1. O arquivo baixado tem nome tipo: `client_secret_305811970280-xxx.json`
2. **Renomeie para:** `google_drive_credentials.json`
3. **Mova para a pasta:** `C:\workstashion\eda-aiminds-i2a2-rb\configs\`
4. **Substitua** o arquivo antigo (se existir)

### 7️⃣ CONFIGURE A PASTA DO GOOGLE DRIVE

1. Acesse: https://drive.google.com
2. Crie uma pasta chamada: `EDA_CSV_Upload`
3. Abra a pasta
4. **Copie o ID da pasta** da URL:
   ```
   https://drive.google.com/drive/folders/10sw4srFutRGzNfhpf04la39fzMsG7Pmk
                                          ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                                          Este é o FOLDER_ID
   ```
5. Já está no `.env`: `GOOGLE_DRIVE_FOLDER_ID=10sw4srFutRGzNfhpf04la39fzMsG7Pmk`

### 8️⃣ VERIFIQUE O ARQUIVO .ENV

Abra `configs/.env` e confirme:

```env
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_FILE=configs/google_drive_token.json
GOOGLE_DRIVE_FOLDER_ID=10sw4srFutRGzNfhpf04la39fzMsG7Pmk
AUTO_INGEST_POLLING_INTERVAL=300
```

### 9️⃣ TESTE A AUTENTICAÇÃO

```powershell
# Ative o ambiente virtual
.venv\Scripts\Activate.ps1

# Execute o teste
python test_google_drive_files.py
```

**O que vai acontecer:**
1. ✅ Navegador abre automaticamente
2. ✅ Faça login com: `aldenir.gil@gmail.com`
3. ✅ Clique em "Permitir"
4. ✅ Sistema salva token em `configs/google_drive_token.json`
5. ✅ Lista arquivos da pasta do Drive

### 🔟 EXECUTE O SISTEMA DE INGESTÃO

```powershell
# Teste único (um ciclo)
python run_auto_ingest.py --once

# Modo contínuo (polling a cada 5min)
python run_auto_ingest.py
```

---

## ✅ CHECKLIST DE VERIFICAÇÃO

Antes de testar, confirme:

- [ ] Projeto criado/selecionado no Google Cloud Console
- [ ] Google Drive API ativada
- [ ] Tela de consentimento OAuth configurada
- [ ] Usuário de teste adicionado (aldenir.gil@gmail.com)
- [ ] Credenciais OAuth 2.0 **tipo "Desktop"** criadas
- [ ] Arquivo JSON baixado e renomeado
- [ ] Arquivo salvo em: `configs/google_drive_credentials.json`
- [ ] Pasta criada no Google Drive
- [ ] FOLDER_ID copiado e configurado no `.env`
- [ ] Variáveis no `.env` verificadas

---

## 🆘 RESOLUÇÃO DE PROBLEMAS

### Erro: "redirect_uri_mismatch"
**Causa:** Credenciais são tipo "Web" ao invés de "Desktop"  
**Solução:** Delete as credenciais e crie novas tipo **"Aplicativo para computador"**

### Erro: "access_denied"
**Causa:** Usuário não está na lista de testadores  
**Solução:** Adicione seu email na "Tela de consentimento OAuth" → "Usuários de teste"

### Erro: "Bibliotecas não instaladas"
**Solução:** 
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Navegador não abre
**Solução:** Copie a URL que aparece no terminal e cole no navegador manualmente

---

## 📸 ONDE ESTÁ CADA COISA

```
Google Cloud Console
├── APIs e Serviços
│   ├── Biblioteca → Ativar Google Drive API
│   ├── Tela de consentimento OAuth → Configurar app e usuários de teste
│   └── Credenciais → Criar OAuth 2.0 (Desktop)
└── Projeto → Selecionar/criar projeto
```

---

## 🎯 RESULTADO ESPERADO

Após configurar corretamente:

1. ✅ Sistema autentica automaticamente
2. ✅ Monitora pasta do Google Drive a cada 5 minutos
3. ✅ Baixa novos CSVs para `data/processando/`
4. ✅ Processa (análise + embeddings + Supabase)
5. ✅ Move para `data/processado/`
6. ✅ **Deleta do Google Drive** após sucesso

---

## 📚 DOCUMENTAÇÃO OFICIAL

- Google Drive API: https://developers.google.com/drive/api/guides/about-sdk
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Python Quickstart: https://developers.google.com/drive/api/quickstart/python

---

**🚨 PONTO CRUCIAL:** Use **"Aplicativo para computador"**, NÃO "Aplicativo da Web"!
