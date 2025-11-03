"""
🔍 SANDBOX MONITOR - Sistema de Monitoramento de Execuções

Coleta métricas detalhadas de cada execução do sandbox seguro e
persiste no Supabase para análise histórica.

Métricas coletadas:
- Tempo de execução (ms)
- Uso de memória (MB)
- Status (sucesso/falha)
- Tipo de erro
- Código executado (hash)
- Timestamp

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
"""

import time
import hashlib
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.logging_config import get_logger
from src.vectorstore.supabase_client import supabase

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS E DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════

class ExecutionStatus(Enum):
    """Status de execução do sandbox."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"


@dataclass
class SandboxMetrics:
    """Métricas de uma execução do sandbox."""
    
    # Identificação
    execution_id: str
    timestamp: datetime
    
    # Código executado
    code_hash: str
    code_length: int
    
    # Resultado
    status: ExecutionStatus
    success: bool
    
    # Performance
    execution_time_ms: float
    memory_used_mb: float
    memory_peak_mb: float
    
    # Configuração
    timeout_limit_s: int
    memory_limit_mb: int
    
    # Erro (se houver)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata adicional
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para persistência."""
        data = asdict(self)
        # Persistir status em UPPERCASE para compatibilidade com constraints antigas do BD
        # e manter consistência de valores. Ex.: success -> SUCCESS
        try:
            data['status'] = str(self.status.value).upper()
        except Exception:
            # Fallback defensivo caso status não seja Enum por alguma razão
            data['status'] = str(self.status).upper()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# METRICS COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════

