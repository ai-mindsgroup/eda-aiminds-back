"""
Teste de visualização com auditoria completa
"""
import asyncio
from src.agent.rag_data_agent import RAGDataAgent

async def main():
    print("\n" + "="*80)
    print("🧪 TESTE: Visualização com Auditoria e Conformidade")
    print("="*80 + "\n")
    
    # Inicializar agente
    agent = RAGDataAgent()
    
    # Executar query com visualização
    result = await agent.process(
        'Qual a distribuição de cada variável (histogramas)?',
        context={'visualization_requested': True}
    )
    
    # Extrair metadados
    meta = result.get('metadata', {})
    
    print("\n" + "="*80)
    print("📊 RESULTADOS")
    print("="*80)
    
    # Gráficos gerados
    graficos = meta.get('graficos_gerados', [])
    print(f"\n✅ Gráficos gerados: {len(graficos)}")
    if graficos:
        print("\nPrimeiros 5 gráficos:")
        for i, g in enumerate(graficos[:5], 1):
            print(f"  {i}. {g}")
    
    # Exceção de conformidade
    print(f"\n🔐 Exceção de conformidade registrada: {'Sim ✅' if meta.get('conformidade_exception') else 'Não ❌'}")
    
    if meta.get('conformidade_exception'):
        exc = meta['conformidade_exception']
        print("\n📋 Detalhes da Exceção:")
        print(f"  • Tipo: {exc.get('type')}")
        print(f"  • Razão: {exc.get('reason')}")
        print(f"  • Aprovado: {'Sim ✅' if exc.get('approved') else 'Não ❌'}")
        print(f"  • Read-only: {'Sim ✅' if exc.get('read_only') else 'Não ❌'}")
        print(f"  • Padrão da indústria: {'Sim ✅' if exc.get('industry_standard') else 'Não ❌'}")
        print(f"  • CSV: {exc.get('csv_path')}")
        print(f"  • Tamanho: {exc.get('csv_size_mb')} MB")
        print(f"  • Documentação: {exc.get('documentation')}")
    
    # Chunks encontrados
    chunks_found = meta.get('chunks_found', 0)
    print(f"\n📦 Chunks de embeddings encontrados: {chunks_found}")
    
    # Método usado
    method = meta.get('method', 'N/A')
    print(f"🔧 Método: {method}")
    
    # Tempo de processamento
    proc_time = meta.get('processing_time_ms', 0)
    print(f"⏱️  Tempo de processamento: {proc_time}ms ({proc_time/1000:.2f}s)")
    
    print("\n" + "="*80)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*80 + "\n")
    
    # Mostrar trecho da resposta
    content = result.get('content', result.get('response', ''))
    if content:
        print("📝 Trecho da resposta:")
        print("-" * 80)
        print(content[:500])
        if len(content) > 500:
            print(f"\n... (mais {len(content) - 500} caracteres)")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main())
