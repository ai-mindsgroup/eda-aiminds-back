import asyncio
import json
import sys
from pathlib import Path

# Garantir que o diretório raiz do projeto esteja no sys.path para permitir `import src`
root_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent(enable_csv_agent=True, enable_rag_agent=True, enable_data_processor=True)
    question = "Qual a distribuição de cada variável (histogramas, distribuições)?"
    print(f"Pergunta: {question}\n")
    result = await orchestrator.process_with_persistent_memory(question, context={}, session_id=None)
    print("Resultado:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
