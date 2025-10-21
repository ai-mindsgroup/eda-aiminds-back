"""
Query Fragmenter - Fragmentação Inteligente de Queries Usando LLM
==================================================================

Usa LLMs para decidir como fragmentar queries grandes de forma inteligente,
selecionando colunas e segmentos relevantes baseados no contexto da pergunta.

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import json
from datetime import datetime

from src.utils.logging_config import get_logger
from src.llm.manager import LLMConfig
from src.llm.query_fragmentation import (
    QueryFragment,
    FragmentStrategy,
    TokenBudgetController,
    TokenBudget,
    get_fragmenter_llm
)

logger = get_logger(__name__)


class QueryFragmenter:
    """
    Fragmentador inteligente de queries usando LLM.
    
    Usa LLM para:
    1. Analisar a query do usuário e estrutura dos dados
    2. Decidir estratégia de fragmentação ideal
    3. Selecionar colunas/segmentos relevantes
    4. Gerar fragmentos otimizados respeitando orçamento de tokens
    """
    
    def __init__(self, token_budget: Optional[TokenBudget] = None):
        """
        Inicializa o fragmentador.
        
        Args:
            token_budget: Orçamento de tokens (usa padrão se None)
        """
        self.logger = get_logger(f"{__name__}.QueryFragmenter")
        self.llm_manager = get_fragmenter_llm()
        self.token_controller = TokenBudgetController(token_budget)
        
    async def analyze_fragmentation_need(
        self,
        query: str,
        df_info: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[FragmentStrategy]]:
        """
        Analisa se query precisa de fragmentação usando LLM.
        
        Args:
            query: Query do usuário
            df_info: Informações do DataFrame (shape, columns, dtypes)
            
        Returns:
            Tuple[bool, str, FragmentStrategy]: (needs_fragmentation, reason, strategy)
        """
        self.logger.info(f"🔍 Analisando necessidade de fragmentação para query...")
        
        # Estima tokens necessários
        num_rows, num_cols = df_info['shape']
        estimated_tokens = self.token_controller.estimate_dataframe_tokens(
            df_shape=(num_rows, num_cols),
            include_values=True
        )
        
        self.logger.info(
            f"   📊 Dataset: {num_rows} linhas, {num_cols} colunas"
        )
        self.logger.info(
            f"   🎯 Tokens estimados: {estimated_tokens} "
            f"(limite: {self.token_controller.budget.available_tokens})"
        )
        
        # Se cabe no orçamento, não precisa fragmentar
        if self.token_controller.budget.can_fit(estimated_tokens):
            self.logger.info("✅ Query cabe no orçamento - sem fragmentação necessária")
            return False, "Query cabe no orçamento de tokens", None
        
        # Precisa fragmentar - usa LLM para decidir estratégia
        prompt = f"""Você é um especialista em otimização de consultas de dados.

Analise a seguinte situação e decida a melhor estratégia de fragmentação:

**QUERY DO USUÁRIO:**
"{query}"

**INFORMAÇÕES DO DATASET:**
- Linhas: {num_rows}
- Colunas: {num_cols}
- Colunas disponíveis: {', '.join(df_info.get('columns', [])[:20])}{'...' if len(df_info.get('columns', [])) > 20 else ''}
- Tipos de dados: {json.dumps(df_info.get('dtypes_sample', {}), indent=2)}

**RESTRIÇÕES:**
- Tokens disponíveis: {self.token_controller.budget.available_tokens}
- Tokens necessários (estimado): {estimated_tokens}
- Excesso: {estimated_tokens - self.token_controller.budget.available_tokens} tokens

**ESTRATÉGIAS DISPONÍVEIS:**
1. **column_groups**: Divide por grupos de colunas relacionadas
   - Use quando: query precisa apenas de subconjunto de colunas
   - Exemplo: "Qual a correlação entre Amount e Time?" → só precisa dessas 2 colunas
   
2. **row_segments**: Divide por segmentos de linhas
   - Use quando: query precisa de todas as colunas mas pode processar em lotes
   - Exemplo: "Mostre todas as transações fraudulentas" → processa em batches

3. **hybrid**: Combina colunas + segmentos
   - Use quando: pode reduzir ambos
   - Exemplo: "Analise Amount e Time para 100k transações" → seleciona colunas E divide linhas

4. **time_windows**: Divide por janelas temporais
   - Use quando: dataset tem coluna temporal e query permite análise por períodos
   - Exemplo: "Padrões por mês" → processa mês a mês

**DECISÃO (JSON apenas, sem markdown):**
{{
    "strategy": "nome_da_estrategia",
    "reasoning": "explicação de 1-2 frases do porquê escolheu esta estratégia",
    "estimated_fragments": número estimado de fragmentos necessários,
    "confidence": 0.0-1.0
}}