class MetricsCollector:
    """
    Coletor de métricas para execuções do sandbox.
    
    Uso:
        collector = MetricsCollector()
        
        # No início da execução
        collector.start_execution(code="resultado = 42")
        
        # No fim da execução
        metrics = collector.end_execution(
            result={'success': True, 'result': 42, ...}
        )
    """
    
    def __init__(self):
        """Inicializa coletor de métricas."""
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.code: Optional[str] = None
        self.execution_id: Optional[str] = None
        self.process = psutil.Process()
    
    def start_execution(self, code: str, execution_id: Optional[str] = None) -> str:
        """
        Inicia coleta de métricas para uma execução.
        
        Args:
            code: Código Python a ser executado
            execution_id: ID customizado (opcional)
            
        Returns:
            ID da execução
        """
        self.start_time = time.time()
        self.code = code
        
        # Memória inicial
        try:
            mem_info = self.process.memory_info()
            self.start_memory = mem_info.rss / (1024 * 1024)  # MB
        except:
            self.start_memory = 0.0
        
        # Gerar execution_id se não fornecido
        if execution_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:8]
            self.execution_id = f"exec_{timestamp}_{code_hash}"
        else:
            self.execution_id = execution_id
        
        logger.debug(f"📊 Iniciando coleta de métricas: {self.execution_id}")
        
        return self.execution_id
    
    def end_execution(
        self,
        result: Dict[str, Any],
        timeout_limit_s: int = 10,
        memory_limit_mb: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SandboxMetrics:
        """
        Finaliza coleta de métricas e cria objeto SandboxMetrics.
        
        Args:
            result: Resultado da execução do sandbox
            timeout_limit_s: Limite de timeout configurado
            memory_limit_mb: Limite de memória configurado
            metadata: Metadata adicional
            
        Returns:
            Objeto SandboxMetrics completo
        """
        if self.start_time is None:
            raise RuntimeError("start_execution() não foi chamado")
        
        # Calcular tempo de execução
        execution_time_ms = (time.time() - self.start_time) * 1000
        
        # Memória final e pico
        try:
            mem_info = self.process.memory_info()
            memory_current = mem_info.rss / (1024 * 1024)  # MB
            memory_peak = memory_current  # Simplificado
            memory_used = max(0, memory_current - self.start_memory)
        except:
            memory_current = 0.0
            memory_peak = 0.0
            memory_used = 0.0
        
        # Determinar status
        if result.get('success'):
            status = ExecutionStatus.SUCCESS
        elif result.get('error_type') == 'TimeoutError':
            status = ExecutionStatus.TIMEOUT
        elif result.get('error_type') == 'MemoryLimitError':
            status = ExecutionStatus.MEMORY_EXCEEDED
        elif result.get('error_type') == 'CompilationError':
            status = ExecutionStatus.COMPILATION_ERROR
        else:
            status = ExecutionStatus.RUNTIME_ERROR
        
        # Criar objeto de métricas
        metrics = SandboxMetrics(
            execution_id=self.execution_id,
            timestamp=datetime.now(),
            code_hash=hashlib.sha256(self.code.encode()).hexdigest(),
            code_length=len(self.code),
            status=status,
            success=result.get('success', False),
            execution_time_ms=execution_time_ms,
            memory_used_mb=memory_used,
            memory_peak_mb=memory_peak,
            timeout_limit_s=timeout_limit_s,
            memory_limit_mb=memory_limit_mb,
            error_type=result.get('error_type'),
            error_message=result.get('error'),
            metadata=metadata or {}
        )
        
        logger.info(
            f"📊 Métricas coletadas: {self.execution_id} | "
            f"Status: {status.value} | "
            f"Tempo: {execution_time_ms:.2f}ms | "
            f"Memória: {memory_used:.2f}MB"
        )
        
        # Reset
        self.start_time = None
        self.start_memory = None
        self.code = None
        self.execution_id = None
        
        return metrics


# ═══════════════════════════════════════════════════════════════════════════
# SANDBOX MONITOR
# ═══════════════════════════════════════════════════════════════════════════

class SandboxMonitor:
    """
    Monitor principal do sandbox seguro.
    
    Responsabilidades:
    - Coletar métricas de execuções
    - Persistir métricas no Supabase
    - Fornecer estatísticas agregadas
    - Detectar padrões anômalos
    
    Uso:
        monitor = SandboxMonitor()
        
        # Registrar execução
        monitor.record_execution(
            code="resultado = 42",
            result={'success': True, 'result': 42, ...}
        )
        
        # Obter estatísticas
        stats = monitor.get_statistics(period_hours=24)
    """
    
    def __init__(self, enable_persistence: bool = True):
        """
        Inicializa monitor.
        
        Args:
            enable_persistence: Se True, persiste métricas no Supabase
        """
        self.enable_persistence = enable_persistence
        self.metrics_buffer: List[SandboxMetrics] = []
        self.buffer_size = 100  # Flush após 100 métricas
        
        logger.info("🔍 SandboxMonitor inicializado")
    
    def record_execution(
        self,
        code: str,
        result: Dict[str, Any],
        timeout_limit_s: int = 10,
        memory_limit_mb: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
        flush_immediately: bool = False
    ) -> SandboxMetrics:
        """
        Registra uma execução do sandbox.
        
        Args:
            code: Código executado
            result: Resultado da execução
            timeout_limit_s: Limite de timeout
            memory_limit_mb: Limite de memória
            metadata: Metadata adicional
            flush_immediately: Se True, persiste imediatamente
            
        Returns:
            Objeto SandboxMetrics
        """
        # Criar coletor
        collector = MetricsCollector()
        collector.start_execution(code)
        
        # Coletar métricas
        metrics = collector.end_execution(
            result=result,
            timeout_limit_s=timeout_limit_s,
            memory_limit_mb=memory_limit_mb,
            metadata=metadata
        )
        
        # Adicionar ao buffer
        self.metrics_buffer.append(metrics)
        
        # Flush se necessário
        if flush_immediately or len(self.metrics_buffer) >= self.buffer_size:
            self.flush_metrics()
        
        return metrics
    
    def flush_metrics(self) -> int:
        """
        Persiste métricas do buffer no Supabase.
        
        Returns:
            Número de métricas persistidas
        """
        if not self.enable_persistence or not self.metrics_buffer:
            return 0
        
        try:
            # Preparar dados para inserção
            records = [m.to_dict() for m in self.metrics_buffer]
            
            # Inserir no Supabase
            result = supabase.table('sandbox_metrics').insert(records).execute()
            
            count = len(self.metrics_buffer)
            logger.info(f"💾 {count} métricas persistidas no Supabase")
            
            # Limpar buffer
            self.metrics_buffer.clear()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Erro ao persistir métricas: {e}")
            return 0
    
    def get_statistics(
        self,
        period_hours: int = 24,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas agregadas do Supabase.
        
        Args:
            period_hours: Período em horas para análise
            filters: Filtros adicionais
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            # Calcular timestamp inicial
            start_time = datetime.now() - timedelta(hours=period_hours)
            
            # Buscar métricas do período
            query = supabase.table('sandbox_metrics')\
                .select('*')\
                .gte('timestamp', start_time.isoformat())
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            metrics = result.data
            
            if not metrics:
                return {
                    'period_hours': period_hours,
                    'total_executions': 0,
                    'success_rate': 0.0,
                    'avg_execution_time_ms': 0.0,
                    'avg_memory_used_mb': 0.0
                }
            
            # Calcular estatísticas
            total = len(metrics)
            successes = sum(1 for m in metrics if m['success'])
            
            stats = {
                'period_hours': period_hours,
                'total_executions': total,
                'success_rate': (successes / total) * 100,
                'failure_rate': ((total - successes) / total) * 100,
                'avg_execution_time_ms': sum(m['execution_time_ms'] for m in metrics) / total,
                'max_execution_time_ms': max(m['execution_time_ms'] for m in metrics),
                'avg_memory_used_mb': sum(m['memory_used_mb'] for m in metrics) / total,
                'max_memory_used_mb': max(m['memory_used_mb'] for m in metrics),
                'error_distribution': self._get_error_distribution(metrics),
                'status_distribution': self._get_status_distribution(metrics)
            }
            
            logger.info(
                f"📈 Estatísticas ({period_hours}h): "
                f"{total} execuções, "
                f"{stats['success_rate']:.1f}% sucesso"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def _get_error_distribution(self, metrics: List[Dict]) -> Dict[str, int]:
        """Calcula distribuição de tipos de erro."""
        distribution = {}
        for m in metrics:
            if not m['success'] and m.get('error_type'):
                error_type = m['error_type']
                distribution[error_type] = distribution.get(error_type, 0) + 1
        return distribution
    
    def _get_status_distribution(self, metrics: List[Dict]) -> Dict[str, int]:
        """Calcula distribuição de status."""
        distribution = {}
        for m in metrics:
            status = m['status']
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def detect_anomalies(
        self,
        period_hours: int = 1,
        failure_threshold: float = 10.0,
        timeout_threshold: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detecta padrões anômalos nas execuções.
        
        Args:
            period_hours: Período para análise
            failure_threshold: Taxa de falha (%) para alertar
            timeout_threshold: Número de timeouts consecutivos para alertar
            
        Returns:
            Lista de anomalias detectadas
        """
        anomalies = []
        
        try:
            stats = self.get_statistics(period_hours=period_hours)
            
            if not stats or stats['total_executions'] == 0:
                return anomalies
            
            # Anomalia 1: Taxa de falha alta
            if stats['failure_rate'] > failure_threshold:
                anomalies.append({
                    'type': 'high_failure_rate',
                    'severity': 'HIGH',
                    'message': f"Taxa de falha {stats['failure_rate']:.1f}% excede limiar de {failure_threshold}%",
                    'value': stats['failure_rate'],
                    'threshold': failure_threshold
                })
            
            # Anomalia 2: Múltiplos timeouts
            timeouts = stats['error_distribution'].get('TimeoutError', 0)
            if timeouts >= timeout_threshold:
                anomalies.append({
                    'type': 'excessive_timeouts',
                    'severity': 'MEDIUM',
                    'message': f"{timeouts} timeouts detectados em {period_hours}h",
                    'value': timeouts,
                    'threshold': timeout_threshold
                })
            
            # Anomalia 3: Uso excessivo de memória
            if stats.get('max_memory_used_mb', 0) > 150:
                anomalies.append({
                    'type': 'high_memory_usage',
                    'severity': 'MEDIUM',
                    'message': f"Pico de memória {stats['max_memory_used_mb']:.1f}MB detectado",
                    'value': stats['max_memory_used_mb'],
                    'threshold': 150
                })
            
            if anomalies:
                logger.warning(f"⚠️ {len(anomalies)} anomalia(s) detectada(s)")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Erro ao detectar anomalias: {e}")
            return []
    
    def __del__(self):
        """Flush métricas ao destruir o objeto."""
        if self.metrics_buffer:
            self.flush_metrics()


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Criar monitor
    monitor = SandboxMonitor()
    
    # Simular execução bem-sucedida
    result_success = {
        'success': True,
        'result': 42,
        'execution_time_ms': 15.5,
        'error': None,
        'error_type': None
    }
    
    monitor.record_execution(
        code="resultado = 2 + 2",
        result=result_success,
        metadata={'source': 'test'}
    )
    
    # Simular execução com erro
    result_error = {
        'success': False,
        'result': None,
        'execution_time_ms': 2.3,
        'error': 'Import bloqueado',
        'error_type': 'CompilationError'
    }
    
    monitor.record_execution(
        code="import os",
        result=result_error,
        metadata={'source': 'test'}
    )
    
    # Obter estatísticas
    stats = monitor.get_statistics(period_hours=1)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Detectar anomalias
    anomalies = monitor.detect_anomalies(period_hours=1)
    print(f"\nAnomalias: {len(anomalies)}")
