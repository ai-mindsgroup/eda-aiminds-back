# 🔧 Guia Completo: Configurar Google Drive API

## ✅ Checklist de Configuração

- [ ] **Passo 1:** Criar projeto no Google Cloud Console
- [ ] **Passo 2:** Habilitar Google Drive API
- [ ] **Passo 3:** Configurar tela de consentimento OAuth
- [ ] **Passo 4:** Criar credenciais OAuth 2.0 e baixar JSON
- [ ] **Passo 5:** Obter ID da pasta do Google Drive
- [ ] **Passo 6:** Configurar arquivo `.env`
- [ ] **Passo 7:** Testar configuração
- [ ] **Passo 8:** Executar primeira autenticação

---

## 📝 **Passo 1: Criar Projeto no Google Cloud Console**

### URL: https://console.cloud.google.com/

1. Clique em **"Selecionar projeto"** (canto superior)
2. Clique em **"Novo Projeto"**
3. Preencha:
   - **Nome do projeto:** `EDA AI Minds`
   - **Organização:** (deixe padrão)
   - **Local:** (deixe padrão)
4. Clique em **"Criar"**
5. Aguarde alguns segundos até o projeto ser criado
6. Selecione o projeto recém-criado

---

## 📝 **Passo 2: Habilitar Google Drive API**

1. No menu lateral (☰), vá em: **APIs e Serviços → Biblioteca**
2. No campo de busca, digite: `Google Drive API`
3. Clique no resultado **"Google Drive API"**
4. Clique no botão azul **"ATIVAR"**
5. Aguarde a ativação (alguns segundos)

---

## 📝 **Passo 3: Configurar Tela de Consentimento OAuth**

1. Menu lateral: **APIs e Serviços → Tela de consentimento OAuth**
2. Escolha o tipo de usuário:
   - ✅ **Externo** (se não tiver Google Workspace)
   - ⚪ Interno (apenas se tiver Google Workspace)
3. Clique em **"Criar"**

### **3.1. Informações do App:**
- **Nome do app:** `EDA AI Minds`
- **E-mail de suporte do usuário:** `seu-email@gmail.com`
- **Logotipo do app:** (deixe em branco)
- **Domínio do app:** (deixe em branco)
- **Domínio da página inicial:** (deixe em branco)
- **Links de política:** (deixe em branco)
- **Domínios autorizados:** (deixe em branco)
- **E-mail do desenvolvedor:** `seu-email@gmail.com`
- Clique em **"Salvar e Continuar"**

### **3.2. Escopos:**
1. Clique em **"Adicionar ou Remover Escopos"**
2. Na lista, procure e marque:
   - ✅ `https://www.googleapis.com/auth/drive.readonly` (Ver e baixar arquivos)
   - ✅ `https://www.googleapis.com/auth/drive.metadata.readonly` (Ver metadados)
3. Clique em **"Atualizar"**
4. Clique em **"Salvar e Continuar"**

### **3.3. Usuários de Teste (apenas para tipo Externo):**
1. Clique em **"+ Adicionar Usuários"**
2. Digite seu e-mail: `seu-email@gmail.com`
3. Clique em **"Adicionar"**
4. Clique em **"Salvar e Continuar"**

### **3.4. Resumo:**
- Revise as informações
- Clique em **"Voltar ao Painel"**

---

## 📝 **Passo 4: Criar Credenciais OAuth 2.0**

1. Menu lateral: **APIs e Serviços → Credenciais**
2. Clique em **"+ Criar Credenciais"** (topo)
3. Selecione: **"ID do cliente OAuth"**
4. Configure:
   - **Tipo de aplicativo:** `Aplicativo para computador` (Desktop app)
   - **Nome:** `EDA AI Minds Desktop Client`
5. Clique em **"Criar"**

### **4.1. Baixar Credenciais:**
- Vai aparecer uma janela com:
  ```
  ID do cliente: 305811970280-xxxxx.apps.googleusercontent.com
  Chave secreta do cliente: GOCSPX-xxxxx
  ```
- Clique em **"Fazer Download do JSON"** ⬇️
- Salve o arquivo na pasta do projeto:
  ```
  C:\workstashion\eda-aiminds-i2a2-rb\configs\google_drive_credentials.json
  ```

⚠️ **IMPORTANTE:** O arquivo deve ter exatamente esse nome e estar nessa pasta!

---

## 📝 **Passo 5: Obter ID da Pasta do Google Drive**

