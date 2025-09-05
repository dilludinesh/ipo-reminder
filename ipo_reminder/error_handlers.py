"""Error handling utilities for the IPO Reminder system."""
import functools
import logging
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
