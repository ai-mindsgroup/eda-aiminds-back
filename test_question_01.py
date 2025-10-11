"""Script rápido para testar se a pergunta 01 funciona com os chunks analíticos."""
import os
from src.agent.rag_agent import RAGAgent
from src.settings import SUPABASE_URL, SUPABASE_KEY

# Configurar credenciais
os.environ['SUPABASE_URL'] = SUPABASE_URL
os.environ['SUPABASE_KEY'] = SUPABASE_KEY

def main():
    print("=" * 80)
    print("🧪 TESTE: Pergunta 01 - Tipos de Dados")
    print("=" * 80)
    
    # Criar agente
    print("\n📦 Inicializando agente RAG...")
    agent = RAGAgent()
    
    # Pergunta 01
    query = "Quais são os tipos de dados (numéricos, categóricos) das colunas do dataset?"
    print(f"\n❓ Pergunta: {query}")
    print("\n🔍 Buscando resposta...")
    
    try:
        # Processar consulta
        result = agent.process(query, context={'source_id': 'creditcard_full'})
        
        if result and 'response' in result:
            print("\n" + "=" * 80)
            print("✅ RESPOSTA OBTIDA:")
            print("=" * 80)
            print(result['response'])
            print("\n" + "=" * 80)
            print("✅ Teste concluído com sucesso!")
            print("=" * 80)
        else:
            print("\n❌ Nenhuma resposta obtida")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
