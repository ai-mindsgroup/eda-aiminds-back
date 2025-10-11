"""
Stub seguro para geração de embeddings.
Adapte para usar o modelo real do projeto (LangChain, OpenAI, etc) se necessário.
"""
import numpy as np

def generate_embedding(text):
    # Exemplo: retorna vetor aleatório (substitua por integração real)
    # O tamanho deve ser igual ao usado no Supabase (ex: 1536)
        return np.random.rand(384).tolist()
