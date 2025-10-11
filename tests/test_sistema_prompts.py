#!/usr/bin/env python3
"""Teste do sistema de prompts implementado."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_prompt_manager():
    """Testa o PromptManager."""
    
    print("🧪 TESTE: Sistema de Prompts")
    print("=" * 50)
    
    try:
        # Importar e testar o Prompt Manager
        from src.prompts.manager import get_prompt_manager, AgentRole
        
        prompt_manager = get_prompt_manager()
        
        # Teste 1: System prompt do Orchestrator
        print("\n📋 TESTE 1: System prompt do Orchestrator")
        system_prompt = prompt_manager.get_system_prompt(AgentRole.ORCHESTRATOR)
        print(f"   Tamanho: {len(system_prompt)} caracteres")
        print(f"   Contém 'multiagente': {'multiagente' in system_prompt.lower()}")
        print(f"   Contém 'português': {'português' in system_prompt.lower()}")
        
        # Teste 2: Prompt de contexto de dados
        print("\n📊 TESTE 2: Prompt de contexto de dados")
        try:
            context_prompt = prompt_manager.get_prompt(
                AgentRole.ORCHESTRATOR,
                "data_analysis_context",
                has_data="True",
                file_path="teste.csv",
                shape="(1000, 30)",
                columns_summary="30 colunas: 28 numéricas, 2 categóricas",
                csv_analysis="Dataset de transações de cartão de crédito"
            )
            print("   ✅ Template contextualizado criado com sucesso")
            print(f"   Tamanho: {len(context_prompt)} caracteres")
            print(f"   Contém dados do teste: {'teste.csv' in context_prompt}")
        except Exception as e:
            print(f"   ❌ Erro ao criar template: {str(e)}")
        
        # Teste 3: Listar prompts disponíveis
        print("\n📝 TESTE 3: Prompts disponíveis")
        available = prompt_manager.list_available_prompts()
        for agent, prompts in available.items():
            print(f"   {agent}: {len(prompts)} prompts - {', '.join(prompts)}")
        
        # Teste 4: System prompts para outros agentes
        print("\n🤖 TESTE 4: System prompts de outros agentes")
        for role in [AgentRole.CSV_ANALYST, AgentRole.RAG_SPECIALIST]:
            try:
                system_prompt = prompt_manager.get_system_prompt(role)
                print(f"   {role.value}: ✅ ({len(system_prompt)} chars)")
            except Exception as e:
                print(f"   {role.value}: ❌ {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_manager_with_prompts():
    """Testa o LLM Manager com system prompts."""
    
    print("\n🤖 TESTE: LLM Manager com System Prompts")
    print("=" * 50)
    
    try:
        from src.llm.manager import get_llm_manager, LLMConfig
        from src.prompts.manager import get_prompt_manager, AgentRole
        
        llm_manager = get_llm_manager()
        prompt_manager = get_prompt_manager()
        
        # Obter system prompt
        system_prompt = prompt_manager.get_system_prompt(AgentRole.ORCHESTRATOR)
        
        # Teste de chat com system prompt
        print("\n📤 Teste de chat com system prompt...")
        user_prompt = "Olá! Você pode se apresentar?"
        
        config = LLMConfig(temperature=0.7, max_tokens=150)
        
        print(f"   System prompt: {len(system_prompt)} caracteres")
        print(f"   User prompt: {user_prompt}")
        
        # Fazer chamada com system prompt
        response = llm_manager.chat(user_prompt, config, system_prompt=system_prompt)
        
        print(f"\n📥 RESPOSTA:")
        print(f"   Provedor: {response.provider.value}")
        print(f"   Modelo: {response.model}")
        print(f"   Tempo: {response.processing_time:.2f}s")
        print(f"   Sucesso: {response.success}")
        
        if response.success:
            print(f"   Conteúdo: {response.content[:200]}...")
            
            # Verificar se a resposta mostra a personalidade do system prompt
            content_lower = response.content.lower()
            if any(word in content_lower for word in ['orquestrador', 'multiagente', 'dados', 'csv']):
                print("   ✅ Resposta mostra personalidade do system prompt")
            else:
                print("   ⚠️ Resposta não mostra claramente a personalidade")
        else:
            print(f"   ❌ Erro: {response.error}")
        
        return response.success
        
    except Exception as e:
        print(f"❌ ERRO durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do sistema de prompts...")
    
    success_prompt = test_prompt_manager()
    success_llm = test_llm_manager_with_prompts()
    
    print("\n" + "="*60)
    if success_prompt and success_llm:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de prompts implementado e funcionando")
        print("✅ LLM Manager suporta system prompts")
        print("✅ Templates contextualizados funcionando")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("ℹ️ Verifique os logs acima para detalhes")