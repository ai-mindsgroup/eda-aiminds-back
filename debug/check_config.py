#!/usr/bin/env python3
"""
Validador de Configuração - EDA AI Minds
========================================

Script para validar se todas as configurações estão corretas.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

def check_env_file() -> Tuple[bool, List[str]]:
    """Verifica se o arquivo .env existe e está acessível."""
    errors = []
    
    env_path = Path("configs/.env")
    if not env_path.exists():
        errors.append("❌ Arquivo configs/.env não encontrado")
        errors.append("💡 Execute: cp configs/.env.example configs/.env")
        return False, errors
    
    if not env_path.is_file():
        errors.append("❌ configs/.env não é um arquivo válido")
        return False, errors
        
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content.strip()) == 0:
            errors.append("❌ Arquivo configs/.env está vazio")
            return False, errors
    except Exception as e:
        errors.append(f"❌ Erro ao ler configs/.env: {e}")
        return False, errors
    
    return True, []

def check_supabase_config() -> Tuple[bool, List[str]]:
    """Verifica configurações do Supabase."""
    errors = []
    
    try:
        from src.settings import SUPABASE_URL, SUPABASE_KEY
        
        if not SUPABASE_URL:
            errors.append("❌ SUPABASE_URL não configurado")
        elif "seu-projeto" in SUPABASE_URL:
            errors.append("❌ SUPABASE_URL ainda é template, configure o seu projeto")
        else:
            print(f"✅ SUPABASE_URL: {SUPABASE_URL[:30]}...")
            
        if not SUPABASE_KEY:
            errors.append("❌ SUPABASE_KEY não configurado")
        elif "sua_chave" in SUPABASE_KEY:
            errors.append("❌ SUPABASE_KEY ainda é template, configure sua chave")
        else:
            print(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:20]}...")
            
    except ImportError as e:
        errors.append(f"❌ Erro ao importar configurações: {e}")
    except Exception as e:
        errors.append(f"❌ Erro ao verificar Supabase: {e}")
    
    return len(errors) == 0, errors

def check_llm_config() -> Tuple[bool, List[str]]:
    """Verifica se pelo menos um LLM está configurado."""
    errors = []
    configured_llms = []
    
    try:
        from src.settings import GOOGLE_API_KEY, GROQ_API_KEY, OPENAI_API_KEY
        
        if GOOGLE_API_KEY and "sua_chave" not in GOOGLE_API_KEY:
            configured_llms.append("Google Gemini")
            print(f"✅ GOOGLE_API_KEY: {GOOGLE_API_KEY[:20]}...")
            
        if GROQ_API_KEY and "sua_chave" not in GROQ_API_KEY:
            configured_llms.append("Groq")
            print(f"✅ GROQ_API_KEY: {GROQ_API_KEY[:20]}...")
            
        if OPENAI_API_KEY and "sua_chave" not in OPENAI_API_KEY:
            configured_llms.append("OpenAI")
            print(f"✅ OPENAI_API_KEY: {OPENAI_API_KEY[:20]}...")
        
        if not configured_llms:
            errors.append("❌ Nenhum LLM configurado")
            errors.append("💡 Configure pelo menos: GOOGLE_API_KEY, GROQ_API_KEY ou OPENAI_API_KEY")
        else:
            print(f"✅ LLMs configurados: {', '.join(configured_llms)}")
            
    except ImportError as e:
        errors.append(f"❌ Erro ao importar configurações LLM: {e}")
    except Exception as e:
        errors.append(f"❌ Erro ao verificar LLMs: {e}")
    
    return len(errors) == 0, errors

def check_database_connection() -> Tuple[bool, List[str]]:
    """Testa conexão com banco de dados."""
    errors = []
    
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Teste simples de conexão
        response = supabase.table('embeddings').select('id').limit(1).execute()
        print("✅ Conexão Supabase funcionando")
        
        # Verificar se há dados
        if response.data:
            print(f"✅ Banco contém dados: {len(response.data)} registro(s) na tabela embeddings")
        else:
            print("⚠️  Tabela embeddings vazia (normal para primeiro uso)")
            
    except Exception as e:
        errors.append(f"❌ Falha na conexão Supabase: {str(e)[:100]}")
        errors.append("💡 Verifique SUPABASE_URL e SUPABASE_KEY")
    
    return len(errors) == 0, errors

def check_llm_manager() -> Tuple[bool, List[str]]:
    """Testa se o LLM Manager está funcionando."""
    errors = []
    
    try:
        from src.llm.manager import get_llm_manager
        
        manager = get_llm_manager()
        
        # Verificar quais provedores estão disponíveis
        available_providers = []
        
        # Verificar status dos provedores através do manager
        if hasattr(manager, '_provider_status'):
            for provider, status in manager._provider_status.items():
                if status.get('available', False):
                    available_providers.append(provider.value.upper())
        
        if available_providers:
            print(f"✅ LLM Manager: {', '.join(available_providers)} disponíveis")
        else:
            errors.append("❌ Nenhum provedor LLM disponível no manager")
            
        # Verificar se há um provedor ativo
        if hasattr(manager, 'active_provider') and manager.active_provider:
            print(f"✅ Provedor ativo: {manager.active_provider.value}")
        else:
            errors.append("❌ Nenhum provedor ativo no manager")
            
    except Exception as e:
        errors.append(f"❌ Erro no LLM Manager: {str(e)[:100]}")
    
    return len(errors) == 0, errors

def main():
    """Executa todos os testes de configuração."""
    print("🔧 VALIDADOR DE CONFIGURAÇÃO - EDA AI MINDS")
    print("=" * 50)
    
    all_ok = True
    
    # Teste 1: Arquivo .env
    print("\n📁 Verificando arquivo .env...")
    env_ok, env_errors = check_env_file()
    if not env_ok:
        all_ok = False
        for error in env_errors:
            print(f"  {error}")
    else:
        print("  ✅ Arquivo .env encontrado e acessível")
    
    if not env_ok:
        print("\n❌ Configure o arquivo .env primeiro!")
        return False
    
    # Teste 2: Supabase
    print("\n🗄️  Verificando configuração Supabase...")
    supabase_ok, supabase_errors = check_supabase_config()
    if not supabase_ok:
        all_ok = False
        for error in supabase_errors:
            print(f"  {error}")
    
    # Teste 3: LLMs
    print("\n🤖 Verificando configuração LLMs...")
    llm_config_ok, llm_config_errors = check_llm_config()
    if not llm_config_ok:
        all_ok = False
        for error in llm_config_errors:
            print(f"  {error}")
    
    # Teste 4: Conexão banco (só se configuração básica OK)
    if supabase_ok:
        print("\n🔌 Testando conexão com banco...")
        db_ok, db_errors = check_database_connection()
        if not db_ok:
            all_ok = False
            for error in db_errors:
                print(f"  {error}")
    
    # Teste 5: LLM Manager (só se há LLMs configurados)
    if llm_config_ok:
        print("\n🧠 Testando LLM Manager...")
        manager_ok, manager_errors = check_llm_manager()
        if not manager_ok:
            all_ok = False
            for error in manager_errors:
                print(f"  {error}")
    
    # Resultado final
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 CONFIGURAÇÃO COMPLETA E FUNCIONAL!")
        print("\nPróximos passos:")
        print("  🚀 python api_simple.py")
        print("  🧪 python examples/exemplo_orchestrator.py") 
        print("  📊 http://127.0.0.1:8000/docs")  # localhost válido
    else:
        print("❌ CONFIGURAÇÃO INCOMPLETA")
        print("\n💡 Consulte o guia: configs/README.md")
        print("💡 Template: configs/.env.example")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)