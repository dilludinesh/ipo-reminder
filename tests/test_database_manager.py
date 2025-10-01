"""Tests for DatabaseManager class."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from ipo_reminder.database import DatabaseManager, IPOData, SystemConfig
from ipo_reminder.exceptions import DBConnectionError, NotFoundError

@pytest.fixture
def db_manager():
    """Fixture to provide a DatabaseManager instance."""
    return DatabaseManager()

@pytest.fixture
def sample_ipo_data():
    """Sample IPO data for testing."""
    return {
        'company_name': 'Test',
        'symbol': 'TST',
        'platform': 'Mainboard',
        'status': 'open'
    }

class TestDatabaseManager:
    """Test cases for DatabaseManager class."""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, db_manager):
        """Test successful session creation."""
        mock_session = AsyncMock()
        db_manager.async_session_factory = MagicMock(return_value=mock_session)
        
        async with db_manager.get_session() as session:
            assert session == mock_session
            
        mock_session.close.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_get_session_connection_error(self, db_manager):
        """Test session creation with connection error."""
        mock_session = AsyncMock()
        mock_session.connection.side_effect = OperationalError("Connection failed", [], None)
        db_manager.async_session_factory = MagicMock(return_value=mock_session)
        
        with pytest.raises(DBConnectionError):
            async with db_manager.get_session():
                pass
                
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_create_success(self, db_manager, sample_ipo_data):
        """Test successful record creation."""
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            result = await db_manager.create(IPOData, **sample_ipo_data)
            
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_get_success(self, db_manager):
        """Test successful record retrieval."""
        mock_ipo = MagicMock()
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_ipo
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            result = await db_manager.get(IPOData, 1)
            
        assert result == mock_ipo
        mock_session.get.assert_called_once_with(IPOData, 1)
        
    @pytest.mark.asyncio
    async def test_get_not_found(self, db_manager):
        """Test record not found scenario."""
        mock_session = AsyncMock()
        mock_session.get.return_value = None
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            with pytest.raises(NotFoundError):
                await db_manager.get(IPOData, 999)
    
    @pytest.mark.asyncio
    async def test_update_success(self, db_manager):
        """Test successful record update."""
        mock_ipo = MagicMock()
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            result = await db_manager.update(mock_ipo, status='closed')
            
        assert result == mock_ipo
        mock_session.add.assert_called_once_with(mock_ipo)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(mock_ipo)
        
    @pytest.mark.asyncio
    async def test_delete_success(self, db_manager):
        """Test successful record deletion."""
        mock_ipo = MagicMock()
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            result = await db_manager.delete(mock_ipo)
            
        assert result is True
        mock_session.delete.assert_called_once_with(mock_ipo)
        mock_session.commit.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_initialize_config(self, db_manager):
        """Test system configuration initialization."""
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)
        
        with patch.object(db_manager, 'get_session', return_value=mock_session):
            await db_manager._initialize_config()
            
        # Verify that config items were added
        assert mock_session.add.call_count > 0
        mock_session.commit.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_get_stats(self, db_manager):
        """Test getting database statistics."""
        # Setup mock engine and pool
        mock_pool = MagicMock()
        mock_pool.checkedin.return_value = 2
        mock_pool.size.return_value = 5
        mock_pool.overflow.return_value = 0
        mock_pool.timeout.return_value = 30
        mock_pool.checkedout.return_value = 1
        
        db_manager.engine = MagicMock()
        db_manager.engine.pool = mock_pool
        db_manager.engine.dialect.name = 'sqlite'
        db_manager.engine.driver = 'aiosqlite'
        db_manager.engine.url = 'sqlite:///test.db'
        
        # Call the method
        stats = await db_manager.get_stats()
        
        # Verify the results
        assert stats['status'] == 'operational'
        assert stats['connection_count'] == 2
        assert stats['pool_size'] == 5
        assert 'url' in stats
