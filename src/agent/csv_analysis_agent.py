"""Agente especializado em análise de dados via tabela embeddings.

Este agente combina:
- Consulta exclusiva à tabela embeddings do Supabase
- Análise inteligente de dados estruturados armazenados como embeddings
- LLM para interpretação e insights baseados em embeddings
- Geração de análises sem acesso direto a arquivos CSV

NOTA CRÍTICA: Este agente NÃO acessa arquivos CSV diretamente.
Todos os dados vêm da tabela embeddings do Supabase.
"""
from __future__ import annotations
import json
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    from src.vectorstore.supabase_client import supabase
    SUPABASE_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    SUPABASE_AVAILABLE = False
    supabase = None
    print(f"⚠️ Supabase não disponível: {str(e)[:100]}...")

from src.agent.base_agent import BaseAgent, AgentError


class EmbeddingsAnalysisAgent(BaseAgent):
    """Agente para análise inteligente de dados via embeddings.
    
    CONFORMIDADE: Este agente acessa APENAS a tabela embeddings do Supabase.
    Jamais lê arquivos CSV diretamente para responder consultas.
    """
    
    def __init__(self):
        super().__init__(
            name="embeddings_analyzer",
            description="Especialista em análise de dados via tabela embeddings do Supabase",
            enable_memory=True  # Habilita sistema de memória
        )
        self.current_embeddings: List[Dict[str, Any]] = []
        self.dataset_metadata: Dict[str, Any] = {}
        
        # Cache de análises em memória local (otimização)
        self._analysis_cache: Dict[str, Any] = {}
        self._patterns_cache: Dict[str, Any] = {}
        
        if not SUPABASE_AVAILABLE:
            raise AgentError(self.name, "Supabase não disponível - necessário para acesso a embeddings")
        
        self.logger.info("Agente de análise via embeddings inicializado com sistema de memória")
    
    def _validate_embeddings_access_only(self) -> None:
        """Valida que o agente só acessa embeddings, nunca CSV diretamente."""
        if hasattr(self, 'current_df') or hasattr(self, 'current_file_path'):
            raise AgentError(
                self.name, 
                "VIOLAÇÃO CRÍTICA: Tentativa de acesso direto a CSV detectada"
            )
    
    def load_from_embeddings(self, 
                           dataset_filter: Optional[str] = None,
                           limit: int = 1000) -> Dict[str, Any]:
        """Carrega dados da tabela embeddings do Supabase para análise.
        
        Args:
            dataset_filter: Filtro opcional por dataset específico
            limit: Limite de embeddings para carregar
        
        Returns:
            Informações sobre os dados carregados dos embeddings
        """
        self._validate_embeddings_access_only()
        
        try:
            self.logger.info(f"Carregando dados da tabela embeddings (limite: {limit})")
            
            # Consultar tabela embeddings
            query = supabase.table('embeddings').select('chunk_text, metadata, created_at')
            
            if dataset_filter:
                query = query.eq('metadata->>source', dataset_filter)
            
            response = query.limit(limit).execute()
            
            if not response.data:
                return self._build_response(
                    "❌ Nenhum embedding encontrado na base de dados",
                    metadata={'embeddings_count': 0}
                )
            
            self.current_embeddings = response.data
            
            # Extrair metadados do dataset
            self.dataset_metadata = self._extract_dataset_metadata()
            
            # Análise inicial dos embeddings
            analysis = self._analyze_embeddings_data()
            
            return self._build_response(
                f"✅ Dados carregados: {len(self.current_embeddings)} embeddings encontrados",
                metadata=analysis
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar embeddings: {str(e)}")
            raise AgentError(self.name, f"Falha ao carregar dados dos embeddings: {str(e)}")
    
    def _extract_dataset_metadata(self) -> Dict[str, Any]:
        """Extrai metadados dos embeddings carregados."""
        if not self.current_embeddings:
            return {}
        
        sources = set()
        providers = set()
        chunk_types = set()
        dates = []
        
        for embedding in self.current_embeddings:
            metadata = embedding.get('metadata', {})
            sources.add(metadata.get('source', 'unknown'))
            providers.add(metadata.get('provider', 'unknown'))
            chunk_types.add(metadata.get('chunk_type', 'unknown'))
            
            if embedding.get('created_at'):
                dates.append(embedding['created_at'])
        
        return {
            'sources': list(sources),
            'providers': list(providers), 
            'chunk_types': list(chunk_types),
            'date_range': {
                'earliest': min(dates) if dates else None,
                'latest': max(dates) if dates else None
            },
            'total_embeddings': len(self.current_embeddings)
        }
    
    def _analyze_embeddings_data(self) -> Dict[str, Any]:
        """Análise dos dados dos embeddings carregados."""
        if not self.current_embeddings:
            return {}
        
        # Analisar conteúdo dos chunks
        chunk_texts = [emb['chunk_text'] for emb in self.current_embeddings]
        
        # Tentar detectar estrutura de dados CSV nos chunks
        detected_columns = set()
        numeric_patterns = []
        
        for chunk_text in chunk_texts[:50]:  # Analisar amostra
            # Buscar padrões de colunas/campos
            if ',' in chunk_text or '|' in chunk_text or '\t' in chunk_text:
                # Possível dados tabulares
                lines = chunk_text.split('\n')
                for line in lines[:3]:  # Primeiras linhas
                    if ',' in line:
                        parts = line.split(',')
                        for part in parts:
                            part = part.strip()
                            if part and len(part) < 50:  # Possível nome de coluna
                                detected_columns.add(part)
        
        return {
            'embeddings_count': len(self.current_embeddings),
            'dataset_metadata': self.dataset_metadata,
            'detected_columns': list(detected_columns)[:20],  # Limite
            'content_analysis': {
                'avg_chunk_length': np.mean([len(text) for text in chunk_texts]),
                'total_content_length': sum(len(text) for text in chunk_texts)
            }
        }
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta sobre dados via embeddings.
        
        Args:
            query: Pergunta ou comando sobre os dados
            context: Contexto adicional (pode incluir dataset_filter)
        
        Returns:
            Resposta com análise baseada em embeddings
        """
        self._validate_embeddings_access_only()
        
        try:
            # Verificar se precisa carregar embeddings
            if not self.current_embeddings:
                dataset_filter = context.get('dataset_filter') if context else None
                load_result = self.load_from_embeddings(dataset_filter=dataset_filter)
                if 'error' in load_result.get('metadata', {}):
                    return load_result
            
            if not self.current_embeddings:
                return self._build_response(
                    "❌ Nenhum embedding carregado. Verifique se há dados na tabela embeddings.",
                    metadata={"error": True, "conformidade": "embeddings_only"}
                )
            
            # Determinar tipo de consulta
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['resumo', 'describe', 'info', 'overview', 'summary']):
                return self._handle_summary_query_from_embeddings(query, context)
            elif any(word in query_lower for word in ['análise', 'analyze', 'estatística', 'statistics']):
                return self._handle_analysis_query_from_embeddings(query, context)
            elif any(word in query_lower for word in ['busca', 'search', 'procura', 'find']):
                return self._handle_search_query_from_embeddings(query, context)
            elif any(word in query_lower for word in ['contagem', 'count', 'quantos', 'quantidade']):
                return self._handle_count_query_from_embeddings(query, context)
            else:
                return self._handle_general_query_from_embeddings(query, context)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar consulta via embeddings: {str(e)}")
            return self._build_response(
                f"Erro ao processar consulta: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )
    
    # ========================================================================
    # MÉTODOS DE PROCESSAMENTO COM MEMÓRIA
    # ========================================================================
    
    async def process_with_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                                session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa consulta utilizando sistema de memória para cache de análises.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
            session_id: ID da sessão
            
        Returns:
            Resposta processada com cache otimizado
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Inicializar sessão de memória se necessário
            if session_id and self.has_memory:
                if not self._current_session_id or self._current_session_id != session_id:
                    await self.init_memory_session(session_id)
            elif not self._current_session_id and self.has_memory:
                await self.init_memory_session()
            
            # 2. Verificar cache de análises específicas
            analysis_key = self._generate_analysis_cache_key(query, context)
            cached_result = await self.recall_cached_analysis(analysis_key)
            
            if cached_result:
                self.logger.info(f"📦 Análise recuperada do cache: {analysis_key}")
                cached_result['metadata']['from_cache'] = True
                cached_result['metadata']['cache_key'] = analysis_key
                return cached_result
            
            # 3. Recuperar padrões de consulta aprendidos
            learned_patterns = await self.recall_learned_patterns()
            if learned_patterns:
                self.logger.debug(f"🧠 Aplicando {len(learned_patterns)} padrões aprendidos")
                context = context or {}
                context['learned_patterns'] = learned_patterns
            
            # 4. Processar consulta normalmente
            result = self.process(query, context)
            
            # 5. Calcular tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            result.setdefault('metadata', {})['processing_time_ms'] = processing_time_ms
            
            # 6. Salvar resultado no cache se significativo
            if self._should_cache_analysis(result, processing_time_ms):
                await self.remember_analysis_result(analysis_key, result, expiry_hours=12)
                self.logger.debug(f"💾 Análise salva no cache: {analysis_key}")
            
            # 7. Aprender padrões da consulta
            await self.learn_query_pattern(query, result)
            
            # 8. Salvar interação na memória
            if self.has_memory and self._current_session_id:
                await self.remember_interaction(
                    query=query,
                    response=result.get('content', str(result)),
                    processing_time_ms=processing_time_ms,
                    metadata=result.get('metadata', {})
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento com memória: {e}")
            # Fallback para processamento sem memória
            return self.process(query, context)
    
    # ========================================================================
    # MÉTODOS DE MEMÓRIA ESPECÍFICOS
    # ========================================================================
    
    def _generate_analysis_cache_key(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Gera chave única para cache de análise."""
        import hashlib
        
        # Normaliza query para cache
        normalized_query = query.lower().strip()
        
        # Adiciona contexto relevante
        context_str = ""
        if context:
            relevant_context = {
                'dataset_filter': context.get('dataset_filter'),
                'limit': context.get('limit'),
                'embeddings_count': len(self.current_embeddings)
            }
            context_str = str(sorted(relevant_context.items()))
        
        # Gera hash
        cache_input = f"{normalized_query}_{context_str}"
        return f"analysis_{hashlib.md5(cache_input.encode()).hexdigest()[:12]}"
    
    def _should_cache_analysis(self, result: Dict[str, Any], processing_time_ms: int) -> bool:
        """Determina se uma análise deve ser cacheada."""
        # Cachear se:
        # 1. Processamento demorado (> 500ms)
        # 2. Resultado significativo (tem metadados de análise)
        # 3. Não é erro
        
        if result.get('metadata', {}).get('error', False):
            return False
        
        if processing_time_ms > 500:
            return True
        
        metadata = result.get('metadata', {})
        has_analysis = any(key in metadata for key in [
            'embeddings_count', 'detected_columns', 'content_analysis'
        ])
        
        return has_analysis
    
    async def learn_query_pattern(self, query: str, result: Dict[str, Any]) -> None:
        """Aprende padrões de consulta para otimização futura."""
        if not self.has_memory or not self._current_session_id:
            return
        
        try:
            # Extrai características da consulta
            query_features = {
                'length': len(query),
                'words': len(query.split()),
                'type': self._classify_query_type(query),
                'embeddings_used': len(self.current_embeddings),
                'success': not result.get('metadata', {}).get('error', False)
            }
            
            # Salva padrão de aprendizado
            pattern_data = {
                'query_sample': query[:100],  # Trunca para privacidade
                'features': query_features,
                'result_type': result.get('metadata', {}).get('query_type', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            pattern_key = f"pattern_{self._classify_query_type(query)}"
            context_key = f"learning_patterns_{pattern_key}"
            
            # Salva na memória de contexto
            await self.remember_data_context(pattern_data, context_key)
            
            self.logger.debug(f"Padrão de consulta aprendido: {pattern_key}")
            
        except Exception as e:
            self.logger.debug(f"Erro ao aprender padrão: {e}")
    
    async def recall_learned_patterns(self) -> List[Dict[str, Any]]:
        """Recupera padrões de consulta aprendidos."""
        if not self.has_memory or not self._current_session_id:
            return []
        
        try:
            # Recupera contexto de aprendizado
            context = await self.recall_conversation_context(hours=168)  # 1 semana
            
            patterns = []
            for key, data in context.get('data_context', {}).items():
                if key.startswith('learning_patterns_'):
                    patterns.append(data)
            
            return patterns
            
        except Exception as e:
            self.logger.debug(f"Erro ao recuperar padrões: {e}")
            return []
    
    def _classify_query_type(self, query: str) -> str:
        """Classifica tipo de consulta para aprendizado."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['resumo', 'describe', 'info']):
            return 'summary'
        elif any(word in query_lower for word in ['análise', 'analyze', 'estatística']):
            return 'analysis'
        elif any(word in query_lower for word in ['busca', 'search', 'procura']):
            return 'search'
        elif any(word in query_lower for word in ['contagem', 'count', 'quantos']):
            return 'count'
        else:
            return 'general'
    
    def _handle_summary_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de resumo usando dados dos embeddings."""
        analysis = self._analyze_embeddings_data()
        
        summary = f"""📊 **Resumo dos Dados (via Embeddings)**
        
**Fonte:** Tabela embeddings do Supabase
**Total de Embeddings:** {analysis['embeddings_count']:,}
**Datasets Identificados:** {', '.join(self.dataset_metadata.get('sources', ['N/A']))}
**Tipos de Chunk:** {', '.join(self.dataset_metadata.get('chunk_types', ['N/A']))}

**Colunas Detectadas nos Dados:**
{', '.join(analysis.get('detected_columns', ['Nenhuma detectada']))}

**Análise de Conteúdo:**
• Tamanho médio dos chunks: {analysis['content_analysis']['avg_chunk_length']:.1f} caracteres
• Conteúdo total analisado: {analysis['content_analysis']['total_content_length']:,} caracteres

⚠️ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings
        """
        
        return self._build_response(summary, metadata={
            **analysis,
            'conformidade': 'embeddings_only',
            'query_type': 'summary'
        })
    
    def _handle_analysis_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de análise usando embeddings."""
        if not self.current_embeddings:
            return self._build_response("❌ Nenhum embedding disponível para análise")
        
        # Análise baseada no conteúdo dos chunks
        chunk_texts = [emb['chunk_text'] for emb in self.current_embeddings]
        
        # Tentar detectar padrões de fraude nos chunks
        fraud_indicators = 0
        transaction_indicators = 0
        
        for chunk_text in chunk_texts:
            chunk_lower = chunk_text.lower()
            if any(word in chunk_lower for word in ['fraud', 'fraude', 'suspeit', 'anormal']):
                fraud_indicators += 1
            if any(word in chunk_lower for word in ['transação', 'transaction', 'valor', 'amount']):
                transaction_indicators += 1
        
        response = f"""🔍 **Análise de Dados (via Embeddings)**
        
**Indicadores Encontrados:**
• Chunks com indicadores de fraude: {fraud_indicators}
• Chunks com indicadores de transação: {transaction_indicators}
• Total de chunks analisados: {len(chunk_texts)}

**Padrões Detectados:**
• {(fraud_indicators/len(chunk_texts)*100):.1f}% dos chunks contêm indicadores de fraude
• {(transaction_indicators/len(chunk_texts)*100):.1f}% dos chunks contêm dados transacionais
        """
        
        return self._build_response(response, metadata={
            'fraud_indicators': fraud_indicators,
            'transaction_indicators': transaction_indicators,
            'total_chunks': len(chunk_texts),
            'conformidade': 'embeddings_only'
        })
    
    def _handle_search_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de busca nos embeddings."""
        search_term = query.lower()
        
        # Buscar termo nos chunks
        matches = []
        for i, embedding in enumerate(self.current_embeddings):
            chunk_text = embedding['chunk_text'].lower()
            if any(term in chunk_text for term in search_term.split()):
                matches.append({
                    'index': i,
                    'chunk_preview': embedding['chunk_text'][:200] + '...',
                    'metadata': embedding.get('metadata', {})
                })
        
        if matches:
            response = f"🔍 **Resultados da Busca (via Embeddings)**\n\n"
            response += f"Encontrados {len(matches)} chunks relevantes:\n\n"
            
            for i, match in enumerate(matches[:5]):  # Limite de 5 resultados
                response += f"**Resultado {i+1}:**\n{match['chunk_preview']}\n\n"
        else:
            response = f"❌ Nenhum resultado encontrado para: '{query}'"
        
        return self._build_response(response, metadata={
            'matches_count': len(matches),
            'query': query,
            'conformidade': 'embeddings_only'
        })
    
    def _handle_count_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de contagem usando embeddings."""
        analysis = self._analyze_embeddings_data()
        
        response = f"""📊 **Contagens dos Dados (via Embeddings)**
        
• Total de embeddings: {analysis['embeddings_count']:,}
• Datasets identificados: {len(self.dataset_metadata.get('sources', []))}
• Tipos de chunk: {len(self.dataset_metadata.get('chunk_types', []))}
• Colunas detectadas: {len(analysis.get('detected_columns', []))}
        """
        
        return self._build_response(response, metadata={
            **analysis,
            'conformidade': 'embeddings_only'
        })
    
    def _handle_general_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas gerais usando embeddings."""
        if not self.current_embeddings:
            return self._build_response("❌ Nenhum embedding disponível")
        
        analysis = self._analyze_embeddings_data()
        
        response = f"""💡 **Informações Disponíveis (via Embeddings)**
        
Dados carregados: {analysis['embeddings_count']} embeddings
Datasets: {', '.join(self.dataset_metadata.get('sources', ['N/A']))}

**Para análises específicas, tente:**
• "resumo" - visão geral dos dados
• "análise" - análise de padrões
• "busca [termo]" - buscar conteúdo específico
• "contagem" - estatísticas básicas
        """
        
        return self._build_response(response, metadata={
            **analysis,
            'conformidade': 'embeddings_only',
            'suggestions': ['resumo', 'análise', 'busca', 'contagem']
        })
    
    def get_embeddings_info(self) -> Dict[str, Any]:
        """Retorna informações dos embeddings carregados.
        
        CONFORMIDADE: Apenas dados da tabela embeddings.
        """
        self._validate_embeddings_access_only()
        
        if not self.current_embeddings:
            return {"error": "Nenhum embedding carregado", "conformidade": "embeddings_only"}
        
        return {
            **self._analyze_embeddings_data(),
            'conformidade': 'embeddings_only',
            'agente': self.name
        }
    
    def validate_architecture_compliance(self) -> Dict[str, Any]:
        """Valida conformidade com arquitetura de embeddings-only.
        
        Returns:
            Relatório de conformidade
        """
        compliance_report = {
            'compliant': True,
            'violations': [],
            'data_source': 'embeddings_table_only',
            'csv_access': False,
            'agent_name': self.name
        }
        
        # Verificar se há vestígios de acesso a CSV
        forbidden_attributes = ['current_df', 'current_file_path', 'pandas_agent']
        for attr in forbidden_attributes:
            if hasattr(self, attr):
                compliance_report['compliant'] = False
                compliance_report['violations'].append(f"Atributo proibido encontrado: {attr}")
        
        # Verificar se usa apenas Supabase
        if not SUPABASE_AVAILABLE:
            compliance_report['compliant'] = False
            compliance_report['violations'].append("Supabase não disponível")
        
        return compliance_report
    
    def export_embeddings_analysis(self, output_path: str) -> Dict[str, Any]:
        """Exporta análise dos embeddings para arquivo.
        
        CONFORMIDADE: Exporta apenas dados derivados da tabela embeddings.
        """
        self._validate_embeddings_access_only()
        
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'agent': self.name,
                'conformidade': 'embeddings_only',
                'embeddings_analysis': self._analyze_embeddings_data(),
                'dataset_metadata': self.dataset_metadata,
                'compliance_report': self.validate_architecture_compliance()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            return self._build_response(
                f"✅ Análise de embeddings exportada para: {output_path}",
                metadata={
                    "export_path": output_path,
                    "conformidade": "embeddings_only"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar análise de embeddings: {str(e)}")
            return self._build_response(
                f"Erro na exportação: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )


# Alias para compatibilidade com código existente
# DEPRECATED: Use EmbeddingsAnalysisAgent diretamente
CSVAnalysisAgent = EmbeddingsAnalysisAgent