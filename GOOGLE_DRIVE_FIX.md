# 🚀 Guia Rápido: Resolver Erro 403 ao Deletar Arquivos

## ❌ Problema

OAuth não pode deletar arquivos do Google Drive que não foram criados pela aplicação:
```
403 Forbidden: "insufficientFilePermissions"
```

## ✅ Solução: Service Account

Use **Service Account** em vez de OAuth. Permite deletar qualquer arquivo da pasta compartilhada.

## 📋 Passos (5 minutos)

### 1. Criar Service Account
1. Acesse: https://console.cloud.google.com/iam-admin/serviceaccounts
2. CREATE SERVICE ACCOUNT
3. Nome: `eda-aiminds-drive-service`
4. Pule roles → DONE

### 2. Baixar Chave JSON
1. Clique no Service Account criado
2. KEYS → ADD KEY → Create new key → JSON
3. Salve como `configs/google_drive_service_account.json`

### 3. Compartilhar Pasta
1. Abra o arquivo JSON e copie `client_email`
2. Acesse sua pasta no Drive
3. Share com o email copiado
4. Permissão: **Editor**

### 4. Configurar `.env`
```env
GOOGLE_DRIVE_AUTH_MODE=service_account
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=configs/google_drive_service_account.json
```

### 5. Testar
```powershell
python test_service_account.py
```

## 📖 Guia Completo

Veja: [`docs/GOOGLE_DRIVE_SERVICE_ACCOUNT_SETUP.md`](docs/GOOGLE_DRIVE_SERVICE_ACCOUNT_SETUP.md)

## 🆚 Comparação

| | OAuth | Service Account |
|---|---|---|
| Deletar arquivos | ❌ Só os criados pelo app | ✅ Todos |
| Configuração | Simples | 5 min extras |
| Automação | ⚠️ Renovação de token | ✅ Sem interação |
| **Recomendado para** | Testes | **Produção** |
