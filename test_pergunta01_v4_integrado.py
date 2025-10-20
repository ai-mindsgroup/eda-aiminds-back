#!/usr/bin/env python3
"""
Teste Rápido - Pergunta 01 com RAGDataAgent V4.0 Integrado
===========================================================

Testa se o sistema principal (interface interativa) responde corretamente
à Pergunta 01 sobre tipos de dados, listando TODAS as 31 colunas com tipos corretos.

CRITÉRIOS DE SUCESSO:
✅ Lista TODAS as 31 colunas
✅ Detecta Class como categórica binária (0=não fraude, 1=fraude)
✅ Não menciona colunas fictícias (A1-A10, V29-V31)
✅ Usa dtypes reais do DataFrame (int64, float64)
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from uuid import uuid4

from src.agent.rag_data_agent import RAGDataAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def test_pergunta_01():
    """Testa Pergunta 01: Quais são os tipos de dados?"""
    
    print("=" * 80)
    print("TESTE - PERGUNTA 01: Tipos de Dados")
    print("RAGDataAgent V4.0 Integrado")
    print("=" * 80)
    print()
    
    # Inicializar agente
    print("🔧 Inicializando RAGDataAgent V4.0...")
    try:
        agent = RAGDataAgent()
        print("✅ Agente inicializado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao inicializar agente: {e}")
        return False
    
    # Pergunta 01
    pergunta = "Quais são os tipos de dados (numéricos, categóricos)?"
    session_id = f"test_pergunta01_{uuid4().hex[:8]}"
    
    print(f"\n📝 Session ID: {session_id}")
    print(f"❓ Pergunta: {pergunta}")
    print("\n⏳ Processando...\n")
    
    try:
        # Processar query
        result = await agent.process(
            query=pergunta,
            context={},
            session_id=session_id
        )
        
        if not result.get('success', False):
            print(f"❌ ERRO: {result.get('error', 'Erro desconhecido')}")
            return False
        
        resposta = result.get('content', '')
        
        # Exibir resposta
        print("=" * 80)
        print("RESPOSTA DO AGENTE:")
        print("=" * 80)
        print(resposta)
        print("=" * 80)
        
        # Validação automática
        print("\n" + "=" * 80)
        print("VALIDAÇÃO AUTOMÁTICA:")
        print("=" * 80)
        
        problemas = []
        acertos = []
        
        # Verificar se menciona todas as 31 colunas
        colunas_esperadas = [
            'Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
            'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 'V20',
            'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'Amount', 'Class'
        ]
        
        colunas_encontradas = [col for col in colunas_esperadas if col in resposta]
        colunas_faltantes = [col for col in colunas_esperadas if col not in resposta]
        
        print(f"\n📊 Colunas encontradas: {len(colunas_encontradas)}/31")
        if len(colunas_encontradas) == 31:
            acertos.append("✅ TODAS as 31 colunas foram listadas")
        else:
            problemas.append(f"❌ Faltam {len(colunas_faltantes)} colunas: {', '.join(colunas_faltantes[:5])}")
        
        # Verificar se não menciona colunas fictícias
        colunas_ficticias = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                             'V29', 'V30', 'V31']
        ficticias_encontradas = [col for col in colunas_ficticias if col in resposta]
        
        if not ficticias_encontradas:
            acertos.append("✅ Nenhuma coluna fictícia mencionada")
        else:
            problemas.append(f"❌ Colunas fictícias encontradas: {', '.join(ficticias_encontradas)}")
        
        # Verificar se menciona tipos de dados
        tipos_esperados = ['int64', 'float64', 'numéric', 'categóric']
        tipos_encontrados = [tipo for tipo in tipos_esperados if tipo.lower() in resposta.lower()]
        
        if len(tipos_encontrados) >= 2:
            acertos.append("✅ Menciona tipos de dados (numéricos/categóricos)")
        else:
            problemas.append("❌ Não menciona tipos de dados claramente")
        
        # Verificar se menciona Class como categórica
        if 'class' in resposta.lower() and any(term in resposta.lower() for term in ['categóric', 'binári', 'fraude', '0', '1']):
            acertos.append("✅ Identifica Class como categórica/binária")
        else:
            problemas.append("⚠️ Class não identificada como categórica binária")
        
        # Mostrar resultados
        print("\n🎯 ACERTOS:")
        for acerto in acertos:
            print(f"  {acerto}")
        
        if problemas:
            print("\n⚠️  PROBLEMAS:")
            for problema in problemas:
                print(f"  {problema}")
        
        # Calcular score
        score = len(acertos) / (len(acertos) + len(problemas))
        print(f"\n📈 SCORE: {score:.2f} ({len(acertos)}/{len(acertos) + len(problemas)})")
        
        # Veredicto final
        print("\n" + "=" * 80)
        if score >= 0.75 and len(colunas_encontradas) == 31:
            print("✅ TESTE PASSOU - Sistema responde Pergunta 01 corretamente!")
            print("=" * 80)
            return True
        else:
            print("❌ TESTE FALHOU - Sistema precisa de ajustes")
            print("=" * 80)
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEÇÃO durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_pergunta_01())
    sys.exit(0 if success else 1)
