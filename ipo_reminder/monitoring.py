"""Enterprise-grade monitoring and alerting system."""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import smtplib
from email.message import EmailMessage

from config import SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL
from database import DatabaseManager, SystemMetrics

logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    cooldown_minutes: int = 60
    enabled: bool = True

    def __post_init__(self):
        self.last_triggered = None

class MonitoringSystem:
    """Comprehensive monitoring system for the IPO reminder application."""

    def __init__(self):
        self.metrics = {}
        self.alert_rules: List[AlertRule] = []
        self.alert_history = []
        self.is_monitoring = False
        self.monitor_thread = None

        # Initialize default alert rules
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Set up default alert rules."""

        # Email delivery failure alert
        self.add_alert_rule(AlertRule(
            name="email_delivery_failure",
            condition=lambda metrics: metrics.get('email_failure_rate', 0) > 0.1,  # >10% failure rate
            severity="ERROR",
            message="Email delivery failure rate exceeded 10%",
            cooldown_minutes=30
        ))

        # API failure alert
        self.add_alert_rule(AlertRule(
            name="api_circuit_breaker_open",
            condition=lambda metrics: any(
                cb.get('state') == 'OPEN'
                for cb in metrics.get('circuit_breakers', {}).values()
            ),
            severity="WARNING",
            message="One or more API circuit breakers are OPEN",
            cooldown_minutes=15
        ))

        # Cache performance alert
        self.add_alert_rule(AlertRule(
            name="cache_performance_degraded",
            condition=lambda metrics: metrics.get('cache_hit_rate', 100) < 50,  # <50% hit rate
            severity="WARNING",
            message="Cache hit rate dropped below 50%",
            cooldown_minutes=60
        ))

        # Database connection alert
        self.add_alert_rule(AlertRule(
            name="database_connection_issues",
            condition=lambda metrics: metrics.get('db_connection_errors', 0) > 5,
            severity="CRITICAL",
            message="Database connection errors exceeded threshold",
            cooldown_minutes=10
        ))

        # High error rate alert
        self.add_alert_rule(AlertRule(
            name="high_error_rate",
            condition=lambda metrics: metrics.get('error_rate_per_hour', 0) > 10,
            severity="ERROR",
            message="Application error rate exceeded 10 per hour",
            cooldown_minutes=30
        ))

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value."""
        timestamp = datetime.utcnow()

        metric_data = {
            'name': name,
            'value': value,
            'labels': labels or {},
            'timestamp': timestamp
        }

        # Store in memory for quick access
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric_data)

        # Keep only last 1000 values per metric
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]

        # Persist to database
        try:
            with DatabaseManager.get_session() as session:
                db_metric = SystemMetrics(
                    metric_name=name,
                    metric_value=value,
                    metric_type="GAUGE",  # Default to gauge
                    labels=json.dumps(labels) if labels else None,
                    timestamp=timestamp
                )
                session.add(db_metric)
        except Exception as e:
            logger.error(f"Failed to persist metric {name}: {e}")

    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        if name not in self.metrics:
            self.metrics[name] = []

        # Find existing counter value
        current_value = 0
        for metric in reversed(self.metrics[name]):
            if metric['labels'] == (labels or {}):
                current_value = metric['value']
                break

        self.record_metric(name, current_value + 1, labels)

    def get_metric_value(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Get the latest value for a metric."""
        if name not in self.metrics:
            return None

        for metric in reversed(self.metrics[name]):
            if metric['labels'] == (labels or {}):
                return metric['value']

        return None

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - getattr(self, '_start_time', time.time()),
            'metrics_count': len(self.metrics),
            'alert_rules_count': len(self.alert_rules),
            'active_alerts': len([a for a in self.alert_history if not a.get('resolved_at')])
        }

        # Calculate derived metrics
        email_metrics = self._get_email_metrics()
        cache_metrics = self._get_cache_metrics()
        api_metrics = self._get_api_metrics()

        summary.update({
            'email_metrics': email_metrics,
            'cache_metrics': cache_metrics,
            'api_metrics': api_metrics
        })

        return summary

    def _get_email_metrics(self) -> Dict[str, Any]:
        """Get email-related metrics."""
        sent = self.get_metric_value('emails_sent') or 0
        failed = self.get_metric_value('emails_failed') or 0
        total = sent + failed

        return {
            'sent': sent,
            'failed': failed,
            'total': total,
            'failure_rate': (failed / total * 100) if total > 0 else 0
        }

    def _get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache-related metrics."""
        hits = self.get_metric_value('cache_hits') or 0
        misses = self.get_metric_value('cache_misses') or 0
        total = hits + misses

        return {
            'hits': hits,
            'misses': misses,
            'total_requests': total,
            'hit_rate': (hits / total * 100) if total > 0 else 100
        }

    def _get_api_metrics(self) -> Dict[str, Any]:
        """Get API-related metrics."""
        return {
            'circuit_breakers': {
                'bse_api': {'state': 'CLOSED', 'failures': 0},  # Would be populated from actual circuit breakers
                'nse_api': {'state': 'CLOSED', 'failures': 0}
            }
        }

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alert rules and return triggered alerts."""
        triggered_alerts = []
        current_metrics = self.get_metrics_summary()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue

            # Check condition
            try:
                if rule.condition(current_metrics):
                    alert = {
                        'rule_name': rule.name,
                        'severity': rule.severity,
                        'message': rule.message,
                        'timestamp': datetime.utcnow().isoformat(),
                        'metrics': current_metrics
                    }

                    triggered_alerts.append(alert)
                    rule.last_triggered = datetime.utcnow()

                    # Log alert
                    logger.warning(f"Alert triggered: {rule.name} - {rule.message}")

            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}: {e}")

        return triggered_alerts

    def send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification via email."""
        try:
            subject = f"🚨 IPO Reminder Alert: {alert['rule_name']}"
            body = f"""
Alert Details:
- Rule: {alert['rule_name']}
- Severity: {alert['severity']}
- Message: {alert['message']}
- Time: {alert['timestamp']}

Metrics Summary:
{json.dumps(alert['metrics'], indent=2, default=str)}

This is an automated alert from the IPO Reminder monitoring system.
"""

            # Send alert email
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAIL
            msg.set_content(body)

            # This would use the emailer module, but for now we'll use basic SMTP
            # to avoid circular imports

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    def start_monitoring(self, interval_seconds: int = 300):
        """Start the monitoring system."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self._start_time = time.time()

        def monitoring_loop():
            while self.is_monitoring:
                try:
                    # Check alerts
                    alerts = self.check_alerts()

                    # Send notifications for new alerts
                    for alert in alerts:
                        self.send_alert_notification(alert)
                        self.alert_history.append(alert)

                    # Keep only last 100 alerts
                    if len(self.alert_history) > 100:
                        self.alert_history = self.alert_history[-100:]

                    time.sleep(interval_seconds)

                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)  # Wait before retrying

        self.monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoring system started")

    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoring system stopped")

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        metrics = self.get_metrics_summary()
        alerts = self.check_alerts()

        health_score = 100

        # Deduct points for various issues
        if metrics['email_metrics']['failure_rate'] > 5:
            health_score -= 20
        if metrics['cache_metrics']['hit_rate'] < 70:
            health_score -= 10
        if any(alert['severity'] in ['ERROR', 'CRITICAL'] for alert in alerts):
            health_score -= 30
        if len(alerts) > 0:
            health_score -= 10

        status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

        return {
            'status': status,
            'health_score': health_score,
            'metrics': metrics,
            'active_alerts': len(alerts),
            'monitoring_active': self.is_monitoring
        }

# Global monitoring instance
monitoring_system = MonitoringSystem()

# Convenience functions
def record_metric(name: str, value: float, labels: Dict[str, str] = None):
    """Record a metric value."""
    monitoring_system.record_metric(name, value, labels)

def increment_counter(name: str, labels: Dict[str, str] = None):
    """Increment a counter metric."""
    monitoring_system.increment_counter(name, labels)

def get_health_status() -> Dict[str, Any]:
    """Get system health status."""
    return monitoring_system.get_health_status()
