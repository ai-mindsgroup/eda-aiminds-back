"""Demonstração do Agente Orquestrador Central.

Este script mostra as capacidades do orquestrador:
- Roteamento inteligente de consultas
- Coordenação de múltiplos agentes
- Manutenção de contexto
- Interface unificada
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.data.data_processor import create_demo_data


def test_orchestrator_comprehensive():
    """Teste completo do sistema orquestrador."""
    
    print("🚀 DEMONSTRAÇÃO DO AGENTE ORQUESTRADOR CENTRAL")
    print("=" * 70)
    
    # 1. Inicializar orquestrador
    print("\n🤖 INICIALIZANDO SISTEMA...")
    print("-" * 50)
    
    try:
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=True, 
            enable_data_processor=True
        )
        print("✅ Sistema inicializado com sucesso!")
        
        # Verificar status
        status = orchestrator.process("status do sistema")
        print(status['content'])
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {str(e)}")
        return
    
    print("\n" + "=" * 70)
    
    # 2. Testes de saudação e ajuda
    print("\n💬 TESTES DE INTERAÇÃO BÁSICA")
    print("-" * 50)
    
    basic_queries = [
        "olá, como você pode me ajudar?",
        "ajuda com o sistema",
        "quais agentes estão disponíveis?"
    ]
    
    for query in basic_queries:
        print(f"\n📝 Consulta: {query}")
        print("─" * 30)
        
        result = orchestrator.process(query)
        print(result['content'])
        
        # Mostrar metadados importantes
        metadata = result.get('metadata', {})
        if 'agents_used' in metadata:
            print(f"🤖 Agentes utilizados: {metadata['agents_used']}")
    
    print("\n" + "=" * 70)
    
    # 3. Teste de carregamento de dados
    print("\n📁 TESTE DE CARREGAMENTO DE DADOS")
    print("-" * 50)
    
    # Criar dados sintéticos para demonstração
    print("🔧 Criando dados sintéticos...")
    try:
        demo_file = create_demo_data()
        print(f"✅ Dados criados: {demo_file}")
        
        # Carregar dados via orquestrador
        load_query = "carregar dados para análise"
        load_context = {"file_path": demo_file}
        
        print(f"\n📝 Consulta: {load_query}")
        print(f"📂 Contexto: {load_context}")
        print("─" * 30)
        
        result = orchestrator.process(load_query, load_context)
        print(result['content'])
        
        if not result.get('metadata', {}).get('error'):
            print("✅ Dados carregados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no carregamento: {str(e)}")
        demo_file = None
    
    print("\n" + "=" * 70)
    
    # 4. Testes de análise CSV (se dados foram carregados)
    if demo_file:
        print("\n📊 TESTES DE ANÁLISE CSV")
        print("-" * 50)
        
        csv_queries = [
            "faça um resumo dos dados carregados",
            "mostre as correlações mais importantes",
            "analise padrões de fraude nos dados",
            "quais são as estatísticas básicas?"
        ]
        
        for query in csv_queries:
            print(f"\n📝 Consulta: {query}")
            print("─" * 30)
            
            result = orchestrator.process(query)
            print(result['content'])
            
            # Mostrar uso de agentes
            metadata = result.get('metadata', {})
            agents_used = metadata.get('agents_used', [])
            print(f"🤖 Agentes: {', '.join(agents_used) if agents_used else 'nenhum'}")
    
    print("\n" + "=" * 70)
    
    # 5. Testes RAG (busca semântica)
    print("\n🔍 TESTES DE BUSCA SEMÂNTICA (RAG)")
    print("-" * 50)
    
    # Primeiro, adicionar alguns documentos à base de conhecimento
    print("📚 Adicionando conhecimento à base...")
    try:
        documents = {
            "fraud_detection": """
            Detecção de fraude em cartões de crédito é um desafio crítico no setor financeiro.
            Os principais indicadores incluem: valor da transação, localização geográfica,
            frequência de uso, e padrões temporais. Machine learning é amplamente usado
            para identificar transações suspeitas através de algoritmos como Random Forest,
            SVM e redes neurais.
            """,
            "data_analysis": """
            Análise exploratória de dados (EDA) é fundamental para entender datasets.
            Inclui estatísticas descritivas, visualizações, correlações e identificação
            de outliers. Python com pandas, matplotlib e seaborn são ferramentas essenciais
            para EDA eficaz.
            """
        }
        
        for doc_id, content in documents.items():
            ingest_result = orchestrator.agents["rag"].ingest_text(
                text=content,
                source_id=doc_id,
                source_type="demo"
            )
            if not ingest_result.get('metadata', {}).get('error'):
                print(f"✅ Documento '{doc_id}' adicionado")
        
        print("📊 Base de conhecimento preparada!")
        
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao preparar base RAG: {str(e)}")
    
    # Consultas RAG
    rag_queries = [
        "busque informações sobre detecção de fraude",
        "encontre dados sobre análise exploratória",
        "procure por técnicas de machine learning",
        "qual o contexto sobre visualização de dados?"
    ]
    
    for query in rag_queries:
        print(f"\n📝 Consulta: {query}")
        print("─" * 30)
        
        try:
            result = orchestrator.process(query)
            content = result['content']
            
            # Limitar saída para demonstração
            if len(content) > 300:
                content = content[:300] + "..."
            
            print(content)
            
            # Mostrar metadados RAG
            metadata = result.get('metadata', {})
            if 'search_results_count' in metadata:
                print(f"🔍 Resultados encontrados: {metadata['search_results_count']}")
            if 'agents_used' in metadata:
                print(f"🤖 Agentes: {', '.join(metadata['agents_used'])}")
            
        except Exception as e:
            print(f"⚠️ Erro na busca: {str(e)}")
    
    print("\n" + "=" * 70)
    
    # 6. Teste de consulta híbrida
    print("\n🔄 TESTE DE CONSULTA HÍBRIDA")
    print("-" * 50)
    
    if demo_file:
        hybrid_query = "analise os dados carregados e busque informações similares sobre fraude"
        print(f"📝 Consulta: {hybrid_query}")
        print("─" * 30)
        
        try:
            result = orchestrator.process(hybrid_query)
            content = result['content']
            
            # Limitar saída
            if len(content) > 500:
                content = content[:500] + "..."
            
            print(content)
            
            # Mostrar que múltiplos agentes foram usados
            metadata = result.get('metadata', {})
            if 'hybrid_query' in metadata:
                print("🔄 ✅ Consulta híbrida processada com múltiplos agentes!")
            print(f"🤖 Agentes utilizados: {metadata.get('agents_used', [])}")
            
        except Exception as e:
            print(f"⚠️ Erro na consulta híbrida: {str(e)}")
    
    print("\n" + "=" * 70)
    
    # 7. Estatísticas finais
    print("\n📈 ESTATÍSTICAS FINAIS")
    print("-" * 50)
    
    try:
        # Histórico da conversa
        history = orchestrator.get_conversation_history()
        print(f"💬 Total de interações: {len(history)}")
        
        # Estatísticas do sistema
        final_status = orchestrator.process("status completo")
        print("\n" + final_status['content'])
        
        print(f"\n✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"🎯 O orquestrador processou {len(history)} consultas diferentes")
        print(f"🤖 Coordenou múltiplos agentes de forma inteligente")
        print(f"💾 Manteve contexto de dados e conversação")
        
    except Exception as e:
        print(f"⚠️ Erro nas estatísticas: {str(e)}")
    
    print("\n" + "=" * 70)


def test_simple_orchestrator():
    """Teste simples e rápido do orquestrador."""
    print("⚡ TESTE RÁPIDO DO ORQUESTRADOR")
    print("=" * 40)
    
    try:
        orchestrator = OrchestratorAgent()
        
        # Teste básico
        queries = [
            "olá",
            "status",
            "ajuda"
        ]
        
        for query in queries:
            print(f"\n❓ {query}")
            result = orchestrator.process(query)
            print(f"✅ Resposta recebida ({len(result['content'])} chars)")
        
        print("\n✅ Teste rápido concluído!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_simple_orchestrator()
    else:
        test_orchestrator_comprehensive()