1. Acesse: https://drive.google.com/
2. Navegue até a pasta que contém os arquivos CSV
3. **Abra a pasta** (clique nela)
4. Veja a URL no navegador:
   ```
   https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J_exemplo
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         Esta é a parte que você precisa!
   ```
5. **Copie apenas a parte após `folders/`**

### Exemplo:
- URL: `https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ`
- ID da pasta: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ` ← **Copie isso!**

---

## 📝 **Passo 6: Configurar arquivo `.env`**

Edite o arquivo: `C:\workstashion\eda-aiminds-i2a2-rb\configs\.env`

### **Localize as linhas:**
```bash
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_FILE=configs/google_drive_token.json
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id_here
```

### **Altere para:**
```bash
GOOGLE_DRIVE_ENABLED=true  ← Mude de false para true
GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json  ← Já está correto
GOOGLE_DRIVE_TOKEN_FILE=configs/google_drive_token.json  ← Já está correto
GOOGLE_DRIVE_FOLDER_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ  ← Cole o ID da sua pasta
```

⚠️ **Substitua `1aBcDeFgHiJkLmNoPqRsTuVwXyZ` pelo ID real da sua pasta!**

---

## 📝 **Passo 7: Verificar Configuração**

Execute este comando para verificar se está tudo certo:

```powershell
python test_auto_ingest.py
```

### **Saída esperada:**
```
✅ Teste 1: Diretórios existem
✅ Teste 2: Configurações válidas
✅ Teste 3: Google Drive habilitado
✅ Teste 4: Credenciais existem
✅ Teste 5: ID da pasta configurado
```

---

## 📝 **Passo 8: Primeira Autenticação**

Na **primeira vez** que executar, você precisa autorizar o app:

```powershell
python run_auto_ingest.py --once
```

### **O que vai acontecer:**
1. Vai abrir o navegador automaticamente
2. Você vai ver uma tela: **"EDA AI Minds quer acessar sua Conta do Google"**
3. Escolha a conta do Google
4. Pode aparecer um aviso: **"Este app não foi verificado pelo Google"**
   - Clique em **"Avançado"**
   - Clique em **"Acessar EDA AI Minds (não seguro)"**
5. Revise as permissões:
   - ✅ Ver e fazer download de todos os seus arquivos do Google Drive
6. Clique em **"Continuar"**
7. Pronto! O sistema vai salvar o token em `configs/google_drive_token.json`

⚠️ **A partir da segunda execução, não vai pedir autenticação novamente!**

---

## 🎯 **Resumo: O Que Você Precisa Me Dar**

Para eu configurar automaticamente, me forneça:

### 1. **ID da Pasta do Google Drive:**
```
Exemplo: 1aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

### 2. **Confirme que você:**
- ✅ Criou o projeto no Google Cloud Console
- ✅ Ativou a Google Drive API
- ✅ Configurou a tela de consentimento OAuth
- ✅ Baixou o arquivo `google_drive_credentials.json`
- ✅ Salvou em `configs/google_drive_credentials.json`

---

## 🆘 **Troubleshooting**

### Problema: "Arquivo credentials não encontrado"
**Solução:** Verifique se o arquivo está em:
```
C:\workstashion\eda-aiminds-i2a2-rb\configs\google_drive_credentials.json
```

### Problema: "ID da pasta inválido"
**Solução:** 
1. Verifique se copiou o ID correto da URL
2. Certifique-se de que tem acesso à pasta
3. Tente compartilhar a pasta com o e-mail do Google Cloud

### Problema: "Este app não foi verificado"
**Solução:** É normal! Clique em "Avançado" → "Acessar EDA AI Minds (não seguro)"

### Problema: "Permissão negada"
**Solução:**
1. Verifique se adicionou seu e-mail como usuário de teste
2. Certifique-se de estar usando o mesmo e-mail do Google Cloud

---

## 📚 **Links Úteis**

- Google Cloud Console: https://console.cloud.google.com/
- Google Drive: https://drive.google.com/
- Documentação Google Drive API: https://developers.google.com/drive/api/guides/about-sdk

---

## ✅ **Depois de Configurado**

Execute o serviço de ingestão automática:

```powershell
# Teste único (processa uma vez e para)
python run_auto_ingest.py --once

# Modo contínuo (fica monitorando a pasta)
python run_auto_ingest.py

# Com debug (mostra mais informações)
python run_auto_ingest.py --debug
```

---

**Precisa de ajuda em algum passo? Me avise! 🚀**
