#!/usr/bin/env python3
"""
Teste Completo - 17 Perguntas do Curso com RAGDataAgent V4.0

Este script testa o sistema melhorado com prompts dinâmicos e parâmetros otimizados,
validando respostas para as 17 perguntas da atividade do curso:

📊 DESCRIÇÃO DOS DADOS (5 perguntas)
📈 IDENTIFICAÇÃO DE PADRÕES (3 perguntas)
🔍 DETECÇÃO DE ANOMALIAS (3 perguntas)
🔗 RELAÇÕES ENTRE VARIÁVEIS (3 perguntas)
📊 ANÁLISES COMPLEMENTARES (3 perguntas adicionais)

MELHORIAS V4.0:
- ✅ Prompts completamente dinâmicos (zero hardcoding)
- ✅ Parâmetros LLM/RAG otimizados (temperatura 0.1-0.35, threshold 0.6-0.65)
- ✅ Fallback inteligente para CSV direto
- ✅ Geração automática de visualizações
- ✅ Logging detalhado com métricas

Autor: EDA AI Minds Team
Data: 2025-10-18
Versão: 4.0.0
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import json

# Adicionar diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.rag_data_agent_v4 import RAGDataAgentV4, create_agent_v4
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 17 PERGUNTAS DO CURSO (4 CATEGORIAS)
# ═══════════════════════════════════════════════════════════════

PERGUNTAS_CURSO = {
    "1. DESCRIÇÃO DOS DADOS": [
        {
            "id": "Q01",
            "pergunta": "Quais são os tipos de dados (numéricos, categóricos)?",
            "categoria": "tipos_dados",
            "expectativa": "Deve listar TODAS as colunas classificadas por dtype real (int64, float64, object, etc)"
        },
        {
            "id": "Q02",
            "pergunta": "Qual a distribuição de cada variável (histogramas, distribuições)?",
            "categoria": "distribuicao",
            "expectativa": "Deve gerar histogramas E descrever formas das distribuições (simétrica, assimétrica, bimodal)"
        },
        {
            "id": "Q03",
            "pergunta": "Qual o intervalo de cada variável (mínimo, máximo)?",
            "categoria": "intervalo",
            "expectativa": "Deve reportar min/max para TODAS as colunas numéricas"
        },
        {
            "id": "Q04",
            "pergunta": "Quais são as medidas de tendência central (média, mediana)?",
            "categoria": "tendencia_central",
            "expectativa": "Deve calcular média E mediana para todas as colunas numéricas, com interpretação"
        },
        {
            "id": "Q05",
            "pergunta": "Qual a variabilidade dos dados (desvio padrão, variância)?",
            "categoria": "variabilidade",
            "expectativa": "Deve calcular std e variância para todas as colunas numéricas, com interpretação"
        },
    ],
    
    "2. IDENTIFICAÇÃO DE PADRÕES E TENDÊNCIAS": [
        {
            "id": "Q06",
            "pergunta": "Existem padrões ou tendências temporais?",
            "categoria": "temporal",
            "expectativa": "Deve identificar colunas temporais OU indicar ausência clara"
        },
        {
            "id": "Q07",
            "pergunta": "Quais os valores mais frequentes ou menos frequentes?",
            "categoria": "frequencia",
            "expectativa": "Deve identificar top N valores mais/menos frequentes para cada coluna relevante"
        },
        {
            "id": "Q08",
            "pergunta": "Existem agrupamentos (clusters) nos dados?",
            "categoria": "clustering",
            "expectativa": "Deve analisar possibilidade de clusters, idealmente com análise exploratória"
        },
    ],
    
    "3. DETECÇÃO DE ANOMALIAS (OUTLIERS)": [
        {
            "id": "Q09",
            "pergunta": "Existem valores atípicos nos dados?",
            "categoria": "outliers_deteccao",
            "expectativa": "Deve detectar outliers usando IQR/Z-score para colunas numéricas, com quantificação"
        },
        {
            "id": "Q10",
            "pergunta": "Como esses outliers afetam a análise?",
            "categoria": "outliers_impacto",
            "expectativa": "Deve explicar impacto em média, mediana, e outras estatísticas"
        },
        {
            "id": "Q11",
            "pergunta": "Podem ser removidos, transformados ou investigados?",
            "categoria": "outliers_tratamento",
            "expectativa": "Deve sugerir estratégias de tratamento baseadas no contexto dos dados"
        },
    ],
    
    "4. RELAÇÕES ENTRE VARIÁVEIS": [
        {
            "id": "Q12",
            "pergunta": "Como as variáveis estão relacionadas umas com as outras? (Gráficos de dispersão, tabelas cruzadas)",
            "categoria": "relacoes",
            "expectativa": "Deve analisar relações entre pares de variáveis, idealmente com visualizações"
        },
        {
            "id": "Q13",
            "pergunta": "Existe correlação entre as variáveis?",
            "categoria": "correlacao",
            "expectativa": "Deve calcular matriz de correlação e identificar correlações fortes/fracas"
        },
        {
            "id": "Q14",
            "pergunta": "Quais variáveis parecem ter maior ou menor influência sobre outras?",
            "categoria": "influencia",
            "expectativa": "Deve identificar variáveis com maior poder preditivo ou associação"
        },
    ],
    
    "5. ANÁLISES COMPLEMENTARES": [
        {
            "id": "Q15",
            "pergunta": "Existem valores ausentes no dataset? Qual o percentual?",
            "categoria": "missing_values",
            "expectativa": "Deve reportar missing values por coluna com percentuais"
        },
        {
            "id": "Q16",
            "pergunta": "Qual a forma das distribuições? São simétricas ou assimétricas?",
            "categoria": "forma_distribuicao",
            "expectativa": "Deve analisar assimetria (skewness) e curtose para cada variável numérica"
        },
        {
            "id": "Q17",
            "pergunta": "Faça um resumo executivo completo do dataset.",
            "categoria": "resumo_executivo",
            "expectativa": "Deve fornecer visão holística: dimensões, tipos, estatísticas-chave, padrões, insights"
        },
    ],
}


def print_separator(title: str = None, char: str = "="):
    """Imprime separador visual."""
    # Usar caracteres ASCII para compatibilidade Windows
    if char not in ['=', '-', '_']:
        char = '='
    
    if title:
        print(f"\n{char * 80}")
        print(f"  {title}")
        print(f"{char * 80}\n")
    else:
        print(f"{char * 80}\n")


def print_question_header(pergunta_dict: dict):
    """Imprime cabeçalho de pergunta formatado."""
    print(f"\n{'>' * 40}")
    print(f"ID: {pergunta_dict['id']}")
    print(f"PERGUNTA: {pergunta_dict['pergunta']}")
    print(f"CATEGORIA: {pergunta_dict['categoria']}")
    print(f"EXPECTATIVA: {pergunta_dict['expectativa']}")
    print(f"{'>' * 40}\n")


def validate_response(
    pergunta_dict: dict,
    result: dict
) -> dict:
    """
    Valida resposta baseada em critérios de qualidade.
    
    Args:
        pergunta_dict: Dicionário com pergunta e expectativas
        result: Resultado do agent.query_v4()
        
    Returns:
        Dicionário com validação: {'passed': bool, 'issues': list, 'score': float}
    """
    validation = {
        'passed': True,
        'issues': [],
        'score': 1.0,
        'metrics': {}
    }
    
    if not result['success']:
        validation['passed'] = False
        validation['issues'].append(f"Query falhou: {result.get('error')}")
        validation['score'] = 0.0
        return validation
    
    answer = result['answer'].lower()
    categoria = pergunta_dict['categoria']
    
    # Validações específicas por categoria
    if categoria == 'tipos_dados':
        # Deve mencionar numérico/categórico E listar colunas
        if 'numéric' not in answer and 'numeric' not in answer:
            validation['issues'].append("Não menciona tipos numéricos claramente")
            validation['score'] -= 0.3
        
        # Deve ter pelo menos 5 nomes de colunas (indicando listagem)
        import re
        col_mentions = len(re.findall(r'`\w+`', result['answer']))  # Colunas em backticks
        validation['metrics']['columns_mentioned'] = col_mentions
        if col_mentions < 5:
            validation['issues'].append(f"Poucas colunas listadas ({col_mentions})")
            validation['score'] -= 0.2
    
    elif categoria == 'distribuicao':
        # Deve gerar visualizações
        if not result.get('visualizations'):
            validation['issues'].append("Nenhuma visualização gerada")
            validation['score'] -= 0.5
        else:
            validation['metrics']['visualizations_count'] = len(result['visualizations'])
        
        # Deve descrever formas (simétrica, assimétrica, bimodal, etc)
        forma_keywords = ['simétric', 'assimétric', 'bimodal', 'normal', 'gaussiana', 'enviesad']
        if not any(kw in answer for kw in forma_keywords):
            validation['issues'].append("Não descreve formas das distribuições")
            validation['score'] -= 0.3
    
    elif categoria in ['intervalo', 'tendencia_central', 'variabilidade']:
        # Deve conter números (estatísticas)
        import re
        numbers = re.findall(r'\d+\.?\d*', answer)
        validation['metrics']['numbers_count'] = len(numbers)
        if len(numbers) < 10:  # Esperamos muitas estatísticas
            validation['issues'].append(f"Poucas estatísticas reportadas ({len(numbers)})")
            validation['score'] -= 0.3
    
    elif categoria == 'correlacao':
        # Deve mencionar correlação E idealmente valores numéricos
        if 'correlação' not in answer and 'correlation' not in answer:
            validation['issues'].append("Não menciona correlação explicitamente")
            validation['score'] -= 0.4
    
    elif categoria == 'outliers_deteccao':
        # Deve mencionar método (IQR, Z-score) E quantificar
        metodos = ['iqr', 'z-score', 'zscore', 'quartil', 'desvio padrão']
        if not any(m in answer for m in metodos):
            validation['issues'].append("Não menciona método de detecção de outliers")
            validation['score'] -= 0.3
    
    # Validações gerais
    answer_length = len(result['answer'])
    validation['metrics']['answer_length'] = answer_length
    
    if answer_length < 200:
        validation['issues'].append(f"Resposta muito curta ({answer_length} chars)")
        validation['score'] -= 0.2
    
    # Deve finalizar com call-to-action
    if 'mais detalhes' not in answer and 'perguntar' not in answer:
        validation['issues'].append("Não inclui call-to-action final")
        validation['score'] -= 0.1
    
    # Score mínimo: 0.0
    validation['score'] = max(0.0, validation['score'])
    
    # Passou se score >= 0.7
    validation['passed'] = validation['score'] >= 0.7
    
    return validation


def save_results(results: list, output_file: str = None):
    """Salva resultados em arquivo JSON e HTML."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/teste_17_perguntas_v4_{timestamp}"
    
    # Criar diretório se não existir
    os.makedirs("outputs", exist_ok=True)
    
    # Salvar JSON
    json_file = f"{output_file}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados salvos em: {json_file}")
    
    # Gerar HTML
    html_file = f"{output_file}.html"
    generate_html_report(results, html_file)
    print(f"📄 Relatório HTML: {html_file}")


