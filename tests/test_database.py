"""Tests for the database module."""
import pytest
from datetime import datetime
from ipo_reminder.database import DatabaseManager, IPOData, IPORecommendation

class TestDatabase:
    """Test cases for database operations."""
    
    @pytest.mark.asyncio
    async def test_initialize_database(self, mock_db_session):
        """Test database initialization."""
        db_manager = DatabaseManager()
        await db_manager.initialize()
        assert db_manager.engine is not None
        
    @pytest.mark.asyncio
    async def test_create_ipo(self, mock_db_session):
        """Test creating a new IPO record."""
        _, mock_session = mock_db_session
        db_manager = DatabaseManager()
        
        ipo_data = {
            'name': 'Test IPO',
            'symbol': 'TST',
            'price_range': '100-110',
            'lot_size': 15,
            'issue_date': '2023-11-01',
            'close_date': '2023-11-03',
            'listing_date': '2023-11-10',
            'min_investment': 15000,
            'source': 'test_source',
            'url': 'http://example.com/ipo/test',
        }
        
        ipo = await db_manager.create_ipo(ipo_data)
        
        assert ipo is not None
        assert ipo.name == 'Test IPO'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_get_ipo_by_id(self, mock_db_session):
        """Test retrieving an IPO by ID."""
        _, mock_session = mock_db_session
        db_manager = DatabaseManager()
        
        mock_ipo = IPOData(
            id=1,
            name='Test IPO',
            symbol='TST',
            price_range='100-110',
            lot_size=15,
            issue_date='2023-11-01',
            close_date='2023-11-03',
            listing_date='2023-11-10',
            min_investment=15000,
            source='test_source',
            url='http://example.com/ipo/test',
        )
        
        mock_session.get.return_value = mock_ipo
        
        ipo = await db_manager.get_ipo_by_id(1)
        
        assert ipo is not None
        assert ipo.id == 1
        assert ipo.name == 'Test IPO'
        mock_session.get.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_update_ipo_status(self, mock_db_session):
        """Test updating IPO status."""
        _, mock_session = mock_db_session
        db_manager = DatabaseManager()
        
        await db_manager.update_ipo_status(1, 'listed', '2023-11-10')
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_get_active_ipos(self, mock_db_session):
        """Test retrieving active IPOs."""
        _, mock_session = mock_db_session
        db_manager = DatabaseManager()
        
        mock_ipo = IPOData(
            id=1,
            name='Test IPO',
            status='open',
            issue_date='2023-11-01',
            close_date='2023-11-10',
        )
        
        mock_session.scalars.return_value.all.return_value = [mock_ipo]
        
        ipos = await db_manager.get_active_ipos()
        
        assert len(ipos) == 1
        assert ipos[0].status == 'open'
        mock_session.scalars.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_recommendation(self, mock_db_session):
        """Test creating an IPO recommendation."""
        _, mock_session = mock_db_session
        db_manager = DatabaseManager()
        
        recommendation_data = {
            'ipo_id': 1,
            'recommendation': 'subscribe',
            'confidence': 0.85,
            'analysis': 'Strong fundamentals and growth potential',
            'risk_level': 'low',
        }
        
        recommendation = await db_manager.create_recommendation(recommendation_data)
        
        assert recommendation is not None
        assert recommendation.recommendation == 'subscribe'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