JSON:"""

        try:
            config = LLMConfig(temperature=0.1, max_tokens=300)
            response = self.llm_manager.chat(prompt=prompt, config=config)
            
            if not response.success:
                self.logger.warning(f"LLM falhou, usando estratégia padrão: {response.error}")
                # Fallback: escolhe estratégia baseada em heurística
                if num_cols > 50:
                    return True, "Muitas colunas - fragmentação automática", FragmentStrategy.COLUMN_GROUPS
                else:
                    return True, "Muitas linhas - fragmentação automática", FragmentStrategy.ROW_SEGMENTS
            
            # Parse resposta JSON
            content = response.content.strip()
            # Remove markdown se presente
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            decision = json.loads(content)
            
            strategy = FragmentStrategy(decision['strategy'])
            reasoning = decision['reasoning']
            
            self.logger.info(f"🎯 Estratégia escolhida: {strategy.value}")
            self.logger.info(f"   💡 Razão: {reasoning}")
            self.logger.info(f"   📦 Fragmentos estimados: {decision.get('estimated_fragments', '?')}")
            self.logger.info(f"   🎲 Confiança: {decision.get('confidence', 0.0):.2f}")
            
            return True, reasoning, strategy
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar fragmentação: {str(e)}")
            # Fallback seguro
            return True, f"Erro na análise - usando fallback: {str(e)}", FragmentStrategy.ROW_SEGMENTS
    
    async def select_relevant_columns(
        self,
        query: str,
        available_columns: List[str],
        dtypes: Dict[str, str]
    ) -> List[str]:
        """
        Usa LLM para selecionar colunas relevantes para a query.
        
        Args:
            query: Query do usuário
            available_columns: Lista de colunas disponíveis
            dtypes: Tipos de dados das colunas
            
        Returns:
            Lista de colunas selecionadas
        """
        self.logger.info(f"🔍 Selecionando colunas relevantes para query...")
        
        prompt = f"""Você é um especialista em análise de dados.

Selecione APENAS as colunas estritamente necessárias para responder a query:

**QUERY:** "{query}"

**COLUNAS DISPONÍVEIS:**
{json.dumps([{'name': col, 'type': dtypes.get(col, 'unknown')} for col in available_columns], indent=2)}

**INSTRUÇÕES:**
1. Selecione APENAS colunas que serão USADAS na resposta
2. Não inclua colunas "por precaução" - seja preciso
3. Se a query pede "todas as informações", inclua todas
4. Se a query menciona colunas específicas, priorize apenas essas

**SELEÇÃO (JSON apenas):**
{{
    "selected_columns": ["col1", "col2", ...],
    "reasoning": "breve explicação da seleção"
}}

