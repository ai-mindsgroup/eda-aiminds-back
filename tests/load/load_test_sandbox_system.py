"""
Load Testing Script - Sandbox System with Monitoring
Sprint 4 - EDA AI Minds

Executa testes de carga intensivos para validar:
- Performance sob alta concorrência (10+ threads)
- Estabilidade de memória com 200+ execuções
- Latência (P50, P95, P99)
- Taxa de sucesso sob carga
- Identificação de gargalos

Author: GitHub Copilot with Sonnet 4.5
Date: 2025-10-17
"""

import time
import threading
import queue
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.security.sandbox import execute_in_sandbox
from src.monitoring.sandbox_monitor import SandboxMonitor
from src.monitoring.alert_manager import AlertManager
from src.monitoring.metrics_aggregator import MetricsAggregator


@dataclass
class LoadTestResult:
    """Resultado de uma execução individual no teste de carga"""
    thread_id: int
    execution_number: int
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    status: str
    execution_id: Optional[str] = None
    error_message: Optional[str] = None
    memory_used_mb: Optional[float] = None


@dataclass
class LoadTestReport:
    """Relatório consolidado do teste de carga"""
    test_name: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    
    # Configuração
    num_threads: int
    executions_per_thread: int
    total_executions: int
    
    # Resultados agregados
    successful_executions: int
    failed_executions: int
    success_rate: float
    
    # Latência (ms)
    latency_min: float
    latency_max: float
    latency_mean: float
    latency_median: float
    latency_p95: float
    latency_p99: float
    latency_stdev: float
    
    # Throughput
    executions_per_second: float
    
    # Memória
    memory_min_mb: float
    memory_max_mb: float
    memory_mean_mb: float
    
    # Distribuição de erros
    error_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Resultados individuais
    individual_results: List[LoadTestResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário (para JSON)"""
        return {
            'test_name': self.test_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration_seconds': self.total_duration_seconds,
            'configuration': {
                'num_threads': self.num_threads,
                'executions_per_thread': self.executions_per_thread,
                'total_executions': self.total_executions
            },
            'results': {
                'successful_executions': self.successful_executions,
                'failed_executions': self.failed_executions,
                'success_rate': self.success_rate
            },
            'latency_ms': {
                'min': self.latency_min,
                'max': self.latency_max,
                'mean': self.latency_mean,
                'median': self.latency_median,
                'p95': self.latency_p95,
                'p99': self.latency_p99,
                'stdev': self.latency_stdev
            },
            'throughput': {
                'executions_per_second': self.executions_per_second
            },
            'memory_mb': {
                'min': self.memory_min_mb,
                'max': self.memory_max_mb,
                'mean': self.memory_mean_mb
            },
            'error_distribution': self.error_distribution
        }


class LoadTester:
    """Executor de testes de carga no sistema de sandbox"""
    
    def __init__(self, num_threads: int = 10, executions_per_thread: int = 20):
        """
        Args:
            num_threads: Número de threads paralelas
            executions_per_thread: Execuções por thread
        """
        self.num_threads = num_threads
        self.executions_per_thread = executions_per_thread
        self.total_executions = num_threads * executions_per_thread
        self.results_queue = queue.Queue()
        self.monitor = SandboxMonitor(enable_persistence=True)
        
    def _worker_thread(self, thread_id: int, code_samples: List[str]):
        """Thread worker que executa múltiplas amostras de código"""
        for i in range(self.executions_per_thread):
            # Seleciona código da lista
            code = code_samples[i % len(code_samples)]
            
            start_time = time.time()
            try:
                result = execute_in_sandbox(
                    code=code,
                    timeout_seconds=5,
                    enable_monitoring=True
                )
                end_time = time.time()
                
                # Extrai informações
                duration_ms = (end_time - start_time) * 1000
                success = result.get('success', False)
                status = result.get('status', 'unknown')
                error_msg = result.get('error', {}).get('message')
                
                monitoring_data = result.get('monitoring', {})
                execution_id = monitoring_data.get('execution_id')
                memory_used = monitoring_data.get('memory_used_mb')
                
                test_result = LoadTestResult(
                    thread_id=thread_id,
                    execution_number=i + 1,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=success,
                    status=status,
                    execution_id=execution_id,
                    error_message=error_msg,
                    memory_used_mb=memory_used
                )
                
                self.results_queue.put(test_result)
                
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                test_result = LoadTestResult(
                    thread_id=thread_id,
                    execution_number=i + 1,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=False,
                    status='exception',
                    error_message=str(e)
                )
                
                self.results_queue.put(test_result)
    
    def run_load_test(self, code_samples: List[str], test_name: str = "Load Test") -> LoadTestReport:
        """
        Executa teste de carga completo
        
        Args:
            code_samples: Lista de códigos Python para executar
            test_name: Nome do teste
            
        Returns:
            LoadTestReport com resultados consolidados
        """
        print(f"\n{'='*80}")
        print(f"🚀 INICIANDO TESTE DE CARGA: {test_name}")
        print(f"{'='*80}")
        print(f"Configuração:")
        print(f"  - Threads: {self.num_threads}")
        print(f"  - Execuções por thread: {self.executions_per_thread}")
        print(f"  - Total de execuções: {self.total_executions}")
        print(f"  - Amostras de código: {len(code_samples)}")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        start_timestamp = time.time()
        
        # Criar e iniciar threads
        threads = []
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self._worker_thread,
                args=(i, code_samples),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar todas as threads
        for thread in threads:
            thread.join()
        
        end_time = datetime.now()
        end_timestamp = time.time()
        total_duration = end_timestamp - start_timestamp
        
        # Coletar todos os resultados
        results = []
        while not self.results_queue.empty():
            results.append(self.results_queue.get())
        
        # Calcular estatísticas
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        durations = [r.duration_ms for r in results]
        memories = [r.memory_used_mb for r in results if r.memory_used_mb is not None]
        
        # Distribuição de erros
        error_dist = {}
        for r in failed:
            status = r.status or 'unknown'
            error_dist[status] = error_dist.get(status, 0) + 1
        
        # Criar relatório
        report = LoadTestReport(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=total_duration,
            num_threads=self.num_threads,
            executions_per_thread=self.executions_per_thread,
            total_executions=len(results),
            successful_executions=len(successful),
            failed_executions=len(failed),
            success_rate=(len(successful) / len(results) * 100) if results else 0.0,
            latency_min=min(durations) if durations else 0.0,
            latency_max=max(durations) if durations else 0.0,
            latency_mean=statistics.mean(durations) if durations else 0.0,
            latency_median=statistics.median(durations) if durations else 0.0,
            latency_p95=self._percentile(durations, 95) if durations else 0.0,
            latency_p99=self._percentile(durations, 99) if durations else 0.0,
            latency_stdev=statistics.stdev(durations) if len(durations) > 1 else 0.0,
            executions_per_second=len(results) / total_duration if total_duration > 0 else 0.0,
            memory_min_mb=min(memories) if memories else 0.0,
            memory_max_mb=max(memories) if memories else 0.0,
            memory_mean_mb=statistics.mean(memories) if memories else 0.0,
            error_distribution=error_dist,
            individual_results=results
        )
        
        return report
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calcula percentil de uma lista"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


def print_report(report: LoadTestReport):
    """Imprime relatório formatado no console"""
    print(f"\n{'='*80}")
    print(f"📊 RELATÓRIO DE TESTE DE CARGA: {report.test_name}")
    print(f"{'='*80}")
    
    print(f"\n⏱️  DURAÇÃO:")
    print(f"  Início: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Fim: {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duração total: {report.total_duration_seconds:.2f}s")
    
    print(f"\n⚙️  CONFIGURAÇÃO:")
    print(f"  Threads: {report.num_threads}")
    print(f"  Execuções por thread: {report.executions_per_thread}")
    print(f"  Total de execuções: {report.total_executions}")
    
    print(f"\n✅ RESULTADOS:")
    print(f"  Sucessos: {report.successful_executions} ({report.success_rate:.2f}%)")
    print(f"  Falhas: {report.failed_executions}")
    
    print(f"\n⚡ LATÊNCIA (ms):")
    print(f"  Mínima: {report.latency_min:.2f}ms")
    print(f"  Máxima: {report.latency_max:.2f}ms")
    print(f"  Média: {report.latency_mean:.2f}ms")
    print(f"  Mediana (P50): {report.latency_median:.2f}ms")
    print(f"  P95: {report.latency_p95:.2f}ms")
    print(f"  P99: {report.latency_p99:.2f}ms")
    print(f"  Desvio padrão: {report.latency_stdev:.2f}ms")
    
    print(f"\n🚀 THROUGHPUT:")
    print(f"  Execuções/segundo: {report.executions_per_second:.2f}")
    
    print(f"\n💾 MEMÓRIA (MB):")
    print(f"  Mínima: {report.memory_min_mb:.2f}MB")
    print(f"  Máxima: {report.memory_max_mb:.2f}MB")
    print(f"  Média: {report.memory_mean_mb:.2f}MB")
    
    if report.error_distribution:
        print(f"\n❌ DISTRIBUIÇÃO DE ERROS:")
        for error_type, count in sorted(report.error_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} ({count / report.failed_executions * 100:.1f}%)")
    
    print(f"\n{'='*80}\n")


def export_report(report: LoadTestReport, output_path: str):
    """Exporta relatório para arquivo JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"✅ Relatório exportado para: {output_path}")


