# Arquivo removido por obsolescência do pipeline semântico
# 
# Teste do sistema corrigido com estatísticas reais
# 
# import sys
# from pathlib import Path
# 
# # Adiciona o diretório raiz do projeto ao PYTHONPATH
# root_dir = Path(__file__).parent
# sys.path.insert(0, str(root_dir))
# 
# from src.agent.orchestrator_agent import OrchestratorAgent
# 
# def test_corrected_system():
#     """Testa o sistema corrigido com ferramentas Python e guardrails"""
#     
#     print("🧪 Teste do Sistema Corrigido")
#     print("=" * 60)
#     
#     # Inicializar orquestrador
#     print("🔧 Inicializando orquestrador com ferramentas corrigidas...")
#     orchestrator = OrchestratorAgent("orchestrator")
#     
#     print("✅ Orquestrador inicializado")
#     
#     # Teste 1: Pergunta sobre tipos de dados
#     print(f"\n{'='*60}")
#     print("📋 TESTE 1: Tipos de dados")
#     print("="*60)
#     
#     query1 = "Quais são os tipos de dados (numéricos, categóricos)?"
#     print(f"❓ Pergunta: {query1}")
#     print("🔄 Processando...")
#     
#     result1 = orchestrator.process(query1)
#     
#     if result1:
#         print("\n✅ Sucesso!")
#         print("🤖 Resposta:")
#         print(result1.get("content", "Sem resposta"))
#         
#         metadata1 = result1.get("metadata", {})
#         print(f"\n🛠️ Agentes usados: {', '.join(metadata1.get('agents_used', []))}")
#         print(f"🤖 Provedor LLM: {metadata1.get('provider', 'N/A')}")
#         print(f"⏱️ Tempo: {metadata1.get('processing_time', 0):.2f}s")
#         
#         if metadata1.get("error", False):
#             print("🎯 Resultado: ❌ FALHA")
#             return False
#         else:
#             print("🎯 Resultado: ✅ SUCESSO")
#     else:
#         print("❌ Erro: Nenhuma resposta recebida")
#         return False
#     
#     # Teste 2: Pergunta sobre estatísticas específicas
#     print(f"\n{'='*60}")
#     print("📊 TESTE 2: Estatísticas específicas")
#     print("="*60)
#     
#     query2 = "Quais são as estatísticas do campo Amount (média, desvio padrão, mín, máx)?"
#     print(f"❓ Pergunta: {query2}")
#     print("🔄 Processando...")
#     
#     result2 = orchestrator.process(query2)
#     
#     if result2:
#         print("\n✅ Sucesso!")
#         print("🤖 Resposta:")
#         print(result2.get("content", "Sem resposta"))
#         
#         metadata2 = result2.get("metadata", {})
#         print(f"\n🛠️ Agentes usados: {', '.join(metadata2.get('agents_used', []))}")
#         print(f"🤖 Provedor LLM: {metadata2.get('provider', 'N/A')}")
#         print(f"⏱️ Tempo: {metadata2.get('processing_time', 0):.2f}s")
#         
#         if metadata2.get("error", False):
#             print("🎯 Resultado: ❌ FALHA")
#             return False
#         else:
#             print("🎯 Resultado: ✅ SUCESSO")
#     else:
#         print("❌ Erro: Nenhuma resposta recebida")
#         return False
#     
#     # Teste 3: Pergunta sobre distribuição de classes
#     print(f"\n{'='*60}")
#     print("📈 TESTE 3: Distribuição de classes")
#     print("="*60)
#     
#     query3 = "Qual é a distribuição das classes de fraude? Quantos % são normais vs fraudulentas?"
#     print(f"❓ Pergunta: {query3}")
#     print("🔄 Processando...")
#     
#     result3 = orchestrator.process(query3)
#     
#     if result3:
#         print("\n✅ Sucesso!")
#         print("🤖 Resposta:")
#         print(result3.get("content", "Sem resposta"))
#         
#         metadata3 = result3.get("metadata", {})
#         print(f"\n🛠️ Agentes usados: {', '.join(metadata3.get('agents_used', []))}")
#         print(f"🤖 Provedor LLM: {metadata3.get('provider', 'N/A')}")
#         print(f"⏱️ Tempo: {metadata3.get('processing_time', 0):.2f}s")
#         
#         if metadata3.get("error", False):
#             print("🎯 Resultado: ❌ FALHA")
#             return False
#         else:
#             print("🎯 Resultado: ✅ SUCESSO")
#     else:
#         print("❌ Erro: Nenhuma resposta recebida")
#         return False
#     
#     print(f"\n{'='*60}")
#     print("🎯 RESULTADO GERAL: ✅ TODOS OS TESTES PASSARAM")
#     print("✅ Sistema corrigido funcionando com estatísticas reais!")
#     print("="*60)
#     return True
# 
# if __name__ == "__main__":
#     success = test_corrected_system()
#     exit(0 if success else 1)
#!/usr/bin/env python3
"""Teste do sistema corrigido com estatísticas reais"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_corrected_system():
    """Testa o sistema corrigido com ferramentas Python e guardrails"""
    
    print("🧪 Teste do Sistema Corrigido")
    print("=" * 60)
    
    # Inicializar orquestrador
    print("🔧 Inicializando orquestrador com ferramentas corrigidas...")
    orchestrator = OrchestratorAgent("orchestrator")
    
    print("✅ Orquestrador inicializado")
    
    # Teste 1: Pergunta sobre tipos de dados
    print(f"\n{'='*60}")
    print("📋 TESTE 1: Tipos de dados")
    print("="*60)
    
    query1 = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"❓ Pergunta: {query1}")
    print("🔄 Processando...")
    
    result1 = orchestrator.process(query1)
    
    if result1:
        print("\n✅ Sucesso!")
        print("🤖 Resposta:")
        print(result1.get("content", "Sem resposta"))
        
        metadata1 = result1.get("metadata", {})
        print(f"\n🛠️ Agentes usados: {', '.join(metadata1.get('agents_used', []))}")
        print(f"🤖 Provedor LLM: {metadata1.get('provider', 'N/A')}")
        print(f"⏱️ Tempo: {metadata1.get('processing_time', 0):.2f}s")
        
        if metadata1.get("error", False):
            print("🎯 Resultado: ❌ FALHA")
            return False
        else:
            print("🎯 Resultado: ✅ SUCESSO")
    else:
        print("❌ Erro: Nenhuma resposta recebida")
        return False
    
    # Teste 2: Pergunta sobre estatísticas específicas
    print(f"\n{'='*60}")
    print("📊 TESTE 2: Estatísticas específicas")
    print("="*60)
    
    query2 = "Quais são as estatísticas do campo Amount (média, desvio padrão, mín, máx)?"
    print(f"❓ Pergunta: {query2}")
    print("🔄 Processando...")
    
    result2 = orchestrator.process(query2)
    
    if result2:
        print("\n✅ Sucesso!")
        print("🤖 Resposta:")
        print(result2.get("content", "Sem resposta"))
        
        metadata2 = result2.get("metadata", {})
        print(f"\n🛠️ Agentes usados: {', '.join(metadata2.get('agents_used', []))}")
        print(f"🤖 Provedor LLM: {metadata2.get('provider', 'N/A')}")
        print(f"⏱️ Tempo: {metadata2.get('processing_time', 0):.2f}s")
        
        if metadata2.get("error", False):
            print("🎯 Resultado: ❌ FALHA")
            return False
        else:
            print("🎯 Resultado: ✅ SUCESSO")
    else:
        print("❌ Erro: Nenhuma resposta recebida")
        return False
    
    # Teste 3: Pergunta sobre distribuição de classes
    print(f"\n{'='*60}")
    print("📈 TESTE 3: Distribuição de classes")
    print("="*60)
    
    query3 = "Qual é a distribuição das classes de fraude? Quantos % são normais vs fraudulentas?"
    print(f"❓ Pergunta: {query3}")
    print("🔄 Processando...")
    
    result3 = orchestrator.process(query3)
    
    if result3:
        print("\n✅ Sucesso!")
        print("🤖 Resposta:")
        print(result3.get("content", "Sem resposta"))
        
        metadata3 = result3.get("metadata", {})
        print(f"\n🛠️ Agentes usados: {', '.join(metadata3.get('agents_used', []))}")
        print(f"🤖 Provedor LLM: {metadata3.get('provider', 'N/A')}")
        print(f"⏱️ Tempo: {metadata3.get('processing_time', 0):.2f}s")
        
        if metadata3.get("error", False):
            print("🎯 Resultado: ❌ FALHA")
            return False
        else:
            print("🎯 Resultado: ✅ SUCESSO")
    else:
        print("❌ Erro: Nenhuma resposta recebida")
        return False
    
    print(f"\n{'='*60}")
    print("🎯 RESULTADO GERAL: ✅ TODOS OS TESTES PASSARAM")
    print("✅ Sistema corrigido funcionando com estatísticas reais!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_corrected_system()
    exit(0 if success else 1)