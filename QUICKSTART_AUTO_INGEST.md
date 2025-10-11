# 🚀 Quick Start - Sistema de Ingestão Automática

## Instalação Rápida

```powershell
# 1. Instalar dependências
pip install -r requirements-auto-ingest.txt

# 2. Configurar .env
# Edite configs/.env e adicione as variáveis do Google Drive

# 3. Testar configuração
python test_auto_ingest.py

# 4. Executar (teste)
python run_auto_ingest.py --once

# 5. Executar (produção)
python run_auto_ingest.py
```

## 📚 Documentação Completa

Veja: [`docs/AUTO_INGEST_SETUP.md`](docs/AUTO_INGEST_SETUP.md)

## 🎯 Funcionalidades

- ✅ Monitoramento automático do Google Drive
- ✅ Download automático de CSVs
- ✅ Processamento via DataIngestor (embeddings)
- ✅ Gerenciamento de ciclo de vida dos arquivos
- ✅ Logging detalhado e estatísticas
- ✅ Compatível com Windows VPS
- ✅ Shutdown gracioso (Ctrl+C)

## 🔧 Comandos Úteis

```powershell
# Teste único ciclo
python run_auto_ingest.py --once

# Modo debug
python run_auto_ingest.py --debug

# Intervalo customizado (60s)
python run_auto_ingest.py --interval 60

# Ver ajuda
python run_auto_ingest.py --help
```

## 📁 Estrutura

```
src/
├── integrations/
│   └── google_drive_client.py     # Cliente Google Drive API
├── data/
│   └── csv_file_manager.py        # Gerenciador de arquivos
└── services/
    └── auto_ingest_service.py     # Serviço principal

run_auto_ingest.py                  # Script executável
test_auto_ingest.py                 # Testes
```

## 🆘 Suporte

Problemas? Veja a seção **Troubleshooting** na documentação completa.
