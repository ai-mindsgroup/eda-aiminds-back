"""Script para modificar RAGAgent.ingest_csv_data() para ingestão DUAL (metadata + ROW + COLUMN)."""

import sys

def modify_rag_agent_dual_chunking():
    """Modifica o método ingest_csv_data() para suportar chunking duplo."""
    
    file_path = r"c:\workstashion\eda-aiminds-i2a2-rb\src\agent\rag_agent.py"
    
    # Ler arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # String a ser substituída (inicio)
    old_code_start = '# ✅ GERAR APENAS CHUNKS DE METADADOS ANALÍTICOS'
    old_code_end = 'return self._build_response(response, metadata=stats)'
    
    # Nova implementação
    new_code = '''# ✅ ESTRATÉGIA DUAL: GERAR CHUNKS DE METADATA + ROW + COLUMN
            all_chunks = []
            
            # 1. CHUNKS DE METADADOS ANALÍTICOS (6 chunks estruturados)
            self.logger.info("📊 Gerando chunks de metadados analíticos...")
            metadata_chunks = self._generate_metadata_chunks(csv_text, source_id)
            
            if not metadata_chunks:
                self.logger.warning("⚠️ Nenhum chunk de metadata foi criado")
            else:
                self.logger.info(f"✅ {len(metadata_chunks)} chunks de metadados criados")
                all_chunks.extend(metadata_chunks)
            
            # 2. CHUNKS POR LINHA (CSV_ROW strategy) - Dados completos linha a linha
            self.logger.info("📝 Gerando chunks por LINHA (CSV_ROW)...")
            from src.embeddings.chunker import ChunkStrategy
            row_chunks = self.chunker.chunk_text(
                text=csv_text,
                source_id=source_id,
                strategy=ChunkStrategy.CSV_ROW
            )
            
            if not row_chunks:
                self.logger.warning("⚠️ Nenhum chunk de linha foi criado")
            else:
                self.logger.info(f"✅ {len(row_chunks)} chunks de linhas criados")
                all_chunks.extend(row_chunks)
            
            # 3. CHUNKS POR COLUNA (CSV_COLUMN strategy) - Análise focada por coluna
            self.logger.info("📊 Gerando chunks por COLUNA (CSV_COLUMN)...")
            column_chunks = self.chunker.chunk_text(
                text=csv_text,
                source_id=source_id,
                strategy=ChunkStrategy.CSV_COLUMN
            )
            
            if not column_chunks:
                self.logger.warning("⚠️ Nenhum chunk de coluna foi criado")
            else:
                self.logger.info(f"✅ {len(column_chunks)} chunks de colunas criados")
                all_chunks.extend(column_chunks)
            
            # Validar se ao menos algum chunk foi criado
            if not all_chunks:
                return self._build_response(
                    "Nenhum chunk foi criado (metadata/row/column)",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ TOTAL: {len(all_chunks)} chunks criados (metadata={len(metadata_chunks)}, row={len(row_chunks)}, column={len(column_chunks)})")
            
            # Gerar embeddings para TODOS os chunks
            self.logger.info("🔢 Gerando embeddings para TODOS os chunks...")
            all_embeddings = self.embedding_generator.generate_embeddings_batch(all_chunks)
            
            if not all_embeddings:
                return self._build_response(
                    "Falha ao gerar embeddings para chunks",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ {len(all_embeddings)} embeddings gerados")
            
            # Armazenar embeddings no vector store
            self.logger.info("💾 Armazenando embeddings no vector store...")
            stored_ids = self.vector_store.store_embeddings(all_embeddings, "csv")
            
            processing_time = time.perf_counter() - start_time
            
            # Estatísticas consolidadas
            stats = {
                "source_id": source_id,
                "source_type": "csv_dual_chunking",
                "processing_time": processing_time,
                "metadata_chunks_created": len(metadata_chunks),
                "row_chunks_created": len(row_chunks),
                "column_chunks_created": len(column_chunks),
                "total_chunks_created": len(all_chunks),
                "total_embeddings_generated": len(all_embeddings),
                "total_embeddings_stored": len(stored_ids),
                "success_rate": len(stored_ids) / len(all_chunks) * 100 if all_chunks else 0
            }
            
            response = f"✅ Ingestão DUAL concluída para '{source_id}'\\n" \\
                      f"📊 Metadata: {len(metadata_chunks)} chunks\\n" \\
                      f"📝 Linhas: {len(row_chunks)} chunks\\n" \\
                      f"📊 Colunas: {len(column_chunks)} chunks\\n" \\
                      f"🔢 TOTAL: {len(all_chunks)} chunks → {len(all_embeddings)} embeddings → {len(stored_ids)} armazenados\\n" \\
                      f"⏱️ Processado em {processing_time:.2f}s"
            
            self.logger.info(f"✅ Ingestão DUAL concluída: {stats['success_rate']:.1f}% sucesso")
            
            return self._build_response(response, metadata=stats)'''
    
    # Encontrar o bloco a ser substituído
    start_idx = content.find(old_code_start)
    if start_idx == -1:
        print(f"❌ Não encontrou o início do código: {old_code_start}")
        return False
    
    # Encontrar o final do bloco (após a última linha que queremos substituir)
    end_marker = 'return self._build_response(response, metadata=stats)'
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"❌ Não encontrou o final do código")
        return False
    
    # Incluir o texto do end_marker na substituição
    end_idx += len(end_marker)
    
    # Montar novo conteúdo
    new_content = content[:start_idx] + new_code + content[end_idx:]
    
    # Salvar backup
    backup_path = file_path + '.backup_dual_chunking'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup salvo em: {backup_path}")
    
    # Salvar novo conteúdo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Arquivo modificado: {file_path}")
    print(f"📊 Implementação DUAL CHUNKING (metadata + ROW + COLUMN) adicionada!")
    return True

if __name__ == "__main__":
    success = modify_rag_agent_dual_chunking()
    sys.exit(0 if success else 1)
