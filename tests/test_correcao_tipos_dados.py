#!/usr/bin/env python3
"""Script de teste para validar correção do parsing de chunk_text e análise correta de tipos de dados"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
import traceback

def test_data_types_query():
    """Testa consulta sobre tipos de dados"""
    print("=" * 80)
    print("TESTE: Analise de Tipos de Dados (pos-correcao)")
    print("=" * 80)
    print()
    
    try:
        # Inicializar orchestrator
        print("Inicializando sistema...")
        orchestrator = OrchestratorAgent("orchestrator")
        print("Sistema inicializado\n")
        
        # Fazer consulta sobre tipos de dados
        query = "Quais são os tipos de dados (numéricos, categóricos)?"
        print(f"Pergunta: {query}")
        print("Processando...\n")
        print("-" * 80)
        
        result = orchestrator.process(query, {})
        
        print("-" * 80)
        print("\nRESULTADO DA ANALISE:")
        print()
        
        if result:
            response = result.get("response", "Sem resposta")
            print(f"Resposta do sistema:\n{response}\n")
            
            # Validar se a resposta está correta
            print("\nVALIDACAO:")
            correct_columns = ['Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 
                             'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 
                             'V19', 'V20', 'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 
                             'V28', 'Amount', 'Class']
            
            response_lower = response.lower()
            
            # Verificar se mencionou colunas corretas
            correct_mentions = sum(1 for col in correct_columns if col.lower() in response_lower)
            
            # Verificar se NÃO mencionou colunas erradas da tabela embeddings
            wrong_mentions = ['chunk_text', 'created_at', 'embedding', 'originais', 'normais', 
                            'sequenciais', 'exemplo', 'temporais']
            wrong_count = sum(1 for word in wrong_mentions if word in response_lower)
            
            print(f"- Mencoes corretas as colunas do CSV: {correct_mentions}/{len(correct_columns)}")
            print(f"- Mencoes incorretas (tabela embeddings/palavras soltas): {wrong_count}")
            
            if correct_mentions >= 5 and wrong_count == 0:
                print("\nTESTE PASSOU! Resposta esta analisando dados CSV corretos.")
            elif correct_mentions >= 2:
                print("\nTESTE PARCIAL: Resposta melhorou mas pode ser refinada.")
            else:
                print("\nTESTE FALHOU: Resposta ainda nao esta correta.")
                
            # Mostrar metadados
            if "metadata" in result:
                metadata = result["metadata"]
                print(f"\nMetadados:")
                print(f"  - Agentes utilizados: {metadata.get('agents_used', 'N/A')}")
                print(f"  - Provedor LLM: {metadata.get('llm_provider', 'N/A')}")
                print(f"  - Tempo: {metadata.get('processing_time', 'N/A')}")
        else:
            print("Nenhum resultado retornado")
            
    except Exception as e:
        print(f"\nERRO NO TESTE: {str(e)}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("\nIniciando teste de validacao da correcao\n")
    success = test_data_types_query()
    
    if success:
        print("\n" + "=" * 80)
        print("Teste concluido com sucesso!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("Teste falhou - verifique os logs")
        print("=" * 80)
        sys.exit(1)
