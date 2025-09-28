"""Teste completo do sistema de embeddings RAG.

Este script demonstra todo o pipeline:
1. Chunking de texto
2. Geração de embeddings  
3. Armazenamento vetorial
4. Busca por similaridade
5. Geração de respostas contextualizadas
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.rag_agent import RAGAgent
from src.embeddings.chunker import ChunkStrategy
from src.embeddings.generator import EmbeddingProvider


def create_sample_documents():
    """Cria documentos de exemplo para teste."""
    documents = {
        "fraudes_cartao": """
        ## Análise de Fraudes em Cartão de Crédito

        As fraudes em cartões de crédito são um problema crescente no setor financeiro. Os principais indicadores de transações fraudulentas incluem:

        ### Padrões Temporais
        - Transações realizadas entre 2h e 6h da manhã têm maior probabilidade de fraude
        - Múltiplas transações em horários incomuns para o cliente
        - Transações em dias da semana atípicos para o perfil do usuário

        ### Padrões Geográficos  
        - Transações em localizações distantes da residência habitual
        - Mudanças súbitas de localização (ex: compra em São Paulo seguida de compra em Miami em poucas horas)
        - Transações em países com alto índice de fraude

        ### Padrões Comportamentais
        - Valores muito acima ou muito abaixo do perfil histórico do cliente
        - Múltiplas tentativas de transação com valores decrescentes
        - Compras em categorias incomuns para o cliente (ex: cliente que só compra combustível fazendo compras em joalherias)

        ### Indicadores Técnicos
        - Falha na verificação do código CVV
        - Tentativas múltiplas com diferentes códigos de segurança
        - Transações online sem autenticação de dois fatores

        ### Métodos de Prevenção
        1. Machine Learning para detecção em tempo real
        2. Análise comportamental contínua
        3. Autenticação biométrica
        4. Limite dinâmico baseado em padrões históricos
        5. Alertas instantâneos para transações suspeitas
        """,
        
        "analise_dados": """
        ## Metodologias de Análise de Dados

        ### Análise Exploratória de Dados (EDA)
        A Análise Exploratória de Dados é fundamental para compreender a estrutura e padrões dos dados antes da modelagem.

        #### Técnicas Estatísticas Descritivas
        - Medidas de tendência central: média, mediana, moda
        - Medidas de dispersão: desvio padrão, variância, amplitude
        - Quartis e percentis para identificar outliers
        - Correlações entre variáveis numéricas

        #### Visualizações Essenciais
        - Histogramas para distribuições univariadas
        - Scatter plots para relações bivariadas  
        - Box plots para identificar outliers
        - Heat maps para matrizes de correlação

        ### Técnicas de Modelagem
        #### Modelos Supervisionados
        - Regressão Linear para previsões numéricas
        - Logística para classificação binária
        - Random Forest para problemas complexos
        - XGBoost para alta performance

        #### Modelos Não-supervisionados
        - K-means para clustering
        - PCA para redução de dimensionalidade
        - DBSCAN para detecção de anomalias

        ### Validação de Modelos
        - Cross-validation k-fold
        - Separação treino/validação/teste
        - Métricas: Accuracy, Precision, Recall, F1-Score
        - Curvas ROC e AUC para classificação
        """,
        
        "pandas_guia": """
        ## Guia Prático do Pandas

        ### Carregamento de Dados
        ```python
        import pandas as pd
        
        # CSV
        df = pd.read_csv('dados.csv')
        
        # Com parâmetros específicos
        df = pd.read_csv('dados.csv', encoding='utf-8', sep=';', decimal=',')
        
        # Excel
        df = pd.read_excel('planilha.xlsx', sheet_name='Dados')
        ```

        ### Exploração Inicial
        ```python
        # Informações gerais
        df.info()
        df.describe()
        df.head(10)
        df.tail(5)
        
        # Verificar valores faltantes
        df.isnull().sum()
        df.isna().any()
        ```

        ### Limpeza de Dados
        ```python
        # Remover valores faltantes
        df.dropna()  # Remove linhas com qualquer NaN
        df.dropna(subset=['coluna_importante'])  # Remove apenas se coluna específica for NaN
        
        # Preencher valores faltantes
        df.fillna(0)  # Preenche com zero
        df.fillna(df.mean())  # Preenche com média
        df.fillna(method='ffill')  # Forward fill
        ```

        ### Manipulação de Dados
        ```python
        # Filtros
        df[df['idade'] > 25]
        df[df['categoria'].isin(['A', 'B'])]
        df[(df['valor'] > 100) & (df['status'] == 'ativo')]
        
        # Agrupamentos
        df.groupby('categoria').sum()
        df.groupby(['categoria', 'regiao']).agg({'valor': 'mean', 'quantidade': 'sum'})
        ```

        ### Transformações
        ```python
        # Criar novas colunas
        df['valor_log'] = np.log(df['valor'])
        df['eh_alto'] = df['valor'] > df['valor'].quantile(0.8)
        
        # Aplicar funções
        df['categoria_upper'] = df['categoria'].str.upper()
        df['data_parsed'] = pd.to_datetime(df['data_texto'])
        ```
        """
    }
    
    return documents


def test_embedding_system():
    """Testa todo o sistema de embeddings."""
    print("🚀 TESTE COMPLETO DO SISTEMA RAG")
    print("=" * 60)
    
    # 1. Inicializar agente RAG
    print("🤖 Inicializando agente RAG...")
    
    try:
        rag_agent = RAGAgent(
            embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
            chunk_size=400,
            chunk_overlap=50
        )
        print("✅ Agente RAG inicializado")
    except Exception as e:
        print(f"❌ Erro na inicialização: {str(e)}")
        return
    
    # 2. Ingerir documentos
    documents = create_sample_documents()
    
    print(f"\n📚 Ingerindo {len(documents)} documentos...")
    
    ingest_results = []
    for doc_id, content in documents.items():
        print(f"\n📄 Processando: {doc_id}")
        
        result = rag_agent.ingest_text(
            text=content,
            source_id=doc_id,
            source_type="documentation",
            chunk_strategy=ChunkStrategy.PARAGRAPH
        )
        
        print(f"   {result['content']}")
        ingest_results.append(result)
    
    # 3. Estatísticas da base de conhecimento
    print(f"\n📊 Estatísticas da Base de Conhecimento:")
    stats_result = rag_agent.get_knowledge_base_stats()
    print(stats_result['content'])
    
    # 4. Teste de consultas RAG
    queries = [
        "Como identificar fraudes em cartões de crédito?",
        "Quais são os principais horários de fraude?", 
        "Como fazer análise exploratória de dados?",
        "Que métricas usar para validar modelos?",
        "Como carregar dados CSV no pandas?",
        "Como tratar valores faltantes no pandas?"
    ]
    
    print(f"\n🔍 TESTANDO CONSULTAS RAG")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Consulta {i}: {query}")
        print("-" * 50)
        
        # Configurar busca
        search_config = {
            'similarity_threshold': 0.3,  # Threshold mais baixo para mais resultados
            'max_results': 3,
            'include_context': True
        }
        
        result = rag_agent.process(query, context=search_config)
        
        print(result['content'])
        
        # Mostrar metadados interessantes
        metadata = result.get('metadata', {})
        if metadata and not metadata.get('error'):
            print(f"\n💡 Metadados:")
            print(f"   • Resultados encontrados: {metadata.get('search_results_count', 0)}")
            print(f"   • Fontes: {', '.join(metadata.get('sources_found', []))}")
            print(f"   • Tempo de processamento: {metadata.get('processing_time', 0):.2f}s")
            
            source_stats = metadata.get('source_stats', {})
            if source_stats:
                print(f"   • Estatísticas por fonte:")
                for source, stats in source_stats.items():
                    print(f"     - {source}: {stats['chunks']} chunks, similaridade máx: {stats['max_similarity']:.3f}")
    
    # 5. Teste de busca sem contexto (apenas resultados)
    print(f"\n🔎 TESTE DE BUSCA SEM CONTEXTO")
    print("-" * 40)
    
    search_only_result = rag_agent.process(
        "outliers pandas",
        context={
            'similarity_threshold': 0.2,
            'max_results': 5,
            'include_context': False  # Apenas busca, sem geração LLM
        }
    )
    
    print(search_only_result['content'])
    
    print(f"\n✅ TESTE COMPLETO CONCLUÍDO!")
    
    # Mostrar estatísticas finais
    final_stats = rag_agent.get_knowledge_base_stats()
    metadata = final_stats.get('metadata', {})
    total_embeddings = metadata.get('total_embeddings', 0)
    
    print(f"📈 Base de conhecimento final: {total_embeddings:,} embeddings armazenados")


if __name__ == "__main__":
    test_embedding_system()