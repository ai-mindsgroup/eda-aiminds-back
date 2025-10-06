#!/usr/bin/env python3
"""
Teste Automático - Todas as Perguntas do Curso V2.1

Executa TODAS as perguntas da descrição da atividade do curso de uma vez,
fazendo cada pergunta sequencialmente e registrando as respostas.

✅ VERSÃO 2.1: Com controle interativo de fluxo
✅ Após cada resposta, aguarda confirmação do usuário para prosseguir
✅ Permite interrupção segura com salvamento de resultados parciais
✅ Memória persistente ATIVA - todas as perguntas na mesma sessão
✅ Contexto conversacional mantido entre perguntas
✅ Usa RAGDataAgent V2.0 com LangChain

Perguntas baseadas na descrição da atividade:
- Descrição dos Dados
- Identificação de Padrões e Tendências
- Detecção de Anomalias (Outliers)
- Relações entre Variáveis

FLUXO:
1. Faz pergunta ao sistema
2. Exibe resposta completa
3. Pergunta: "Posso prosseguir? [Sim (s) / Não (n)]"
4. Se 's': vai para próxima pergunta
5. Se 'n': salva resultados parciais e encerra
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import json
import asyncio

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# PERGUNTAS DA ATIVIDADE DO CURSO
# ═══════════════════════════════════════════════════════════════

PERGUNTAS_CURSO = {
    "1. DESCRIÇÃO DOS DADOS": [
        "Quais são os tipos de dados (numéricos, categóricos)?",
        "Qual a distribuição de cada variável (histogramas, distribuições)?",
        "Qual o intervalo de cada variável (mínimo, máximo)?",
        "Quais são as medidas de tendência central (média, mediana)?",
        "Qual a variabilidade dos dados (desvio padrão, variância)?",
    ],
    
    "2. IDENTIFICAÇÃO DE PADRÕES E TENDÊNCIAS": [
        "Existem padrões ou tendências temporais?",
        "Quais os valores mais frequentes ou menos frequentes?",
        "Existem agrupamentos (clusters) nos dados?",
    ],
    
    "3. DETECÇÃO DE ANOMALIAS (OUTLIERS)": [
        "Existem valores atípicos nos dados?",
        "Como esses outliers afetam a análise?",
        "Podem ser removidos, transformados ou investigados?",
    ],
    
    "4. RELAÇÕES ENTRE VARIÁVEIS": [
        "Como as variáveis estão relacionadas umas com as outras? (Gráficos de dispersão, tabelas cruzadas)",
        "Existe correlação entre as variáveis?",
        "Quais variáveis parecem ter maior ou menor influência sobre outras?",
    ],
}


def print_separator(title: str = None):
    """Imprime separador visual."""
    if title:
        print(f"\n{'═' * 70}")
        print(f"  {title}")
        print(f"{'═' * 70}\n")
    else:
        print(f"{'─' * 70}\n")


def save_results(results: list, output_file: str = None):
    """Salva resultados em arquivo JSON e texto."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/teste_perguntas_curso_{timestamp}"
    
    # Criar diretório se não existir
    os.makedirs("outputs", exist_ok=True)
    
    # Salvar JSON
    json_file = f"{output_file}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Salvar TXT legível
    txt_file = f"{output_file}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("═" * 70 + "\n")
        f.write("  TESTE AUTOMÁTICO - PERGUNTAS DO CURSO\n")
        f.write("  EDA AI MINDS - Sistema Multiagente RAG Vetorial\n")
        f.write(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("═" * 70 + "\n\n")
        
        for result in results:
            f.write(f"\n{'═' * 70}\n")
            f.write(f"CATEGORIA: {result['categoria']}\n")
            f.write(f"{'═' * 70}\n\n")
            f.write(f"PERGUNTA {result['numero']}:\n{result['pergunta']}\n\n")
            f.write(f"{'─' * 70}\n")
            f.write(f"RESPOSTA:\n{result['resposta']}\n\n")
            
            if result.get('metadata'):
                f.write(f"METADADOS:\n")
                for key, value in result['metadata'].items():
                    f.write(f"  • {key}: {value}\n")
            
            f.write(f"\n{'─' * 70}\n")
            f.write(f"Status: {result['status']}\n")
            if result.get('erro'):
                f.write(f"Erro: {result['erro']}\n")
            f.write(f"Tempo: {result['tempo']:.2f}s\n")
            f.write(f"{'─' * 70}\n\n")
    
    return json_file, txt_file


async def main():
    """Executa teste com todas as perguntas do curso COM MEMÓRIA PERSISTENTE e CONTROLE INTERATIVO."""
    print_separator("🧪 TESTE AUTOMÁTICO - PERGUNTAS DO CURSO V2.1")
    
    print("📋 Este script executará TODAS as perguntas da atividade do curso:")
    print("   1. Descrição dos Dados (5 perguntas)")
    print("   2. Identificação de Padrões e Tendências (3 perguntas)")
    print("   3. Detecção de Anomalias/Outliers (3 perguntas)")
    print("   4. Relações entre Variáveis (3 perguntas)")
    print(f"   TOTAL: {sum(len(perguntas) for perguntas in PERGUNTAS_CURSO.values())} perguntas\n")
    
    print("ℹ️  IMPORTANTE:")
    print("   ✅ Memória persistente ATIVA - todas as perguntas na mesma sessão")
    print("   ✅ Contexto conversacional mantido entre perguntas")
    print("   ✅ Histórico salvo em Supabase (tabelas agent_sessions/agent_conversations)")
    print("   🔄 NOVO: Controle interativo - confirma antes de cada pergunta")
    print("   💾 NOVO: Salvamento automático ao interromper (resultados parciais)\n")
    print("   Este teste busca dados diretamente na base vetorial Supabase.")
    print("   Certifique-se de ter carregado dados com:")
    print("   python load_csv_data.py data/creditcard.csv\n")
    
    # Gerar session_id único para toda a sequência de testes
    session_id = str(uuid4())
    print(f"🔑 Sessão de teste: {session_id}\n")
    
    # Confirmar execução
    confirmar = input("▶️  Iniciar teste? (s/n): ").strip().lower()
    if confirmar not in ['s', 'sim', 'y', 'yes']:
        print("❌ Teste cancelado.")
        return
    
    # Inicializar orchestrador
    print("\n🔧 Inicializando sistema multiagente...")
    try:
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=True,
            enable_data_processor=True
        )
        print("✅ Sistema inicializado com sucesso!")
        print("✅ RAGDataAgent V2.0: Memória persistente + LangChain")
        print("✅ Sessão iniciada - histórico será mantido entre perguntas")
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema: {e}")
        logger.error(f"Erro na inicialização: {e}", exc_info=True)
        return
    
    # Executar perguntas
    print_separator("🚀 INICIANDO TESTE DAS PERGUNTAS")
    
    results = []
    total_perguntas = sum(len(perguntas) for perguntas in PERGUNTAS_CURSO.values())
    contador = 0
    
    for categoria, perguntas in PERGUNTAS_CURSO.items():
        print_separator(categoria)
        
        for idx, pergunta in enumerate(perguntas, 1):
            contador += 1
            
            print(f"[{contador}/{total_perguntas}] ❓ Pergunta: {pergunta}")
            
            # Executar pergunta COM MEMÓRIA PERSISTENTE
            start_time = datetime.now()
            
            try:
                # USAR MÉTODO ASYNC COM MEMÓRIA PERSISTENTE
                response = await orchestrator.process_with_persistent_memory(
                    pergunta,
                    context={},
                    session_id=session_id
                )
                
                end_time = datetime.now()
                tempo = (end_time - start_time).total_seconds()
                
                if response and response.get('content'):
                    resposta = response['content']
                    metadata = response.get('metadata', {})
                    status = "✅ SUCESSO"
                    erro = None
                    
                    # Mostrar resposta resumida
                    resposta_preview = resposta[:150] + "..." if len(resposta) > 150 else resposta
                    print(f"   ✅ Resposta: {resposta_preview}")
                    
                    if metadata.get('agent_used'):
                        print(f"   📌 Agente: {metadata['agent_used']}")
                    if metadata.get('previous_interactions') is not None:
                        print(f"   📌 Histórico: {metadata['previous_interactions']} interações anteriores")
                else:
                    resposta = "Sem resposta"
                    metadata = {}
                    status = "⚠️ SEM RESPOSTA"
                    erro = "Resposta vazia do agente"
                    print(f"   ⚠️  Sem resposta do agente")
            
            except Exception as e:
                end_time = datetime.now()
                tempo = (end_time - start_time).total_seconds()
                resposta = f"ERRO: {str(e)}"
                metadata = {}
                status = "❌ ERRO"
                erro = str(e)
                print(f"   ❌ Erro: {str(e)[:100]}")
                logger.error(f"Erro na pergunta '{pergunta}': {e}", exc_info=True)
            
            # Registrar resultado
            result = {
                "numero": contador,
                "categoria": categoria,
                "pergunta": pergunta,
                "resposta": resposta,
                "metadata": metadata,
                "status": status,
                "erro": erro,
                "tempo": tempo,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            
            print(f"   ⏱️  Tempo: {tempo:.2f}s\n")
            
            # === NOVO: Aguardar confirmação do usuário ===
            if contador < total_perguntas:  # Não perguntar na última pergunta
                print("─" * 70)
                while True:
                    prosseguir = input("📋 Posso prosseguir para a próxima pergunta? [Sim (s) / Não (n)]: ").strip().lower()
                    if prosseguir in ['s', 'sim', 'y', 'yes']:
                        print("✅ Prosseguindo...\n")
                        break
                    elif prosseguir in ['n', 'não', 'nao', 'no']:
                        print("\n❌ Teste interrompido pelo usuário.")
                        print(f"📊 Perguntas processadas até o momento: {contador}/{total_perguntas}")
                        print(f"💾 Salvando resultados parciais...\n")
                        
                        # Salvar resultados parciais
                        try:
                            json_file, txt_file = save_results(results)
                            print(f"✅ Resultados parciais salvos:")
                            print(f"   • JSON: {json_file}")
                            print(f"   • TXT:  {txt_file}")
                        except Exception as e:
                            print(f"❌ Erro ao salvar resultados: {e}")
                        
                        return  # Encerra a função main()
                    else:
                        print("⚠️  Resposta inválida. Digite 's' para Sim ou 'n' para Não.")
            
            print_separator()
    
    # Resumo final
    print_separator("📊 RESUMO DO TESTE")
    
    total = len(results)
    sucessos = sum(1 for r in results if r['status'] == "✅ SUCESSO")
    sem_resposta = sum(1 for r in results if r['status'] == "⚠️ SEM RESPOSTA")
    erros = sum(1 for r in results if r['status'] == "❌ ERRO")
    tempo_total = sum(r['tempo'] for r in results)
    tempo_medio = tempo_total / total if total > 0 else 0
    
    print(f"Total de perguntas: {total}")
    print(f"✅ Sucessos: {sucessos} ({sucessos/total*100:.1f}%)")
    print(f"⚠️  Sem resposta: {sem_resposta} ({sem_resposta/total*100:.1f}%)")
    print(f"❌ Erros: {erros} ({erros/total*100:.1f}%)")
    print(f"⏱️  Tempo total: {tempo_total:.2f}s")
    print(f"⏱️  Tempo médio: {tempo_medio:.2f}s/pergunta")
    print(f"🔑 Sessão ID: {session_id}")
    print(f"💾 Histórico salvo em: agent_sessions / agent_conversations (Supabase)")
    
    # Salvar resultados
    print("\n💾 Salvando resultados...")
    try:
        json_file, txt_file = save_results(results)
        print(f"✅ Resultados salvos:")
        print(f"   • JSON: {json_file}")
        print(f"   • TXT:  {txt_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar resultados: {e}")
        logger.error(f"Erro ao salvar: {e}", exc_info=True)
    
    print_separator("✅ TESTE CONCLUÍDO")
    
    # Mostrar perguntas com erro se houver
    if erros > 0:
        print("\n⚠️  PERGUNTAS COM ERRO:")
        for result in results:
            if result['status'] == "❌ ERRO":
                print(f"   • [{result['numero']}] {result['pergunta']}")
                print(f"     Erro: {result['erro'][:100]}")
        print()


if __name__ == "__main__":
    # Executar loop async
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Teste interrompido pelo usuário.\n")
