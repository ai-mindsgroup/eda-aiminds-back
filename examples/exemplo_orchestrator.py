"""Exemplo prático do Agente Orquestrador com dados CSV.

Demonstra o uso completo do orquestrador:
- Carregamento de dados
- Análise via CSV Agent
- Coordenação inteligente
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.data.data_processor import create_demo_data


def demo_orchestrator_with_data():
    """Demonstração completa com dados reais."""
    
    print("🚀 DEMONSTRAÇÃO PRÁTICA DO ORQUESTRADOR COM DADOS CSV")
    print("=" * 65)
    
    # 1. Inicializar sistema
    print("\n🤖 INICIALIZANDO SISTEMA...")
    try:
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=False,  # Pode não estar disponível
            enable_data_processor=True
        )
        print("✅ Sistema inicializado e operacional!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return
    
    # 2. Preparar dados de demonstração
    print("\n📊 PREPARANDO DADOS DE DEMONSTRAÇÃO...")
    print("-" * 50)
    
    try:
        # Criar dados sintéticos e salvar em arquivo temporário
        from src.data.data_loader import DataLoader
        import tempfile
        
        loader = DataLoader()
        df, metadata = loader.create_synthetic_data("fraud_detection", 1000)
        
        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            demo_file = f.name
        
        df.to_csv(demo_file, index=False)
        print(f"✅ Arquivo criado: {demo_file}")
        
        # Verificar se arquivo existe
        if os.path.exists(demo_file):
            print(f"📁 Tamanho: {os.path.getsize(demo_file)} bytes")
            print(f"📊 Dados: {metadata.get('rows', 0)} linhas x {metadata.get('columns', 0)} colunas")
        
    except Exception as e:
        print(f"❌ Erro ao criar dados: {str(e)}")
        return
    
    # 3. Carregamento de dados via orquestrador
    print("\n📂 CARREGAMENTO DE DADOS VIA ORQUESTRADOR")
    print("-" * 50)
    
    load_context = {"file_path": demo_file}
    load_query = "carregar e validar os dados do arquivo"
    
    print(f"📝 Consulta: {load_query}")
    print(f"📂 Arquivo: {demo_file}")
    print("─" * 30)
    
    try:
        result = orchestrator.process(load_query, load_context)
        print(result['content'])
        
        # Verificar se dados foram carregados
        metadata = result.get('metadata', {})
        if metadata.get('data_loaded'):
            print("\n✅ Dados carregados com sucesso no orquestrador!")
            data_info = metadata.get('data_info', {})
            print(f"📊 Dimensões: {data_info.get('rows', 0)} x {data_info.get('columns', 0)}")
        
    except Exception as e:
        print(f"❌ Erro no carregamento: {str(e)}")
        return
    
    print("\n" + "=" * 65)
    
    # 4. Análises via orquestrador
    print("\n📈 ANÁLISES COORDENADAS PELO ORQUESTRADOR")
    print("-" * 50)
    
    analysis_queries = [
        "faça um resumo completo dos dados carregados",
        "mostre as correlações mais importantes", 
        "analise padrões suspeitos de fraude",
        "quais são as estatísticas básicas das transações?"
    ]
    
    for i, query in enumerate(analysis_queries, 1):
        print(f"\n📝 Análise {i}: {query}")
        print("─" * 30)
        
        try:
            result = orchestrator.process(query)
            
            # Mostrar resposta (limitada para demonstração)
            content = result['content']
            if len(content) > 400:
                content = content[:400] + "\n[...resposta truncada para demonstração...]"
            
            print(content)
            
            # Informações de coordenação
            metadata = result.get('metadata', {})
            agents_used = metadata.get('agents_used', [])
            if agents_used:
                print(f"\n🤖 Agentes coordenados: {', '.join(agents_used)}")
            
        except Exception as e:
            print(f"❌ Erro na análise: {str(e)}")
    
    print("\n" + "=" * 65)
    
    # 5. Consultas mistas (diferentes tipos)
    print("\n🔀 CONSULTAS MISTAS E INTELIGÊNCIA DE ROTEAMENTO")
    print("-" * 50)
    
    mixed_queries = [
        ("Tipo geral", "olá, como você funciona?"),
        ("Carregamento", "preciso importar novos dados"),
        ("Análise CSV", "calcule a média das transações"),
        ("Desconhecido", "xyz123 pergunta estranha"),
        ("Status", "qual é o status atual do sistema?")
    ]
    
    for query_type, query in mixed_queries:
        print(f"\n📝 [{query_type}] {query}")
        print("─" * 30)
        
        try:
            result = orchestrator.process(query)
            
            # Mostrar resposta resumida
            content = result['content']
            if len(content) > 200:
                content = content[:200] + "..."
            print(content)
            
            # Mostrar classificação
            metadata = result.get('metadata', {})
            agents_used = metadata.get('agents_used', [])
            print(f"🏷️ Agentes: {agents_used if agents_used else ['nenhum']}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
    
    print("\n" + "=" * 65)
    
    # 6. Estatísticas finais do orquestrador
    print("\n📊 ESTATÍSTICAS E RELATÓRIO FINAL")
    print("-" * 50)
    
    try:
        # Histórico da sessão
        history = orchestrator.get_conversation_history()
        print(f"💬 Total de interações processadas: {len(history)}")
        
        # Contar tipos de interação
        user_queries = [h for h in history if h.get('type') == 'user_query']
        system_responses = [h for h in history if h.get('type') == 'system_response']
        
        print(f"❓ Consultas do usuário: {len(user_queries)}")
        print(f"🤖 Respostas do sistema: {len(system_responses)}")
        
        # Status final
        print(f"\n📋 STATUS FINAL:")
        status = orchestrator.process("status completo")
        
        # Extrair informações essenciais do status
        status_content = status['content']
        if "Agentes Disponíveis" in status_content:
            agents_line = [line for line in status_content.split('\n') if 'Agentes Disponíveis' in line]
            if agents_line:
                print(f"🤖 {agents_line[0]}")
        
        if orchestrator.current_data_context:
            file_path = orchestrator.current_data_context.get('file_path', 'N/A')
            print(f"📁 Dados carregados: {os.path.basename(file_path)}")
        
        print(f"\n🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"✨ Orquestrador coordenou análises complexas de forma inteligente")
        print(f"🎯 Roteamento automático baseado no tipo de consulta")
        print(f"💾 Contexto de dados mantido durante toda a sessão")
        
    except Exception as e:
        print(f"⚠️ Erro nas estatísticas: {str(e)}")
    
    print("\n" + "=" * 65)


def quick_demo():
    """Demo rápido com poucas interações."""
    print("⚡ DEMO RÁPIDO DO ORQUESTRADOR")
    print("=" * 35)
    
    try:
        orchestrator = OrchestratorAgent(enable_rag_agent=False)
        
        queries = [
            "olá",
            "status do sistema", 
            "ajuda com análise de dados"
        ]
        
        for query in queries:
            print(f"\n❓ {query}")
            result = orchestrator.process(query)
            content = result['content']
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"✅ {content}")
        
        print("\n✅ Demo rápido concluído!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_demo()
    else:
        demo_orchestrator_with_data()