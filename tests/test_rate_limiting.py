"""
Tests for rate limiting and circuit breaking functionality.
"""
import asyncio
import itertools
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from ipo_reminder.rate_limiting import (
    RateLimiter, CircuitBreaker, RateLimitExceeded, 
    CircuitOpenError, Bulkhead, RateLimitConfig, CircuitBreakerConfig
)

@pytest.fixture
def rate_limit_config():
    return RateLimitConfig(
        requests_per_second=10,
        burst_capacity=20,
        time_window=60
    )

@pytest.fixture
def circuit_breaker_config():
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_requests=2
    )

@pytest.mark.asyncio
async def test_rate_limiter_acquire(rate_limit_config):
    """Test basic rate limiting functionality."""
    limiter = RateLimiter(rate_limit_config)
    
    # First 20 requests should pass (burst capacity)
    for _ in range(20):
        assert await limiter.acquire() is True
    
    # Next requests should be rate limited
    assert await limiter.acquire() is False

@pytest.mark.asyncio
async def test_rate_limiter_wait_for_token(rate_limit_config):
    """Test waiting for token becomes available."""
    limiter = RateLimiter(rate_limit_config)
    
    # Exhaust the burst capacity
    for _ in range(20):
        assert await limiter.acquire() is True
    
    # Next request should be rate limited
    assert await limiter.acquire() is False
    
    # Test that wait_for_token returns True when a token becomes available
    # We'll mock time to simulate waiting
    with patch('time.monotonic', side_effect=itertools.cycle([0.0, 1.0])):
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.return_value = None
            result = await limiter.wait_for_token(timeout=2.0)
            assert result is True
            mock_sleep.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_breaker_success(circuit_breaker_config):
    """Test circuit breaker with successful operations."""
    cb = CircuitBreaker("test_service", circuit_breaker_config)
    
    async def success_func():
        return "success"
    
    # Should work normally
    result = await cb.execute(success_func)
    assert result == "success"
    assert cb.state == "CLOSED"

@pytest.mark.asyncio
async def test_circuit_breaker_failure(circuit_breaker_config):
    """Test circuit breaker opening on failures."""
    cb = CircuitBreaker("test_service", circuit_breaker_config)
    
    async def failing_func():
        raise Exception("Failed")
    
    # First 2 failures should be passed through
    for _ in range(2):
        with pytest.raises(Exception):
            await cb.execute(failing_func)
    
    # 3rd failure should open the circuit
    with pytest.raises(CircuitOpenError):
        await cb.execute(failing_func)
    
    assert cb.state == "OPEN"

@pytest.mark.asyncio
async def test_circuit_breaker_half_open(circuit_breaker_config):
    """Test circuit breaker half-open state and recovery."""
    cb = CircuitBreaker("test_service", circuit_breaker_config)
    
    # Open the circuit
    cb.state = "OPEN"
    cb.last_failure_time = datetime.now().timestamp() - 35  # Past recovery timeout
    
    # First request in half-open state
    async def success_func():
        return "success"
    
    result = await cb.execute(success_func)
    assert result == "success"
    assert cb.state == "CLOSED"  # Should close on success

@pytest.mark.asyncio
async def test_bulkhead_limits_concurrency():
    """Test bulkhead limits concurrent operations."""
    bulkhead = Bulkhead(2)  # Max 2 concurrent operations
    
    # Use an event to track concurrency
    concurrency = 0
    max_concurrency = 0
    concurrency_event = asyncio.Event()
    
    async def long_running():
        nonlocal concurrency, max_concurrency
        concurrency += 1
        max_concurrency = max(max_concurrency, concurrency)
        
        # Signal that we've started
        concurrency_event.set()
        
        try:
            await asyncio.sleep(0.1)
            return "done"
        finally:
            concurrency -= 1
    
    # Start 3 operations
    tasks = [asyncio.create_task(bulkhead.execute(long_running)) for _ in range(3)]
    
    # Wait for at least one task to start
    await asyncio.wait_for(concurrency_event.wait(), timeout=1.0)
    
    # Should have at most 2 tasks running in parallel
    assert max_concurrency <= 2
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all tasks completed successfully
    for task in tasks:
        assert task.done()
        assert await task == "done"

@pytest.mark.asyncio
async def test_rate_limiter_with_circuit_breaker(rate_limit_config, circuit_breaker_config):
    """Test integration of rate limiter with circuit breaker."""
    limiter = RateLimiter(rate_limit_config)
    cb = CircuitBreaker("test_service", circuit_breaker_config)
    
    async def limited_operation():
        if not await limiter.acquire():
            raise RateLimitExceeded("Rate limit exceeded")
        return "success"
    
    # First 20 should work (burst capacity)
    for _ in range(20):
        result = await cb.execute(limited_operation)
        assert result == "success"
    
    # Next should be rate limited
    with pytest.raises(RateLimitExceeded):
        await cb.execute(limited_operation)
    
    # After rate limit, circuit should still be closed
    assert cb.state == "CLOSED"
