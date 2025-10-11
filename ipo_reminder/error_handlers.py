"""Error handling utilities for the IPO Reminder system."""
import asyncio
import functools
import logging
import signal
import time
from typing import Any, Callable, TypeVar, Optional
from .exceptions import IPOReminderError
from .logging_config import get_logger

logger = get_logger(__name__)
F = TypeVar('F', bound=Callable[..., Any])

def handle_errors(
    log_errors: bool = True,
    reraise: bool = True,
    default_msg: str = "An error occurred"
) -> Callable[[F], F]:
    """Decorator for consistent error handling and logging."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except IPOReminderError as e:
                if log_errors:
                    logger.error(f"{e.__class__.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return None
            except Exception as e:
                error_msg = f"{default_msg}: {str(e)}"
                if log_errors:
                    logger.error(error_msg, exc_info=True)
                if reraise:
                    raise IPOReminderError(error_msg) from e
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except IPOReminderError as e:
                if log_errors:
                    logger.error(f"{e.__class__.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return None
            except Exception as e:
                error_msg = f"{default_msg}: {str(e)}"
                if log_errors:
                    logger.error(error_msg, exc_info=True)
                if reraise:
                    raise IPOReminderError(error_msg) from e
                return None
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def retry_on_failure(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry a function with exponential backoff on failure."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def timeout_handler(timeout_seconds: float = 30.0):
    """Decorator to handle function timeouts."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                error_msg = f"Function {func.__name__} timed out after {timeout_seconds} seconds"
                logger.error(error_msg)
                raise IPOReminderError(error_msg) from None
            except Exception as e:
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            def signal_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            old_handler = signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple = (Exception,)
):
    """Circuit breaker pattern to prevent cascading failures."""
    def decorator(func: F) -> F:
        failure_count = 0
        last_failure_time = 0
        state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal failure_count, last_failure_time, state
            
            current_time = time.time()
            
            # Check if we should attempt recovery
            if state == "OPEN" and (current_time - last_failure_time) > recovery_timeout:
                state = "HALF_OPEN"
                logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
            
            # Reject if circuit is open
            if state == "OPEN":
                raise IPOReminderError(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                if state == "HALF_OPEN":
                    state = "CLOSED"
                    failure_count = 0
                    logger.info(f"Circuit breaker for {func.__name__} reset to CLOSED")
                return result
                
            except expected_exceptions as e:
                failure_count += 1
                last_failure_time = current_time
                
                if failure_count >= failure_threshold:
                    state = "OPEN"
                    logger.error(f"Circuit breaker for {func.__name__} opened after {failure_count} failures")
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal failure_count, last_failure_time, state
            
            current_time = time.time()
            
            # Check if we should attempt recovery
            if state == "OPEN" and (current_time - last_failure_time) > recovery_timeout:
                state = "HALF_OPEN"
                logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
            
            # Reject if circuit is open
            if state == "OPEN":
                raise IPOReminderError(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                if state == "HALF_OPEN":
                    state = "CLOSED"
                    failure_count = 0
                    logger.info(f"Circuit breaker for {func.__name__} reset to CLOSED")
                return result
                
            except expected_exceptions as e:
                failure_count += 1
                last_failure_time = current_time
                
                if failure_count >= failure_threshold:
                    state = "OPEN"
                    logger.error(f"Circuit breaker for {func.__name__} opened after {failure_count} failures")
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class ErrorContext:
    """Context manager for error handling and cleanup."""
    
    def __init__(self, operation_name: str, cleanup_func: Optional[Callable] = None):
        self.operation_name = operation_name
        self.cleanup_func = cleanup_func
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"Operation {self.operation_name} completed successfully in {duration:.2f}s")
        else:
            logger.error(f"Operation {self.operation_name} failed after {duration:.2f}s: {exc_val}")
            
            if self.cleanup_func:
                try:
                    self.cleanup_func()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed for {self.operation_name}: {cleanup_error}")
        
        return False  # Don't suppress exceptions


def safe_execute(
    func: Callable,
    *args,
    default_return=None,
    timeout: Optional[float] = None,
    max_retries: int = 0,
    **kwargs
) -> Any:
    """Safely execute a function with error handling and optional retry."""
    try:
        # Handle timeout for async functions
        if timeout and asyncio.iscoroutinefunction(func):
            async def run_with_timeout():
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task
                return loop.run_until_complete(run_with_timeout())
            except RuntimeError:
                # No running loop, use asyncio.run
                return asyncio.run(run_with_timeout())
        elif timeout:
            # For sync functions, we can't easily implement timeout without signals
            logger.warning("Timeout not supported for synchronous functions")
        
        # Handle retries
        if max_retries > 0:
            # Apply retry decorator to the function
            retry_func = retry_on_failure(max_retries)(func)
            return retry_func(*args, **kwargs)
        
        return func(*args, **kwargs)
        
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return default_return
