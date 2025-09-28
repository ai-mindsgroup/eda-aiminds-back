#!/usr/bin/env python3
"""
Teste de Classificação LLM - Verificar se consultas são corretamente direcionadas
==============================================================================
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def main():
    print("🧪 TESTE DE CLASSIFICAÇÃO LLM")
    print("=" * 50)
    
    # Consultas que DEVEM usar LLM
    consultas_llm = [
        "faça um resumo detalhado dos dados",
        "analise as correlações",
        "explique os padrões de fraude", 
        "qual sua conclusão sobre os dados?",
        "dê uma recomendação baseada na análise",
        "interprete os resultados",
        "o que você descobriu?",
        "quais anomalias encontrou?",
        "como você avalia esses dados?",
        "discuta os comportamentos suspeitos"
    ]
    
    # Inicializar orquestrador
    orchestrator = OrchestratorAgent()
    
    print(f"\n🎯 Testando {len(consultas_llm)} consultas:")
    
    acertos = 0
    total = len(consultas_llm)
    
    for i, query in enumerate(consultas_llm, 1):
        print(f"\n--- Teste {i}/{total} ---")
        print(f"❓ Query: '{query}'")
        
        # Classificar sem processar completamente
        query_type = orchestrator._classify_query(query, {"file_path": "test.csv"})
        
        print(f"📝 Classificado como: {query_type.value}")
        
        if query_type.value == "llm_analysis":
            print("✅ CORRETO - Vai usar LLM Agent")
            acertos += 1
        else:
            print(f"❌ INCORRETO - Vai usar {query_type.value}")
    
    print(f"\n🏁 RESULTADO FINAL:")
    print(f"✅ Acertos: {acertos}/{total} ({acertos/total*100:.1f}%)")
    print(f"❌ Erros: {total-acertos}/{total}")
    
    if acertos == total:
        print("🎉 PERFEITO! Todas as consultas LLM foram classificadas corretamente!")
    elif acertos/total >= 0.8:
        print("✅ BOM! Maioria das consultas LLM classificadas corretamente.")
    else:
        print("⚠️ PRECISA MELHORAR - Muitas consultas LLM não classificadas.")

if __name__ == "__main__":
    main()