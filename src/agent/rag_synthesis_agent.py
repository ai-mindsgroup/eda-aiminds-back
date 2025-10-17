"""
Agente de Síntese para respostas RAG no EDA AIMinds
- Recebe chunks recuperados do banco vetorial
- Usa LangChain + LLM (via camada de abstração) para gerar resposta consolidada
- Fallback manual para síntese se LLM indisponível
"""
from langchain_core.prompts import PromptTemplate
from src.llm.manager import get_llm_manager

# Prompt estruturado para síntese
SYNTHESIS_PROMPT = """Você é um assistente especializado em análise de dados. Sua tarefa é consolidar informações de múltiplos chunks de dados para responder de forma CLARA, HUMANIZADA e ESTRUTURADA à pergunta do usuário.
PERGUNTA DO USUÁRIO: {question}

DADOS RECUPERADOS DO BANCO VETORIAL:
{chunks}

INSTRUÇÕES OBRIGATÓRIAS:
1. Analise todos os chunks fornecidos e extraia as informações relevantes
2. Identifique todas as variáveis numéricas e categóricas realmente presentes nos dados
3. Extraia estatísticas relevantes (média, desvio padrão, mínimo, máximo) apenas para variáveis que existirem
4. Formate a resposta de forma clara, humanizada e estruturada, SEM mencionar colunas que não estejam nos dados

MODELO DE RESPOSTA ESPERADO:

Pergunta feita: {question}

Olá! Aqui está uma análise dos tipos de variáveis presentes no seu conjunto de dados:

**Variáveis Numéricas**
- [Liste apenas variáveis numéricas presentes nos chunks]

**Variáveis Categóricas**
- [Liste apenas variáveis categóricas presentes nos chunks]

**Estatísticas relevantes (se existirem):**
- Média: [valor]
- Desvio padrão: [valor]
- Valor mínimo: [valor]
- Valor máximo: [valor]
"""

def synthesize_response(chunks, question, use_llm=True):
    """Se use_llm=True, usa LLM via camada de abstração. Senão, faz pós-processamento manual."""
    if use_llm:
        # Lógica para usar LLM via LangChain
        llm_manager = get_llm_manager()
        prompt = PromptTemplate.from_template(SYNTHESIS_PROMPT)
        return llm_manager.generate(prompt, question=question, chunks="\n".join(chunks))
    else:
        import re
        full_text = "\n".join(chunks)
        # Tenta extrair colunas de tabelas markdown (| Coluna | ... |)
        num_vars = []
        cat_vars = []
        # Busca tabela de variáveis numéricas
        num_table_match = re.search(r'## Colunas Numéricas[\s\S]*?\| Coluna \|.*?\n((?:\|.*?\n)+)', full_text)
        if num_table_match:
            lines = num_table_match.group(1).split('\n')
            for line in lines:
                cols = [c.strip() for c in line.split('|') if c.strip()]
                if len(cols) > 0 and cols[0] != 'Coluna':
                    num_vars.append(cols[0])
        # Busca tabela de variáveis categóricas
        cat_table_match = re.search(r'## Colunas Categóricas[\s\S]*?\| Coluna \|.*?\n((?:\|.*?\n)+)', full_text)
        if cat_table_match:
            lines = cat_table_match.group(1).split('\n')
            for line in lines:
                cols = [c.strip() for c in line.split('|') if c.strip()]
                if len(cols) > 0 and cols[0] != 'Coluna':
                    cat_vars.append(cols[0])
        resposta = f"Pergunta feita: {question}\n\n"
        resposta += "Olá! Aqui está uma análise dos tipos de variáveis presentes no seu conjunto de dados:\n\n"
        resposta += "**Variáveis Numéricas**\n"
        for col in num_vars:
            resposta += f"- {col}\n"
        resposta += "\n**Variáveis Categóricas**\n"
        for col in cat_vars:
            resposta += f"- {col}\n"
        resposta += "\nSe precisar de mais detalhes ou quiser analisar outra variável, é só perguntar!\n"
        return resposta
