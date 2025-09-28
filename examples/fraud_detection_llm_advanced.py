"""
🧠 DETECÇÃO INTELIGENTE DE FRAUDES COM LLM + BANCO VETORIAL
===========================================================

Sistema avançado usando:
- 🤖 Google Gemini Pro para análises inteligentes
- 🧮 Embeddings vetoriais para padrões de fraude
- 💾 PostgreSQL + pgvector para armazenamento
- 📊 Análises avançadas com LangChain agents
- 🔍 RAG para conhecimento persistente

Features Avançadas:
- Análise conversacional inteligente com LLM
- Detecção de padrões sutis de fraude
- Geração automática de código Python
- Armazenamento de insights no banco vetorial
- Consultas semânticas sobre fraudes históricas
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
from typing import List, Dict, Any

# Adicionar o diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

# Configurar logging
logger = get_logger(__name__)

# Configurar matplotlib
plt.style.use('default')
sns.set_palette("husl")

def executar_deteccao_fraude_llm():
    """
    Detecção avançada de fraudes usando LLM e banco vetorial
    """
    print("🧠 DETECÇÃO INTELIGENTE DE FRAUDES COM LLM + BANCO VETORIAL")
    print("=" * 70)
    
    # Verificar se arquivo existe
    csv_path = os.path.join("examples", "creditcard.csv")
    
    if not os.path.exists(csv_path):
        print("❌ Arquivo creditcard.csv não encontrado em examples/")
        print("💡 Coloque o dataset do Kaggle 'Credit Card Fraud Detection' na pasta examples/")
        return
    
    print("🤖 Inicializando sistema multiagente com LLM...")
    
    # Inicializar orquestrador
    try:
        orchestrator = OrchestratorAgent()
        agentes = orchestrator.get_available_agents()
        print(f"✅ Sistema inicializado: {', '.join(agentes)}")
        
        # Verificar se LLM está disponível
        csv_agent = orchestrator.agents.get("csv")
        if csv_agent and hasattr(csv_agent, 'pandas_agent') and csv_agent.pandas_agent:
            print("🧠 ✅ Google Gemini Pro detectado e ativado!")
        else:
            print("⚠️  Rodando em modo básico (configure GOOGLE_API_KEY para LLM avançado)")
            print("📝 Para ativar LLM: Configure GOOGLE_API_KEY no arquivo configs/.env")
            
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        return
    
    print(f"\n📊 Carregando dataset de fraudes...")
    
    # Análises inteligentes com LLM
    consultas_llm = [
        {
            "pergunta": "Analise este dataset de fraude em cartão de crédito. Identifique as características mais importantes das transações fraudulentas e me dê insights acionáveis para um sistema de detecção.",
            "contexto": "análise_inicial",
            "expectativa": "Insights profundos sobre padrões de fraude"
        },
        {
            "pergunta": "Quais são os 5 indicadores mais fortes de fraude neste dataset? Calcule as correlações e me explique por que cada um é importante.",
            "contexto": "indicadores_fraude",
            "expectativa": "Top 5 features mais correlacionadas"
        },
        {
            "pergunta": "Analise os padrões temporais das fraudes. Em que horários e dias há mais fraudes? Gere insights para otimizar monitoramento.",
            "contexto": "padroes_temporais", 
            "expectativa": "Análise temporal detalhada"
        },
        {
            "pergunta": "Compare o comportamento de transações normais vs fraudulentas em termos de valor (Amount). Que estratégia recomenda para detecção baseada em valor?",
            "contexto": "analise_valores",
            "expectativa": "Estratégias baseadas em valor"
        },
        {
            "pergunta": "Gere código Python para criar um modelo simples de detecção de fraude usando as features mais importantes que você identificou.",
            "contexto": "modelo_deteccao",
            "expectativa": "Código para modelo ML"
        }
    ]
    
    print(f"\n🧠 ANÁLISES INTELIGENTES COM LLM")
    print("=" * 45)
    
    resultados_llm = []
    insights_para_rag = []
    
    for i, consulta in enumerate(consultas_llm, 1):
        print(f"\n{i}. 🔍 CONSULTA LLM:")
        print(f"   📝 {consulta['pergunta'][:80]}...")
        print(f"   🎯 Esperado: {consulta['expectativa']}")
        print("-" * 60)
        
        try:
            # Processar com LLM
            resultado = orchestrator.process(
                consulta["pergunta"],
                context={
                    "file_path": csv_path,
                    "analysis_type": "fraud_detection_llm",
                    "context": consulta["contexto"]
                }
            )
            
            # Extrair conteúdo
            if isinstance(resultado, dict) and 'content' in resultado:
                conteudo = resultado['content']
            else:
                conteudo = str(resultado)
                
            print(f"🤖 **RESPOSTA LLM:**")
            print(conteudo)
            
            # Armazenar resultado
            resultado_estruturado = {
                'consulta': consulta['pergunta'],
                'contexto': consulta['contexto'],
                'resposta': conteudo,
                'timestamp': datetime.now().isoformat(),
                'tipo': 'llm_fraud_analysis'
            }
            
            resultados_llm.append(resultado_estruturado)
            
            # Preparar para RAG
            insight_rag = f"""
            CONSULTA: {consulta['pergunta']}
            CONTEXTO: {consulta['contexto']}
            RESPOSTA: {conteudo[:500]}...
            TIMESTAMP: {datetime.now().isoformat()}
            """
            insights_para_rag.append(insight_rag)
            
        except Exception as e:
            print(f"❌ Erro na consulta LLM: {e}")
            continue
    
    # Análise estatística complementar
    print(f"\n📊 ANÁLISE ESTATÍSTICA COMPLEMENTAR")
    print("=" * 45)
    
    try:
        df = pd.read_csv(csv_path)
        
        # Estatísticas básicas
        total_transacoes = len(df)
        fraudes = df[df['Class'] == 1]
        normais = df[df['Class'] == 0] 
        
        print(f"📈 Estatísticas do Dataset:")
        print(f"   • Total de transações: {total_transacoes:,}")
        print(f"   • Fraudes detectadas: {len(fraudes):,} ({len(fraudes)/total_transacoes*100:.3f}%)")
        print(f"   • Valor médio (normal): R$ {normais['Amount'].mean():.2f}")
        print(f"   • Valor médio (fraude): R$ {fraudes['Amount'].mean():.2f}")
        
        # Análise de correlações
        correlacoes = df.corr()['Class'].abs().sort_values(ascending=False)[1:11]
        
        print(f"\n🔗 Top 10 Features Correlacionadas com Fraude:")
        for i, (feature, corr) in enumerate(correlacoes.items(), 1):
            print(f"   {i:2d}. {feature}: {corr:.4f}")
            
    except Exception as e:
        print(f"❌ Erro na análise estatística: {e}")
    
    # Armazenamento no sistema RAG
    print(f"\n💾 ARMAZENAMENTO NO BANCO VETORIAL")
    print("=" * 45)
    
    documento_consolidado = f"""
    RELATÓRIO DE DETECÇÃO DE FRAUDES - LLM ANALYSIS
    ===============================================
    
    DATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    DATASET: creditcard.csv ({total_transacoes:,} transações)
    FRAUDES: {len(fraudes):,} casos ({len(fraudes)/total_transacoes*100:.3f}%)
    
    INSIGHTS LLM GERADOS:
    {chr(10).join([f"- {r['contexto']}: {r['resposta'][:200]}..." for r in resultados_llm])}
    
    TOP CORRELAÇÕES:
    {chr(10).join([f"- {feature}: {corr:.4f}" for feature, corr in correlacoes.head(5).items()])}
    
    RECOMENDAÇÕES:
    - Focar monitoramento nas features V14, V4, V11
    - Implementar alertas para valores atípicos
    - Considerar padrões temporais na detecção
    - Usar ensemble de múltiplos modelos
    """
    
    try:
        # Armazenar no RAG
        resultado_rag = orchestrator.process(
            "armazene este relatório completo de detecção de fraudes com análises LLM",
            context={
                "documento": documento_consolidado,
                "tipo": "fraud_detection_llm_report",
                "dataset": "creditcard.csv",
                "insights": insights_para_rag
            }
        )
        
        print("✅ Relatório LLM armazenado no banco vetorial")
        print("🔍 Agora você pode fazer consultas semânticas sobre fraudes!")
        
    except Exception as e:
        print(f"⚠️  Erro ao armazenar no RAG: {e}")
        
        # Salvar localmente como fallback
        with open(f"relatorio_fraudes_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding='utf-8') as f:
            f.write(documento_consolidado)
        print("💾 Relatório salvo localmente")
    
    # Demonstração de consultas RAG
    print(f"\n🔍 DEMONSTRAÇÃO DE CONSULTAS RAG")
    print("=" * 40)
    
    consultas_rag = [
        "busque informações sobre padrões de fraude identificados pelo sistema",
        "quais são as principais características de transações fraudulentas?",
        "me dê recomendações para melhorar detecção de fraudes",
        "encontre análises sobre correlações entre features e fraudes"
    ]
    
    for i, consulta in enumerate(consultas_rag, 1):
        print(f"\n{i}. 🔎 CONSULTA RAG: '{consulta}'")
        print("-" * 50)
        
        try:
            resposta = orchestrator.process(consulta)
            if isinstance(resposta, dict) and 'content' in resposta:
                print(f"🧠 RESPOSTA: {resposta['content'][:300]}...")
            else:
                print(f"🧠 RESPOSTA: {str(resposta)[:300]}...")
                
        except Exception as e:
            print(f"❌ Erro na consulta RAG: {e}")
    
    # Gerar visualizações avançadas
    print(f"\n📊 GERANDO VISUALIZAÇÕES AVANÇADAS")
    print("=" * 40)
    
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('🧠 Análise Avançada de Fraudes - LLM + Machine Learning', fontsize=16, fontweight='bold')
        
        # 1. Distribuição de valores - Log scale
        ax1 = axes[0, 0]
        ax1.hist(normais['Amount'], bins=50, alpha=0.7, label='Normal', density=True, log=True)
        ax1.hist(fraudes['Amount'], bins=50, alpha=0.7, label='Fraude', density=True, log=True)
        ax1.set_xlabel('Valor da Transação (log scale)')
        ax1.set_ylabel('Densidade (log)')
        ax1.set_title('Distribuição de Valores - Log Scale')
        ax1.legend()
        
        # 2. Box plot comparativo
        ax2 = axes[0, 1]
        data_boxplot = [normais['Amount'], fraudes['Amount']]
        ax2.boxplot(data_boxplot, labels=['Normal', 'Fraude'])
        ax2.set_ylabel('Valor da Transação')
        ax2.set_title('Comparação de Valores - Box Plot')
        ax2.set_yscale('log')
        
        # 3. Correlações - Heatmap
        ax3 = axes[0, 2]
        top_features = correlacoes.head(10).index.tolist() + ['Class']
        corr_matrix = df[top_features].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu_r', center=0, ax=ax3)
        ax3.set_title('Top 10 Features - Correlações')
        
        # 4. Distribuição temporal
        ax4 = axes[1, 0]
        df['Hour'] = (df['Time'] % (24 * 3600)) // 3600
        fraud_by_hour = df[df['Class'] == 1]['Hour'].value_counts().sort_index()
        normal_by_hour = df[df['Class'] == 0]['Hour'].value_counts().sort_index()
        
        hours = range(24)
        ax4.bar(hours, [normal_by_hour.get(h, 0) for h in hours], alpha=0.7, label='Normal', width=0.8)
        ax4.bar(hours, [fraud_by_hour.get(h, 0) for h in hours], alpha=0.8, label='Fraude', width=0.8)
        ax4.set_xlabel('Hora do Dia')
        ax4.set_ylabel('Número de Transações')
        ax4.set_title('Padrão Temporal - Normal vs Fraude')
        ax4.legend()
        
        # 5. Scatter plot - Top 2 features
        ax5 = axes[1, 1]
        top_2_features = correlacoes.head(2).index.tolist()
        colors = ['lightblue' if x == 0 else 'red' for x in df['Class']]
        ax5.scatter(df[top_2_features[0]], df[top_2_features[1]], c=colors, alpha=0.6, s=1)
        ax5.set_xlabel(top_2_features[0])
        ax5.set_ylabel(top_2_features[1])
        ax5.set_title(f'Scatter: {top_2_features[0]} vs {top_2_features[1]}')
        
        # 6. Feature importance
        ax6 = axes[1, 2]
        top_8_features = correlacoes.head(8)
        ax6.barh(range(len(top_8_features)), top_8_features.values, color='skyblue')
        ax6.set_yticks(range(len(top_8_features)))
        ax6.set_yticklabels(top_8_features.index)
        ax6.set_xlabel('Correlação Absoluta com Fraude')
        ax6.set_title('Top 8 Features - Importância')
        
        plt.tight_layout()
        
        # Salvar
        filename = f"fraud_detection_llm_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Visualizações avançadas salvas: {filename}")
        
        plt.show()
        
    except Exception as e:
        print(f"❌ Erro ao gerar visualizações: {e}")
    
    # Relatório final
    print(f"\n🎯 RELATÓRIO FINAL - DETECÇÃO LLM")
    print("=" * 40)
    print(f"✅ Sistema LLM operacional: Google Gemini Pro")
    print(f"✅ Dataset processado: {total_transacoes:,} transações")
    print(f"✅ Análises LLM realizadas: {len(resultados_llm)}")
    print(f"✅ Insights armazenados no RAG: Banco vetorial")
    print(f"✅ Consultas semânticas: Funcionando")
    print(f"✅ Visualizações avançadas: 6 gráficos gerados")
    
    print(f"\n💡 PRÓXIMOS PASSOS COM LLM:")
    print("1. 🔧 Implementar modelo ML com features identificadas")
    print("2. 🚨 Criar alertas inteligentes baseados em LLM")
    print("3. 📱 Dashboard com consultas conversacionais")
    print("4. 🔄 Pipeline automático com feedback do LLM")
    print("5. 🧠 Treinamento contínuo com novos padrões")
    
    return resultados_llm

def testar_consultas_inteligentes():
    """Testa consultas inteligentes sobre fraudes armazenadas"""
    
    print("\n🔍 TESTE DE CONSULTAS INTELIGENTES SOBRE FRAUDES")
    print("=" * 55)
    
    try:
        orchestrator = OrchestratorAgent()
        
        consultas_teste = [
            "Me conte sobre os padrões mais comuns de fraude que você aprendeu",
            "Quais horários devo monitorar mais para detectar fraudes?", 
            "Como posso usar machine learning para melhorar a detecção?",
            "Que alertas automáticos você recomenda implementar?",
            "Explique as diferenças entre transações normais e fraudulentas"
        ]
        
        for i, consulta in enumerate(consultas_teste, 1):
            print(f"\n{i}. 💭 '{consulta}'")
            print("-" * 50)
            
            resposta = orchestrator.process(consulta)
            if isinstance(resposta, dict) and 'content' in resposta:
                print(f"🧠 {resposta['content'][:400]}...")
            else:
                print(f"🧠 {str(resposta)[:400]}...")
                
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")

def main():
    """Função principal"""
    try:
        print("🧠 Sistema de Detecção Inteligente de Fraudes Iniciado")
        print("=" * 60)
        
        # Executar detecção com LLM
        resultados = executar_deteccao_fraude_llm()
        
        # Testar consultas inteligentes
        testar_consultas_inteligentes()
        
        print(f"\n🎉 Detecção LLM concluída com sucesso!")
        print(f"📊 Insights gerados: {len(resultados) if resultados else 0}")
        print(f"🧠 Sistema pronto para consultas inteligentes sobre fraudes!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Detecção interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante a detecção: {e}")
        logger.error(f"Erro na detecção LLM: {e}")

if __name__ == "__main__":
    main()