# ========================================
# AMOSTRAS DE CÓDIGO PARA TESTE DE CARGA
# ========================================

SIMPLE_CODE_SAMPLES = [
    # Operações matemáticas básicas
    "resultado = 2 + 2",
    "resultado = sum(range(100))",
    "resultado = [x**2 for x in range(50)]",
    "resultado = {'a': 1, 'b': 2, 'c': 3}",
    "resultado = len('teste de carga')",
    
    # Operações com strings
    "resultado = 'hello'.upper()",
    "resultado = '-'.join(['a', 'b', 'c'])",
    "resultado = 'teste' * 10",
    
    # Operações com listas
    "resultado = sorted([5, 2, 8, 1, 9])",
    "resultado = list(filter(lambda x: x > 5, range(20)))",
]

PANDAS_CODE_SAMPLES = [
    """
import pandas as pd
import numpy as np
df = pd.DataFrame({'A': range(100), 'B': np.random.rand(100)})
resultado = df['A'].mean()
""",
    """
import pandas as pd
df = pd.DataFrame({'vendas': [100, 200, 150, 300], 'lucro': [20, 50, 30, 80]})
resultado = df['vendas'].sum()
""",
    """
import pandas as pd
import numpy as np
data = {'valores': np.random.randint(1, 100, 50)}
df = pd.DataFrame(data)
resultado = df.describe().to_dict()
""",
    """
import pandas as pd
df = pd.DataFrame({'categoria': ['A', 'B', 'A', 'B'], 'valor': [10, 20, 30, 40]})
resultado = df.groupby('categoria')['valor'].sum().to_dict()
""",
]

