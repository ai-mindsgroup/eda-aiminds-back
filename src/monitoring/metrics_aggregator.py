"""
📊 METRICS AGGREGATOR - Agregador de Métricas

Agrega e analisa métricas do sandbox para geração de relatórios.

Funcionalidades:
- Agregação temporal (hora, dia, semana)
- Análise de tendências
- Geração de relatórios automatizados
- Exportação em múltiplos formatos (JSON, CSV, HTML)

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import statistics

from src.utils.logging_config import get_logger
from src.vectorstore.supabase_client import supabase

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MetricsReport:
    """Relatório agregado de métricas."""
    
    # Período
    start_time: datetime
    end_time: datetime
    period_hours: float
    
    # Contadores
    total_executions: int
    successful_executions: int
    failed_executions: int
    
    # Taxas
    success_rate: float
    failure_rate: float
    
    # Performance
    avg_execution_time_ms: float
    median_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    max_execution_time_ms: float
    
    # Memória
    avg_memory_used_mb: float
    median_memory_used_mb: float
    max_memory_used_mb: float
    
    # Erros
    error_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    top_errors: List[Dict[str, Any]]
    
    # Tendências
    hourly_trend: Optional[List[Dict[str, Any]]] = None
    daily_trend: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data
    
    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# METRICS AGGREGATOR
# ═══════════════════════════════════════════════════════════════════════════

class MetricsAggregator:
    """
    Agregador de métricas do sandbox.
    
    Responsabilidades:
    - Agregar métricas por período temporal
    - Calcular percentis e estatísticas avançadas
    - Identificar tendências
    - Gerar relatórios detalhados
    
    Uso:
        aggregator = MetricsAggregator()
        report = aggregator.generate_report(period_hours=24)
        print(report.to_json())
    """
    
    def __init__(self):
        """Inicializa agregador."""
        logger.info("📊 MetricsAggregator inicializado")
    
    def generate_report(
        self,
        period_hours: int = 24,
        include_trends: bool = True
    ) -> Optional[MetricsReport]:
        """
        Gera relatório agregado de métricas.
        
        Args:
            period_hours: Período em horas
            include_trends: Se True, inclui análise de tendências
            
        Returns:
            MetricsReport ou None se sem dados
        """
        try:
            # Definir período
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=period_hours)
            
            # Buscar métricas do Supabase
            result = supabase.table('sandbox_metrics')\
                .select('*')\
                .gte('timestamp', start_time.isoformat())\
                .lte('timestamp', end_time.isoformat())\
                .execute()
            
            metrics = result.data
            
            if not metrics:
                logger.warning(f"⚠️ Nenhuma métrica encontrada para período de {period_hours}h")
                return None
            
            # Calcular estatísticas básicas
            total = len(metrics)
            successes = sum(1 for m in metrics if m['success'])
            failures = total - successes
            
            success_rate = (successes / total * 100) if total > 0 else 0
            failure_rate = (failures / total * 100) if total > 0 else 0
            
            # Estatísticas de tempo de execução
            exec_times = [m['execution_time_ms'] for m in metrics]
            exec_times.sort()
            
            avg_time = statistics.mean(exec_times) if exec_times else 0
            median_time = statistics.median(exec_times) if exec_times else 0
            p95_time = self._percentile(exec_times, 95) if exec_times else 0
            p99_time = self._percentile(exec_times, 99) if exec_times else 0
            max_time = max(exec_times) if exec_times else 0
            
            # Estatísticas de memória
            memory_values = [m['memory_used_mb'] for m in metrics]
            memory_values.sort()
            
            avg_memory = statistics.mean(memory_values) if memory_values else 0
            median_memory = statistics.median(memory_values) if memory_values else 0
            max_memory = max(memory_values) if memory_values else 0
            
            # Distribuições
            error_dist = self._get_error_distribution(metrics)
            status_dist = self._get_status_distribution(metrics)
            top_errors = self._get_top_errors(metrics, limit=5)
            
            # Criar relatório
            report = MetricsReport(
                start_time=start_time,
                end_time=end_time,
                period_hours=period_hours,
                total_executions=total,
                successful_executions=successes,
                failed_executions=failures,
                success_rate=success_rate,
                failure_rate=failure_rate,
                avg_execution_time_ms=avg_time,
                median_execution_time_ms=median_time,
                p95_execution_time_ms=p95_time,
                p99_execution_time_ms=p99_time,
                max_execution_time_ms=max_time,
                avg_memory_used_mb=avg_memory,
                median_memory_used_mb=median_memory,
                max_memory_used_mb=max_memory,
                error_distribution=error_dist,
                status_distribution=status_dist,
                top_errors=top_errors
            )
            
            # Adicionar tendências se solicitado
            if include_trends and period_hours >= 24:
                report.hourly_trend = self._calculate_hourly_trend(metrics)
                if period_hours >= 168:  # 7 dias
                    report.daily_trend = self._calculate_daily_trend(metrics)
            
            logger.info(
                f"📊 Relatório gerado: {total} execuções, "
                f"{success_rate:.1f}% sucesso, "
                f"{avg_time:.2f}ms avg"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return None
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcula percentil de uma lista de valores."""
        if not data:
            return 0.0
        
        data_sorted = sorted(data)
        index = int((percentile / 100) * len(data_sorted))
        index = min(index, len(data_sorted) - 1)
        
        return data_sorted[index]
    
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
    
    def _get_top_errors(self, metrics: List[Dict], limit: int = 5) -> List[Dict[str, Any]]:
        """Identifica os erros mais frequentes."""
        error_counts = {}
        error_examples = {}
        
        for m in metrics:
            if not m['success'] and m.get('error_type'):
                error_type = m['error_type']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                if error_type not in error_examples:
                    error_examples[error_type] = m.get('error_message', 'N/A')[:200]
        
        # Ordenar por contagem
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {
                'error_type': error_type,
                'count': count,
                'example': error_examples.get(error_type, 'N/A')
            }
            for error_type, count in sorted_errors
        ]
    
    def _calculate_hourly_trend(self, metrics: List[Dict]) -> List[Dict[str, Any]]:
        """Calcula tendência hora-a-hora."""
        hourly_buckets = {}
        
        for m in metrics:
            timestamp = datetime.fromisoformat(m['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in hourly_buckets:
                hourly_buckets[hour_key] = []
            
            hourly_buckets[hour_key].append(m)
        
        trend = []
        for hour, hour_metrics in sorted(hourly_buckets.items()):
            total = len(hour_metrics)
            successes = sum(1 for m in hour_metrics if m['success'])
            
            trend.append({
                'hour': hour,
                'total_executions': total,
                'successful': successes,
                'failed': total - successes,
                'success_rate': (successes / total * 100) if total > 0 else 0,
                'avg_execution_time_ms': statistics.mean([m['execution_time_ms'] for m in hour_metrics])
            })
        
        return trend
    
    def _calculate_daily_trend(self, metrics: List[Dict]) -> List[Dict[str, Any]]:
        """Calcula tendência dia-a-dia."""
        daily_buckets = {}
        
        for m in metrics:
            timestamp = datetime.fromisoformat(m['timestamp'])
            day_key = timestamp.strftime('%Y-%m-%d')
            
            if day_key not in daily_buckets:
                daily_buckets[day_key] = []
            
            daily_buckets[day_key].append(m)
        
        trend = []
        for day, day_metrics in sorted(daily_buckets.items()):
            total = len(day_metrics)
            successes = sum(1 for m in day_metrics if m['success'])
            
            trend.append({
                'day': day,
                'total_executions': total,
                'successful': successes,
                'failed': total - successes,
                'success_rate': (successes / total * 100) if total > 0 else 0,
                'avg_execution_time_ms': statistics.mean([m['execution_time_ms'] for m in day_metrics]),
                'avg_memory_used_mb': statistics.mean([m['memory_used_mb'] for m in day_metrics])
            })
        
        return trend
    
    def export_report_html(self, report: MetricsReport, output_path: str):
        """
        Exporta relatório em formato HTML.
        
        Args:
            report: Relatório a exportar
            output_path: Caminho do arquivo de saída
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório de Métricas - Sandbox Segura</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .success {{ color: #10b981; }}
        .failure {{ color: #ef4444; }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Relatório de Métricas - Sandbox Segura</h1>
        <p>Período: {report.start_time.strftime('%Y-%m-%d %H:%M')} até {report.end_time.strftime('%Y-%m-%d %H:%M')}</p>
        <p>Duração: {report.period_hours:.1f} horas</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{report.total_executions}</div>
            <div class="metric-label">Total de Execuções</div>
        </div>
        <div class="metric-card">
            <div class="metric-value success">{report.success_rate:.1f}%</div>
            <div class="metric-label">Taxa de Sucesso</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report.avg_execution_time_ms:.2f}ms</div>
            <div class="metric-label">Tempo Médio</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report.avg_memory_used_mb:.2f}MB</div>
            <div class="metric-label">Memória Média</div>
        </div>
    </div>

    <div class="section">
        <h2>📈 Performance</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Tempo Médio de Execução</td>
                <td>{report.avg_execution_time_ms:.2f}ms</td>
            </tr>
            <tr>
                <td>Mediana de Tempo</td>
                <td>{report.median_execution_time_ms:.2f}ms</td>
            </tr>
            <tr>
                <td>P95</td>
                <td>{report.p95_execution_time_ms:.2f}ms</td>
            </tr>
            <tr>
                <td>P99</td>
                <td>{report.p99_execution_time_ms:.2f}ms</td>
            </tr>
            <tr>
                <td>Tempo Máximo</td>
                <td>{report.max_execution_time_ms:.2f}ms</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>🔴 Top Erros</h2>
        <table>
            <tr>
                <th>Tipo de Erro</th>
                <th>Contagem</th>
                <th>Exemplo</th>
            </tr>
            {"".join(f'''
            <tr>
                <td>{error['error_type']}</td>
                <td>{error['count']}</td>
                <td>{error['example']}</td>
            </tr>
            ''' for error in report.top_errors)}
        </table>
    </div>

    <div class="section">
        <p style="color: #666; text-align: center;">
            Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 
            por MetricsAggregator v1.0.0
        </p>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📄 Relatório HTML exportado: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    aggregator = MetricsAggregator()
    
    # Gerar relatório
    report = aggregator.generate_report(period_hours=24, include_trends=True)
    
    if report:
        print(report.to_json())
        
        # Exportar HTML
        aggregator.export_report_html(report, 'metrics_report.html')
        print("\n✅ Relatório HTML gerado: metrics_report.html")
