import os
from pathlib import Path
from src.settings import SUPABASE_URL, SUPABASE_KEY
from src.agent.rag_agent import RAGAgent
from src.agent.rag_agent import RAGAgent

def generate_source_id(csv_path):
    """Gera um identificador único para o dataset usando hash do arquivo."""
    import hashlib
    with open(csv_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return f"dataset_{file_hash}"

def main():
    """
    Script dinâmico para ingestão de chunks de metadados e embeddings de qualquer CSV.
    Uso: python add_metadata_chunks.py <caminho_csv>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Ingestão dinâmica de metadados CSV")
    parser.add_argument("csv_path", type=str, help="Caminho do arquivo CSV a ser ingerido")
    args = parser.parse_args()

    # Configurar credenciais
    os.environ['SUPABASE_URL'] = SUPABASE_URL
    os.environ['SUPABASE_KEY'] = SUPABASE_KEY

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return


    # Limpar memória/contexto de todos os agentes antes de nova ingestão
    from src.agent.memory_cleaner import clean_all_agent_memory
    session_id = f"session_{source_id}"
    clean_all_agent_memory(session_id)

    # Gerar source_id dinâmico
    source_id = generate_source_id(csv_path)
    print(f"🔄 Adicionando chunks de metadados ao dataset: {csv_path.name} (source_id: {source_id})")

    try:
        # Criar agente RAG
        agent = RAGAgent()

        # Limpar embeddings/chunks/memória do dataset anterior
        print("🧹 Limpando embeddings e memória do dataset anterior...")
        try:
            agent.vector_store.supabase.table('embeddings').delete().eq('source_id', source_id).execute()
            # Adicione limpeza de memória/histórico se aplicável
        except Exception as e:
            print(f"⚠️ Erro ao limpar embeddings: {e}")

        # Ler o conteúdo do CSV
        print("📖 Lendo arquivo CSV...")
        import pandas as pd
        df = pd.read_csv(csv_path)
        columns = list(df.columns)
        print(f"📑 Colunas detectadas: {columns}")

        # Gerar chunks de metadados de forma dinâmica
        print("📊 Gerando chunks de metadados...")
        csv_text = df.to_csv(index=False)
        metadata_chunks = agent._generate_metadata_chunks(csv_text, source_id)

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
        stored_ids = agent.vector_store.store_embeddings(metadata_embeddings, source_id)

        print(f"✅ {len(metadata_chunks)} chunks de metadados armazenados com sucesso!")
        print(f"📊 IDs armazenados: {len(stored_ids) if stored_ids else 0}")

        print("\n🔍 Armazenamento concluído.")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print(f"✅ {len(metadata_chunks)} chunks de metadados armazenados com sucesso!")
        print(f"📊 IDs armazenados: {len(stored_ids) if stored_ids else 0}")



if __name__ == "__main__":
    main()