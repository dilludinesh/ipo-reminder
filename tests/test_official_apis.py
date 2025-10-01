"""Tests for the official_apis module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
import json

class TestBSEAPIClient:
    """Test cases for the BSEAPIClient class."""
    
    @pytest.fixture
    def bse_client(self):
        """Create a BSEAPIClient instance with mocked dependencies."""
        with patch('aiohttp.ClientSession') as mock_session:
            from ipo_reminder.official_apis import BSEAPIClient
            client = BSEAPIClient(api_key="test_key")
            client.session = mock_session.return_value
            yield client
    
    @pytest.mark.asyncio
    async def test_initialize(self, bse_client):
        """Test client initialization."""
        await bse_client.initialize()
        assert bse_client.initialized is True
    
    @pytest.mark.asyncio
    async def test_fetch_ipos_success(self, bse_client):
        """Test successful IPO data fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'Table1': [
                {
                    'COMPANY_NAME': 'Test Company',
                    'SYMBOL': 'TEST',
                    'ISSUE_PRICE': '100-110',
                    'ISSUE_OPEN': '01/11/2023',
                    'ISSUE_CLOSE': '10/11/2023',
                    'LISTING_DATE': '20/11/2023',
                    'LOT_SIZE': '15',
                    'MIN_INVESTMENT': '15000',
                    'ISSUE_DETAILS_URL': 'http://example.com/ipo/test'
                }
            ]
        }
        
        # Configure the mock session
        bse_client.session.get.return_value.__aenter__.return_value = mock_response
        
        # Fetch IPOs
        ipos = await bse_client.fetch_ipos()
        
        # Verify the result
        assert len(ipos) == 1
        assert ipos[0]['name'] == 'Test Company'
        assert ipos[0]['symbol'] == 'TEST'
        assert ipos[0]['price_range'] == '100-110'
        
        # Verify the API call
        bse_client.session.get.assert_called_once()
        assert 'api_key=test_key' in bse_client.session.get.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_fetch_ipos_failure(self, bse_client):
        """Test handling of API failure."""
        # Mock a failed response
        mock_response = MagicMock()
        mock_response.status = 500
        bse_client.session.get.return_value.__aenter__.return_value = mock_response
        
        # Fetch IPOs and expect an empty list on failure
        ipos = await bse_client.fetch_ipos()
        assert ipos == []
    
    @pytest.mark.asyncio
    async def test_shutdown(self, bse_client):
        """Test client shutdown."""
        bse_client.session.close = AsyncMock()
        await bse_client.shutdown()
        bse_client.session.close.assert_awaited_once()
        assert bse_client.initialized is False


class TestNSEAPIClient:
    """Test cases for the NSEAPIClient class."""
    
    @pytest.fixture
    def nse_client(self):
        """Create an NSEAPIClient instance with mocked dependencies."""
        with patch('aiohttp.ClientSession') as mock_session:
            from ipo_reminder.official_apis import NSEAPIClient
            client = NSEAPIClient(api_key="test_key")
            client.session = mock_session.return_value
            yield client
    
    @pytest.mark.asyncio
    async def test_initialize(self, nse_client):
        """Test client initialization."""
        await nse_client.initialize()
        assert nse_client.initialized is True
    
    @pytest.mark.asyncio
    async def test_fetch_ipos_success(self, nse_client):
        """Test successful IPO data fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'data': {
                'data': [
                    {
                        'symbol': 'TEST',
                        'companyName': 'Test Company',
                        'priceRange': '100-110',
                        'openDate': '01-11-2023',
                        'closeDate': '10-11-2023',
                        'listingDate': '20-11-2023',
                        'lotSize': '15',
                        'minInvestment': '15000',
                        'url': 'http://example.com/ipo/test'
                    }
                ]
            }
        }
        
        # Configure the mock session
        nse_client.session.get.return_value.__aenter__.return_value = mock_response
        
        # Fetch IPOs
        ipos = await nse_client.fetch_ipos()
        
        # Verify the result
        assert len(ipos) == 1
        assert ipos[0]['name'] == 'Test Company'
        assert ipos[0]['symbol'] == 'TEST'
        assert ipos[0]['price_range'] == '100-110'
        
        # Verify the API call
        nse_client.session.get.assert_called_once()
        assert 'api_key=test_key' in nse_client.session.get.call_args[1]['headers']['Authorization']
    
    @pytest.mark.asyncio
    async def test_fetch_ipos_failure(self, nse_client):
        """Test handling of API failure."""
        # Mock a failed response
        mock_response = MagicMock()
        mock_response.status = 500
        nse_client.session.get.return_value.__aenter__.return_value = mock_response
        
        # Fetch IPOs and expect an empty list on failure
        ipos = await nse_client.fetch_ipos()
        assert ipos == []
    
    @pytest.mark.asyncio
    async def test_shutdown(self, nse_client):
        """Test client shutdown."""
        nse_client.session.close = AsyncMock()
        await nse_client.shutdown()
        nse_client.session.close.assert_awaited_once()
        assert nse_client.initialized is False
