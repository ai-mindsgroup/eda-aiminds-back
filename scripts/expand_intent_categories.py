"""
Script para Expansão Dinâmica de Categorias de Intenção no Classificador Semântico
=================================================================================

Este módulo permite:
- Detectar novas categorias/intentos a partir de logs reais e feedback dos usuários
- Gerar embeddings e atualizar o VectorStore/Supabase sem downtime
- Documentar e simular o processo de expansão com exemplos

Fluxo:
1. Coleta perguntas reais dos logs e feedback
2. Detecta padrões/categorias emergentes
3. Gera embeddings para exemplos dessas novas categorias
4. Atualiza VectorStore de forma incremental (sem afetar embeddings existentes)
5. Documenta e valida a expansão

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
# Função para detectar novas categorias a partir de logs e feedback
# ============================================================================

def detect_new_intent_categories(log_questions: List[str], feedback: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """
    Analisa perguntas dos logs e feedback para sugerir novas categorias de intenção.
    Args:
        log_questions: Lista de perguntas reais dos usuários
        feedback: Dicionário {pergunta: categoria_sugerida}
    Returns:
        Dicionário de novas categorias detectadas
    """
    # Simulação: Agrupa perguntas por palavras-chave e feedback
    # Na prática, pode usar clustering, LLM ou análise semântica
    new_categories = {}
    for question, category in feedback.items():
        if category not in new_categories:
            new_categories[category] = {
                "description": f"Categoria emergente detectada via feedback: {category}",
                "examples": [],
                "keywords": [],
                "priority": 7
            }
        new_categories[category]["examples"].append(question)
        # Extrai palavras-chave simples
        new_categories[category]["keywords"].extend([w for w in question.lower().split() if len(w) > 3])
    # Remove duplicatas
    for cat in new_categories:
        new_categories[cat]["keywords"] = list(set(new_categories[cat]["keywords"]))
    return new_categories

# ============================================================================
# Função para expandir e atualizar embeddings no VectorStore sem downtime
# ============================================================================

def expand_intent_embeddings(new_intent_categories: Dict[str, Dict[str, Any]], embedding_generator: EmbeddingGenerator, vector_store: VectorStore) -> Dict[str, Any]:
    """
    Gera embeddings para novas categorias e insere incrementalmente no VectorStore.
    Args:
        new_intent_categories: Dicionário de novas categorias
        embedding_generator: Instância do gerador de embeddings
        vector_store: Instância do VectorStore
    Returns:
        Estatísticas da expansão
    """
    logger.info("\n🔄 Expandindo categorias de intenção...")
    total = 0
    success = 0
    failed = 0
    for category, data in new_intent_categories.items():
        logger.info(f"  • Categoria detectada: {category}")
        for example in data["examples"]:
            try:
                # Gerar embedding
                embedding_result = embedding_generator.generate_embedding(example)
                # Adicionar metadados customizados ao chunk_metadata
                if embedding_result.chunk_metadata is None:
                    embedding_result.chunk_metadata = {}
                embedding_result.chunk_metadata.update({
                    "category": category,
                    "description": data["description"],
                    "keywords": data["keywords"],
                    "priority": data["priority"],
                    "example_text": example,
                    "created_at": datetime.now().isoformat(),
                    "source": "intent_expansion",
                    "version": "1.0"
                })
                # Inserir usando store_embeddings
                vector_store.store_embeddings([embedding_result], source_type="intent_expansion")
                success += 1
            except Exception as e:
                logger.error(f"❌ Falha ao inserir embedding: {str(e)}")
                failed += 1
            total += 1
    logger.info(f"✅ Expansão concluída: {success}/{total} inseridos com sucesso")
    return {"total": total, "success": success, "failed": failed}

# ============================================================================
# Função para simular expansão com exemplos não previstos
# ============================================================================

def simulate_expansion():
    """
    Simula o processo de expansão usando perguntas reais e feedback fictício.
    """
    # Exemplo de perguntas reais dos logs
    log_questions = [
        "Quais transações foram aprovadas por IA?",
        "Mostre clusters de comportamento de compra",
        "Existe padrão de recorrência nas fraudes?",
        "Quais variáveis influenciam o risco?",
        "Gere gráfico de dispersão temporal",
        "Quais clientes têm maior propensão a fraude?"
    ]
    # Feedback do usuário (simulado)
    feedback = {
        "Quais transações foram aprovadas por IA?": "ai_approval",
        "Mostre clusters de comportamento de compra": "behavior_clustering",
        "Existe padrão de recorrência nas fraudes?": "fraud_recurrence",
        "Quais variáveis influenciam o risco?": "risk_analysis",
        "Gere gráfico de dispersão temporal": "temporal_visualization",
        "Quais clientes têm maior propensão a fraude?": "fraud_propensity"
    }
    # Detecta novas categorias
    new_intents = detect_new_intent_categories(log_questions, feedback)
    logger.info("\nCategorias sugeridas:")
    for cat, data in new_intents.items():
        logger.info(f"  • {cat}: {data['description']}")
        logger.info(f"    Exemplos: {data['examples']}")
        logger.info(f"    Keywords: {data['keywords']}")
    # Inicializa componentes
    embedding_generator = EmbeddingGenerator(provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
    vector_store = VectorStore()
    # Expande embeddings
    stats = expand_intent_embeddings(new_intents, embedding_generator, vector_store)
    logger.info(f"\n📊 Estatísticas da expansão: {stats}")
    logger.info("\n💡 Novas categorias estão disponíveis para roteamento semântico!")

# ============================================================================
# Documentação do Processo
# ============================================================================
"""
Processo de Expansão Dinâmica:
-----------------------------
1. Coleta perguntas reais dos logs e feedback dos usuários
2. Detecta padrões/categorias emergentes (clustering, LLM, análise semântica)
3. Gera embeddings para exemplos dessas novas categorias
4. Atualiza VectorStore de forma incremental (sem afetar embeddings existentes)
5. Classificador semântico passa a reconhecer novas intenções automaticamente
6. Não há downtime: inserção é incremental, sem reindexação global
7. Para adicionar manualmente, basta incluir exemplos e rodar o script

Como simular expansão:
----------------------
- Edite a função simulate_expansion() com perguntas reais e feedback
- Execute: python scripts/expand_intent_categories.py
- Novas categorias serão inseridas e reconhecidas pelo roteador semântico

"""

if __name__ == "__main__":
    simulate_expansion()
