#!/usr/bin/env python3
"""
Teste Completo do Sistema de Embeddings - EDA AI Minds
=====================================================

Script para testar geração, busca e armazenamento de embeddings.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import VectorStore
import pandas as pd
import tempfile

def test_embeddings_system():
    """Teste completo do sistema de embeddings."""
    print("🧮 TESTE DO SISTEMA DE EMBEDDINGS")
    print("=" * 50)
    
    try:
        # 1. Inicializar gerador de embeddings
        print("🔧 Inicializando gerador de embeddings...")
        generator = EmbeddingGenerator()
        print("✅ Gerador de embeddings inicializado")
        
        # 2. Testar geração de embeddings
        print("\n📝 Testando geração de embeddings...")
        test_texts = [
            "Análise de dados de cartão de crédito para detecção de fraude",
            "Transações suspeitas com valores altos em horários atípicos", 
            "Padrões de comportamento normal de clientes regulares",
            "Machine learning aplicado a segurança financeira"
        ]
        
        embeddings = []
        for text in test_texts:
            result = generator.generate_embedding(text)
            embeddings.append(result.embedding)
        
        print(f"✅ Embeddings gerados: {len(embeddings)} vetores de {len(embeddings[0])} dimensões")
        
        # 3. Testar vector store
        print("\n🗄️ Testando Vector Store...")
        vector_store = VectorStore()
        print("✅ Vector Store inicializado")
        
        # 4. Armazenar embeddings de teste
        print("\n💾 Armazenando embeddings de teste...")
        chunk_data = []
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            chunk_data.append({
                'chunk_text': text,
                'embedding': embedding,
                'metadata': {
                    'source': 'test_embeddings',
                    'chunk_id': i,
                    'type': 'test_data'
                }
            })
        
        # Simular armazenamento (sem inserir no banco real para teste)
        print(f"✅ Preparados {len(chunk_data)} chunks para armazenamento")
        for i, chunk in enumerate(chunk_data):
            print(f"   📄 Chunk {i+1}: {chunk['chunk_text'][:50]}...")
        
        # 5. Testar busca semântica
        print("\n🔍 Testando busca semântica...")
        query = "detecção de fraude em cartões"
        query_result = generator.generate_embedding(query)
        query_embedding = query_result.embedding
        
        print(f"🔍 Consulta: '{query}'")
        print(f"✅ Embedding da consulta gerado: {len(query_embedding)} dimensões")
        
        # 6. Calcular similaridades localmente (simulação)
        print("\n📊 Calculando similaridades...")
        import numpy as np
        
        similarities = []
        for i, chunk in enumerate(chunk_data):
            similarity = np.dot(query_embedding, chunk['embedding']) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk['embedding'])
            )
            similarities.append((i, similarity, chunk['chunk_text']))
        
        # Ordenar por similaridade
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print("🎯 Resultados mais similares:")
        for i, (chunk_id, similarity, text) in enumerate(similarities[:3]):
            score = similarity * 100
            print(f"   {i+1}. [{score:.1f}%] {text[:60]}...")
        
        # 7. Testar com dados CSV simulados
        print("\n📊 Testando com dados CSV...")
        csv_data = {
            'Time': [1, 2, 3, 4, 5],
            'V1': [-1.359, 1.191, -1.358, -0.966, -1.158],
            'Amount': [149.62, 2.69, 378.66, 123.50, 69.99],
            'Class': [0, 0, 0, 0, 1]
        }
        
        df = pd.DataFrame(csv_data)
        
        # Converter para texto para embeddings
        csv_texts = []
        for _, row in df.iterrows():
            text = f"Time: {row['Time']}, V1: {row['V1']:.3f}, Amount: {row['Amount']}, Class: {row['Class']}"
            csv_texts.append(text)
        
        csv_embeddings = []
        for text in csv_texts:
            result = generator.generate_embedding(text)
            csv_embeddings.append(result.embedding)
            
        print(f"✅ Embeddings de CSV gerados: {len(csv_embeddings)} vetores")
        
        for i, text in enumerate(csv_texts):
            print(f"   📄 Linha {i+1}: {text}")
        
        # 8. Verificar conexão com Supabase (se disponível)
        print("\n🔌 Testando conexão com Supabase...")
        try:
            # Gerar embedding para busca
            search_query = "fraude"
            search_result = generator.generate_embedding(search_query)
            search_embedding = search_result.embedding
            
            results = vector_store.search_similar(search_embedding, limit=3)
            print(f"✅ Busca no Supabase funcionando: {len(results)} resultados")
            
            for i, result in enumerate(results):
                print(f"   {i+1}. [{result.similarity_score:.2f}] {result.chunk_text[:50]}...")
                
        except Exception as e:
            print(f"⚠️ Conexão Supabase: {str(e)[:100]}")
        
        print("\n" + "=" * 50)
        print("🎉 TESTE DE EMBEDDINGS CONCLUÍDO!")
        print("📊 Funcionalidades testadas:")
        print("   ✅ Geração de embeddings")
        print("   ✅ Cálculo de similaridade")
        print("   ✅ Processamento de dados CSV")
        print("   ✅ Vector Store inicializado")
        print("   ✅ Busca semântica simulada")
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embeddings_system()