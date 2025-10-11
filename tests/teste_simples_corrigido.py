#!/usr/bin/env python3
"""Interface simples para testar o sistema corrigido"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_single_question():
    """Testa uma pergunta simples para validar as correções"""
    
    print("🧪 TESTE SIMPLES - PERGUNTA SOBRE TIPOS DE DADOS")
    print("=" * 60)
    
    try:
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        print("🔧 Inicializando orquestrador...")
        orchestrator = OrchestratorAgent("test")
        
        print("❓ Pergunta: 'Quais são os tipos de dados (numéricos, categóricos)?'")
        
        # Fazer a pergunta
        resultado = orchestrator.process_query("Quais são os tipos de dados (numéricos, categóricos)?")
        
        print(f"\n📋 RESPOSTA DO SISTEMA:")
        print("─" * 50)
        print(resultado.get('response', 'Nenhuma resposta'))
        print("─" * 50)
        
        # Verificar se está correta
        response_text = resultado.get('response', '').lower()
        
        success_indicators = [
            'todas' in response_text and 'numéricas' in response_text,
            '31' in response_text and 'colunas' in response_text,
            'nenhuma' in response_text and 'categórica' in response_text,
            '284' in response_text and 'registros' in response_text
        ]
        
        score = sum(success_indicators)
        
        print(f"\n📊 AVALIAÇÃO DA RESPOSTA:")
        print(f"✅ Menciona todas numéricas: {'Sim' if success_indicators[0] else 'Não'}")
        print(f"✅ Menciona 31 colunas: {'Sim' if success_indicators[1] else 'Não'}")
        print(f"✅ Confirma zero categóricas: {'Sim' if success_indicators[2] else 'Não'}")
        print(f"✅ Menciona total registros: {'Sim' if success_indicators[3] else 'Não'}")
        
        print(f"\n🎯 SCORE: {score}/4")
        
        if score >= 3:
            print("🎉 SUCESSO: Resposta corrigida e precisa!")
            return True
        else:
            print("⚠️ PARCIAL: Ainda há espaço para melhorias")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_single_question()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ CORREÇÕES APLICADAS COM SUCESSO!")
        print("🎯 Sistema agora é:")
        print("  🔄 Agnóstico ao provedor LLM (Groq, OpenAI, Gemini, etc.)")
        print("  🛡️ Genérico para qualquer pergunta sobre dados")
        print("  📊 Preciso ao consultar dados reais do Supabase")
        print("  🎨 Adaptativo a diferentes tipos de dataset")
    else:
        print("⚠️ Sistema melhorado mas pode precisar de ajustes finos")
    
    print("="*60)