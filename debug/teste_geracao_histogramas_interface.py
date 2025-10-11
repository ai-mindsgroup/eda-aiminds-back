#!/usr/bin/env python3
"""
Script de teste para verificar se a interface interativa gera histogramas corretamente
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
import traceback

def testar_geracao_histogramas():
    """Testa a geração de histogramas através do OrchestratorAgent"""
    
    print("=" * 80)
    print("TESTE DE GERAÇÃO DE HISTOGRAMAS VIA INTERFACE INTERATIVA")
    print("=" * 80)
    print()
    
    try:
        # Inicializar orquestrador
        print("🔧 Inicializando OrchestratorAgent...")
        orchestrator = OrchestratorAgent("orchestrator")
        print("✅ OrchestratorAgent inicializado com sucesso!")
        print()
        
        # Testar com diferentes perguntas que devem gerar histogramas
        perguntas_teste = [
            "Mostre a distribuição das variáveis",
            "Gere histogramas para os dados",
            "Quero ver gráficos de distribuição",
        ]
        
        for i, pergunta in enumerate(perguntas_teste, 1):
            print(f"\n{'='*80}")
            print(f"TESTE {i}: {pergunta}")
            print(f"{'='*80}\n")
            
            try:
                resultado = orchestrator.process(pergunta)
                
                if resultado:
                    print(f"✅ Resposta recebida:")
                    print(resultado.get("content", "Sem conteúdo"))
                    print()
                    
                    metadata = resultado.get("metadata", {})
                    
                    if metadata.get("visualization_success"):
                        print("🎉 SUCESSO! Visualizações foram geradas!")
                        graficos = metadata.get("graficos_gerados", [])
                        print(f"📊 Total de gráficos: {len(graficos)}")
                        
                        if graficos:
                            print("\n📁 Arquivos gerados:")
                            for grafico in graficos:
                                print(f"   • {grafico}")
                        
                        # Verificar se os arquivos realmente existem
                        print("\n🔍 Verificando existência dos arquivos...")
                        arquivos_existentes = 0
                        for grafico in graficos:
                            if Path(grafico).exists():
                                arquivos_existentes += 1
                                print(f"   ✅ {Path(grafico).name} - EXISTE")
                            else:
                                print(f"   ❌ {Path(grafico).name} - NÃO ENCONTRADO")
                        
                        print(f"\n📈 Resultado: {arquivos_existentes}/{len(graficos)} arquivos existem")
                        
                        if arquivos_existentes == len(graficos):
                            print("🎉🎉🎉 TESTE PASSOU! Todos os arquivos foram gerados corretamente!")
                            return True
                        else:
                            print("⚠️ TESTE PARCIAL: Alguns arquivos não foram encontrados")
                    else:
                        print("⚠️ Visualizações não foram geradas neste teste")
                        if metadata.get("error"):
                            print(f"❌ Erro: {metadata.get('exception', 'Erro desconhecido')}")
                else:
                    print("❌ Nenhuma resposta recebida")
                    
            except Exception as e:
                print(f"❌ Erro durante o teste: {str(e)}")
                traceback.print_exc()
            
            print()
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    sucesso = testar_geracao_histogramas()
    print()
    print("=" * 80)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("⚠️ TESTE NÃO CONCLUÍDO - Verifique os logs acima")
    print("=" * 80)
    print()
