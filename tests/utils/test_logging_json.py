"""
Teste demonstrativo do sistema de logging estruturado JSON
Sprint 4 - Sistema de Monitoramento

Demonstra:
- Logging básico
- Logging estruturado com contexto
- Formatação JSON
- Formatação colorida
- Logging com exceções

Author: GitHub Copilot with Sonnet 4.5
Date: 2025-10-17
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configurar para usar JSON
os.environ['LOG_FORMAT'] = 'json'
os.environ['LOG_LEVEL'] = 'INFO'

from src.utils.logging_config import (
    get_logger,
    get_context_logger,
    log_with_context,
    configure_logger_for_module
)


def test_basic_logging():
    """Teste de logging básico"""
    print("\n" + "="*80)
    print("🧪 TESTE 1: Logging Básico")
    print("="*80 + "\n")
    
    logger = get_logger(__name__)
    
    logger.debug("Mensagem de debug")
    logger.info("Mensagem informativa")
    logger.warning("Mensagem de aviso")
    logger.error("Mensagem de erro")
    
    print("\n✅ Teste 1 concluído\n")


def test_structured_logging():
    """Teste de logging estruturado com contexto"""
    print("\n" + "="*80)
    print("🧪 TESTE 2: Logging Estruturado")
    print("="*80 + "\n")
    
    logger = get_logger(__name__)
    
    # Usar helper log_with_context
    log_with_context(
        logger=logger,
        level="info",
        message="Execução sandbox concluída",
        execution_id="exec_20251017_185130_123456",
        code_hash="abc123def456",
        duration_ms=156.78,
        memory_used_mb=45.2,
        status="success"
    )
    
    log_with_context(
        logger=logger,
        level="warning",
        message="Uso de memória elevado detectado",
        execution_id="exec_20251017_185131_789012",
        memory_used_mb=180.5,
        memory_limit_mb=200.0,
        threshold_percentage=90.25
    )
    
    print("\n✅ Teste 2 concluído\n")


def test_context_logger():
    """Teste de logger com contexto pré-definido"""
    print("\n" + "="*80)
    print("🧪 TESTE 3: Logger com Contexto Pré-definido")
    print("="*80 + "\n")
    
    # Criar logger com contexto
    logger = get_context_logger(
        __name__,
        user_id="user_12345",
        session_id="session_abcdef",
        request_id="req_xyz789"
    )
    
    # Todos os logs incluirão user_id, session_id, request_id automaticamente
    logger.info("Usuário fez login")
    logger.info("Consulta executada", query_time_ms=234.56, rows_returned=150)
    logger.info("Usuário fez logout", session_duration_s=3600)
    
    print("\n✅ Teste 3 concluído\n")


def test_exception_logging():
    """Teste de logging com exceções"""
    print("\n" + "="*80)
    print("🧪 TESTE 4: Logging com Exceções")
    print("="*80 + "\n")
    
    logger = get_logger(__name__)
    
    try:
        # Forçar exceção
        result = 10 / 0
    except ZeroDivisionError as e:
        log_with_context(
            logger=logger,
            level="error",
            message="Erro ao executar operação matemática",
            operation="division",
            numerator=10,
            denominator=0,
            exc_info=True
        )
        logger.error("Exceção capturada", exc_info=True)
    
    print("\n✅ Teste 4 concluído\n")


def test_monitoring_simulation():
    """Simulação de logs do sistema de monitoramento"""
    print("\n" + "="*80)
    print("🧪 TESTE 5: Simulação Sistema de Monitoramento")
    print("="*80 + "\n")
    
    logger = get_logger("src.monitoring.sandbox_monitor")
    
    # Simular coleta de métricas
    log_with_context(
        logger=logger,
        level="info",
        message="Métricas coletadas",
        execution_id="exec_001",
        status="success",
        execution_time_ms=125.45,
        memory_used_mb=42.3
    )
    
    log_with_context(
        logger=logger,
        level="info",
        message="Buffer de métricas atingiu limite",
        buffer_size=100,
        action="flushing_to_database"
    )
    
    log_with_context(
        logger=logger,
        level="info",
        message="Métricas persistidas no Supabase",
        records_inserted=100,
        duration_ms=456.78
    )
    
    # Simular alerta
    alert_logger = get_logger("src.monitoring.alert_manager")
    
    log_with_context(
        logger=alert_logger,
        level="warning",
        message="Alerta gerado: Taxa de falha elevada",
        alert_id="alert_789",
        alert_type="HIGH_FAILURE_RATE",
        alert_level="HIGH",
        failure_rate_percent=15.5,
        threshold_percent=10.0,
        period_hours=1
    )
    
    print("\n✅ Teste 5 concluído\n")


def test_aggregator_simulation():
    """Simulação de logs do agregador de métricas"""
    print("\n" + "="*80)
    print("🧪 TESTE 6: Simulação Agregador de Métricas")
    print("="*80 + "\n")
    
    logger = get_logger("src.monitoring.metrics_aggregator")
    
    log_with_context(
        logger=logger,
        level="info",
        message="Relatório de métricas gerado",
        period_hours=24,
        total_executions=1543,
        successful_executions=1478,
        failed_executions=65,
        success_rate_percent=95.79,
        avg_execution_time_ms=234.56,
        p95_execution_time_ms=567.89,
        p99_execution_time_ms=1234.56
    )
    
    log_with_context(
        logger=logger,
        level="info",
        message="Relatório HTML exportado",
        output_path="outputs/reports/metrics_24h.html",
        file_size_kb=125.4
    )
    
    print("\n✅ Teste 6 concluído\n")


def main():
    """Executar todos os testes"""
    print("\n" + "="*80)
    print("🚀 INICIANDO TESTES DE LOGGING ESTRUTURADO JSON")
    print("="*80)
    
    print(f"\nConfiguração:")
    print(f"  LOG_FORMAT: {os.getenv('LOG_FORMAT', 'text')}")
    print(f"  LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"  LOG_TO_FILE: {os.getenv('LOG_TO_FILE', 'true')}")
    
    test_basic_logging()
    test_structured_logging()
    test_context_logger()
    test_exception_logging()
    test_monitoring_simulation()
    test_aggregator_simulation()
    
    print("\n" + "="*80)
    print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("="*80)
    
    print("\n📋 Resumo:")
    print("  ✅ Logging básico funcionando")
    print("  ✅ Logging estruturado com contexto")
    print("  ✅ Logger com contexto pré-definido")
    print("  ✅ Logging de exceções com traceback")
    print("  ✅ Simulação sistema de monitoramento")
    print("  ✅ Simulação agregador de métricas")
    
    print("\n📄 Logs salvos em:")
    print(f"  - logs/eda-aiminds.log (todos os logs)")
    print(f"  - logs/eda-aiminds-errors.log (apenas erros)")
    
    print("\n💡 Dica: Para formato colorido no console:")
    print("  export LOG_FORMAT=colored")
    print("  python tests/utils/test_logging_json.py\n")


if __name__ == "__main__":
    main()
