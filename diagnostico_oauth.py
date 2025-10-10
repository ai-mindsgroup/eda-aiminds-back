#!/usr/bin/env python3
"""Mostra a porta OAuth que será usada na autenticação."""
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔍 DIAGNÓSTICO DE CONFIGURAÇÃO OAUTH")
print("=" * 70)

# 1. Verifica arquivo de credenciais
from src.settings import GOOGLE_DRIVE_CREDENTIALS_FILE
print(f"\n📄 Arquivo de credenciais: {GOOGLE_DRIVE_CREDENTIALS_FILE}")

import json
try:
    with open(GOOGLE_DRIVE_CREDENTIALS_FILE) as f:
        creds = json.load(f)
        
    if 'installed' in creds:
        print("\n✅ Tipo: Aplicativo Desktop (installed)")
        redirect_uris = creds['installed'].get('redirect_uris', [])
        if redirect_uris:
            print(f"📍 URIs no arquivo JSON:")
            for uri in redirect_uris:
                print(f"   - {uri}")
        else:
            print("⚠️  Nenhuma URI encontrada no arquivo JSON")
            print("   O Google vai usar porta aleatória (ex: localhost:xxxxx)")
            print("   Você precisa adicionar TODAS as portas possíveis no Console")
    
    print(f"\n🔑 Client ID: {creds.get('installed', {}).get('client_id', 'N/A')}")
    
except FileNotFoundError:
    print(f"❌ Arquivo não encontrado: {GOOGLE_DRIVE_CREDENTIALS_FILE}")
except Exception as e:
    print(f"❌ Erro ao ler arquivo: {e}")

print("\n" + "=" * 70)
print("💡 SOLUÇÃO")
print("=" * 70)
print("""
Se as URIs não estão no arquivo JSON, o Google OAuth vai gerar
uma porta aleatória. Você tem 2 opções:

OPÇÃO 1 (Recomendada): Adicionar URIs genéricas no Google Cloud Console
   - http://localhost:8080/
   - http://localhost:52628/
   - http://localhost/

OPÇÃO 2: Baixar novo arquivo JSON com URIs configuradas
   1. No Google Cloud Console, vá em "Credenciais"
   2. Clique na sua credencial OAuth 2.0
   3. Role até "URIs de redirecionamento autorizados"
   4. Adicione as URIs necessárias
   5. Clique em SALVAR
   6. AGUARDE 2-3 MINUTOS para propagar
   7. Tente novamente
""")
