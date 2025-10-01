"""Tests for the enterprise orchestrator module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

class TestEnterpriseOrchestrator:
    """Test cases for the EnterpriseIPOOrchestrator class."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an EnterpriseIPOOrchestrator instance with mocked dependencies."""
        with patch('ipo_reminder.database.DatabaseManager') as mock_db, \
             patch('ipo_reminder.cache.CacheManager') as mock_cache, \
             patch('ipo_reminder.official_apis.BSEAPIClient') as mock_bse, \
             patch('ipo_reminder.official_apis.NSEAPIClient') as mock_nse, \
             patch('ipo_reminder.emailer.Emailer') as mock_emailer, \
             patch('ipo_reminder.ipo_categorizer.IPOCategorizer') as mock_categorizer, \
             patch('ipo_reminder.investment_advisor.InvestmentAdvisor') as mock_advisor, \
             patch('ipo_reminder.deep_analyzer.DeepIPOAnalyzer') as mock_analyzer:
            
            from ipo_reminder.enterprise_orchestrator import EnterpriseIPOOrchestrator
            
            # Create the orchestrator
            orchestrator = EnterpriseIPOOrchestrator()
            
            # Set up mock return values
            mock_db.return_value.initialize = AsyncMock()
            mock_cache.return_value.initialize = AsyncMock(return_value=True)
            mock_bse.return_value.initialize = AsyncMock()
            mock_nse.return_value.initialize = AsyncMock()
            
            # Store mock references for assertions
            orchestrator._mocks = {
                'db': mock_db.return_value,
                'cache': mock_cache.return_value,
                'bse': mock_bse.return_value,
                'nse': mock_nse.return_value,
                'emailer': mock_emailer.return_value,
                'categorizer': mock_categorizer.return_value,
                'advisor': mock_advisor.return_value,
                'analyzer': mock_analyzer.return_value
            }
            
            yield orchestrator
    
    @pytest.mark.asyncio
    async def test_initialize(self, orchestrator):
        """Test orchestrator initialization."""
        # Call initialize
        await orchestrator.initialize()
        
        # Verify all components were initialized
        orchestrator._mocks['db'].initialize.assert_awaited_once()
        orchestrator._mocks['cache'].initialize.assert_awaited_once()
        orchestrator._mocks['bse'].initialize.assert_awaited_once()
        orchestrator._mocks['nse'].initialize.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_shutdown(self, orchestrator):
        """Test orchestrator shutdown."""
        # Setup mocks
        orchestrator._mocks['bse'].shutdown = AsyncMock()
        orchestrator._mocks['nse'].shutdown = AsyncMock()
        orchestrator._mocks['emailer'].close = AsyncMock()
        
        # Call shutdown
        await orchestrator.shutdown()
        
        # Verify all components were shut down
        orchestrator._mocks['bse'].shutdown.assert_awaited_once()
        orchestrator._mocks['nse'].shutdown.assert_awaited_once()
        orchestrator._mocks['emailer'].close.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_run_enterprise_cycle(self, orchestrator):
        """Test the main enterprise cycle."""
        # Setup mocks
        orchestrator._mocks['db'].get_active_ipos = AsyncMock(return_value=[])
        orchestrator._mocks['bse'].fetch_ipos = AsyncMock(return_value=[])
        orchestrator._mocks['nse'].fetch_ipos = AsyncMock(return_value=[])
        orchestrator._mocks['categorizer'].categorize = MagicMock(return_value={
            'category': 'MAIN',
            'risk_level': 'low',
            'key_metrics': {}
        })
        orchestrator._mocks['advisor'].analyze = AsyncMock(return_value={
            'recommendation': 'subscribe',
            'confidence': 0.85,
            'analysis': 'Strong fundamentals',
            'risk_level': 'low'
        })
        orchestrator._mocks['analyzer'].analyze = AsyncMock(return_value={
            'sentiment': 'positive',
            'key_phrases': ['growth potential', 'strong management'],
            'entities': [{'text': 'Test Company', 'type': 'ORGANIZATION'}]
        })
        
        # Mock the scrapers
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = []
        orchestrator.scrapers = {'test': mock_scraper}
        
        # Run the enterprise cycle
        await orchestrator.run_enterprise_cycle()
        
        # Verify the flow
        orchestrator._mocks['db'].get_active_ipos.assert_awaited_once()
        orchestrator._mocks['bse'].fetch_ipos.assert_awaited_once()
        orchestrator._mocks['nse'].fetch_ipos.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_process_ipo(self, orchestrator):
        """Test processing a single IPO."""
        # Setup test data
        ipo_data = {
            'name': 'Test IPO',
            'symbol': 'TST',
            'price_range': '100-110',
            'lot_size': 15,
            'issue_date': '2023-11-01',
            'close_date': '2023-11-10',
            'listing_date': '2023-11-20',
            'min_investment': 15000,
            'source': 'test_source',
            'url': 'http://example.com/ipo/test',
        }
        
        # Setup mocks
        orchestrator._mocks['db'].get_ipo_by_name_and_dates = AsyncMock(return_value=None)
        orchestrator._mocks['db'].create_ipo = AsyncMock(return_value=MagicMock(id=1))
        orchestrator._mocks['db'].create_recommendation = AsyncMock()
        orchestrator._mocks['emailer'].send_ipo_notification = AsyncMock(return_value=True)
        
        # Mock the analyze methods
        orchestrator._mocks['categorizer'].categorize.return_value = {
            'category': 'MAIN',
            'risk_level': 'low',
            'key_metrics': {}
        }
        orchestrator._mocks['advisor'].analyze.return_value = {
            'recommendation': 'subscribe',
            'confidence': 0.85,
            'analysis': 'Strong fundamentals',
            'risk_level': 'low'
        }
        orchestrator._mocks['analyzer'].analyze.return_value = {
            'sentiment': 'positive',
            'key_phrases': ['growth potential'],
            'entities': []
        }
        
        # Process the IPO
        result = await orchestrator._process_ipo(ipo_data)
        
        # Verify the result
        assert result is not None
        orchestrator._mocks['db'].create_ipo.assert_awaited_once()
        orchestrator._mocks['emailer'].send_ipo_notification.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, orchestrator):
        """Test getting system status."""
        # Setup mocks
        orchestrator._mocks['db'].get_status = AsyncMock(return_value={
            'status': 'ok',
            'connection': True,
            'tables': ['ipos', 'recommendations']
        })
        orchestrator._mocks['cache'].get_status = AsyncMock(return_value={
            'status': 'ok',
            'connection': True,
            'keys': 5
        })
        orchestrator._mocks['bse'].get_status = AsyncMock(return_value={
            'status': 'ok',
            'last_success': '2023-11-01T10:00:00Z'
        })
        orchestrator._mocks['nse'].get_status = AsyncMock(return_value={
            'status': 'ok',
            'last_success': '2023-11-01T10:00:00Z'
        })
        
        # Get the status
        status = await orchestrator.get_system_status()
        
        # Verify the status
        assert status['overall_status'] == 'operational'
        assert 'database' in status['components']
        assert 'cache' in status['components']
        assert 'bse_api' in status['components']
        assert 'nse_api' in status['components']
        
        # Verify the timestamps
        assert 'start_time' in status
        assert 'current_time' in status
        assert 'uptime' in status
