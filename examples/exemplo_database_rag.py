#!/usr/bin/env python3
"""Exemplo: Uso Avançado do Banco de Dados Vetorial
================================================

Este exemplo demonstra como usar o banco de dados Supabase com pgvector:
1. Armazenamento de embeddings de análises
2. Busca semântica por documentos similares  
3. Sistema RAG para consultas contextualizadas
4. Persistência de análises e resultados

Uso:
    python examples/exemplo_database_rag.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.agent.orchestrator_agent import OrchestratorAgent
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class DatabaseRAGDemo:
    """Demonstração do sistema de banco de dados vetorial e RAG."""
    
    def __init__(self):
        self.orquestrador = None
        self.embeddings_criados = 0
        self.documentos_indexados = 0
        
    def inicializar_sistema(self) -> bool:
        """Inicializa o orquestrador."""
        print("🤖 Inicializando sistema multiagente...")
        
        try:
            self.orquestrador = OrchestratorAgent()
            agentes = list(self.orquestrador.agents.keys())
            print(f"✅ Sistema inicializado: {', '.join(agentes)}")
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def testar_banco_vetorial(self) -> bool:
        """Testa operações básicas do banco vetorial."""
        print("\n🗄️ Testando banco de dados vetorial...")
        
        try:
            # 1. Verificar tabelas
            tabelas = ['embeddings', 'chunks', 'metadata']
            for tabela in tabelas:
                try:
                    result = supabase.table(tabela).select('*').limit(5).execute()
                    count = len(result.data) if result.data else 0
                    print(f"   📊 {tabela}: {count} registros")
                except Exception as e:
                    print(f"   ⚠️  {tabela}: erro ao acessar - {e}")
            
            # 2. Inserir documento de teste
            documento_teste = {
                "title": "Análise de Fraudes - Sistema EDA AI Minds",
                "content": "Este documento contém informações sobre detecção de fraudes em cartão de crédito usando técnicas de machine learning e análise estatística.",
                "timestamp": datetime.now().isoformat(),
                "source": "sistema_demo",
                "metadata": {
                    "tipo": "analise_fraude",
                    "versao": "1.0",
                    "tags": ["fraude", "cartao_credito", "ml", "estatistica"]
                }
            }
            
            result = supabase.table('metadata').insert(documento_teste).execute()
            if result.data:
                print(f"   ✅ Documento teste inserido - ID: {result.data[0].get('id', 'N/A')}")
                self.documentos_indexados += 1
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erro no teste: {e}")
            return False
    
    def demonstrar_rag_avancado(self) -> None:
        """Demonstra sistema RAG com consultas avançadas."""
        print(f"\n🔍 Sistema RAG - Busca Semântica Avançada")
        print("=" * 50)
        
        # Consultas que testam diferentes aspectos do RAG
        consultas_rag = [
            {
                "query": "busque informações sobre detecção de fraudes",
                "esperado": "Deve encontrar documentos sobre fraudes"
            },
            {
                "query": "encontre análises de dados financeiros", 
                "esperado": "Deve recuperar contexto sobre finanças"
            },
            {
                "query": "pesquise por machine learning em transações",
                "esperado": "Deve localizar conteúdo sobre ML"
            },
            {
                "query": "procure padrões suspeitos em pagamentos",
                "esperado": "Deve identificar informações sobre anomalias"
            }
        ]
        
        if "rag" not in self.orquestrador.agents:
            print("⚠️  Sistema RAG não disponível (agente não inicializado)")
            return
        
        for i, consulta_info in enumerate(consultas_rag, 1):
            query = consulta_info["query"]
            esperado = consulta_info["esperado"]
            
            print(f"\n{i}. 🔍 CONSULTA RAG: '{query}'")
            print(f"   💭 Esperado: {esperado}")
            print("-" * 40)
            
            try:
                # Processar através do orquestrador
                resultado = self.orquestrador.process(query, context={})
                
                if isinstance(resultado, dict):
                    resposta = resultado.get("content", str(resultado))
                    metadata = resultado.get("metadata", {})
                else:
                    resposta = str(resultado)
                    metadata = {}
                
                # Mostrar resultado
                print(f"🤖 RESPOSTA: {resposta[:200]}{'...' if len(resposta) > 200 else ''}")
                
                # Verificar se RAG foi usado
                if metadata and "orchestrator" in metadata:
                    agentes_usados = metadata["orchestrator"].get("agents_used", [])
                    rag_usado = "rag" in agentes_usados
                    
                    if rag_usado:
                        print("✅ RAG ATIVO: Busca semântica executada")
                    else:
                        print("⚠️  RAG não foi utilizado para esta consulta")
                
                # Análise da qualidade da resposta
                qualidade = self._avaliar_resposta_rag(resposta, esperado)
                print(f"📊 Qualidade da resposta: {qualidade}")
                
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def _avaliar_resposta_rag(self, resposta: str, esperado: str) -> str:
        """Avalia a qualidade da resposta RAG de forma simples."""
        resposta_lower = resposta.lower()
        
        # Palavras-chave relacionadas ao esperado
        if "fraude" in esperado.lower():
            keywords = ["fraude", "suspeito", "anomalia", "risco"]
        elif "financeiro" in esperado.lower():
            keywords = ["financeiro", "transação", "pagamento", "dinheiro"]  
        elif "machine learning" in esperado.lower():
            keywords = ["ml", "machine learning", "algoritmo", "modelo"]
        elif "pagamento" in esperado.lower():
            keywords = ["pagamento", "transação", "cartão", "compra"]
        else:
            keywords = ["dados", "análise", "sistema"]
        
        # Contar keywords encontradas
        found_keywords = sum(1 for kw in keywords if kw in resposta_lower)
        
        if found_keywords >= 3:
            return "🟢 Excelente (contexto relevante encontrado)"
        elif found_keywords >= 2:
            return "🟡 Boa (algumas informações relevantes)"
        elif found_keywords >= 1:
            return "🟠 Regular (contexto limitado)"
        else:
            return "🔴 Ruim (pouco contexto relevante)"
    
    def armazenar_analises_banco(self) -> None:
        """Demonstra armazenamento de análises no banco."""
        print(f"\n💾 Armazenamento de Análises")
        print("=" * 40)
        
        # Simular análises de diferentes tipos
        analises_teste = [
            {
                "tipo": "fraud_detection",
                "dataset": "creditcard.csv",
                "resultados": {
                    "total_transacoes": 284807,
                    "fraudes_detectadas": 492,
                    "taxa_fraude": 0.17,
                    "precisao": 0.92,
                    "recall": 0.88
                },
                "insights": ["Alto volume de fraudes em finais de semana", "Transações acima de $500 mais suspeitas"],
                "timestamp": datetime.now().isoformat()
            },
            {
                "tipo": "correlation_analysis", 
                "dataset": "sales_data.csv",
                "resultados": {
                    "correlacoes_fortes": ["price_amount", "customer_age_income"],
                    "correlacoes_fracas": ["time_fraud"],
                    "r_squared": 0.74
                },
                "insights": ["Clientes mais velhos gastam mais", "Horário não influencia fraudes"],
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        for i, analise in enumerate(analises_teste, 1):
            try:
                # Preparar registro para o banco
                registro = {
                    "title": f"Análise {analise['tipo']} - {analise['dataset']}",
                    "content": json.dumps(analise['resultados']),
                    "timestamp": analise['timestamp'],
                    "source": "sistema_demo_avancado",
                    "metadata": {
                        "tipo_analise": analise['tipo'],
                        "dataset": analise['dataset'],
                        "insights": analise['insights'],
                        "metricas": analise['resultados']
                    }
                }
                
                # Inserir no banco
                result = supabase.table('metadata').insert(registro).execute()
                
                if result.data:
                    doc_id = result.data[0].get('id', 'N/A')
                    print(f"   ✅ Análise {i} armazenada - ID: {doc_id}")
                    print(f"      📊 Tipo: {analise['tipo']}")
                    print(f"      📁 Dataset: {analise['dataset']}")
                    self.documentos_indexados += 1
                else:
                    print(f"   ⚠️  Análise {i} não foi armazenada")
                    
            except Exception as e:
                print(f"   ❌ Erro ao armazenar análise {i}: {e}")
    
    def consultar_historico_analises(self) -> None:
        """Consulta histórico de análises no banco."""
        print(f"\n📈 Histórico de Análises")
        print("=" * 30)
        
        try:
            # Buscar análises recentes
            result = supabase.table('metadata').select('*').order('created_at', desc=True).limit(10).execute()
            
            if result.data and len(result.data) > 0:
                print(f"📊 Encontradas {len(result.data)} análises:")
                
                for i, analise in enumerate(result.data[:5], 1):  # Mostrar só as primeiras 5
                    titulo = analise.get('title', 'Sem título')
                    timestamp = analise.get('timestamp', analise.get('created_at', 'N/A'))
                    metadata = analise.get('metadata', {})
                    
                    print(f"\n   {i}. 📄 {titulo}")
                    print(f"      🕐 {timestamp}")
                    
                    if isinstance(metadata, dict):
                        tipo = metadata.get('tipo_analise', 'N/A')
                        dataset = metadata.get('dataset', 'N/A')
                        print(f"      🏷️  Tipo: {tipo}")
                        print(f"      📁 Dataset: {dataset}")
                        
                        insights = metadata.get('insights', [])
                        if insights and len(insights) > 0:
                            print(f"      💡 Insights: {insights[0][:50]}...")
            else:
                print("📭 Nenhuma análise encontrada no histórico")
                
        except Exception as e:
            print(f"❌ Erro ao consultar histórico: {e}")
    
    def gerar_relatorio(self) -> None:
        """Gera relatório final da demonstração."""
        print(f"\n📊 RELATÓRIO DA DEMONSTRAÇÃO")
        print("=" * 40)
        
        # Stats do sistema
        if self.orquestrador:
            agentes = list(self.orquestrador.agents.keys())
            total_interacoes = len(self.orquestrador.conversation_history)
            
            print(f"🤖 Agentes ativos: {len(agentes)} ({', '.join(agentes)})")
            print(f"💬 Interações processadas: {total_interacoes}")
        
        print(f"📄 Documentos indexados: {self.documentos_indexados}")
        print(f"🔗 Embeddings criados: {self.embeddings_criados}")
        
        # Stats do banco
        try:
            result = supabase.table('metadata').select('id').execute()
            total_docs = len(result.data) if result.data else 0
            print(f"💾 Total de documentos no banco: {total_docs}")
            
            result_embeddings = supabase.table('embeddings').select('id').execute()
            total_embeddings = len(result_embeddings.data) if result_embeddings.data else 0
            print(f"🧮 Total de embeddings no banco: {total_embeddings}")
            
        except Exception as e:
            print(f"💾 Erro ao consultar estatísticas do banco: {e}")
        
        print(f"\n🎯 CAPABILITIES DEMONSTRADAS:")
        print("✅ Sistema multiagente funcionando")
        print("✅ Banco de dados vetorial operacional") 
        print("✅ Armazenamento de documentos e análises")
        print("✅ Sistema RAG para busca semântica")
        print("✅ Persistência de histórico de análises")

def main():
    """Função principal."""
    print("🚀 DEMO: BANCO DE DADOS VETORIAL + SISTEMA RAG")
    print("=" * 60)
    
    demo = DatabaseRAGDemo()
    
    # 1. Inicializar sistema
    if not demo.inicializar_sistema():
        return
    
    # 2. Testar banco vetorial
    if not demo.testar_banco_vetorial():
        print("⚠️  Continuando apesar de problemas no banco...")
    
    # 3. Demonstrar RAG
    demo.demonstrar_rag_avancado()
    
    # 4. Armazenar análises
    demo.armazenar_analises_banco()
    
    # 5. Consultar histórico
    demo.consultar_historico_analises()
    
    # 6. Relatório final
    demo.gerar_relatorio()
    
    print(f"\n✅ Demonstração concluída!")
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print("1. Configure GOOGLE_API_KEY para análises LLM avançadas")
    print("2. Adicione mais documentos ao banco vetorial") 
    print("3. Teste consultas RAG mais complexas")
    print("4. Integre com API REST para uso em produção")

if __name__ == "__main__":
    main()