def generate_html_report(results: list, output_file: str):
    """Gera relatório HTML com os resultados."""
    # Calcular estatísticas gerais
    total = len(results)
    passed = sum(1 for r in results if r['validation']['passed'])
    avg_score = sum(r['validation']['score'] for r in results) / total if total > 0 else 0
    avg_time = sum(r['result']['metadata']['processing_time_seconds'] for r in results if r['result']['success']) / total
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste 17 Perguntas - RAGDataAgent V4.0</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .question-card {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .question-card.passed {{
            border-left: 5px solid #10b981;
        }}
        .question-card.failed {{
            border-left: 5px solid #ef4444;
        }}
        .question-id {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge.success {{
            background: #10b981;
            color: white;
        }}
        .badge.warning {{
            background: #f59e0b;
            color: white;
        }}
        .badge.error {{
            background: #ef4444;
            color: white;
        }}
        .answer {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
            font-size: 0.85em;
            color: #666;
        }}
        .issues {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .issues ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Teste 17 Perguntas do Curso</h1>
        <h2>RAGDataAgent V4.0 - Prompts Dinâmicos e Parâmetros Otimizados</h2>
        <p>Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{passed}/{total}</div>
            <div class="stat-label">Perguntas Aprovadas</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_score:.2f}</div>
            <div class="stat-label">Score Médio</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_time:.2f}s</div>
            <div class="stat-label">Tempo Médio</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{(passed/total*100):.1f}%</div>
            <div class="stat-label">Taxa de Sucesso</div>
        </div>
    </div>
