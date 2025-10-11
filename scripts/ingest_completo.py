"""Script de Ingestão Completa - Creditcard.csv (284,807 registros)

CONFIGURAÇÃO OTIMIZADA PARA CARGA COMPLETA:
- Chunks grandes (500 linhas) para reduzir overhead
- Overlap mínimo (50 linhas) para manter contexto
- Processamento assíncrono com múltiplos workers
- Monitoramento de progresso detalhado
- Estimativa de tempo baseada em performance real

ESTIMATIVA: 1-3 horas para dataset completo
"""
from __future__ import annotations

import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main() -> int:
    print("\n" + "="*80)
    print("🚀 INGESTÃO COMPLETA - creditcard.csv (284,807 registros)")
    print("="*80 + "\n")
    
    # Configurações otimizadas para carga completa
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=8192,  # Chunks grandes de texto
        chunk_overlap=512,  # Overlap adequado
        csv_chunk_size_rows=500,  # 500 linhas por chunk (otimizado)
        csv_overlap_rows=50,  # 10% de overlap
    )
    
    print("✅ CONFIGURAÇÕES OTIMIZADAS PARA CARGA COMPLETA:")
    print(f"   • Linhas por chunk: 500 (máxima eficiência)")
    print(f"   • Overlap: 50 linhas (10% - preserva contexto)")
    print(f"   • Provider: Sentence Transformer (rápido e local)")
    print(f"   • Processamento: Assíncrono (múltiplos workers)")
    print(f"   • Batch embeddings: 30 (padrão)")
    print(f"   • Batch Supabase: 50 (padrão)")
    
    # Calcular estimativa de chunks
    total_lines = 284807  # Total exato do creditcard.csv
    chunk_step = 500 - 50  # chunk_size - overlap
    estimated_chunks = (total_lines // chunk_step) + 1
    
    print(f"\n📊 ESTIMATIVAS:")
    print(f"   • Total de linhas: {total_lines:,}")
    print(f"   • Chunks estimados: ~{estimated_chunks:,}")
    print(f"   • Tempo estimado: 1-3 horas (depende do hardware)")
    
    # Confirmar antes de iniciar
    print("\n⚠️  ATENÇÃO: Esta operação processará TODOS os {total_lines:,} registros.")
    print("   Certifique-se de que a tabela embeddings foi limpa antes de continuar.")
    
    # Pausar para confirmação (comentar para execução automática)
    # input("\nPressione ENTER para continuar ou Ctrl+C para cancelar...")
    
    print("\n🔄 Iniciando processamento completo...")
    print("-"*80)
    
    start_time = time.time()
    
    try:
        result = agent.ingest_csv_file(
            file_path="data/creditcard.csv",
            source_id="creditcard_complete_v1",
            encoding="utf-8",
            errors="ignore",
        )
        
        processing_time = time.time() - start_time
        
        content = result.get("content", "")
        metadata = result.get("metadata", {})
        
        print("\n" + "="*80)
        
        if metadata.get("error"):
            print("❌ FALHA NA INGESTÃO:")
            print(f"   {content}")
            return 1
        
        print("✅ INGESTÃO COMPLETA CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print(content)
        
        if metadata:
            print("\n📊 ESTATÍSTICAS FINAIS:")
            print("-"*80)
            
            chunks_created = metadata.get('chunks_created', 0)
            embeddings_generated = metadata.get('embeddings_generated', 0)
            embeddings_stored = metadata.get('embeddings_stored', 0)
            proc_time = metadata.get('processing_time', processing_time)
            
            print(f"   • Chunks criados:       {chunks_created:>10,}")
            print(f"   • Embeddings gerados:   {embeddings_generated:>10,}")
            print(f"   • Embeddings armazenados: {embeddings_stored:>10,}")
            print(f"   • Tempo total:          {proc_time:>10.1f}s ({proc_time/60:.1f} min)")
            
            # Calcular métricas de performance
            if chunks_created and proc_time:
                speed_chunks_sec = chunks_created / proc_time
                speed_chunks_min = speed_chunks_sec * 60
                speed_records_sec = (chunks_created * 500) / proc_time  # Estimativa de registros/s
                
                print(f"\n📈 PERFORMANCE:")
                print(f"   • Velocidade: {speed_chunks_sec:.2f} chunks/segundo")
                print(f"   • Velocidade: {speed_chunks_min:.1f} chunks/minuto")
                print(f"   • Registros/s: ~{speed_records_sec:.1f}")
            
            # Taxa de sucesso
            if embeddings_generated:
                success_rate = (embeddings_stored / embeddings_generated) * 100
                print(f"\n✅ TAXA DE SUCESSO: {success_rate:.2f}%")
                
                if success_rate < 100:
                    failed = embeddings_generated - embeddings_stored
                    print(f"   ⚠️  {failed} embeddings falharam no armazenamento")
            
            print("="*80)
        
        # Validação automática
        print("\n🔍 VALIDANDO CARGA...")
        print("-"*80)
        
        try:
            from verificar_carga_completa import verificar_carga_completa
            resultado_validacao = verificar_carga_completa("data/creditcard.csv")
            
            if resultado_validacao['completo']:
                print("\n🎉 VALIDAÇÃO CONCLUÍDA: Carga 100% completa!")
            else:
                print(f"\n⚠️  VALIDAÇÃO: {resultado_validacao['percentual']:.2f}% carregado")
                print(f"   Faltam {resultado_validacao['diferenca']:,} registros")
                
        except Exception as e:
            logger.warning(f"Não foi possível executar validação automática: {e}")
            print("\n   ℹ️  Execute manualmente: python verificar_carga_completa.py")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        processing_time = time.time() - start_time
        print(f"   Tempo decorrido: {processing_time:.1f}s ({processing_time/60:.1f} min)")
        return 130
        
    except Exception as e:
        logger.error(f"Erro durante ingestão: {e}")
        print(f"\n❌ ERRO: {e}")
        processing_time = time.time() - start_time
        print(f"   Tempo decorrido: {processing_time:.1f}s")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestão cancelada pelo usuário")
        raise SystemExit(130)
