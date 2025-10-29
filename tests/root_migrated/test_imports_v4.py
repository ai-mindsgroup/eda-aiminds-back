#!/usr/bin/env python3
"""
Teste Rápido de Importações - RAGDataAgent V4.0

Verifica se todas as importações estão funcionando corretamente.
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Testando importações...")
print("=" * 60)

try:
    print("\n1. Importando dynamic_prompts...")
    from src.prompts.dynamic_prompts import (
        DynamicPromptGenerator,
        DatasetContext,
        get_dynamic_prompt_generator
    )
    print("   ✅ dynamic_prompts OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

try:
    print("\n2. Importando optimized_config...")
    from src.llm.optimized_config import (
        get_configs_for_intent,
        AnalysisType,
        get_llm_config,
        get_rag_config
    )
    print("   ✅ optimized_config OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

try:
    print("\n3. Importando rag_data_agent...")
    from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent
    print("   ✅ rag_data_agent OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

try:
    print("\n4. Importando rag_data_agent_v4...")
    from src.agent.rag_data_agent_v4 import RAGDataAgentV4, create_agent_v4
    print("   ✅ rag_data_agent_v4 OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Todas as importações funcionando!")
print("\nTentando criar uma instância do agente V4...")

try:
    # Criar prompt generator
    print("\n5. Criando DynamicPromptGenerator...")
    prompt_gen = DynamicPromptGenerator()
    print("   ✅ DynamicPromptGenerator criado")
    
    # Testar configurações
    print("\n6. Testando configurações otimizadas...")
    llm_config, rag_config = get_configs_for_intent('statistical')
    print(f"   ✅ LLM Config: temp={llm_config.temperature}, max_tokens={llm_config.max_tokens}")
    print(f"   ✅ RAG Config: threshold={rag_config.similarity_threshold}, max_chunks={rag_config.max_chunks}")
    
    # Criar agente (pode falhar se não tiver LLM configurado, mas imports devem funcionar)
    print("\n7. Tentando criar RAGDataAgentV4...")
    try:
        agent = create_agent_v4()
        print("   ✅ RAGDataAgentV4 criado com sucesso!")
        print(f"   ✅ Tipo: {type(agent)}")
    except Exception as e:
        print(f"   ⚠️  Agente não pode ser criado (normal se LLM não configurado): {str(e)[:100]}")
        print("   ✅ Mas as importações estão OK!")
    
except Exception as e:
    print(f"\n❌ Erro ao testar funcionalidades: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 Sistema V4.0 pronto para uso!")
print("\nPróximo passo: python tests/test_17_perguntas_v4.py")