"""
    
    for item in results:
        pergunta = item['pergunta']
        result = item['result']
        validation = item['validation']
        
        status_class = 'passed' if validation['passed'] else 'failed'
        status_badge = f'<span class="badge success">✅ APROVADA</span>' if validation['passed'] else f'<span class="badge error">❌ REPROVADA</span>'
        
        html += f"""
    <div class="question-card {status_class}">
        <div>
            <span class="question-id">{pergunta['id']}</span>
            {status_badge}
            <span class="badge warning">Score: {validation['score']:.2f}</span>
        </div>
        <h3>{pergunta['pergunta']}</h3>
        <p><strong>Categoria:</strong> {pergunta['categoria']}</p>
        <p><strong>Expectativa:</strong> {pergunta['expectativa']}</p>
"""
        
        if validation['issues']:
            html += f"""
        <div class="issues">
            <strong>⚠️ Problemas Identificados:</strong>
            <ul>
                {''.join(f'<li>{issue}</li>' for issue in validation['issues'])}
            </ul>
        </div>
"""
        
        if result['success']:
            html += f"""
        <div class="answer">
{result['answer'][:1000]}{'...' if len(result['answer']) > 1000 else ''}
        </div>
        
        <div class="metadata">
            <div><strong>Intent:</strong> {result['intent']}</div>
            <div><strong>Confidence:</strong> {result['confidence']:.2f}</div>
            <div><strong>Temperature:</strong> {result['metadata']['llm_config']['temperature']}</div>
            <div><strong>Max Tokens:</strong> {result['metadata']['llm_config']['max_tokens']}</div>
            <div><strong>RAG Threshold:</strong> {result['metadata']['rag_config']['threshold']}</div>
            <div><strong>Processing Time:</strong> {result['metadata']['processing_time_seconds']:.2f}s</div>
        </div>