STATISTICAL_CODE_SAMPLES = [
    """
import statistics
dados = [10, 20, 30, 40, 50]
resultado = {
    'media': statistics.mean(dados),
    'mediana': statistics.median(dados),
    'desvio': statistics.stdev(dados)
}
""",
    """
import numpy as np
dados = np.random.normal(100, 15, 100)
resultado = {
    'media': float(np.mean(dados)),
    'desvio': float(np.std(dados)),
    'min': float(np.min(dados)),
    'max': float(np.max(dados))
}
""",
]

COMPLEX_CODE_SAMPLES = [
    """
import pandas as pd
import numpy as np

# Análise de vendas
vendas = pd.DataFrame({
    'mes': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
    'vendas': [1000, 1200, 1100, 1300, 1250, 1400],
    'custos': [600, 700, 650, 750, 700, 800]
})

vendas['lucro'] = vendas['vendas'] - vendas['custos']
vendas['margem'] = (vendas['lucro'] / vendas['vendas'] * 100).round(2)

resultado = {
    'total_vendas': int(vendas['vendas'].sum()),
    'total_lucro': int(vendas['lucro'].sum()),
    'margem_media': float(vendas['margem'].mean()),
    'melhor_mes': vendas.loc[vendas['lucro'].idxmax(), 'mes']
}
""",
    """
import pandas as pd
import numpy as np

# Time series analysis
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=30, freq='D')
data = pd.DataFrame({
    'data': dates,
    'acessos': np.random.poisson(1500, 30) + np.arange(30) * 20
})

data['media_movel'] = data['acessos'].rolling(window=7).mean()

resultado = {
    'total_acessos': int(data['acessos'].sum()),
    'media_diaria': float(data['acessos'].mean()),
    'tendencia': 'crescente' if data['acessos'].iloc[-1] > data['acessos'].iloc[0] else 'decrescente'
}
""",
]


