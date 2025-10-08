"""
Script para Popular VectorStore com Embeddings de Categorias de Intenção
=========================================================================

Este script cria embeddings de consultas exemplo para cada categoria/intenção,
armazenando-os no Supabase com metadados adequados para o classificador semântico.

CATEGORIAS SUPORTADAS:
- statistical_analysis: Estatísticas e medidas (média, mediana, desvio, etc.)
- fraud_detection: Detecção de fraudes e anomalias
- data_distribution: Análise de distribuição de dados
- data_visualization: Geração de gráficos e visualizações
- contextual_embedding: Busca contextual e semântica
- data_loading: Carregamento e importação de dados
- llm_generic: Análise genérica via LLM

COMO ADICIONAR NOVAS INTENÇÕES:
1. Adicione nova categoria em INTENT_CATEGORIES
2. Defina exemplos de consultas
3. Especifique metadados (palavras-chave, prioridade)
4. Execute o script: python scripts/populate_intent_embeddings.py
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Adicionar raiz do projeto ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
from src.embeddings.vector_store import VectorStore
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# DEFINIÇÃO DE CATEGORIAS E INTENÇÕES
# ============================================================================

INTENT_CATEGORIES = {
    "statistical_analysis": {
        "description": "Análise estatística de dados (média, mediana, moda, desvio, percentis)",
        "examples": [
            "Qual a média da variável Amount?",
            "Calcule a mediana de V1",
            "Mostre o desvio padrão de todas as variáveis",
            "Qual o percentil 75 da variável Time?",
            "Calcule a variância de V2",
            "Mostre estatísticas descritivas do dataset",
            "Qual o coeficiente de variação de Amount?",
            "Calcule a moda da variável Class",
            "Qual a amplitude de V3?",
            "Mostre quartis da variável Amount",
            "Calcule a mediana absoluta de V1",
            "Qual a curtose da distribuição de V2?",
            "Mostre a assimetria de Amount"
        ],
        "keywords": ["média", "mediana", "moda", "desvio", "variância", "percentil", 
                     "quartil", "estatística", "descritiva", "amplitude", "curtose", 
                     "assimetria", "coeficiente", "mean", "median", "std", "var"],
        "priority": 10  # Alta prioridade para análises estatísticas
    },
    
    "fraud_detection": {
        "description": "Detecção de fraudes, anomalias e padrões suspeitos",
        "examples": [
            "Detecte fraudes no dataset",
            "Identifique transações suspeitas",
            "Mostre anomalias nos dados",
            "Quais registros são outliers?",
            "Existe algum padrão de fraude?",
            "Identifique transações fraudulentas",
            "Mostre casos suspeitos de fraude",
            "Analise comportamento anômalo",
            "Detecte outliers em Amount",
            "Há fraudes na variável Class?",
            "Identifique padrões irregulares",
            "Mostre transações com comportamento atípico"
        ],
        "keywords": ["fraude", "fraudes", "anomalia", "anomalias", "outlier", "suspeito",
                     "fraudulento", "irregular", "atípico", "detecção", "identificar",
                     "fraud", "anomaly", "suspicious", "outliers"],
        "priority": 9
    },
    
    "data_distribution": {
        "description": "Análise de distribuição e intervalos de dados",
        "examples": [
            "Mostre o intervalo de valores da variável Time",
            "Qual a distribuição de Amount?",
            "Como estão distribuídos os valores de V1?",
            "Mostre a faixa de valores de V2",
            "Qual o range da variável Class?",
            "Analise a distribuição das variáveis",
            "Mostre valores mínimo e máximo de Amount",
            "Como se distribuem os dados?",
            "Qual a amplitude dos valores?",
            "Mostre histograma da distribuição",
            "Analise a dispersão dos dados",
            "Qual a frequência de cada valor?"
        ],
        "keywords": ["distribuição", "intervalo", "range", "amplitude", "faixa",
                     "mínimo", "máximo", "min", "max", "dispersão", "frequência",
                     "distribution", "interval", "spread"],
        "priority": 8
    },
    
    "data_visualization": {
        "description": "Geração de gráficos, plots e visualizações",
        "examples": [
            "Gere um histograma da distribuição de Amount",
            "Crie um gráfico de barras para Class",
            "Mostre um boxplot de V1",
            "Plote um scatter de V1 vs V2",
            "Gere visualizações das variáveis",
            "Crie um heatmap de correlação",
            "Mostre gráfico de linha de Time",
            "Plote distribuição de todas as variáveis",
            "Gere um gráfico de pizza para Class",
            "Crie visualização da distribuição",
            "Mostre plot de dispersão",
            "Gere gráficos para análise exploratória"
        ],
        "keywords": ["gráfico", "histograma", "plot", "visualização", "boxplot",
                     "scatter", "heatmap", "gerar", "criar", "mostrar", "plote",
                     "chart", "graph", "visualization", "histogram"],
        "priority": 8
    },
    
    "contextual_embedding": {
        "description": "Busca semântica e contextual em embeddings",
        "examples": [
            "Busque informações sobre fraudes",
            "Procure padrões nos dados",
            "Encontre contexto sobre transações",
            "Pesquise dados similares",
            "Recupere informações relevantes",
            "Busca semântica sobre anomalias",
            "Encontre documentos sobre estatísticas",
            "Pesquise por contexto relacionado",
            "Busque conhecimento sobre o dataset",
            "Recupere informações contextuais"
        ],
        "keywords": ["buscar", "procurar", "encontrar", "pesquisar", "recuperar",
                     "busca", "pesquisa", "contexto", "semântica", "similar",
                     "search", "find", "retrieve", "lookup"],
        "priority": 6
    },
    
    "data_loading": {
        "description": "Carregamento e importação de dados",
        "examples": [
            "Carregue o arquivo CSV",
            "Importe os dados do dataset",
            "Abra o arquivo creditcard.csv",
            "Carregue dados de fraudes",
            "Importe o dataset para análise",
            "Leia os dados do arquivo",
            "Carregue dados sintéticos",
            "Importe novo dataset"
        ],
        "keywords": ["carregar", "importar", "abrir", "ler", "arquivo", "dataset",
                     "dados", "csv", "load", "import", "read", "file"],
        "priority": 5
    },
    
    "llm_generic": {
        "description": "Análise genérica via LLM (interpretação, insights, conclusões)",
        "examples": [
            "Explique os padrões encontrados nos dados",
            "Interprete os resultados da análise",
            "Tire conclusões sobre o dataset",
            "Gere insights sobre as transações",
            "Recomende ações baseadas nos dados",
            "Analise profundamente o comportamento",
            "Comente os resultados encontrados",
            "Sugira melhorias na análise",
            "Discuta as descobertas",
            "Avalie a qualidade dos dados",
            "Explique o significado das variáveis",
            "Interprete as correlações"
        ],
        "keywords": ["explicar", "interpretar", "concluir", "insight", "recomendar",
                     "sugerir", "comentar", "discutir", "avaliar", "analisar",
                     "explain", "interpret", "conclude", "recommend", "suggest"],
        "priority": 7
    }
}


# ============================================================================
# FUNÇÕES DE POPULAÇÃO
# ============================================================================

def generate_intent_embeddings(
    intent_category: str,
    intent_data: Dict[str, Any],
    embedding_generator: EmbeddingGenerator
) -> List[Dict[str, Any]]:
    """
    Gera embeddings para todas as consultas exemplo de uma categoria.
    
    Args:
        intent_category: Nome da categoria (ex: 'statistical_analysis')
        intent_data: Dados da categoria (examples, keywords, priority)
        embedding_generator: Gerador de embeddings configurado
    
    Returns:
        Lista de dicionários com embedding e metadados
    """
    logger.info(f"🔄 Gerando embeddings para categoria: {intent_category}")
    
    results = []
    examples = intent_data["examples"]
    
    for i, example in enumerate(examples, 1):
        try:
            # Gerar embedding para o exemplo
            logger.debug(f"  Processando exemplo {i}/{len(examples)}: {example[:50]}...")
            embedding_result = embedding_generator.generate_embedding(example)
            
            # Preparar metadados
            metadata = {
                "category": intent_category,
                "description": intent_data["description"],
                "keywords": intent_data["keywords"],
                "priority": intent_data["priority"],
                "example_text": example,
                "created_at": datetime.now().isoformat(),
                "source": "intent_training",
                "version": "1.0"
            }
            
            # Preparar resultado
            result = {
                "chunk_text": example,  # Texto original
                "embedding": embedding_result.embedding,  # Vetor de embeddings
                "metadata": metadata,  # Metadados estruturados
                "source": f"intent_category:{intent_category}"
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar exemplo '{example[:50]}...': {str(e)}")
            continue
    
    logger.info(f"✅ Gerados {len(results)} embeddings para '{intent_category}'")
    return results


def store_intent_embeddings(
    embeddings_data: List[Dict[str, Any]],
    vector_store: VectorStore,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Armazena embeddings no VectorStore (Supabase).
    
    Args:
        embeddings_data: Lista de embeddings com metadados
        vector_store: VectorStore configurado
        batch_size: Tamanho do lote para inserção
    
    Returns:
        Estatísticas da inserção (sucesso, falhas, total)
    """
    logger.info(f"💾 Armazenando {len(embeddings_data)} embeddings no Supabase...")
    
    success_count = 0
    failure_count = 0
    
    # Processar em lotes
    for i in range(0, len(embeddings_data), batch_size):
        batch = embeddings_data[i:i + batch_size]
        logger.info(f"  Processando lote {i//batch_size + 1}: {len(batch)} embeddings")
        
        for item in batch:
            try:
                # Inserir no vector store
                vector_store.store_embedding(
                    chunk_text=item["chunk_text"],
                    embedding=item["embedding"],
                    metadata=item["metadata"],
                    source=item["source"]
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao armazenar embedding: {str(e)}")
                failure_count += 1
    
    stats = {
        "total": len(embeddings_data),
        "success": success_count,
        "failure": failure_count,
        "success_rate": (success_count / len(embeddings_data)) * 100 if embeddings_data else 0
    }
    
    logger.info(f"✅ Armazenamento concluído: {success_count} sucesso, {failure_count} falhas")
    return stats


def validate_intent_classification(
    vector_store: VectorStore,
    embedding_generator: EmbeddingGenerator,
    test_queries: List[Dict[str, str]]
) -> None:
    """
    Valida se a classificação de intenções está funcionando.
    
    Args:
        vector_store: VectorStore com embeddings de intenção
        embedding_generator: Gerador de embeddings
        test_queries: Lista de queries de teste com categoria esperada
    """
    logger.info("\n" + "="*80)
    logger.info("🧪 VALIDANDO CLASSIFICAÇÃO DE INTENÇÕES")
    logger.info("="*80 + "\n")
    
    correct = 0
    total = len(test_queries)
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        expected_category = test["expected_category"]
        
        logger.info(f"Teste {i}/{total}: {query}")
        logger.info(f"  Categoria esperada: {expected_category}")
        
        try:
            # Gerar embedding da query
            embedding_result = embedding_generator.generate_embedding(query)
            
            # Buscar correspondência no vector store
            results = vector_store.search_similar(
                query_embedding=embedding_result.embedding,
                similarity_threshold=0.5,
                limit=3
            )
            
            if results:
                top_result = results[0]
                detected_category = top_result.metadata.get("category", "unknown")
                similarity_score = top_result.similarity_score
                
                logger.info(f"  Categoria detectada: {detected_category}")
                logger.info(f"  Similaridade: {similarity_score:.3f}")
                
                if detected_category == expected_category:
                    logger.info("  ✅ CORRETO\n")
                    correct += 1
                else:
                    logger.warning(f"  ❌ INCORRETO (esperado: {expected_category})\n")
            else:
                logger.warning("  ⚠️ NENHUMA CORRESPONDÊNCIA ENCONTRADA\n")
                
        except Exception as e:
            logger.error(f"  ❌ Erro no teste: {str(e)}\n")
    
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    logger.info("="*80)
    logger.info(f"📊 RESULTADO DA VALIDAÇÃO: {correct}/{total} corretos ({accuracy:.1f}%)")
    logger.info("="*80 + "\n")


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal para popular o VectorStore com embeddings de intenções.
    
    FLUXO:
    1. Inicializa embedding generator e vector store
    2. Para cada categoria de intenção:
       - Gera embeddings dos exemplos
       - Armazena no Supabase com metadados
    3. Valida classificação com queries de teste
    4. Exibe estatísticas finais
    """
    logger.info("\n" + "="*80)
    logger.info("🚀 INICIANDO POPULAÇÃO DE EMBEDDINGS DE INTENÇÕES")
    logger.info("="*80 + "\n")
    
    try:
        # ============================================================================
        # ETAPA 1: INICIALIZAÇÃO
        # ============================================================================
        logger.info("📦 Inicializando componentes...")
        
        # Inicializar embedding generator (SENTENCE_TRANSFORMER para consistência)
        embedding_generator = EmbeddingGenerator(
            provider=EmbeddingProvider.SENTENCE_TRANSFORMER
        )
        logger.info("✅ EmbeddingGenerator inicializado")
        
        # Inicializar vector store
        vector_store = VectorStore()
        logger.info("✅ VectorStore inicializado\n")
        
        # ============================================================================
        # ETAPA 2: GERAÇÃO E ARMAZENAMENTO
        # ============================================================================
        logger.info(f"🔄 Processando {len(INTENT_CATEGORIES)} categorias de intenção...\n")
        
        all_embeddings = []
        category_stats = {}
        
        for category, data in INTENT_CATEGORIES.items():
            # Gerar embeddings para a categoria
            embeddings = generate_intent_embeddings(category, data, embedding_generator)
            all_embeddings.extend(embeddings)
            category_stats[category] = len(embeddings)
        
        logger.info(f"\n✅ Total de embeddings gerados: {len(all_embeddings)}\n")
        
        # Armazenar embeddings no Supabase
        storage_stats = store_intent_embeddings(all_embeddings, vector_store)
        
        logger.info(f"\n📊 ESTATÍSTICAS DE ARMAZENAMENTO:")
        logger.info(f"  Total: {storage_stats['total']}")
        logger.info(f"  Sucesso: {storage_stats['success']}")
        logger.info(f"  Falhas: {storage_stats['failure']}")
        logger.info(f"  Taxa de sucesso: {storage_stats['success_rate']:.1f}%\n")
        
        # ============================================================================
        # ETAPA 3: VALIDAÇÃO
        # ============================================================================
        
        # Queries de teste para validação
        test_queries = [
            {"query": "Qual a média de Amount?", "expected_category": "statistical_analysis"},
            {"query": "Mostre a mediana de V1", "expected_category": "statistical_analysis"},
            {"query": "Detecte fraudes no dataset", "expected_category": "fraud_detection"},
            {"query": "Identifique anomalias", "expected_category": "fraud_detection"},
            {"query": "Mostre o intervalo de valores", "expected_category": "data_distribution"},
            {"query": "Qual a distribuição de Time?", "expected_category": "data_distribution"},
            {"query": "Gere um histograma", "expected_category": "data_visualization"},
            {"query": "Crie um gráfico de barras", "expected_category": "data_visualization"},
            {"query": "Explique os padrões", "expected_category": "llm_generic"},
            {"query": "Interprete os resultados", "expected_category": "llm_generic"}
        ]
        
        validate_intent_classification(vector_store, embedding_generator, test_queries)
        
        # ============================================================================
        # ETAPA 4: RESUMO FINAL
        # ============================================================================
        logger.info("="*80)
        logger.info("✅ POPULAÇÃO DE EMBEDDINGS CONCLUÍDA COM SUCESSO!")
        logger.info("="*80)
        logger.info("\n📊 RESUMO POR CATEGORIA:")
        for category, count in category_stats.items():
            logger.info(f"  • {category}: {count} embeddings")
        
        logger.info(f"\n💡 PRÓXIMOS PASSOS:")
        logger.info("  1. Execute teste_integracao_semantic_router.py para validar roteamento")
        logger.info("  2. Monitore acurácia da classificação em produção")
        logger.info("  3. Adicione novas categorias conforme necessário")
        logger.info("\n💾 Os embeddings estão armazenados no Supabase e prontos para uso!\n")
        
    except Exception as e:
        logger.error(f"\n❌ ERRO FATAL: {str(e)}")
        logger.error("Verifique logs acima para detalhes do erro")
        raise


# ============================================================================
# INSTRUÇÕES PARA ADICIONAR NOVAS INTENÇÕES
# ============================================================================

"""
COMO ADICIONAR UMA NOVA CATEGORIA DE INTENÇÃO:

1. Adicione nova entrada em INTENT_CATEGORIES:

INTENT_CATEGORIES["nova_categoria"] = {
    "description": "Descrição clara da categoria",
    "examples": [
        "Exemplo de consulta 1",
        "Exemplo de consulta 2",
        # Adicione 10-15 exemplos variados
    ],
    "keywords": ["palavra1", "palavra2", "palavra3"],
    "priority": 8  # 1-10, onde 10 é mais alta
}

2. Execute o script:
   python scripts/populate_intent_embeddings.py

3. Valide a classificação:
   python teste_integracao_semantic_router.py

4. Adicione mapeamento em orchestrator_agent.py:
   route_mapping = {
       ...
       'nova_categoria': QueryType.NOVO_TIPO,
   }

DICAS:
- Use exemplos reais de como usuários fariam perguntas
- Varie a formulação das perguntas (afirmativa, interrogativa, imperativa)
- Inclua sinônimos e variações de palavras-chave
- Prioridade: 10 (crítico), 7-9 (importante), 4-6 (normal), 1-3 (baixa)
"""


if __name__ == "__main__":
    main()
