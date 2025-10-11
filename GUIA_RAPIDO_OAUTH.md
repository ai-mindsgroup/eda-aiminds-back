# 🚀 GUIA RÁPIDO: Correção OAuth Google Drive

## ⚠️ PROBLEMA IDENTIFICADO
**Erro:** `redirect_uri_mismatch` - URI `http://localhost:52628/` não está autorizada

## ✅ SOLUÇÃO EM 3 PASSOS

### PASSO 1: Acesse o Google Cloud Console
```
1. Vá para: https://console.cloud.google.com/apis/credentials
2. Faça login com: aldenir.gil@gmail.com
3. Selecione o projeto: EDA_AI_Minds-CSV-Upload
```

### PASSO 2: Configure a URI de Redirecionamento
```
1. Na lista de credenciais, procure por "Client ID OAuth 2.0"
2. Clique no nome da credencial (ícone de lápis para editar)
3. Role até "URIs de redirecionamento autorizados"
4. Clique em "+ ADICIONAR URI"
5. Adicione estas URIs (uma por vez):
   
   http://localhost:52628/
   http://localhost:8080/
   http://localhost/
   
6. Clique em SALVAR no fim da página
```

### PASSO 3: Limpe o Token e Reautentique
Execute no PowerShell:
```powershell
# 1. Remove token antigo
Remove-Item -Path "configs\google_drive_token.json" -Force -ErrorAction SilentlyContinue

# 2. Teste a autenticação
python test_google_drive_files.py
```

---

## 🎯 O QUE VAI ACONTECER

Quando executar o comando acima:
1. ✅ Uma janela do navegador vai abrir automaticamente
2. ✅ Você verá a tela de consentimento do Google
3. ✅ Selecione sua conta: aldenir.gil@gmail.com
4. ✅ Clique em "Permitir" para dar acesso ao Drive
5. ✅ O sistema salvará o token e funcionará automaticamente

---

## 📸 ONDE ENCONTRAR NO GOOGLE CLOUD CONSOLE

```
Google Cloud Console
  └── APIs e Serviços
       └── Credenciais
            └── [Seu Client ID OAuth 2.0]
                 └── URIs de redirecionamento autorizados
                      └── [ADICIONAR URI AQUI]
```

---

## 🆘 SE DER ERRO NOVAMENTE

Execute este comando para ver detalhes:
```powershell
python -c "from src.settings import *; print(f'Credentials: {GOOGLE_DRIVE_CREDENTIALS_FILE}'); print(f'Token: {GOOGLE_DRIVE_TOKEN_FILE}'); print(f'Folder ID: {GOOGLE_DRIVE_FOLDER_ID}')"
```

---

## 📞 PRECISA DE AJUDA?

O erro exato é:
```
Erro 400: redirect_uri_mismatch
Detalhes: redirect_uri=http://localhost:52628/
```

Isso significa que você PRECISA adicionar `http://localhost:52628/` no Google Cloud Console!

---

**IMPORTANTE:** Após adicionar a URI no Google Cloud Console, aguarde 1-2 minutos para a configuração propagar.