def main():
    """Executa bateria completa de testes de carga"""
    output_dir = Path(project_root) / "outputs" / "load_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ========================================
    # TESTE 1: Código Simples (Alta Throughput)
    # ========================================
    print("\n🔥 TESTE 1: Código Simples - Alta Throughput")
    tester1 = LoadTester(num_threads=10, executions_per_thread=20)
    report1 = tester1.run_load_test(SIMPLE_CODE_SAMPLES, "Simple Code - High Throughput")
    print_report(report1)
    export_report(report1, str(output_dir / f"load_test_simple_{timestamp}.json"))
    
    # ========================================
    # TESTE 2: Operações Pandas (Carga Média)
    # ========================================
    print("\n🔥 TESTE 2: Operações Pandas - Carga Média")
    tester2 = LoadTester(num_threads=8, executions_per_thread=15)
    report2 = tester2.run_load_test(PANDAS_CODE_SAMPLES, "Pandas Operations - Medium Load")
    print_report(report2)
    export_report(report2, str(output_dir / f"load_test_pandas_{timestamp}.json"))
    
    # ========================================
    # TESTE 3: Análises Estatísticas
    # ========================================
    print("\n🔥 TESTE 3: Análises Estatísticas")
    tester3 = LoadTester(num_threads=6, executions_per_thread=20)
    report3 = tester3.run_load_test(STATISTICAL_CODE_SAMPLES, "Statistical Analysis")
    print_report(report3)
    export_report(report3, str(output_dir / f"load_test_statistics_{timestamp}.json"))
    
    # ========================================
    # TESTE 4: Código Complexo (Carga Pesada)
    # ========================================
    print("\n🔥 TESTE 4: Código Complexo - Carga Pesada")
    tester4 = LoadTester(num_threads=5, executions_per_thread=10)
    report4 = tester4.run_load_test(COMPLEX_CODE_SAMPLES, "Complex Analysis - Heavy Load")
    print_report(report4)
    export_report(report4, str(output_dir / f"load_test_complex_{timestamp}.json"))
    
    # ========================================
    # TESTE 5: Carga Mista (Realista)
    # ========================================
    print("\n🔥 TESTE 5: Carga Mista - Cenário Realista")
    mixed_samples = SIMPLE_CODE_SAMPLES + PANDAS_CODE_SAMPLES + STATISTICAL_CODE_SAMPLES + COMPLEX_CODE_SAMPLES
    tester5 = LoadTester(num_threads=10, executions_per_thread=25)
    report5 = tester5.run_load_test(mixed_samples, "Mixed Workload - Realistic Scenario")
    print_report(report5)
    export_report(report5, str(output_dir / f"load_test_mixed_{timestamp}.json"))
    
    # ========================================
    # RESUMO CONSOLIDADO
    # ========================================
    print("\n" + "="*80)
    print("📋 RESUMO CONSOLIDADO DE TODOS OS TESTES")
    print("="*80)
    
    all_reports = [report1, report2, report3, report4, report5]
    
    total_executions = sum(r.total_executions for r in all_reports)
    total_successful = sum(r.successful_executions for r in all_reports)
    total_duration = sum(r.total_duration_seconds for r in all_reports)
    
    avg_success_rate = statistics.mean([r.success_rate for r in all_reports])
    avg_latency_p95 = statistics.mean([r.latency_p95 for r in all_reports])
    avg_throughput = statistics.mean([r.executions_per_second for r in all_reports])
    
    print(f"\nTotal de execuções: {total_executions}")
    print(f"Total de sucessos: {total_successful}")
    print(f"Duração total: {total_duration:.2f}s")
    print(f"Taxa de sucesso média: {avg_success_rate:.2f}%")
    print(f"Latência P95 média: {avg_latency_p95:.2f}ms")
    print(f"Throughput médio: {avg_throughput:.2f} exec/s")
    
    # Verificação de SLA
    print(f"\n{'='*80}")
    print("🎯 VERIFICAÇÃO DE SLA")
    print(f"{'='*80}")
    
    sla_checks = {
        'Taxa de sucesso >= 95%': avg_success_rate >= 95.0,
        'Latência P95 <= 500ms': avg_latency_p95 <= 500.0,
        'Throughput >= 5 exec/s': avg_throughput >= 5.0
    }
    
    all_passed = True
    for check, passed in sla_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {check}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 TODOS OS SLAs ATENDIDOS!")
    else:
        print(f"\n⚠️  ALGUNS SLAs NÃO FORAM ATENDIDOS")
    
    print(f"\n{'='*80}\n")
    
    # Exportar resumo consolidado
    consolidated = {
        'timestamp': timestamp,
        'total_tests': len(all_reports),
        'total_executions': total_executions,
        'total_successful': total_successful,
        'total_duration_seconds': total_duration,
        'averages': {
            'success_rate': avg_success_rate,
            'latency_p95_ms': avg_latency_p95,
            'throughput_exec_per_sec': avg_throughput
        },
        'sla_checks': {k: ('PASS' if v else 'FAIL') for k, v in sla_checks.items()},
        'individual_reports': [r.to_dict() for r in all_reports]
    }
    
    consolidated_path = output_dir / f"load_test_consolidated_{timestamp}.json"
    with open(consolidated_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Relatório consolidado exportado para: {consolidated_path}\n")


if __name__ == "__main__":
    main()
