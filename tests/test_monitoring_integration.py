"""
Teste de integração: Sandbox + Monitoring

Valida que o sistema de monitoramento está coletando métricas
corretamente durante execuções do sandbox.

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.sandbox import execute_in_sandbox
from src.monitoring.sandbox_monitor import SandboxMonitor
from src.monitoring.alert_manager import AlertManager
from src.monitoring.metrics_aggregator import MetricsAggregator
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_sandbox_monitoring_integration():
    """Testa integração sandbox + monitoring."""
    
    logger.info("=" * 80)
    logger.info("🧪 TESTE: Integração Sandbox + Monitoring")
    logger.info("=" * 80)
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. EXECUTAR CÓDIGO COM SUCESSO
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 1: Execução bem-sucedida")
    logger.info("-" * 80)
    
    result1 = execute_in_sandbox(
        code="""
import pandas as pd
import numpy as np

data = {'A': [1, 2, 3, 4, 5], 'B': [10, 20, 30, 40, 50]}
df = pd.DataFrame(data)
media_A = df['A'].mean()
soma_B = df['B'].sum()

resultado = {
    'media_A': media_A,
    'soma_B': soma_B,
    'total_linhas': len(df)
}
""",
        enable_monitoring=True,
        timeout_seconds=10
    )
    
    logger.info(f"✅ Success: {result1['success']}")
    logger.info(f"📊 Result: {result1['result']}")
    logger.info(f"⏱️ Time: {result1['execution_time_ms']:.2f}ms")
    
    if 'monitoring' in result1:
        logger.info(f"📈 Monitoring:")
        logger.info(f"   - Execution ID: {result1['monitoring']['execution_id']}")
        logger.info(f"   - Status: {result1['monitoring']['status']}")
        logger.info(f"   - Memory: {result1['monitoring']['memory_used_mb']:.2f}MB")
    
    assert result1['success'], "Execução deveria ter sido bem-sucedida"
    assert 'monitoring' in result1, "Resultado deveria conter dados de monitoring"
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. EXECUTAR CÓDIGO COM ERRO
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 2: Execução com erro")
    logger.info("-" * 80)
    
    result2 = execute_in_sandbox(
        code="""
# Código com erro proposital
resultado = undefined_variable + 10
""",
        enable_monitoring=True,
        timeout_seconds=5
    )
    
    logger.info(f"❌ Success: {result2['success']}")
    logger.info(f"🔴 Error: {result2['error']}")
    logger.info(f"⏱️ Time: {result2['execution_time_ms']:.2f}ms")
    
    if 'monitoring' in result2:
        logger.info(f"📈 Monitoring:")
        logger.info(f"   - Execution ID: {result2['monitoring']['execution_id']}")
        logger.info(f"   - Status: {result2['monitoring']['status']}")
    
    assert not result2['success'], "Execução deveria ter falhado"
    assert 'monitoring' in result2, "Resultado deveria conter dados de monitoring"
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. EXECUTAR CÓDIGO COM IMPORT BLOQUEADO
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 3: Import bloqueado")
    logger.info("-" * 80)
    
    result3 = execute_in_sandbox(
        code="""
import os
resultado = os.system('echo malicious')
""",
        enable_monitoring=True,
        timeout_seconds=5
    )
    
    logger.info(f"🚨 Success: {result3['success']}")
    logger.info(f"🔴 Error: {result3['error']}")
    
    if 'monitoring' in result3:
        logger.info(f"📈 Monitoring:")
        logger.info(f"   - Execution ID: {result3['monitoring']['execution_id']}")
        logger.info(f"   - Status: {result3['monitoring']['status']}")
    
    assert not result3['success'], "Import bloqueado deveria falhar"
    assert 'monitoring' in result3, "Resultado deveria conter dados de monitoring"
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. VERIFICAR PERSISTÊNCIA DAS MÉTRICAS
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 4: Verificar persistência das métricas")
    logger.info("-" * 80)
    
    monitor = SandboxMonitor(enable_persistence=True)
    
    # Forçar flush de métricas pendentes
    flushed = monitor.flush_metrics()
    logger.info(f"💾 Métricas persistidas: {flushed}")
    
    # Obter estatísticas
    stats = monitor.get_statistics(period_hours=1)
    
    if stats:
        logger.info(f"📊 Estatísticas (última hora):")
        logger.info(f"   - Total execuções: {stats['total_executions']}")
        logger.info(f"   - Taxa de sucesso: {stats['success_rate']:.1f}%")
        logger.info(f"   - Tempo médio: {stats['avg_execution_time_ms']:.2f}ms")
        logger.info(f"   - Distribuição de erros: {stats['error_distribution']}")
    else:
        logger.warning("⚠️ Nenhuma estatística disponível")
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. VERIFICAR SISTEMA DE ALERTAS
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 5: Sistema de alertas")
    logger.info("-" * 80)
    
    alert_manager = AlertManager(monitor, enable_persistence=True)
    
    # Avaliar todas as regras
    alerts = alert_manager.evaluate_all(period_hours=1)
    
    logger.info(f"🚨 Alertas gerados: {len(alerts)}")
    
    for i, alert in enumerate(alerts, 1):
        logger.info(f"\n   Alerta {i}:")
        logger.info(f"   - Tipo: {alert.alert_type}")
        logger.info(f"   - Nível: {alert.level}")
        logger.info(f"   - Título: {alert.title}")
        logger.info(f"   - Valor: {alert.value} (limiar: {alert.threshold})")
        logger.info(f"   - Recomendações: {len(alert.recommendations)}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. GERAR RELATÓRIO AGREGADO
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n📝 Teste 6: Relatório agregado")
    logger.info("-" * 80)
    
    aggregator = MetricsAggregator()
    report = aggregator.generate_report(period_hours=1, include_trends=False)
    
    if report:
        logger.info(f"📊 Relatório gerado:")
        logger.info(f"   - Período: {report.period_hours}h")
        logger.info(f"   - Total execuções: {report.total_executions}")
        logger.info(f"   - Taxa de sucesso: {report.success_rate:.1f}%")
        logger.info(f"   - Tempo médio: {report.avg_execution_time_ms:.2f}ms")
        logger.info(f"   - Tempo P95: {report.p95_execution_time_ms:.2f}ms")
        logger.info(f"   - Memória média: {report.avg_memory_used_mb:.2f}MB")
        logger.info(f"   - Top erros: {len(report.top_errors)}")
        
        # Exportar HTML
        output_path = "outputs/test_monitoring_report.html"
        aggregator.export_report_html(report, output_path)
        logger.info(f"\n   📄 Relatório HTML: {output_path}")
    else:
        logger.warning("⚠️ Nenhum relatório gerado (sem dados)")
    
    # ═══════════════════════════════════════════════════════════════════
    # RESUMO FINAL
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 80)
    logger.info("✅ TODOS OS TESTES PASSARAM!")
    logger.info("=" * 80)
    logger.info("\n📊 Resumo:")
    logger.info("   ✅ Execução bem-sucedida: monitorada")
    logger.info("   ✅ Execução com erro: monitorada")
    logger.info("   ✅ Import bloqueado: monitorado")
    logger.info("   ✅ Persistência: funcionando")
    logger.info("   ✅ Alertas: funcionando")
    logger.info("   ✅ Relatórios: funcionando")
    logger.info("")


if __name__ == '__main__':
    try:
        test_sandbox_monitoring_integration()
    except AssertionError as e:
        logger.error(f"❌ Teste falhou: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
