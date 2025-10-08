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
2. Identifique todas as variáveis numéricas e categóricas mencionadas
3. Extraia estatísticas relevantes (média, desvio padrão, mínimo, máximo)
4. Formate a resposta EXATAMENTE conforme o modelo abaixo

MODELO DE RESPOSTA ESPERADO:

Pergunta feita: {question}

Olá! Aqui está uma análise dos tipos de variáveis presentes no seu conjunto de dados:

**Variáveis Numéricas**

- Time
- V1 a V28: Variáveis numéricas agrupadas, todas apresentam alta variabilidade.
- Amount

**Variáveis Categóricas**

- Class: Variável categórica com valores possíveis 0 e 1. Utilizada para indicar fraude ou não fraude.

**Estatísticas relevantes (coluna Amount):**
- Média: R$ [valor]
- Desvio padrão: R$ [valor]
- Valor mínimo: R$ [valor]
- Valor máximo: R$ [valor]

Se precisar de mais detalhes ou quiser analisar outra variável, é só perguntar!

IMPORTANTE: 
- Agrupe V1 a V28 como "V1 a V28", não liste individualmente
- Siga EXATAMENTE essa estrutura humanizada
- Não adicione análises extras ou interpretações não solicitadas
- Não mostre os chunks brutos na resposta
- Não mencione frequência de valores para variáveis categóricas
"""

def synthesize_response(chunks, question, use_llm=True):
    """
    Recebe lista de chunks e pergunta, retorna resposta consolidada.
    Se use_llm=True, usa LLM via camada de abstração. Senão, faz pós-processamento manual.
    """
    context = "\n\n".join(chunks)
    if use_llm:
        llm_manager = get_llm_manager()
        prompt = SYNTHESIS_PROMPT.format(question=question, chunks=context)
        # Usar o método chat do LLMManager
        response = llm_manager.chat(prompt, {})
        return response.get('content', 'Erro na síntese via LLM.')
    else:
        # Fallback manual: parsing inteligente e estruturado
        import re
        
        # Unificar todos os chunks
        full_text = "\n".join(chunks)
        
        # Extrair variáveis numéricas da seção "## Colunas Numéricas"
        num_vars = []
        numeric_section = re.search(r'## Colunas Numéricas.*?\n.*?\n.*?\n(.*?)(?=\n\s*##|\Z)', full_text, re.DOTALL)
        if numeric_section:
            table_content = numeric_section.group(1)
            # Extrair apenas nomes de colunas (primeira coluna da tabela)
            for line in table_content.split('\n'):
                if line.strip().startswith('|'):
                    # Pegar apenas o primeiro campo (nome da variável)
                    parts = line.split('|')
                    if len(parts) >= 2:
                        var_name = parts[1].strip()
                        # Validar: não deve ser header, separator ou valor numérico
                        if var_name and var_name not in ['', 'Coluna', 'Mínimo', 'Máximo', 'Média']:
                            if not re.match(r'^-+$', var_name):  # não é separator
                                if not var_name.replace('.', '').replace('-', '').isdigit():  # não é número puro
                                    if var_name not in num_vars:
                                        num_vars.append(var_name)
        
        # Extrair variáveis categóricas da seção "## Colunas Categóricas"
        cat_vars = []
        categoric_section = re.search(r'## Colunas Categóricas.*?\n.*?\n.*?\n(.*?)(?=\n\s*##|\Z)', full_text, re.DOTALL)
        if categoric_section:
            table_content = categoric_section.group(1)
            for line in table_content.split('\n'):
                if line.strip().startswith('|'):
                    parts = line.split('|')
                    if len(parts) >= 2:
                        var_name = parts[1].strip()
                        if var_name and var_name not in ['', 'Coluna', 'Valor', 'Mais', 'Frequente']:
                            if not re.match(r'^-+$', var_name):
                                if not var_name.replace('.', '').isdigit():
                                    if var_name not in cat_vars and var_name not in num_vars:
                                        cat_vars.append(var_name)
        
        # Fallback: se não encontrou Class nas tabelas, buscar diretamente
        if not cat_vars or 'Class' not in cat_vars:
            if '| Class |' in full_text:
                cat_vars.append('Class')
        
        # Extrair estatísticas da coluna Amount
        stats = {}
        amount_row = re.search(r'\|\s*Amount\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*[^|]*\|\s*[^|]*\|\s*([0-9.]+)\s*\|', full_text)
        if amount_row:
            try:
                stats['Amount'] = {
                    'Mínimo': f"R$ {float(amount_row.group(1)):.2f}",
                    'Máximo': f"R$ {float(amount_row.group(2)):.2f}",
                    'Média': f"R$ {float(amount_row.group(3)):.2f}",
                    'Desvio Padrão': f"R$ {float(amount_row.group(4)):.2f}"
                }
            except:
                pass
        
        # Agrupar variáveis V1-V28 para formatação compacta
        v_vars = [v for v in num_vars if re.match(r'^V\d+$', v)]
        other_num_vars = [v for v in num_vars if v not in v_vars]
        
        # Formatar resposta humanizada
        resposta = f"Pergunta feita: {question}\n\n"
        resposta += "Olá! Aqui está uma análise dos tipos de variáveis presentes no seu conjunto de dados:\n\n"
        
        # Variáveis numéricas (formatação compacta)
        if num_vars:
            resposta += "**Variáveis Numéricas**\n\n"
            if 'Time' in other_num_vars:
                resposta += "- Time\n"
            if v_vars:
                resposta += "- V1 a V28: Variáveis numéricas agrupadas, todas apresentam alta variabilidade.\n"
            if 'Amount' in other_num_vars:
                resposta += "- Amount\n"
            resposta += "\n"
        
        # Variáveis categóricas
        if cat_vars:
            resposta += "**Variáveis Categóricas**\n\n"
            for var in cat_vars:
                if var == 'Class':
                    resposta += "- Class: Variável categórica com valores possíveis 0 e 1. Utilizada para indicar fraude ou não fraude.\n"
                else:
                    resposta += f"- {var}\n"
            resposta += "\n"
        
        # Estatísticas
        if 'Amount' in stats:
            resposta += "**Estatísticas relevantes (coluna Amount):**\n"
            resposta += f"- Média: {stats['Amount']['Média']}\n"
            resposta += f"- Desvio padrão: {stats['Amount']['Desvio Padrão']}\n"
            resposta += f"- Valor mínimo: {stats['Amount']['Mínimo']}\n"
            resposta += f"- Valor máximo: {stats['Amount']['Máximo']}\n\n"
        
        resposta += "Se precisar de mais detalhes ou quiser analisar outra variável, é só perguntar!\n"
        
        return resposta
