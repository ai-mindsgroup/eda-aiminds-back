"""
⚠️ DEPRECADO - Use RAGAgent ao invés deste módulo

Agente de Ingestão Simplificado para EDA AIMinds
- Limpa base vetorial Supabase
- Analisa CSV e gera estatísticas descritivas e insights
- Chunking automático e inserção de embeddings
- Mantém tudo em memória, sem arquivos intermediários

❌ PROBLEMA: Esta implementação é SIMPLIFICADA e gera resultados inferiores:
- Apenas 2 chunks estatísticos básicos
- Metadata pobre (apenas {'source': path})
- Sem enriquecimento de contexto
- Sem estratégia CSV_ROW especializada

✅ SOLUÇÃO: Use src.agent.rag_agent.RAGAgent ao invés:
- Gera 6 chunks analíticos estruturados
- Metadata completo e rastreável
- Enriquecimento automático de contexto
- Estratégia CSV_ROW especializada para CSV
- Integração completa com sistema RAG

EXEMPLO DE USO CORRETO:
    from src.agent.rag_agent import RAGAgent
    from src.embeddings.generator import EmbeddingProvider
    
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        csv_chunk_size_rows=500,
        csv_overlap_rows=50
    )
    
    result = agent.ingest_csv_file(
        file_path="data/creditcard.csv",
        source_id="creditcard_v1",
        encoding="utf-8"
    )

Data de Deprecação: 2025-10-10
Documentação: docs/2025-10-10_ANALISE_CRITICA_INGESTAO.md
"""
import pandas as pd
from src.vectorstore.supabase_client import supabase
from src.embeddings.embedding_generator import generate_embedding
import numpy as np
import logging
import warnings

logger = logging.getLogger("eda.data_ingestor")

