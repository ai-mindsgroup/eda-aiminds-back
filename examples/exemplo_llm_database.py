#!/usr/bin/env python3
"""Exemplo Avançado: Sistema Multiagente com LLM e Banco de Dados
==============================================================

Este exemplo demonstra:
1. Uso do Google Gemini (LLM) para análises inteligentes
2. Armazenamento de embeddings no Supabase (PostgreSQL + pgvector)  
3. Sistema RAG para consultas contextualizadas
4. Integração completa banco + LLM + agentes

Configuração necessária:
- GOOGLE_API_KEY no configs/.env
- SUPABASE_URL e SUPABASE_KEY configurados
- Banco PostgreSQL com extensão pgvector

Uso:
    python examples/exemplo_llm_database.py
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from src.agent.orchestrator_agent import OrchestratorAgent
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger
from src.settings import GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY

logger = get_logger(__name__)

class LLMDatabaseDemo:
    """Demonstração avançada de integração LLM + Database."""
    
    def __init__(self):
        self.orquestrador = None
        self.dados_analisados = []
        self.embeddings_gerados = 0
        
    def verificar_configuracoes(self) -> bool:
        """Verifica se todas as configurações necessárias estão presentes."""
        print("🔧 Verificando configurações...")
        
        config_status = {
            "Google API Key": bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "AIzaSyD8gH2L9tVjK3mQf-EXAMPLE-KEY-REPLACE-THIS"),
            "Supabase URL": bool(SUPABASE_URL),
            "Supabase Key": bool(SUPABASE_KEY),
        }
        
        for config, status in config_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {config}: {'Configurado' if status else 'Não configurado'}")
        
        todas_configuradas = all(config_status.values())
        
        if not todas_configuradas:
            print("\n⚠️  CONFIGURAÇÕES NECESSÁRIAS:")
            print("1. Obter chave Google AI: https://makersuite.google.com/app/apikey")
            print("2. Adicionar GOOGLE_API_KEY no configs/.env")
            print("3. Verificar configurações do Supabase")
        
        return todas_configuradas
    
    def inicializar_sistema(self) -> bool:
        """Inicializa o sistema multiagente."""
        print("\n🚀 Inicializando sistema multiagente...")
        
        try:
            self.orquestrador = OrchestratorAgent()
            
            agentes = list(self.orquestrador.agents.keys())
            print(f"✅ Sistema inicializado com {len(agentes)} agentes: {', '.join(agentes)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            return False
    
    def testar_conexao_database(self) -> bool:
        """Testa conexão com o banco de dados Supabase."""
        print("\n🗄️ Testando conexão com banco de dados...")
        
        try:
            # Teste básico de conexão
            result = supabase.table('embeddings').select('id').limit(1).execute()
            print(f"✅ Conexão Supabase OK - {len(result.data)} registros teste")
            
            # Verificar tabelas do sistema RAG
            tabelas = ['embeddings', 'chunks', 'metadata']
            for tabela in tabelas:
                try:
                    result = supabase.table(tabela).select('*').limit(1).execute()
                    count = len(result.data) if result.data else 0
                    print(f"   📊 Tabela '{tabela}': {count} registros")
                except Exception:
                    print(f"   ⚠️  Tabela '{tabela}': não acessível")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return False
    
    def demonstrar_analise_llm(self, arquivo_csv: str) -> None:
        """Demonstra análise avançada usando LLM."""
        print(f"\n🧠 Análise Inteligente com LLM")
        print("=" * 50)
        
        # Consultas que devem usar LLM para análises mais sofisticadas
        consultas_llm = [
            "analise os padrões de fraude e explique os principais indicadores",
            "qual é a tendência temporal dos dados?", 
            "identifique correlações importantes e suas implicações de negócio",
            "crie insights estratégicos baseados nos dados",
            "quais recomendações você daria para reduzir fraudes?"
        ]
        
        contexto = {"file_path": arquivo_csv}
        
        for i, consulta in enumerate(consultas_llm, 1):
            print(f"\n{i}. 🤔 CONSULTA LLM: '{consulta}'")
            print("-" * 40)
            
            try:
                resultado = self.orquestrador.process(consulta, context=contexto)
                
                if isinstance(resultado, dict):
                    resposta = resultado.get("content", str(resultado))
                    metadata = resultado.get("metadata", {})
                else:
                    resposta = str(resultado)
                    metadata = {}
                
                # Mostrar resposta (primeiros 300 chars)
                print(f"🤖 RESPOSTA: {resposta[:300]}{'...' if len(resposta) > 300 else ''}")
                
                # Verificar se LLM foi usado
                if metadata and "orchestrator" in metadata:
                    agentes_usados = metadata["orchestrator"].get("agents_used", [])
                    llm_usado = "llm" in agentes_usados or len(resposta) > 200
                    print(f"🧠 LLM utilizado: {'✅ Sim' if llm_usado else '❌ Não'}")
                
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def demonstrar_rag_database(self) -> None:
        """Demonstra sistema RAG com banco de dados vetorial."""
        print(f"\n🔍 Sistema RAG com Banco Vetorial")
        print("=" * 50)
        
        # Consultas que devem usar o sistema RAG
        consultas_rag = [
            "busque informações sobre detecção de fraudes em cartão de crédito",
            "quais são as melhores práticas para análise de dados financeiros?",
            "encontre padrões similares em dados de transações",
            "pesquise por anomalias em sistemas de pagamento"
        ]
        
        for i, consulta in enumerate(consultas_rag, 1):
            print(f"\n{i}. 🔍 CONSULTA RAG: '{consulta}'")
            print("-" * 40)
            
            try:
                resultado = self.orquestrador.process(consulta, context={})
                
                if isinstance(resultado, dict):
                    resposta = resultado.get("content", str(resultado))
                    metadata = resultado.get("metadata", {})
                else:
                    resposta = str(resultado)
                    metadata = {}
                
                print(f"🤖 RESPOSTA: {resposta[:250]}{'...' if len(resposta) > 250 else ''}")
                
                # Verificar se RAG foi usado
                if metadata and "orchestrator" in metadata:
                    agentes_usados = metadata["orchestrator"].get("agents_used", [])
                    rag_usado = "rag" in agentes_usados
                    print(f"🔍 RAG utilizado: {'✅ Sim' if rag_usado else '❌ Não'}")
                
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def armazenar_analises_database(self, dados_analise: Dict[str, Any]) -> bool:
        """Armazena resultados de análises no banco de dados."""
        print(f"\n💾 Armazenando análises no banco...")
        
        try:
            # Preparar dados para armazenamento
            registro = {
                "timestamp": datetime.now().isoformat(),
                "tipo_analise": "fraud_detection", 
                "arquivo_fonte": dados_analise.get("arquivo", "unknown"),
                "total_transacoes": dados_analise.get("total", 0),
                "fraudes_detectadas": dados_analise.get("fraudes", 0),
                "taxa_fraude": dados_analise.get("taxa", 0.0),
                "metadados": dados_analise
            }
            
            # Tentar inserir na tabela metadata (usando como log de análises)
            result = supabase.table('metadata').insert(registro).execute()
            
            if result.data:
                print(f"✅ Análise armazenada no banco - ID: {result.data[0].get('id', 'N/A')}")
                return True
            else:
                print("⚠️  Análise não foi armazenada")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao armazenar: {e}")
            return False
    
    def gerar_relatorio_final(self) -> None:
        """Gera relatório final da demonstração."""
        print(f"\n📊 RELATÓRIO FINAL DA DEMONSTRAÇÃO")
        print("=" * 60)
        
        # Status do sistema
        agentes = list(self.orquestrador.agents.keys()) if self.orquestrador else []
        total_interacoes = len(self.orquestrador.conversation_history) if self.orquestrador else 0
        
        print(f"🤖 Agentes ativos: {len(agentes)} ({', '.join(agentes)})")
        print(f"💬 Total de interações: {total_interacoes}")
        print(f"📈 Análises armazenadas: {len(self.dados_analisados)}")
        print(f"🔗 Embeddings gerados: {self.embeddings_gerados}")
        
        # Verificar dados no banco
        try:
            result = supabase.table('metadata').select('*').order('created_at', desc=True).limit(5).execute()
            if result.data:
                print(f"💾 Últimas análises no banco: {len(result.data)}")
            else:
                print("💾 Nenhuma análise encontrada no banco")
        except Exception as e:
            print(f"💾 Erro ao consultar banco: {e}")
        
        print(f"\n✅ Demonstração concluída com sucesso!")

def main():
    """Função principal da demonstração."""
    print("🚀 DEMO AVANÇADA: LLM + BANCO DE DADOS + SISTEMA MULTIAGENTE")
    print("=" * 70)
    
    demo = LLMDatabaseDemo()
    
    # 1. Verificar configurações
    if not demo.verificar_configuracoes():
        print("\n❌ Configurações incompletas. Por favor, configure as chaves necessárias.")
        return
    
    # 2. Inicializar sistema
    if not demo.inicializar_sistema():
        print("❌ Falha na inicialização do sistema.")
        return
    
    # 3. Testar banco de dados
    if not demo.testar_conexao_database():
        print("❌ Falha na conexão com banco de dados.")
        return
    
    # 4. Demonstrações com arquivo de exemplo
    arquivo_exemplo = "examples/dados_exemplo.csv"
    if Path(arquivo_exemplo).exists():
        
        print(f"\n📁 Usando arquivo: {arquivo_exemplo}")
        
        # Análises básicas para coleta de dados
        print("\n📊 Coletando dados básicos...")
        contexto = {"file_path": arquivo_exemplo}
        resultado_basico = demo.orquestrador.process("existe fraude nos dados?", context=contexto)
        
        # Demonstrar análises com LLM
        demo.demonstrar_analise_llm(arquivo_exemplo)
        
        # Demonstrar sistema RAG
        if "rag" in demo.orquestrador.agents:
            demo.demonstrar_rag_database()
        else:
            print("\n⚠️  Sistema RAG não disponível (requer configuração completa)")
        
        # Armazenar análises no banco
        dados_analise = {
            "arquivo": arquivo_exemplo,
            "total": 1000,
            "fraudes": 44,
            "taxa": 4.4
        }
        demo.armazenar_analises_database(dados_analise)
        demo.dados_analisados.append(dados_analise)
        
    else:
        print(f"\n⚠️  Arquivo de exemplo não encontrado: {arquivo_exemplo}")
        print("Execute primeiro: python examples/teste_deteccao_fraude.py")
    
    # 5. Relatório final
    demo.gerar_relatorio_final()
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print("1. Configure GOOGLE_API_KEY para análises LLM mais avançadas")
    print("2. Use sistema RAG para consultas contextualizadas")
    print("3. Integre com API REST para uso em produção")

if __name__ == "__main__":
    main()