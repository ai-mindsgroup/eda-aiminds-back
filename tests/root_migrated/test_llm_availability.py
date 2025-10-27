"""
Teste de Disponibilidade da Camada de Abstração de LLM
========================================================

Verifica quais provedores LLM estão disponíveis e funcionais.
"""

from src.llm.manager import get_llm_manager, LLMConfig
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_llm_abstraction():
    """Testa a camada de abstração de LLM."""
    print("\n" + "="*80)
    print("🧪 TESTE: Camada de Abstração de LLM")
    print("="*80)
    
    try:
        # Obter gerenciador (usa camada de abstração)
        print("\n1️⃣ Inicializando LLM Manager...")
        manager = get_llm_manager()
        print(f"   ✅ Manager inicializado")
        print(f"   ✅ Provedor ativo: {manager.active_provider.value}")
        
        # Verificar status de todos os provedores
        print("\n2️⃣ Status dos Provedores:")
        for provider, status in manager._provider_status.items():
            available = "✅" if status['available'] else "❌"
            print(f"   {available} {provider.value.upper()}: {status['message']}")
        
        # Teste de chamada simples
        print("\n3️⃣ Testando chamada LLM...")
        config = LLMConfig(temperature=0.1, max_tokens=50)
        response = manager.chat(
            prompt="Responda apenas 'OK' se você me entende",
            config=config
        )
        
        if response.success:
            print(f"   ✅ Chamada bem-sucedida!")
            print(f"   ✅ Provedor usado: {response.provider.value}")
            print(f"   ✅ Modelo: {response.model}")
            print(f"   ✅ Resposta: {response.content[:100]}")
            print(f"   ✅ Tempo: {response.processing_time:.2f}s")
            return True
        else:
            print(f"   ❌ Chamada falhou: {response.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_abstraction()
    
    print("\n" + "="*80)
    if success:
        print("✅ TESTE PASSOU: Camada de abstração funcionando corretamente")
    else:
        print("❌ TESTE FALHOU: Verifique configuração de API keys")
    print("="*80 + "\n")
    
    exit(0 if success else 1)
