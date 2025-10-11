#!/usr/bin/env python3
"""
Script para adicionar chunks de metadados ao dataset creditcard já existente.
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.rag_agent import RAGAgent
from src.settings import SUPABASE_URL, SUPABASE_KEY

def main():
    # Configurar credenciais
    os.environ['SUPABASE_URL'] = SUPABASE_URL
    os.environ['SUPABASE_KEY'] = SUPABASE_KEY

    print("🔄 Adicionando chunks de metadados ao dataset creditcard...")

    try:
        # Criar agente RAG
        agent = RAGAgent()

        # Caminho do arquivo CSV
        csv_path = root_dir / "data" / "creditcard.csv"

        if not csv_path.exists():
            print(f"❌ Arquivo não encontrado: {csv_path}")
            return

        # Ler o conteúdo do CSV
        print("📖 Lendo arquivo CSV...")
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_text = f.read()

        # Gerar chunks de metadados
        print("📊 Gerando chunks de metadados...")
        metadata_chunks = agent._generate_metadata_chunks(csv_text, "creditcard_full")

        if not metadata_chunks:
            print("❌ Nenhum chunk de metadados gerado")
            return

        print(f"✅ {len(metadata_chunks)} chunks de metadados criados")

        # Gerar embeddings
        print("🧮 Gerando embeddings para chunks de metadados...")
        metadata_embeddings = agent.embedding_generator.generate_embeddings_batch(metadata_chunks)

        if not metadata_embeddings:
            print("❌ Falha ao gerar embeddings")
            return

        # Armazenar embeddings
        print("💾 Armazenando embeddings de metadados...")
        stored_ids = agent.vector_store.store_embeddings(metadata_embeddings, "csv")

        print(f"✅ {len(metadata_chunks)} chunks de metadados armazenados com sucesso!")
        print(f"📊 IDs armazenados: {len(stored_ids) if stored_ids else 0}")

        # Verificar se foram armazenados
        print("\\n🔍 Verificando armazenamento...")
        try:
            result = agent.vector_store.supabase.table('embeddings').select('count').eq('metadata->>source', 'creditcard_full').eq('metadata->>chunk_type', 'metadata_types').execute()
            count = len(result.data) if result.data else 0
            print(f"✅ Chunks de tipos armazenados: {count}")
        except Exception as e:
            print(f"⚠️ Erro na verificação: {e}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()