"""
        else:
            html += f"""
        <div class="issues">
            <strong>❌ Erro:</strong> {result.get('error', 'Erro desconhecido')}
        </div>
"""
        
        html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    """Executa teste completo das 17 perguntas."""
    print_separator("TESTE COMPLETO - 17 PERGUNTAS DO CURSO", "=")
    print("RAGDataAgent V4.0 - Prompts Dinamicos e Parametros Otimizados")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    
    # Inicializar agente V4
    print("Inicializando RAGDataAgent V4.0...")
    try:
        agent = create_agent_v4()
        print("OK: Agente inicializado com sucesso!")
    except Exception as e:
        print(f"ERRO ao inicializar agente: {e}")
        return
    
    # ID da sessão para memória persistente
    session_id = f"test_17_perguntas_{uuid4().hex[:8]}"
    print(f"📝 Session ID: {session_id}")
    
    # Executar todas as perguntas
    results = []
    total_perguntas = sum(len(perguntas) for perguntas in PERGUNTAS_CURSO.values())
    current = 0
    
    for categoria, perguntas in PERGUNTAS_CURSO.items():
        print_separator(categoria)
        
        for pergunta_dict in perguntas:
            current += 1
            print_question_header(pergunta_dict)
            print(f"⏳ Processando ({current}/{total_perguntas})...")
            
            try:
                # Fazer query
                result = agent.query_v4(
                    query=pergunta_dict['pergunta'],
                    session_id=session_id
                )
                
                # Validar resposta
                validation = validate_response(pergunta_dict, result)
                
                # Exibir resultado
                if result['success']:
                    print(f"\n✅ RESPOSTA ({len(result['answer'])} chars):")
                    print("─" * 80)
                    print(result['answer'][:500])
                    if len(result['answer']) > 500:
                        print("...")
                    print("─" * 80)
                    
                    print(f"\n📊 VALIDAÇÃO:")
                    print(f"  - Score: {validation['score']:.2f}")
                    print(f"  - Status: {'✅ PASSOU' if validation['passed'] else '❌ FALHOU'}")
                    if validation['issues']:
                        print(f"  - Problemas:")
                        for issue in validation['issues']:
                            print(f"    • {issue}")
                    
                    print(f"\n⚙️  CONFIGURAÇÕES:")
                    print(f"  - Intent: {result['intent']}")
                    print(f"  - Temperature: {result['metadata']['llm_config']['temperature']}")
                    print(f"  - RAG Threshold: {result['metadata']['rag_config']['threshold']}")
                    print(f"  - Processing Time: {result['metadata']['processing_time_seconds']:.2f}s")
                    
                    if result.get('visualizations'):
                        print(f"  - Visualizações: {len(result['visualizations'])} gráficos gerados")
                else:
                    print(f"\n❌ ERRO: {result.get('error')}")
                    validation['passed'] = False
                    validation['score'] = 0.0
                
                # Salvar resultado
                results.append({
                    'pergunta': pergunta_dict,
                    'result': result,
                    'validation': validation,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"\n❌ EXCEÇÃO: {str(e)}")
                logger.error(f"Erro na pergunta {pergunta_dict['id']}: {e}", exc_info=True)
                results.append({
                    'pergunta': pergunta_dict,
                    'result': {'success': False, 'error': str(e)},
                    'validation': {'passed': False, 'score': 0.0, 'issues': [str(e)]},
                    'timestamp': datetime.now().isoformat()
                })
            
            print_separator(char="─")
    
    # Salvar resultados
    print_separator("SALVANDO RESULTADOS", "═")
    save_results(results)
    
    # Estatísticas finais
    print_separator("ESTATÍSTICAS FINAIS", "═")
    total = len(results)
    passed = sum(1 for r in results if r['validation']['passed'])
    avg_score = sum(r['validation']['score'] for r in results) / total if total > 0 else 0
    
    print(f"📊 Total de perguntas: {total}")
    print(f"✅ Aprovadas: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Reprovadas: {total - passed} ({(total-passed)/total*100:.1f}%)")
    print(f"📈 Score médio: {avg_score:.2f}")
    
    # Perguntas com menor score
    print(f"\n📉 Perguntas com menor score:")
    sorted_results = sorted(results, key=lambda x: x['validation']['score'])
    for i, item in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {item['pergunta']['id']} - Score: {item['validation']['score']:.2f}")
        print(f"     Pergunta: {item['pergunta']['pergunta'][:60]}...")
        if item['validation']['issues']:
            print(f"     Problemas: {item['validation']['issues'][0]}")
    
    print_separator("TESTE CONCLUÍDO", "═")
    print(f"✨ Resultados salvos! Consulte o relatório HTML para análise detalhada.")


if __name__ == "__main__":
    main()
