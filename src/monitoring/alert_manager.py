"""
🚨 ALERT MANAGER - Sistema de Alertas para Sandbox

Detecta anomalias e envia alertas quando padrões suspeitos são identificados.

Alertas suportados:
- Taxa de falhas acima do limiar
- Timeouts repetidos
- Uso excessivo de memória
- Padrões suspeitos de execução

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json

from src.utils.logging_config import get_logger
from src.vectorstore.supabase_client import supabase

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS E DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════

class AlertLevel(Enum):
    """Níveis de severidade de alertas."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Tipos de alertas."""
    HIGH_FAILURE_RATE = "high_failure_rate"
    EXCESSIVE_TIMEOUTS = "excessive_timeouts"
    MEMORY_EXCEEDED = "memory_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    SYSTEM_DEGRADATION = "system_degradation"


@dataclass
class Alert:
    """Representa um alerta gerado pelo sistema."""
    
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    
    # Dados do alerta
    value: Any
    threshold: Any
    period_hours: int
    
    # Contexto adicional
    metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'threshold': self.threshold,
            'period_hours': self.period_hours,
            'metrics': self.metrics,
            'recommendations': self.recommendations
        }
    
    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AlertRule:
    """Regra para geração de alertas."""
    
    rule_id: str
    alert_type: AlertType
    level: AlertLevel
    enabled: bool
    
    # Condições
    metric_name: str
    threshold: Any
    comparison: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    
    # Configuração
    period_hours: int = 1
    cooldown_minutes: int = 30  # Tempo mínimo entre alertas do mesmo tipo
    
    # Callback customizado
    callback: Optional[Callable[[Alert], None]] = None
    
    def evaluate(self, value: Any) -> bool:
        """
        Avalia se a condição do alerta foi atingida.
        
        Args:
            value: Valor atual da métrica
            
        Returns:
            True se alerta deve ser gerado
        """
        if not self.enabled:
            return False
        
        if self.comparison == 'gt':
            return value > self.threshold
        elif self.comparison == 'gte':
            return value >= self.threshold
        elif self.comparison == 'lt':
            return value < self.threshold
        elif self.comparison == 'lte':
            return value <= self.threshold
        elif self.comparison == 'eq':
            return value == self.threshold
        else:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# ALERT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class AlertManager:
    """
    Gerenciador de alertas para o sandbox.
    
    Responsabilidades:
    - Definir e gerenciar regras de alerta
    - Avaliar métricas contra regras
    - Gerar e persistir alertas
    - Prevenir spam de alertas (cooldown)
    - Notificar callbacks registrados
    
    Uso:
        manager = AlertManager(monitor)
        
        # Adicionar regra customizada
        manager.add_rule(AlertRule(
            rule_id='custom_rule',
            alert_type=AlertType.HIGH_FAILURE_RATE,
            level=AlertLevel.HIGH,
            enabled=True,
            metric_name='failure_rate',
            threshold=15.0,
            comparison='gt'
        ))
        
        # Avaliar alertas
        alerts = manager.evaluate_all()
    """
    
    def __init__(self, sandbox_monitor, enable_persistence: bool = True):
        """
        Inicializa gerenciador de alertas.
        
        Args:
            sandbox_monitor: Instância do SandboxMonitor
            enable_persistence: Se True, persiste alertas no Supabase
        """
        self.monitor = sandbox_monitor
        self.enable_persistence = enable_persistence
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Configurar regras padrão
        self._setup_default_rules()
        
        logger.info("🚨 AlertManager inicializado")
    
    def _setup_default_rules(self):
        """Configura regras de alerta padrão."""
        
        # Regra 1: Taxa de falha alta (>10%)
        self.add_rule(AlertRule(
            rule_id='high_failure_rate',
            alert_type=AlertType.HIGH_FAILURE_RATE,
            level=AlertLevel.HIGH,
            enabled=True,
            metric_name='failure_rate',
            threshold=10.0,
            comparison='gt',
            period_hours=1,
            cooldown_minutes=30
        ))
        
        # Regra 2: Múltiplos timeouts (>=5)
        self.add_rule(AlertRule(
            rule_id='excessive_timeouts',
            alert_type=AlertType.EXCESSIVE_TIMEOUTS,
            level=AlertLevel.MEDIUM,
            enabled=True,
            metric_name='timeout_count',
            threshold=5,
            comparison='gte',
            period_hours=1,
            cooldown_minutes=15
        ))
        
        # Regra 3: Uso excessivo de memória (>80% do limite)
        self.add_rule(AlertRule(
            rule_id='memory_exceeded',
            alert_type=AlertType.MEMORY_EXCEEDED,
            level=AlertLevel.MEDIUM,
            enabled=True,
            metric_name='memory_usage_pct',
            threshold=80.0,
            comparison='gt',
            period_hours=1,
            cooldown_minutes=20
        ))
        
        # Regra 4: Taxa de sucesso muito baixa (<50%)
        self.add_rule(AlertRule(
            rule_id='system_degradation',
            alert_type=AlertType.SYSTEM_DEGRADATION,
            level=AlertLevel.CRITICAL,
            enabled=True,
            metric_name='success_rate',
            threshold=50.0,
            comparison='lt',
            period_hours=1,
            cooldown_minutes=60
        ))
    
    def add_rule(self, rule: AlertRule):
        """
        Adiciona uma regra de alerta.
        
        Args:
            rule: Regra a ser adicionada
        """
        self.rules[rule.rule_id] = rule
        logger.debug(f"✅ Regra adicionada: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str):
        """Remove uma regra de alerta."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.debug(f"🗑️ Regra removida: {rule_id}")
    
    def evaluate_all(self, period_hours: Optional[int] = None) -> List[Alert]:
        """
        Avalia todas as regras contra as métricas atuais.
        
        Args:
            period_hours: Período customizado (sobrescreve regras)
            
        Returns:
            Lista de alertas gerados
        """
        alerts = []
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Verificar cooldown
            if not self._check_cooldown(rule_id, rule.cooldown_minutes):
                continue
            
            # Obter métricas do período
            hours = period_hours if period_hours is not None else rule.period_hours
            stats = self.monitor.get_statistics(period_hours=hours)
            
            if not stats or stats.get('total_executions', 0) == 0:
                continue
            
            # Avaliar regra específica
            alert = self._evaluate_rule(rule, stats, hours)
            if alert:
                alerts.append(alert)
                self.alert_history.append(alert)
                self.last_alert_times[rule_id] = datetime.now()
                
                # Persistir alerta
                if self.enable_persistence:
                    self._persist_alert(alert)
                
                # Executar callback se existir
                if rule.callback:
                    try:
                        rule.callback(alert)
                    except Exception as e:
                        logger.error(f"❌ Erro ao executar callback: {e}")
        
        if alerts:
            logger.warning(f"🚨 {len(alerts)} alerta(s) gerado(s)")
        
        return alerts
    
    def _evaluate_rule(
        self,
        rule: AlertRule,
        stats: Dict[str, Any],
        period_hours: int
    ) -> Optional[Alert]:
        """
        Avalia uma regra específica contra as estatísticas.
        
        Args:
            rule: Regra a avaliar
            stats: Estatísticas atuais
            period_hours: Período analisado
            
        Returns:
            Alert se condição for atingida, None caso contrário
        """
        # Extrair valor da métrica
        if rule.metric_name == 'failure_rate':
            value = stats.get('failure_rate', 0.0)
        elif rule.metric_name == 'success_rate':
            value = stats.get('success_rate', 100.0)
        elif rule.metric_name == 'timeout_count':
            value = stats.get('error_distribution', {}).get('TimeoutError', 0)
        elif rule.metric_name == 'memory_usage_pct':
            max_mem = stats.get('max_memory_used_mb', 0)
            limit_mem = 200  # Default limit
            value = (max_mem / limit_mem) * 100 if limit_mem > 0 else 0
        else:
            value = stats.get(rule.metric_name, 0)
        
        # Avaliar condição
        if not rule.evaluate(value):
            return None
        
        # Gerar ID do alerta
        timestamp = datetime.now()
        alert_id = f"{rule.rule_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Criar mensagem e recomendações
        title, message, recommendations = self._build_alert_content(
            rule, value, stats
        )
        
        # Criar alerta
        alert = Alert(
            alert_id=alert_id,
            alert_type=rule.alert_type,
            level=rule.level,
            title=title,
            message=message,
            timestamp=timestamp,
            value=value,
            threshold=rule.threshold,
            period_hours=period_hours,
            metrics=stats,
            recommendations=recommendations
        )
        
        logger.warning(
            f"🚨 ALERTA [{alert.level.value.upper()}]: {alert.title}"
        )
        
        return alert
    
    def _build_alert_content(
        self,
        rule: AlertRule,
        value: Any,
        stats: Dict[str, Any]
    ) -> tuple[str, str, List[str]]:
        """Constrói conteúdo do alerta (título, mensagem, recomendações)."""
        
        if rule.alert_type == AlertType.HIGH_FAILURE_RATE:
            title = "🔴 Taxa de Falha Alta Detectada"
            message = (
                f"A taxa de falha atingiu {value:.1f}%, excedendo o limiar de {rule.threshold}%. "
                f"Total de execuções: {stats['total_executions']}"
            )
            recommendations = [
                "Revisar logs de erro para identificar causas comuns",
                "Verificar se há problemas com código de usuário",
                "Validar whitelist/blacklist de imports",
                "Considerar aumentar limites de timeout/memória"
            ]
        
        elif rule.alert_type == AlertType.EXCESSIVE_TIMEOUTS:
            title = "⏱️ Múltiplos Timeouts Detectados"
            message = (
                f"{value} timeout(s) detectado(s) em {rule.period_hours}h, "
                f"excedendo o limiar de {rule.threshold}."
            )
            recommendations = [
                "Analisar códigos que estão causando timeout",
                "Verificar se há loops infinitos não detectados",
                "Considerar aumentar limite de timeout para códigos legítimos",
                "Implementar timeout granular por tipo de operação"
            ]
        
        elif rule.alert_type == AlertType.MEMORY_EXCEEDED:
            title = "💾 Uso Excessivo de Memória"
            max_mem = stats.get('max_memory_used_mb', 0)
            message = (
                f"Uso de memória atingiu {value:.1f}% do limite "
                f"(pico: {max_mem:.1f}MB), excedendo {rule.threshold}%."
            )
            recommendations = [
                "Revisar códigos com alto consumo de memória",
                "Verificar alocações de arrays grandes (numpy/pandas)",
                "Considerar aumentar limite de memória",
                "Implementar garbage collection mais agressivo"
            ]
        
        elif rule.alert_type == AlertType.SYSTEM_DEGRADATION:
            title = "⚠️ Degradação do Sistema"
            message = (
                f"Taxa de sucesso caiu para {value:.1f}%, abaixo do limiar de {rule.threshold}%. "
                f"Sistema pode estar instável."
            )
            recommendations = [
                "🚨 AÇÃO URGENTE: Investigar causa raiz imediatamente",
                "Revisar logs de sistema e aplicação",
                "Verificar saúde do Supabase e conexões",
                "Considerar rollback de mudanças recentes",
                "Monitorar recursos de infraestrutura (CPU, memória, disco)"
            ]
        
        else:
            title = f"🔔 Alerta: {rule.alert_type.value}"
            message = f"Valor {value} excedeu limiar {rule.threshold}"
            recommendations = ["Investigar causa do alerta"]
        
        return title, message, recommendations
    
    def _check_cooldown(self, rule_id: str, cooldown_minutes: int) -> bool:
        """
        Verifica se o cooldown expirou para uma regra.
        
        Args:
            rule_id: ID da regra
            cooldown_minutes: Tempo de cooldown em minutos
            
        Returns:
            True se pode gerar alerta, False se em cooldown
        """
        if rule_id not in self.last_alert_times:
            return True
        
        last_time = self.last_alert_times[rule_id]
        elapsed = (datetime.now() - last_time).total_seconds() / 60
        
        return elapsed >= cooldown_minutes
    
    def _persist_alert(self, alert: Alert):
        """Persiste alerta no Supabase."""
        try:
            supabase.table('sandbox_alerts').insert(alert.to_dict()).execute()
            logger.debug(f"💾 Alerta persistido: {alert.alert_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao persistir alerta: {e}")
    
    def get_recent_alerts(
        self,
        hours: int = 24,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """
        Obtém alertas recentes do histórico.
        
        Args:
            hours: Período em horas
            level: Filtrar por nível (opcional)
            
        Returns:
            Lista de alertas
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        alerts = [
            a for a in self.alert_history
            if a.timestamp >= cutoff
        ]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def register_callback(self, rule_id: str, callback: Callable[[Alert], None]):
        """
        Registra callback para uma regra específica.
        
        Args:
            rule_id: ID da regra
            callback: Função a ser chamada quando alerta for gerado
        """
        if rule_id in self.rules:
            self.rules[rule_id].callback = callback
            logger.debug(f"📞 Callback registrado para: {rule_id}")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from src.monitoring.sandbox_monitor import SandboxMonitor
    from datetime import timedelta
    
    # Criar monitor e alert manager
    monitor = SandboxMonitor(enable_persistence=False)
    alert_manager = AlertManager(monitor, enable_persistence=False)
    
    # Callback customizado
    def send_email_notification(alert: Alert):
        print(f"\n📧 EMAIL ENVIADO:")
        print(f"Para: admin@example.com")
        print(f"Assunto: {alert.title}")
        print(f"Mensagem: {alert.message}")
        print(f"Recomendações:")
        for rec in alert.recommendations or []:
            print(f"  - {rec}")
    
    # Registrar callback
    alert_manager.register_callback('high_failure_rate', send_email_notification)
    
    # Simular execuções com falhas
    for i in range(20):
        result = {
            'success': i % 2 == 0,  # 50% falha
            'result': None if i % 2 != 0 else 42,
            'execution_time_ms': 10.0,
            'error': 'Test error' if i % 2 != 0 else None,
            'error_type': 'RuntimeError' if i % 2 != 0 else None
        }
        monitor.record_execution(
            code=f"resultado = {i}",
            result=result
        )
    
    # Avaliar alertas
    alerts = alert_manager.evaluate_all()
    
    print(f"\n{'='*60}")
    print(f"Total de alertas gerados: {len(alerts)}")
    for alert in alerts:
        print(f"\n{alert.to_json()}")
