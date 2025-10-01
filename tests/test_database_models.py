"""Tests for database models."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from ipo_reminder.database import (
    IPOData, 
    IPORecommendation, 
    SystemConfig,
    AuditLog,
    SystemMetrics
)

class TestModels:
    """Test cases for database models."""
    
    def test_ipo_data_model(self):
        """Test IPOData model."""
        now = datetime.utcnow()
        ipo = IPOData(
            company_name='Test',
            symbol='TST',
            platform='Mainboard',
            status='open',
            open_date=now
        )
        assert ipo.company_name == 'Test'
        assert ipo.status == 'open'

    def test_ipo_recommendation_model(self):
        """Test IPORecommendation model."""
        ipo = IPOData(company_name='Test', symbol='TST')
        rec = IPORecommendation(
            ipo=ipo,
            recommendation='BUY',
            target_price=120.0,
            confidence_score=80
        )
        assert rec.recommendation == 'BUY'
        assert rec.confidence_score == 80

    def test_system_config_model(self):
        """Test SystemConfig model."""
        config = SystemConfig(
            key='test',
            value='value',
            description='Test config'
        )
        assert config.key == 'test'
        assert config.value == 'value'

    def test_audit_log_model(self):
        """Test AuditLog model."""
        log = AuditLog(
            action='CREATE',
            entity_type='IPO',
            status='SUCCESS'
        )
        assert log.action == 'CREATE'
        assert log.status == 'SUCCESS'

    def test_system_metrics_model(self):
        """Test SystemMetrics model."""
        metrics = SystemMetrics(
            metric_name='cpu_usage',
            metric_value=75.5,
            metric_type='GAUGE'
        )
        assert metrics.metric_name == 'cpu_usage'
        assert metrics.metric_value == 75.5
