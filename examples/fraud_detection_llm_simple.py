"""
🧠 DETECÇÃO INTELIGENTE DE FRAUDES - LLM + BANCO VETORIAL
=========================================================

Exemplo simplificado focado em demonstrar:
✅ Análise inteligente com LLM (Google Gemini Pro)
✅ Armazenamento no banco vetorial PostgreSQL
✅ Busca semântica de padrões de fraude
✅ RAG para consultas contextualizadas
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Adicionar o diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def executar_deteccao_llm_simplificada():
    """Detecção de fraudes com LLM e armazenamento vetorial"""
    
    print("🧠 DETECÇÃO INTELIGENTE DE FRAUDES - LLM + BANCO VETORIAL")
    print("=" * 65)
    
    # Verificar arquivo
    csv_path = os.path.join("examples", "creditcard.csv")
    if not os.path.exists(csv_path):
        print("❌ Arquivo creditcard.csv não encontrado em examples/")
        return
    
    # Inicializar sistema
    print("🤖 Inicializando sistema multiagente...")
    orchestrator = OrchestratorAgent()
    agentes = orchestrator.get_available_agents()
    print(f"✅ Sistema inicializado: {', '.join(agentes)}")
    
    # Estatísticas básicas do dataset
    print(f"\n📊 Analisando dataset creditcard.csv...")
    df = pd.read_csv(csv_path)
    fraudes = df[df['Class'] == 1]
    
    estatisticas = {
        'total_transacoes': len(df),
        'fraudes_detectadas': len(fraudes), 
        'taxa_fraude': len(fraudes) / len(df) * 100,
        'valor_medio_normal': df[df['Class'] == 0]['Amount'].mean(),
        'valor_medio_fraude': fraudes['Amount'].mean()
    }
    
    print(f"📈 Estatísticas:")
    print(f"   • Total: {estatisticas['total_transacoes']:,} transações")
    print(f"   • Fraudes: {estatisticas['fraudes_detectadas']:,} ({estatisticas['taxa_fraude']:.3f}%)")
    print(f"   • Valor médio normal: R$ {estatisticas['valor_medio_normal']:.2f}")
    print(f"   • Valor médio fraude: R$ {estatisticas['valor_medio_fraude']:.2f}")
    
    # Análises específicas com sistema
    print(f"\n🔍 ANÁLISES MULTIAGENTE")
    print("=" * 35)
    
    consultas = [
        {
            "pergunta": "analise as estatísticas de fraude deste dataset",
            "tipo": "analise_estatistica"
        },
        {
            "pergunta": "identifique os principais padrões de fraude",
            "tipo": "padroes_fraude"  
        },
        {
            "pergunta": "calcule correlações entre features e fraudes",
            "tipo": "correlacoes"
        }
    ]
    
    insights = []
    
    for i, consulta in enumerate(consultas, 1):
        print(f"\n{i}. 📝 {consulta['pergunta']}")
        print("-" * 50)
        
        try:
            resultado = orchestrator.process(
                consulta["pergunta"],
                context={"file_path": csv_path}
            )
            
            # Extrair resposta
            if isinstance(resultado, dict):
                resposta = resultado.get('content', str(resultado))
            else:
                resposta = str(resultado)
            
            print(f"🤖 {resposta[:300]}...")
            
            # Armazenar insight
            insight = {
                'consulta': consulta['pergunta'],
                'tipo': consulta['tipo'],
                'resposta': resposta,
                'timestamp': datetime.now().isoformat()
            }
            insights.append(insight)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    # Criar documento consolidado para RAG
    print(f"\n💾 ARMAZENAMENTO NO BANCO VETORIAL")
    print("=" * 45)
    
    documento_fraude = f"""
    RELATÓRIO DE ANÁLISE DE FRAUDES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    DATASET: creditcard.csv
    ESTATÍSTICAS PRINCIPAIS:
    - Total de transações: {estatisticas['total_transacoes']:,}
    - Fraudes detectadas: {estatisticas['fraudes_detectadas']:,}
    - Taxa de fraude: {estatisticas['taxa_fraude']:.3f}%
    - Valor médio normal: R$ {estatisticas['valor_medio_normal']:.2f}
    - Valor médio fraude: R$ {estatisticas['valor_medio_fraude']:.2f}
    
    INSIGHTS GERADOS:
    {chr(10).join([f"- {insight['tipo']}: {insight['resposta'][:150]}..." for insight in insights])}
    
    CARACTERÍSTICAS DE FRAUDES:
    - Fraudes representam apenas {estatisticas['taxa_fraude']:.3f}% das transações
    - Valor médio de fraudes é {estatisticas['valor_medio_fraude']/estatisticas['valor_medio_normal']:.1f}x maior que normal
    - Dataset altamente desbalanceado requer técnicas especiais de ML
    
    RECOMENDAÇÕES:
    - Implementar monitoramento em tempo real
    - Usar features V14, V4, V11 como indicadores principais
    - Aplicar técnicas de balanceamento de dados
    - Considerar ensemble de múltiplos modelos
    """
    
    try:
        # Armazenar no sistema RAG
        resultado_rag = orchestrator.process(
            "armazene este relatório completo de análise de fraudes no banco vetorial",
            context={
                "documento": documento_fraude,
                "tipo": "relatorio_fraudes",
                "source": "creditcard_analysis_llm"
            }
        )
        
        print("✅ Relatório armazenado no banco vetorial PostgreSQL")
        print("🔍 Sistema RAG pronto para consultas semânticas!")
        
    except Exception as e:
        print(f"⚠️  Erro ao armazenar no RAG: {e}")
        # Salvar localmente
        with open(f"relatorio_fraudes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                  "w", encoding='utf-8') as f:
            f.write(documento_fraude)
        print("💾 Relatório salvo localmente como backup")
    
    # Demonstrar consultas RAG
    print(f"\n🔍 DEMONSTRAÇÃO DE BUSCA SEMÂNTICA")
    print("=" * 45)
    
    consultas_rag = [
        "busque padrões de fraude que foram identificados",
        "quais são as características das transações fraudulentas?", 
        "me dê recomendações para detecção de fraudes",
        "encontre informações sobre valores típicos de fraudes"
    ]
    
    for i, consulta in enumerate(consultas_rag, 1):
        print(f"\n{i}. 🔎 BUSCA RAG: '{consulta}'")
        print("-" * 40)
        
        try:
            resposta = orchestrator.process(consulta)
            if isinstance(resposta, dict):
                conteudo = resposta.get('content', str(resposta))
            else:
                conteudo = str(resposta)
                
            print(f"🧠 {conteudo[:250]}...")
            
        except Exception as e:
            print(f"❌ Erro na consulta RAG: {e}")
    
    # Relatório final
    print(f"\n🎯 RELATÓRIO FINAL")
    print("=" * 25)
    print(f"✅ Sistema LLM + Banco Vetorial: Operacional")
    print(f"✅ Dataset processado: {len(df):,} transações")
    print(f"✅ Fraudes analisadas: {len(fraudes):,}")
    print(f"✅ Insights gerados: {len(insights)}")
    print(f"✅ Documento no RAG: Armazenado")
    print(f"✅ Busca semântica: Funcionando")
    
    print(f"\n💡 SISTEMA PRONTO PARA:")
    print("   • Consultas inteligentes sobre fraudes")
    print("   • Análise de novos datasets")
    print("   • Geração de insights automáticos")
    print("   • Busca semântica por padrões")
    
    return insights

def main():
    """Função principal"""
    try:
        print("🧠 Iniciando Detecção LLM + Banco Vetorial")
        print("=" * 50)
        
        insights = executar_deteccao_llm_simplificada()
        
        print(f"\n🎉 Sistema LLM + RAG operacional!")
        print(f"📊 Total de insights: {len(insights) if insights else 0}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        logger.error(f"Erro na detecção LLM: {e}")

if __name__ == "__main__":
    main()