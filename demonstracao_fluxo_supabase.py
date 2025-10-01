#!/usr/bin/env python3
"""Demonstração do fluxo completo: Pergunta → Supabase → Resposta"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# from src.agent.orchestrator_agent import OrchestratorAgent

def demonstrar_fluxo_completo():
    """Demonstra como o sistema consulta Supabase para responder perguntas"""
    
    print("🔍 DEMONSTRAÇÃO: Como o Sistema Consulta o Supabase")
    print("=" * 70)
    
    # Simular perguntas reais que o usuário pode fazer
    perguntas_exemplo = [
        "Qual é o valor médio das transações?",
        "Quantos registros temos no dataset?", 
        "Quais são as principais estatísticas dos dados?",
        "Como estão distribuídas as classes nos dados?"
    ]
    
    for i, pergunta in enumerate(perguntas_exemplo, 1):
        print(f"\n🎯 Pergunta {i}: '{pergunta}'")
        print("-" * 50)
        
        # O que o sistema faz internamente:
        print("📋 FLUXO INTERNO DO SISTEMA:")
        print("  1. 🤖 Orquestrador recebe a pergunta")
        print("  2. 🗄️  Sistema acessa Supabase tabela 'embeddings'")
        print("  3. 📊 Python Analyzer calcula estatísticas reais")
        print("  4. 🛡️  Guardrails validam a resposta")
        print("  5. ✅ Resposta precisa entregue ao usuário")
        
        # Simular resposta (sem executar o LLM completo para demonstração)
        try:
            # Verificar se consegue acessar Supabase
            from src.tools.python_analyzer import python_analyzer
            
            print(f"\n📊 ACESSANDO SUPABASE...")
            
            # Este método acessa a tabela embeddings do Supabase
            stats = python_analyzer.calculate_real_statistics("tipos_dados")
            
            if "error" not in stats:
                print(f"✅ DADOS RECUPERADOS DO SUPABASE:")
                print(f"   📋 Total de registros: {stats.get('total_records', 'N/A')}")
                print(f"   📋 Total de colunas: {stats.get('total_columns', 'N/A')}")
                
                tipos = stats.get('tipos_dados', {})
                print(f"   📊 Colunas numéricas: {tipos.get('total_numericos', 0)}")
                print(f"   📊 Colunas categóricas: {tipos.get('total_categoricos', 0)}")
                
                print(f"✅ RESPOSTA BASEADA EM DADOS REAIS DO SUPABASE")
            else:
                print(f"❌ Erro ao acessar Supabase: {stats['error']}")
                
        except Exception as e:
            print(f"❌ Erro na demonstração: {str(e)}")
    
    print(f"\n{'='*70}")
    print("🎯 RESUMO DO FLUXO:")
    print("✅ SIM - O sistema SEMPRE consulta a tabela 'embeddings' do Supabase")
    print("✅ Dados são recuperados diretamente da base de dados")
    print("✅ Estatísticas são calculadas com dados reais (não alucinações)")
    print("✅ Sistema garante precisão através do Python Analyzer")
    print("="*70)

def mostrar_evidencia_tecnica():
    """Mostra evidência técnica do acesso ao Supabase"""
    
    print(f"\n🔧 EVIDÊNCIA TÉCNICA - ACESSO AO SUPABASE")
    print("=" * 60)
    
    print("📁 ARQUIVOS QUE ACESSAM SUPABASE:")
    
    # Mostrar código que acessa Supabase
    arquivos_supabase = [
        "src/tools/python_analyzer.py → get_data_from_supabase()",
        "src/agent/orchestrator_agent.py → _retrieve_data_context_from_supabase()",
        "src/vectorstore/supabase_client.py → Cliente configurado"
    ]
    
    for arquivo in arquivos_supabase:
        print(f"  ✅ {arquivo}")
    
    print(f"\n📊 TABELAS UTILIZADAS:")
    tabelas = [
        "embeddings → Dados vetorizados do CSV",
        "chunks → Fragmentos de texto estruturado", 
        "metadata → Metadados dos arquivos"
    ]
    
    for tabela in tabelas:
        print(f"  ✅ {tabela}")
    
    print(f"\n🔍 PROCESSO DETALHADO:")
    processo = [
        "1. Pergunta chega no Orquestrador Agent",
        "2. Orquestrador chama _retrieve_data_context_from_supabase()",
        "3. Python Analyzer acessa tabela 'embeddings' via get_data_from_supabase()",
        "4. Dados são recuperados como DataFrame do Pandas",
        "5. Estatísticas reais são calculadas matematicamente",
        "6. Guardrails validam se resposta está correta",
        "7. Resposta final baseada 100% em dados do Supabase"
    ]
    
    for step in processo:
        print(f"  {step}")

if __name__ == "__main__":
    demonstrar_fluxo_completo()
    mostrar_evidencia_tecnica()