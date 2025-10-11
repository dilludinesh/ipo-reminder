#!/usr/bin/env python3
"""Test script for error handlers."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ipo_reminder.error_handlers import (
    handle_errors, retry_on_failure, timeout_handler,
    circuit_breaker, ErrorContext, safe_execute
)


# Test function that always fails
@retry_on_failure(max_retries=2)
def failing_function():
    print("Function called - will fail")
    raise ValueError("Test error")


# Test function that succeeds after retries
attempt_count = 0
@retry_on_failure(max_retries=3)
def eventually_succeeding_function():
    global attempt_count
    attempt_count += 1
    print(f"Attempt {attempt_count}")
    if attempt_count < 3:
        raise ConnectionError("Temporary failure")
    return "Success!"


# Test timeout function
@timeout_handler(timeout_seconds=2)
async def slow_async_function():
    await asyncio.sleep(1)
    return "Completed"


@timeout_handler(timeout_seconds=0.5)
async def timeout_async_function():
    await asyncio.sleep(2)  # This should timeout
    return "Should not reach here"


# Test circuit breaker
call_count = 0
@circuit_breaker(failure_threshold=2, recovery_timeout=1)
def flaky_function():
    global call_count
    call_count += 1
    if call_count <= 2:
        raise ConnectionError("Service unavailable")
    return f"Success on call {call_count}"


async def test_error_handlers():
    print("🧪 Testing Error Handlers...")
    print("=" * 50)

    # Test 1: Retry with eventual success
    print("\n1. Testing retry with eventual success:")
    try:
        result = eventually_succeeding_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 2: Retry with failure
    print("\n2. Testing retry with failure:")
    try:
        failing_function()
        print("❌ Should have failed")
    except Exception as e:
        print(f"✅ Expected failure: {e}")

    # Test 3: Async timeout success
    print("\n3. Testing async timeout (success):")
    try:
        result = await slow_async_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 4: Async timeout failure
    print("\n4. Testing async timeout (failure):")
    try:
        result = await timeout_async_function()
        print(f"❌ Should have timed out: {result}")
    except Exception as e:
        print(f"✅ Expected timeout: {e}")

# Test circuit breaker
call_count = 0
@circuit_breaker(failure_threshold=2, recovery_timeout=1)
def flaky_function():
    global call_count
    call_count += 1
    if call_count <= 2:
        raise ConnectionError("Service unavailable")
    return f"Success on call {call_count}"


async def test_error_handlers():
    print("🧪 Testing Error Handlers...")
    print("=" * 50)

    # Test 1: Retry with eventual success
    print("\n1. Testing retry with eventual success:")
    try:
        result = eventually_succeeding_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 2: Retry with failure
    print("\n2. Testing retry with failure:")
    try:
        failing_function()
        print("❌ Should have failed")
    except Exception as e:
        print(f"✅ Expected failure: {e}")

    # Test 3: Async timeout success
    print("\n3. Testing async timeout (success):")
    try:
        result = await slow_async_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 4: Async timeout failure
    print("\n4. Testing async timeout (failure):")
    try:
        result = await timeout_async_function()
        print(f"❌ Should have timed out: {result}")
    except Exception as e:
        print(f"✅ Expected timeout: {e}")

    # Test 5: Circuit breaker (test multiple failures)
    print("\n5. Testing circuit breaker:")
    try:
        # First call - should fail
        result = flaky_function()
        print(f"❌ Should have failed: {result}")
    except Exception as e:
        print(f"✅ First failure: {e}")

    try:
        # Second call - should open circuit
        result = flaky_function()
        print(f"❌ Should have opened circuit: {result}")
    except Exception as e:
        print(f"✅ Circuit opened: {e}")

    # Test 6: Error context
    print("\n6. Testing error context:")
    try:
        with ErrorContext("test operation"):
            raise ValueError("Test error")
    except ValueError as e:
        print(f"✅ Context manager handled error: {e}")

    # Test 7: Safe execute
    print("\n7. Testing safe execute:")
    result = safe_execute(lambda: "success")
    print(f"✅ Safe execute result: {result}")

    result = safe_execute(lambda: (_ for _ in ()).throw(ValueError("test")))
    print(f"✅ Safe execute with error: {result}")

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_error_handlers())
