"""Agente especializado em análise de dados CSV.

Este agente combina:
- Pandas para manipulação de dados
- LangChain para g                if any(word in query_lower for word in ['correlação', 'correlation', 'relação']):
                    return self._handle_correlation_query(query, context)ação de código e análises
- LLM para interpretação e insights
- Matplotlib/Seaborn para visualizações
"""
from __future__ import annotations
import io
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

try:
    from langchain_experimental.agents import create_pandas_dataframe_agent
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("langchain-experimental não disponível, usando análise básica")

# Desabilitar Google GenAI por enquanto devido a conflitos de versão
GOOGLE_GENAI_AVAILABLE = False

from src.agent.base_agent import BaseAgent, AgentError
from src.settings import OPENAI_API_KEY


class CSVAnalysisAgent(BaseAgent):
    """Agente para análise inteligente de dados CSV."""
    
    def __init__(self):
        super().__init__(
            name="csv_analyzer",
            description="Especialista em análise de dados CSV com Pandas e LangChain"
        )
        self.current_df: Optional[pd.DataFrame] = None
        self.current_file_path: Optional[str] = None
        self.pandas_agent: Optional[Any] = None
        
        # Configurar LLM para análise de dados (desabilitado por enquanto)
        self.llm = None
        self.logger.info("Usando análise básica com Pandas (sem LLM)")
    
    def load_csv(self, file_path: str, **pandas_kwargs) -> Dict[str, Any]:
        """Carrega arquivo CSV e prepara para análise.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **pandas_kwargs: Argumentos adicionais para pd.read_csv()
        
        Returns:
            Informações sobre o dataset carregado
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            self.logger.info(f"Carregando CSV: {file_path}")
            
            # Configurações padrão para CSV
            default_kwargs = {
                'encoding': 'utf-8',
                'low_memory': False
            }
            default_kwargs.update(pandas_kwargs)
            
            # Carregar dados
            self.current_df = pd.read_csv(file_path, **default_kwargs)
            self.current_file_path = file_path
            
            # Criar agente Pandas se LLM disponível
            if self.llm and LANGCHAIN_AVAILABLE:
                self.pandas_agent = create_pandas_dataframe_agent(
                    self.llm,
                    self.current_df,
                    verbose=True,
                    allow_dangerous_code=True
                )
                self.logger.info("Agente Pandas criado com sucesso")
            else:
                self.logger.info("Agente Pandas não disponível (sem LLM ou langchain-experimental)")
            
            # Análise inicial
            info = self._analyze_dataset()
            
            return self._build_response(
                f"Dataset carregado com sucesso: {info['rows']} linhas, {info['columns']} colunas",
                metadata=info
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV: {str(e)}")
            raise AgentError(self.name, f"Falha ao carregar CSV: {str(e)}")
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta sobre os dados CSV.
        
        Args:
            query: Pergunta ou comando sobre os dados
            context: Contexto adicional (pode incluir file_path para carregar)
        
        Returns:
            Resposta com análise ou visualização
        """
        try:
            # Verificar se precisa carregar dados
            if context and 'file_path' in context and not self.current_df is not None:
                load_result = self.load_csv(context['file_path'])
                if 'error' in load_result:
                    return load_result
            
            if self.current_df is None:
                return self._build_response(
                    "Nenhum dataset carregado. Use context={'file_path': 'caminho.csv'} para carregar dados.",
                    metadata={"error": True}
                )
            
            # Determinar tipo de consulta
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['gráfico', 'plot', 'visualiz', 'chart']):
                return self._handle_visualization_query(query, context)
            elif any(word in query_lower for word in ['resumo', 'describe', 'info', 'overview']):
                return self._handle_summary_query(query, context)
            elif any(word in query_lower for word in ['correlação', 'correlation', 'relação']):
                return self._handle_correlation_query(query, context)
            else:
                return self._handle_general_query(query, context)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar consulta: {str(e)}")
            return self._build_response(
                f"Erro ao processar consulta: {str(e)}",
                metadata={"error": True}
            )
    
    def _analyze_dataset(self) -> Dict[str, Any]:
        """Análise inicial do dataset."""
        if self.current_df is None:
            return {}
        
        df = self.current_df
        
        # Informações básicas
        info = {
            "file_path": self.current_file_path,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
        }
        
        # Estatísticas básicas para colunas numéricas
        if info["numeric_columns"]:
            info["numeric_stats"] = df[info["numeric_columns"]].describe().to_dict()
        
        return info
    
    def _handle_visualization_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de visualização."""
        try:
            # Por ora, apenas sugestões de visualização
            numeric_cols = self.current_df.select_dtypes(include=['number']).columns
            categorical_cols = self.current_df.select_dtypes(include=['object']).columns
            
            suggestions = []
            
            if len(numeric_cols) >= 2:
                suggestions.append("📊 Scatter plot entre variáveis numéricas")
                suggestions.append("📈 Histograma das variáveis numéricas")
                
            if len(categorical_cols) > 0:
                suggestions.append("📊 Gráfico de barras para variáveis categóricas")
                
            if 'is_fraud' in self.current_df.columns or 'eh_fraude' in self.current_df.columns or 'Class' in self.current_df.columns:
                suggestions.append("🚨 Gráfico de distribuição de fraudes")
                
            response = "🎨 Sugestões de Visualização:\n" + "\n".join(f"• {s}" for s in suggestions)
            
            if not suggestions:
                response = "Não há colunas adequadas para visualização no dataset atual."
            
            return self._build_response(response, metadata={"visualization_suggestions": suggestions})
                
        except Exception as e:
            self.logger.error(f"Erro na visualização: {str(e)}")
            return self._build_response(
                f"Erro ao processar visualização: {str(e)}",
                metadata={"error": True}
            )
    
    def _handle_summary_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de resumo dos dados."""
        info = self._analyze_dataset()
        
        summary = f"""
        📊 **Resumo do Dataset**
        
        **Arquivo:** {info.get('file_path', 'N/A')}
        **Dimensões:** {info['rows']:,} linhas × {info['columns']} colunas
        
        **Colunas Numéricas ({len(info['numeric_columns'])}):**
        {', '.join(info['numeric_columns'])}
        
        **Colunas Categóricas ({len(info['categorical_columns'])}):**
        {', '.join(info['categorical_columns'])}
        
        **Valores Faltantes:**
        {self._format_missing_values(info['missing_values'])}
        
        **Uso de Memória:** {info['memory_usage'] / (1024*1024):.1f} MB
        """
        
        return self._build_response(summary, metadata=info)
    
    def _handle_correlation_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de correlação."""
        numeric_cols = self.current_df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) < 2:
            return self._build_response(
                "Não há colunas numéricas suficientes para análise de correlação.",
                metadata={"error": True}
            )
        
        # Calcular matriz de correlação
        corr_matrix = self.current_df[numeric_cols].corr()
        
        # Encontrar correlações mais altas
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:  # Correlações significativas
                    corr_pairs.append((col1, col2, corr_val))
        
        # Ordenar por valor absoluto
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        response = "🔗 **Análise de Correlação**\n\n"
        
        if corr_pairs:
            response += "**Correlações Significativas (|r| > 0.5):**\n"
            for col1, col2, corr in corr_pairs[:10]:  # Top 10
                emoji = "🔴" if corr > 0.7 else "🟡" if corr > 0.5 else "🔵"
                response += f"{emoji} {col1} ↔ {col2}: {corr:.3f}\n"
        else:
            response += "Nenhuma correlação significativa encontrada."
        
        return self._build_response(
            response,
            metadata={
                "correlation_matrix": corr_matrix.to_dict(),
                "significant_correlations": corr_pairs
            }
        )
    
    def _handle_general_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas gerais usando o agente Pandas."""
        try:
            if self.pandas_agent and LANGCHAIN_AVAILABLE:
                result = self.pandas_agent.invoke(query)
                return self._build_response(
                    str(result),
                    metadata={"pandas_agent_result": True}
                )
            else:
                # Fallback: análise básica com pandas puro
                self.logger.info("Usando análise básica (sem agente LangChain)")
                
                # Análises básicas baseadas na consulta
                query_lower = query.lower()
                
                if 'fraud' in query_lower or 'fraude' in query_lower:
                    return self._analyze_fraud_basic()
                elif 'count' in query_lower or 'quantos' in query_lower or 'quantidade' in query_lower:
                    return self._count_analysis()
                elif 'mean' in query_lower or 'média' in query_lower or 'average' in query_lower:
                    return self._mean_analysis()
                else:
                    # Resposta genérica com informações do dataset
                    info = self._analyze_dataset()
                    response = f"Dataset atual: {info['rows']} linhas, {info['columns']} colunas. " \
                              f"Para análises mais específicas, use consultas como: 'resumo', 'correlação', etc."
                    return self._build_response(response, metadata=info)
                
        except Exception as e:
            self.logger.error(f"Erro na consulta geral: {str(e)}")
            return self._build_response(
                f"Erro ao processar consulta: {str(e)}",
                metadata={"error": True}
            )
    
    def _analyze_fraud_basic(self) -> Dict[str, Any]:
        """Análise básica de fraude sem LLM."""
        # Tentar diferentes nomes de coluna de fraude
        fraud_cols = ['is_fraud', 'eh_fraude', 'fraud', 'fraude', 'Class', 'class', 'target', 'label']
        fraud_col = None
        
        for col in fraud_cols:
            if col in self.current_df.columns:
                fraud_col = col
                break
        
        if fraud_col:
            fraud_count = self.current_df[fraud_col].sum()
            total_count = len(self.current_df)
            fraud_rate = (fraud_count / total_count) * 100
            
            response = f"📊 Análise de Fraude:\n" \
                      f"• Total de transações: {total_count:,}\n" \
                      f"• Transações fraudulentas: {fraud_count:,}\n" \
                      f"• Taxa de fraude: {fraud_rate:.2f}%"
            
            return self._build_response(response, metadata={
                "fraud_count": fraud_count,
                "total_count": total_count,
                "fraud_rate": fraud_rate
            })
        else:
            return self._build_response("Coluna de fraude não encontrada no dataset. Colunas disponíveis: " + 
                                      ", ".join(self.current_df.columns.tolist()))
    
    def _count_analysis(self) -> Dict[str, Any]:
        """Análise de contagem."""
        info = self._analyze_dataset()
        response = f"📊 Contagens do Dataset:\n" \
                  f"• Total de registros: {info['rows']:,}\n" \
                  f"• Total de colunas: {info['columns']}\n" \
                  f"• Colunas numéricas: {len(info['numeric_columns'])}\n" \
                  f"• Colunas categóricas: {len(info['categorical_columns'])}"
        
        return self._build_response(response, metadata=info)
    
    def _mean_analysis(self) -> Dict[str, Any]:
        """Análise de médias."""
        numeric_cols = self.current_df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) == 0:
            return self._build_response("Não há colunas numéricas para calcular médias.")
        
        means = self.current_df[numeric_cols].mean()
        
        response = "📊 Médias das Colunas Numéricas:\n"
        for col, mean_val in means.items():
            response += f"• {col}: {mean_val:.2f}\n"
        
        return self._build_response(response, metadata={"means": means.to_dict()})
    
    def _format_missing_values(self, missing_dict: Dict[str, int]) -> str:
        """Formata informações de valores faltantes."""
        if not any(missing_dict.values()):
            return "✅ Nenhum valor faltante"
        
        result = ""
        for col, count in missing_dict.items():
            if count > 0:
                percentage = (count / len(self.current_df)) * 100
                result += f"• {col}: {count} ({percentage:.1f}%)\n"
        
        return result.strip()
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Retorna informações do dataset atual."""
        if self.current_df is None:
            return {"error": "Nenhum dataset carregado"}
        
        return self._analyze_dataset()
    
    def export_results(self, results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """Exporta resultados de análises para arquivo."""
        try:
            # Implementar exportação conforme necessário
            # Por ora, salvar como JSON
            import json
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            return self._build_response(
                f"Resultados exportados para: {output_path}",
                metadata={"export_path": output_path}
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar: {str(e)}")
            return self._build_response(
                f"Erro na exportação: {str(e)}",
                metadata={"error": True}
            )