class DataIngestor:
    """
    ⚠️ DEPRECADO - Use RAGAgent ao invés
    
    Esta classe será removida em versões futuras.
    Use src.agent.rag_agent.RAGAgent para ingestão completa e robusta.
    """
    
    def __init__(self, supabase_client=None):
        # Emitir warning de deprecação
        warnings.warn(
            "\n"
            "⚠️ DEPRECADO: DataIngestor é uma implementação simplificada.\n"
            "Use RAGAgent para ingestão completa:\n"
            "  from src.agent.rag_agent import RAGAgent\n"
            "  agent = RAGAgent(csv_chunk_size_rows=500, csv_overlap_rows=50)\n"
            "  agent.ingest_csv_file(file_path, source_id)\n"
            "\n"
            "Motivos:\n"
            "  - DataIngestor: 2 chunks básicos, metadata pobre\n"
            "  - RAGAgent: 6 chunks analíticos, metadata completo\n"
            "\n"
            "Ver: docs/2025-10-10_ANALISE_CRITICA_INGESTAO.md",
            DeprecationWarning,
            stacklevel=2
        )
        self.supabase = supabase_client or supabase

    def clean_vector_db(self):
        logger.info("Limpando base vetorial Supabase...")
        self.supabase.table('embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        self.supabase.table('chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        self.supabase.table('metadata').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        logger.info("Base vetorial limpa com sucesso.")

    def analyze_csv(self, csv_path):
        df = pd.read_csv(csv_path)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        # Estatísticas numéricas
        num_stats = []
        for col in num_cols:
            stats = {
                'Coluna': col,
                'Mínimo': df[col].min(),
                'Máximo': df[col].max(),
                'Média': df[col].mean(),
                'Mediana': df[col].median(),
                'Moda': df[col].mode().iloc[0] if not df[col].mode().empty else '',
                'Desvio Padrão': df[col].std(),
                'Valores Nulos': df[col].isnull().sum()
            }
            num_stats.append(stats)
        # Estatísticas categóricas
        cat_stats = []
        for col in cat_cols:
            freq = df[col].value_counts(dropna=True)
            stats = {
                'Coluna': col,
                'Valor Mais Frequente': freq.idxmax() if not freq.empty else '',
                'Frequência': freq.max() if not freq.empty else '',
                'Valores Únicos': df[col].nunique(),
                'Valores Nulos': df[col].isnull().sum()
            }
            cat_stats.append(stats)
        # Insights
        insights = []
        for stat in num_stats:
            if stat['Desvio Padrão'] > stat['Média'] * 0.5:
                insights.append(f"A coluna '{stat['Coluna']}' apresenta alta variabilidade.")
            if stat['Valores Nulos'] > 0:
                insights.append(f"A coluna '{stat['Coluna']}' possui {stat['Valores Nulos']} valores nulos.")
        for stat in cat_stats:
            if stat['Frequência'] > 0 and stat['Frequência'] > df.shape[0] * 0.5:
                insights.append(f"A coluna '{stat['Coluna']}' está desbalanceada, com '{stat['Valor Mais Frequente']}' dominante.")
            if stat['Valores Nulos'] > 0:
                insights.append(f"A coluna '{stat['Coluna']}' possui {stat['Valores Nulos']} valores nulos.")
        # Markdown
        md = "# Análise Descritiva do Dataset\n\n## Colunas Numéricas\n\n| Coluna | Mínimo | Máximo | Média | Mediana | Moda | Desvio Padrão | Valores Nulos |\n|--------|--------|--------|-------|---------|------|---------------|---------------|\n"
        for stat in num_stats:
            md += f"| {stat['Coluna']} | {stat['Mínimo']} | {stat['Máximo']} | {stat['Média']:.2f} | {stat['Mediana']:.2f} | {stat['Moda']} | {stat['Desvio Padrão']:.2f} | {stat['Valores Nulos']} |\n"
        md += "\n## Colunas Categóricas\n\n| Coluna | Valor Mais Frequente | Frequência | Valores Únicos | Valores Nulos |\n|--------|---------------------|------------|----------------|---------------|\n"
        for stat in cat_stats:
            md += f"| {stat['Coluna']} | {stat['Valor Mais Frequente']} | {stat['Frequência']} | {stat['Valores Únicos']} | {stat['Valores Nulos']} |\n"
        md += "\n## Insights\n\n"
        for insight in insights:
            md += f"- {insight}\n"
        return md

    def chunk_text(self, text, max_length=2000, overlap=200):
        """
        Chunking inteligente com overlap para preservar contexto.
        Evita quebrar tabelas Markdown no meio.
        """
        chunks = []
        lines = text.split('\n')
        buffer = []
        size = 0
        
        for line in lines:
            buffer.append(line)
            size += len(line) + 1  # +1 para o \n
            
            # Se atingiu o tamanho máximo E não estamos no meio de uma tabela
            if size > max_length and not line.startswith('|'):
                chunks.append('\n'.join(buffer))
                # Manter overlap (últimas N linhas)
                overlap_lines = []
                overlap_size = 0
                for l in reversed(buffer):
                    if overlap_size < overlap:
                        overlap_lines.insert(0, l)
                        overlap_size += len(l) + 1
                    else:
                        break
                buffer = overlap_lines
                size = overlap_size
        
        # Adicionar último chunk se houver
        if buffer:
            chunks.append('\n'.join(buffer))
        
        return chunks

    def ingest_csv(self, csv_path):
        self.clean_vector_db()
        logger.info(f"Processando CSV: {csv_path}")
        md_text = self.analyze_csv(csv_path)
        chunks = self.chunk_text(md_text)
        logger.info(f"Gerando embeddings e inserindo {len(chunks)} chunks...")
        for chunk in chunks:
            embedding = generate_embedding(chunk)
            self.supabase.table('embeddings').insert({
                'chunk_text': chunk,
                'embedding': embedding,
                'metadata': {'source': csv_path}
            }).execute()
        logger.info("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    import sys
    csv_path = "data/creditcard.csv"
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    ingestor = DataIngestor()
    ingestor.ingest_csv(csv_path)
