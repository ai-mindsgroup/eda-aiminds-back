# 🔧 Como Corrigir Erro OAuth 400: redirect_uri_mismatch do Google Drive

**Data:** 09/10/2025  
**Erro:** `Erro 400: redirect_uri_mismatch`  
**Causa:** A URI de redirecionamento não está configurada no Google Cloud Console

---

## 📋 Passo a Passo para Correção

### 1. Acesse o Google Cloud Console
1. Vá para: https://console.cloud.google.com/
2. Selecione seu projeto: **EDA_AI_Minds-CSV-Upload**

### 2. Configure a URI de Redirecionamento
1. No menu lateral, vá em: **APIs e Serviços** → **Credenciais**
2. Encontre suas credenciais OAuth 2.0 (Client ID)
3. Clique para editar
4. Na seção **URIs de redirecionamento autorizados**, adicione:
   ```
   http://localhost:52628/
   http://localhost:8080/
   http://localhost/
   ```
5. Clique em **Salvar**

### 3. Limpe o Token Antigo
Execute no terminal:
```powershell
# Remove token antigo (se existir)
Remove-Item -Path "configs\google_drive_token.json" -ErrorAction SilentlyContinue
```

### 4. Reautentique
Execute o sistema novamente:
```powershell
python run_auto_ingest.py --once
```

Ele abrirá o navegador para autenticação. Faça login com sua conta Google.

---

## 🔍 Verificando a Configuração Atual

Execute este comando para ver suas credenciais:
```powershell
python -c "from src.settings import GOOGLE_DRIVE_CREDENTIALS_FILE; import json; print(json.dumps(json.load(open(GOOGLE_DRIVE_CREDENTIALS_FILE)), indent=2))"
```

Procure pela seção `redirect_uris` e anote as URIs listadas.

---

## ✅ Validação

Após configurar, execute:
```powershell
python test_google_drive_files.py
```

Você deve ver:
- ✅ Autenticação bem-sucedida
- Lista de arquivos no Google Drive

---

## 🆘 Problemas Comuns

### Problema: "Token inválido"
**Solução:** Delete `configs/google_drive_token.json` e reautentique

### Problema: "Credenciais não encontradas"
**Solução:** Verifique se `configs/google_drive_credentials.json` existe e está correto

### Problema: Navegador não abre automaticamente
**Solução:** Copie a URL do terminal e cole no navegador manualmente

---

## 📚 Referências
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API Python Quickstart](https://developers.google.com/drive/api/quickstart/python)
