"""
Rate limiting and circuit breaking utilities for the IPO Reminder system.

This module provides:
- Token bucket rate limiting
- Sliding window rate limiting
- Circuit breaker pattern
- Request timeouts
- Bulkhead pattern
"""
import time
import asyncio
from typing import Dict, Optional, Callable, Any, Awaitable, TypeVar, cast
from functools import wraps
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import random

# Type variable for generic function wrapping
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: int = 10
    burst_capacity: int = 20
    time_window: int = 60  # seconds

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: int = 300  # seconds
    half_open_max_requests: int = 3

class RateLimiter:
    """Implements token bucket rate limiting algorithm."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a token if available."""
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            
            # Add tokens based on time passed
            self.tokens = min(
                self.config.burst_capacity,
                self.tokens + (time_passed * (self.config.requests_per_second / self.config.time_window))
            )
            self.last_update = now
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False
    
    async def wait_for_token(self, timeout: Optional[float] = None) -> bool:
        """Wait until a token is available or timeout occurs."""
        # First try to acquire without waiting
        if await self.acquire():
            return True
            
        if timeout is None or timeout <= 0:
            return False
            
        start_time = time.monotonic()
        end_time = start_time + timeout
        
        while time.monotonic() < end_time:
            # Calculate time until next token should be available
            now = time.monotonic()
            elapsed = now - self.last_update
            new_tokens = elapsed * (self.config.requests_per_second / self.config.time_window)
            
            if new_tokens >= 1.0:  # At least one token is available
                self.tokens = min(self.tokens + new_tokens, self.config.burst_capacity)
                self.last_update = now
                
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
            
            # Calculate time to wait before next check
            time_to_wait = min(0.1, end_time - time.monotonic())
            if time_to_wait > 0:
                await asyncio.sleep(time_to_wait)
        
        return False

class SlidingWindowRateLimiter:
    """Implements sliding window rate limiting with Redis backend."""
    
    def __init__(self, redis_client: Any, key_prefix: str, config: RateLimitConfig):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.config = config
    
    def _get_key(self, identifier: str) -> str:
        """Get the Redis key for the given identifier."""
        return f"{self.key_prefix}:{identifier}"
    
    async def is_rate_limited(self, identifier: str) -> bool:
        """Check if the request should be rate limited."""
        key = self._get_key(identifier)
        now = int(time.time() * 1000)  # Current time in milliseconds
        window = self.config.time_window * 1000  # Convert to milliseconds
        
        async with self.redis.pipeline() as pipe:
            try:
                # Add current timestamp to the sorted set
                pipe.zadd(key, {str(now): now})
                # Remove timestamps outside the current window
                pipe.zremrangebyscore(key, 0, now - window)
                # Get count of requests in current window
                pipe.zcard(key)
                # Set expiration on the key
                pipe.expire(key, self.config.time_window + 1)
                
                # Execute all commands in a single transaction
                _, _, count, _ = await pipe.execute()
                
                return count > self.config.requests_per_second
                
            except Exception as e:
                logger.error(f"Redis error in rate limiting: {e}")
                # Fail open - don't rate limit if Redis is down
                return False

class CircuitBreaker:
    """Implements the circuit breaker pattern."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_requests = 0
        self.lock = asyncio.Lock()
    
    async def execute(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute the function with circuit breaker protection."""
        if not await self.allow_request():
            raise CircuitOpenError(f"Circuit breaker for {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            if self.state == "OPEN":
                raise CircuitOpenError(f"Circuit breaker for {self.name} is open") from e
            raise
    
    async def allow_request(self) -> bool:
        """Check if a request is allowed based on circuit state."""
        async with self.lock:
            if self.state == "OPEN":
                # Check if we should move to HALF_OPEN
                if (self.last_failure_time is not None and 
                    time.time() - self.last_failure_time > self.config.recovery_timeout):
                    self.state = "HALF_OPEN"
                    self.half_open_requests = 1
                    return True
                return False
            
            if self.state == "HALF_OPEN":
                if self.half_open_requests >= self.config.half_open_max_requests:
                    return False
                self.half_open_requests += 1
            
            return True
    
    async def record_success(self) -> None:
        """Record a successful operation."""
        async with self.lock:
            if self.state == "HALF_OPEN":
                # Success in HALF_OPEN state, close the circuit
                self.state = "CLOSED"
                self.failure_count = 0
                self.half_open_requests = 0
            elif self.state == "CLOSED":
                # Reset failure count on success
                self.failure_count = 0
    
    async def record_failure(self, error: Exception) -> None:
        """Record a failed operation."""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == "CLOSED" and self.failure_count >= self.config.failure_threshold:
                self.state = "OPEN"
            elif self.state == "HALF_OPEN":
                # Failure in HALF_OPEN state, open the circuit
                self.state = "OPEN"
                self.half_open_requests = 0

class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open."""
    pass

def rate_limited(requests: int = 10, window: int = 60):
    """Decorator to rate limit function calls."""
    def decorator(func: F) -> F:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_second=requests,
            time_window=window
        ))
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await limiter.acquire():
                raise RateLimitExceeded(
                    f"Rate limit exceeded: {requests} requests per {window} seconds"
                )
            return await func(*args, **kwargs)
            
        return cast(F, wrapper)
    return decorator

class RateLimitExceeded(Exception):
    """Raised when the rate limit is exceeded."""
    pass

class Bulkhead:
    """Implements the bulkhead pattern to limit concurrent operations."""
    
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute the function with bulkhead protection."""
        async with self.semaphore:
            return await func(*args, **kwargs)

# Global rate limiters and circuit breakers
rate_limiters: Dict[str, RateLimiter] = {}
circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_rate_limiter(name: str, config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create a named rate limiter."""
    if name not in rate_limiters:
        rate_limiters[name] = RateLimiter(config or RateLimitConfig())
    return rate_limiters[name]

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(name, config or CircuitBreakerConfig())
    return circuit_breakers[name]
