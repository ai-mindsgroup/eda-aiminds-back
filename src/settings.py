"""Carrega configurações do ambiente.

- Prioriza variáveis do sistema.
- Se existir um arquivo configs/.env, carrega via python-dotenv.
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env se existir
ENV_PATH = Path(__file__).resolve().parents[1] / "configs" / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GROQ_API_BASE: str = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
SONAR_API_KEY: str | None = os.getenv("SONAR_API_KEY")
SONAR_API_BASE: str = os.getenv("SONAR_API_BASE", "https://api.perplexity.ai")
SONAR_DEFAULT_MODEL: str = os.getenv("SONAR_DEFAULT_MODEL", "sonar-pro")

# Validações leves (opcionalmente tornar estritas em produção)
REQUIRED_ON_RUNTIME = [
    ("SUPABASE_URL", SUPABASE_URL),
    ("SUPABASE_KEY", SUPABASE_KEY),
]

missing = [name for name, val in REQUIRED_ON_RUNTIME if not val]
if missing:
    # Evita quebrar import em ambientes de desenvolvimento; logue um aviso
    import warnings
    warnings.warn(f"Variáveis ausentes: {', '.join(missing)}. Configure configs/.env ou variáveis de ambiente.")

HISTOGRAMS_DIR: str = os.getenv("HISTOGRAMS_DIR", "static/histogramas")

# ========================================================================
# CONFIGURAÇÕES DA API
# ========================================================================

# Host e Porta da API
# API_HOST: 0.0.0.0 = aceita conexões de qualquer IP (incluindo IPs externos da VPS)
#           127.0.0.1 = aceita apenas conexões locais
# API_PORT: Use porta não comum para segurança (evita ataques em portas conhecidas)
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8011"))

# ========================================================================
# CONFIGURAÇÕES DE INGESTÃO AUTOMÁTICA DE CSV
# ========================================================================

# Diretórios locais de gerenciamento de arquivos CSV

EDA_DATA_DIR: Path = Path(os.getenv("EDA_DATA_DIR", "data"))
EDA_DATA_DIR_PROCESSANDO: Path = Path(os.getenv("EDA_DATA_DIR_PROCESSANDO", "data/processando"))
EDA_DATA_DIR_PROCESSADO: Path = Path(os.getenv("EDA_DATA_DIR_PROCESSADO", "data/processado"))
EDA_DATA_DIR_HISTORICO: Path = Path(os.getenv("EDA_DATA_DIR_HISTORICO", "data/historico"))

# Google Drive API
GOOGLE_DRIVE_ENABLED: bool = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"

# Modo de autenticação: "oauth" (padrão) ou "service_account"
GOOGLE_DRIVE_AUTH_MODE: str = os.getenv("GOOGLE_DRIVE_AUTH_MODE", "oauth")

# OAuth credentials (para modo "oauth")
GOOGLE_DRIVE_CREDENTIALS_FILE: Path = Path(os.getenv("GOOGLE_DRIVE_CREDENTIALS_FILE", "configs/google_drive_credentials.json"))
GOOGLE_DRIVE_TOKEN_FILE: Path = Path(os.getenv("GOOGLE_DRIVE_TOKEN_FILE", "configs/google_drive_token.json"))

# Service Account credentials (para modo "service_account")
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE: Path = Path(os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE", "configs/google_drive_service_account.json"))

# ID da pasta do Google Drive a monitorar
GOOGLE_DRIVE_FOLDER_ID: str | None = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# ID da pasta "processados" no Google Drive (criada automaticamente se não existir)
GOOGLE_DRIVE_PROCESSED_FOLDER_ID: str | None = os.getenv("GOOGLE_DRIVE_PROCESSED_FOLDER_ID")

# Comportamento após processamento: "delete" ou "move" (recomendado: move)
GOOGLE_DRIVE_POST_PROCESS_ACTION: str = os.getenv("GOOGLE_DRIVE_POST_PROCESS_ACTION", "move")

# Configurações de polling
AUTO_INGEST_POLLING_INTERVAL: int = int(os.getenv("AUTO_INGEST_POLLING_INTERVAL", "300"))
AUTO_INGEST_FILE_PATTERN: str = os.getenv("AUTO_INGEST_FILE_PATTERN", r".*\.csv$")

# ========================================================================
# CONFIGURAÇÕES DE BANCO (Postgres/Supabase)
# ========================================================================

# Configurações de banco (Postgres/Supabase)
DB_HOST: str | None = os.getenv("DB_HOST")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str | None = os.getenv("DB_NAME")
DB_USER: str | None = os.getenv("DB_USER")
DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")

def build_db_dsn() -> str:
    """Monta DSN para conexão psycopg.

    Exemplo: postgresql://user:pass@host:5432/dbname
    """
    user = DB_USER or "postgres"
    host = DB_HOST or "localhost"
    name = DB_NAME or "postgres"
    port = DB_PORT or "5432"
    password = DB_PASSWORD or ""
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return f"postgresql://{user}@{host}:{port}/{name}"
