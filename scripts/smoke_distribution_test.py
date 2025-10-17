from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Removido: agente obsoleto csv_analysis_agent.py
from src.tools.python_analyzer import PythonDataAnalyzer
from src.tools.graph_generator import GraphGenerator
from src.utils.logging_config import get_logger

logger = get_logger('smoke_test')

# Construir dummy agente (não executa __init__ que exige supabase)
class DummyAgent:
    pass

agent = DummyAgent()
agent.logger = logger

# Simular current_embeddings com chunk_text contendo header CSV + linhas
agent.current_embeddings = [
    {"chunk_text": '"A","B","C"\n"1","alpha","10"\n"2","beta","20"\n"3","alpha","15"'}
]

# Criar função _build_response simples
def _build_response(content, metadata=None):
    return {'content': content, 'metadata': metadata or {}}

agent._build_response = _build_response

# Preparar df usando PythonDataAnalyzer.parse_chunk_text (via parse helper)
analyzer = PythonDataAnalyzer()
full_text = "\n".join([emb.get('chunk_text', '') for emb in agent.current_embeddings])
# Preparar DataFrame de embeddings com coluna 'chunk_text' (formato esperado pelo parser)
import pandas as pd
embeddings_df = pd.DataFrame([{'chunk_text': full_text}])
df = analyzer._parse_chunk_text_to_dataframe(embeddings_df=embeddings_df)

print(f"Reconstructed df shape: {None if df is None else df.shape}")

# Monkeypatch a visualization handler that uses GraphGenerator to save histograms
from typing import Optional, Dict, Any

def fake_visualization_handler(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    gg = GraphGenerator(output_dir=Path('outputs/histogramas'))
    graficos = []
    estat = {}
    # Rebuild or retrieve df inside the handler to ensure availability
    df_local = analyzer.reconstruct_original_data()
    if df_local is None:
        # fallback to parsed df if available
        df_local = df

    if df_local is None:
        return {'metadata': {'graficos_gerados': [], 'estatisticas': {}, 'visualization_success': False}}

    numeric_cols = df_local.select_dtypes(include=['number']).columns.tolist()
    for col in numeric_cols:
        try:
            img_path, stats = gg.histogram(df_local, column=col, bins=10, return_base64=False)
            graficos.append(img_path)
            estat[col] = stats
        except Exception as e:
            print(f"Erro gerando gráfico para {col}: {e}")
    return {'metadata': {'graficos_gerados': graficos, 'estatisticas': estat, 'visualization_success': bool(graficos)}}

agent._handle_visualization_query = fake_visualization_handler

# Import the handler function and call it
# Removido: agente obsoleto csv_analysis_agent.py

# Call the distribution handler function unbound with our dummy agent
result = EmbeddingsAnalysisAgent._handle_distribution_query_from_embeddings(agent, "Qual a distribuição de cada variável (histogramas, distribuições)?", context={})

print('Result metadata:', result.get('metadata'))

# List generated files
out_dir = Path('outputs/histogramas')
if out_dir.exists():
    files = sorted([str(p) for p in out_dir.glob('*.png')])
    print('Generated files:', files)
else:
    print('No output dir found')
