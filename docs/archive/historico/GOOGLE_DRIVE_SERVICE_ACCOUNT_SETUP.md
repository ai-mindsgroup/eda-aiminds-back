# Configuração Service Account para Google Drive

## 🎯 Por Que Service Account?

**Problema com OAuth:** Não pode deletar arquivos que não foram criados pela aplicação (erro 403).

**Solução com Service Account:**
- ✅ Acesso total à pasta compartilhada
- ✅ Pode deletar qualquer arquivo
- ✅ Sem necessidade de interação do usuário
- ✅ Ideal para automação server-side

---

## 📋 Passo a Passo Completo

### **1. Criar Service Account no Google Cloud Console**

1. Acesse: https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Selecione seu projeto** (ID: 83525436581)
3. Clique em **"+ CREATE SERVICE ACCOUNT"**
4. Preencha:
   ```
   Service account name: eda-aiminds-drive-service
   Service account ID: eda-aiminds-drive-service (será gerado automaticamente)
   Description: Service account para auto-ingest de CSV do Google Drive
   ```
5. Clique **"CREATE AND CONTINUE"**
6. **IMPORTANTE:** Na seção "Grant this service account access to project":
   - **Pule esta etapa** (não precisa adicionar roles de IAM)
   - Clique **"CONTINUE"**
7. **Pule** também "Grant users access to this service account"
8. Clique **"DONE"**

### **2. Gerar Chave JSON**

1. Na lista de Service Accounts, clique no que você acabou de criar
2. Vá na aba **"KEYS"**
3. Clique **"ADD KEY" → "Create new key"**
4. Selecione **"JSON"**
5. Clique **"CREATE"**
6. O arquivo será baixado automaticamente (ex: `eda-aiminds-drive-service-xxxxx.json`)

### **3. Copiar Arquivo JSON para o Projeto**

```powershell
# Copie o arquivo baixado para a pasta configs
Copy-Item "C:\Users\SEU_USUARIO\Downloads\eda-aiminds-drive-service-xxxxx.json" `
          "C:\workstashion\eda-aiminds-i2a2-rb\configs\google_drive_service_account.json"
```

### **4. Obter Email do Service Account**

Abra o arquivo JSON e copie o valor de `client_email`:

```json
{
  "type": "service_account",
  "project_id": "seu-projeto",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "eda-aiminds-drive-service@seu-projeto.iam.gserviceaccount.com",
  ...
}
```

O email será algo como:  
`eda-aiminds-drive-service@PROJECT_ID.iam.gserviceaccount.com`

### **5. Compartilhar Pasta do Google Drive**

1. Acesse sua pasta: https://drive.google.com/drive/folders/1TZRAYnvGAQt--Dp3jWuPEV36bVVLpv2M
2. Clique com botão direito na pasta → **"Share"** (ou **"Compartilhar"**)
3. No campo de email, **cole o email do Service Account**
4. Selecione permissão **"Editor"** (ou melhor ainda: **"Manager"**)
5. **DESMARQUE** a caixa "Notify people" (não precisa enviar email)
6. Clique **"Share"**

**✅ PRONTO!** O Service Account agora tem acesso total à pasta.

### **6. Atualizar Configuração no `.env`**

Edite `configs/.env` e adicione/modifique:

```env
# Modo de autenticação: "oauth" ou "service_account"
GOOGLE_DRIVE_AUTH_MODE=service_account

# Caminho para o arquivo JSON do Service Account
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=configs/google_drive_service_account.json

# Manter outras configurações
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=1TZRAYnvGAQt--Dp3jWuPEV36bVVLpv2M
```

### **7. Testar**

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Executar teste
python run_auto_ingest.py --once
```

**Resultado esperado:**
```
✅ Service Account autenticado com sucesso
📥 Encontrados X novos arquivos CSV
⬇️ Baixando: arquivo.csv
✅ Ingestão concluída com sucesso
✅ Movido para: data\processado\arquivo.csv
🗑️ Deletando arquivo do Google Drive: XXXXXX
✅ Arquivo deletado com sucesso do Google Drive
```

---

## 🔐 Segurança

**IMPORTANTE:** O arquivo `google_drive_service_account.json` contém credenciais sensíveis!

1. **NUNCA** faça commit dele no Git
2. Está incluído no `.gitignore` automaticamente
3. Em produção, use variáveis de ambiente ou secret manager

---

## 🆚 Comparação: OAuth vs Service Account

| Característica | OAuth | Service Account |
|---|---|---|
| Autenticação | Requer interação do usuário | Automático |
| Deletar arquivos | ❌ Só os criados pelo app | ✅ Todos na pasta compartilhada |
| Renovação de token | Precisa renovar periodicamente | ✅ Não expira |
| Uso ideal | Aplicações desktop/web | ✅ Automação server-side |
| Configuração | Mais simples | Requer passos extras |

**Recomendação:** Use **Service Account** para automação em produção.

---

## 🐛 Troubleshooting

### Erro: "Service Account file not found"
- Verifique se copiou o arquivo para `configs/google_drive_service_account.json`
- Confirme que o caminho está correto no `.env`

### Erro: "The caller does not have permission"
- Service Account não tem acesso à pasta
- Compartilhe a pasta novamente com o email correto
- Use permissão "Editor" ou "Manager"

### Erro: "Invalid JSON file"
- Arquivo JSON está corrompido
- Baixe a chave novamente do Google Cloud Console

---

## 📚 Referências

- [Google Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Drive API with Service Account](https://developers.google.com/drive/api/guides/service-accounts)
- [Python Google Auth](https://google-auth.readthedocs.io/en/latest/user-guide.html#service-account-credentials)