JSON:"""

        try:
            config = LLMConfig(temperature=0.1, max_tokens=400)
            response = self.llm_manager.chat(prompt=prompt, config=config)
            
            if not response.success:
                self.logger.warning("LLM falhou, usando todas as colunas")
                return available_columns
            
            # Parse resposta
            content = response.content.strip()
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            selection = json.loads(content)
            selected = selection['selected_columns']
            
            # Valida que colunas existem
            valid_columns = [col for col in selected if col in available_columns]
            
            if not valid_columns:
                self.logger.warning("Nenhuma coluna válida selecionada, usando todas")
                return available_columns
            
            self.logger.info(f"✅ {len(valid_columns)}/{len(available_columns)} colunas selecionadas")
            self.logger.info(f"   💡 Razão: {selection.get('reasoning', 'N/A')}")
            self.logger.info(f"   📋 Colunas: {', '.join(valid_columns[:10])}{'...' if len(valid_columns) > 10 else ''}")
            
            return valid_columns
            
        except Exception as e:
            self.logger.error(f"Erro ao selecionar colunas: {str(e)}")
            return available_columns
    
    async def create_fragments(
        self,
        query: str,
        df_info: Dict[str, Any],
        strategy: FragmentStrategy
    ) -> List[QueryFragment]:
        """
        Cria fragmentos baseado na estratégia escolhida.
        
        Args:
            query: Query do usuário
            df_info: Informações do DataFrame
            strategy: Estratégia de fragmentação
            
        Returns:
            Lista de fragmentos criados
        """
        self.logger.info(f"📦 Criando fragmentos com estratégia: {strategy.value}")
        
        fragments = []
        num_rows, num_cols = df_info['shape']
        all_columns = df_info['columns']
        
        if strategy == FragmentStrategy.COLUMN_GROUPS:
            # Seleciona colunas relevantes primeiro
            selected_columns = await self.select_relevant_columns(
                query=query,
                available_columns=all_columns,
                dtypes=df_info.get('dtypes', {})
            )
            
            # Calcula quantas colunas cabem por fragmento
            max_rows_per_fragment = self.token_controller.calculate_max_rows(len(selected_columns))
            
            if num_rows <= max_rows_per_fragment:
                # Um único fragmento com colunas selecionadas
                fragment = QueryFragment(
                    fragment_id=f"frag_cols_0",
                    strategy=strategy,
                    columns=selected_columns,
                    row_range=(0, num_rows),
                    estimated_tokens=self.token_controller.estimate_dataframe_tokens(
                        (num_rows, len(selected_columns))
                    )
                )
                fragments.append(fragment)
            else:
                # Divide em segmentos de linhas também
                num_segments = (num_rows + max_rows_per_fragment - 1) // max_rows_per_fragment
                for i in range(num_segments):
                    start_row = i * max_rows_per_fragment
                    end_row = min((i + 1) * max_rows_per_fragment, num_rows)
                    
                    fragment = QueryFragment(
                        fragment_id=f"frag_cols_{i}",
                        strategy=strategy,
                        columns=selected_columns,
                        row_range=(start_row, end_row),
                        estimated_tokens=self.token_controller.estimate_dataframe_tokens(
                            (end_row - start_row, len(selected_columns))
                        )
                    )
                    fragments.append(fragment)
        
        elif strategy == FragmentStrategy.ROW_SEGMENTS:
            # Usa todas as colunas, divide apenas linhas
            max_rows_per_fragment = self.token_controller.calculate_max_rows(num_cols)
            num_segments = (num_rows + max_rows_per_fragment - 1) // max_rows_per_fragment
            
            for i in range(num_segments):
                start_row = i * max_rows_per_fragment
                end_row = min((i + 1) * max_rows_per_fragment, num_rows)
                
                fragment = QueryFragment(
                    fragment_id=f"frag_rows_{i}",
                    strategy=strategy,
                    columns=all_columns,
                    row_range=(start_row, end_row),
                    estimated_tokens=self.token_controller.estimate_dataframe_tokens(
                        (end_row - start_row, num_cols)
                    )
                )
                fragments.append(fragment)
        
        elif strategy == FragmentStrategy.HYBRID:
            # Seleciona colunas E divide linhas
            selected_columns = await self.select_relevant_columns(
                query=query,
                available_columns=all_columns,
                dtypes=df_info.get('dtypes', {})
            )
            
            max_rows_per_fragment = self.token_controller.calculate_max_rows(len(selected_columns))
            num_segments = (num_rows + max_rows_per_fragment - 1) // max_rows_per_fragment
            
            for i in range(num_segments):
                start_row = i * max_rows_per_fragment
                end_row = min((i + 1) * max_rows_per_fragment, num_rows)
                
                fragment = QueryFragment(
                    fragment_id=f"frag_hybrid_{i}",
                    strategy=strategy,
                    columns=selected_columns,
                    row_range=(start_row, end_row),
                    estimated_tokens=self.token_controller.estimate_dataframe_tokens(
                        (end_row - start_row, len(selected_columns))
                    )
                )
                fragments.append(fragment)
        
        elif strategy == FragmentStrategy.TIME_WINDOWS:
            # TODO: Implementar fragmentação por janelas temporais
            # Requer análise de coluna temporal
            self.logger.warning("TIME_WINDOWS ainda não implementado, usando ROW_SEGMENTS")
            return await self.create_fragments(query, df_info, FragmentStrategy.ROW_SEGMENTS)
        
        # Valida todos os fragmentos
        for fragment in fragments:
            valid, msg = self.token_controller.validate_fragment(fragment)
            if not valid:
                self.logger.error(f"❌ Fragmento inválido: {msg}")
                fragment.metadata['validation_error'] = msg
        
        self.logger.info(f"✅ {len(fragments)} fragmentos criados")
        for i, frag in enumerate(fragments[:5]):  # Log apenas primeiros 5
            self.logger.info(
                f"   📦 {frag.fragment_id}: "
                f"{len(frag.columns or [])} cols, "
                f"{frag.row_range[1] - frag.row_range[0] if frag.row_range else '?'} rows, "
                f"~{frag.estimated_tokens} tokens"
            )
        if len(fragments) > 5:
            self.logger.info(f"   ... e mais {len(fragments) - 5} fragmentos")
        
        return fragments


async def fragment_query(
    query: str,
    df: pd.DataFrame,
    token_budget: Optional[TokenBudget] = None
) -> Tuple[bool, List[QueryFragment], str]:
    """
    Função helper para fragmentar uma query.
    
    Args:
        query: Query do usuário
        df: DataFrame a ser fragmentado
        token_budget: Orçamento de tokens (opcional)
        
    Returns:
        Tuple[bool, List[QueryFragment], str]: (needs_fragmentation, fragments, reason)
    """
    fragmenter = QueryFragmenter(token_budget)
    
    # Prepara informações do DataFrame
    df_info = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'dtypes_sample': {col: str(dtype) for col, dtype in list(df.dtypes.items())[:10]}
    }
    
    # Analisa necessidade
    needs_frag, reason, strategy = await fragmenter.analyze_fragmentation_need(query, df_info)
    
    if not needs_frag:
        return False, [], reason
    
    # Cria fragmentos
    fragments = await fragmenter.create_fragments(query, df_info, strategy)
    
    return True, fragments, reason
