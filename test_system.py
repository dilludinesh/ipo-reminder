#!/usr/bin/env python3
"""Simple test script to verify the IPO Reminder system is working."""

import os
import sys

def test_env_configuration():
    """Test that environment variables are loaded correctly."""
    print("🧪 Testing Environment Configuration...")
    print("=" * 50)

    # Load .env file manually
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    # Check email configuration
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    print("📧 Email Configuration:")
    print(f"  SENDER_EMAIL: {sender_email}")
    print(f"  SENDER_PASSWORD: {'***' if sender_password else 'Not set'}")
    print(f"  RECIPIENT_EMAIL: {recipient_email}")

    if all([sender_email, sender_password, recipient_email]):
        print("✅ Email configuration loaded successfully")
        return True
    else:
        print("❌ Email configuration incomplete")
        return False

def test_imports():
    """Test that our modules can be imported."""
    print("\n🧪 Testing Module Imports...")
    print("=" * 50)

    try:
        # Test basic imports
        import asyncio
        print("✅ asyncio imported successfully")

        # Test our modules (without database dependencies for now)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Test error handlers (should work without external deps)
        from ipo_reminder.error_handlers import handle_errors, retry_on_failure, ErrorContext
        print("✅ Error handlers imported successfully")

        # Test config module
        from ipo_reminder.config import SENDER_EMAIL, RECIPIENT_EMAIL
        print("✅ Config module imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_error_handlers():
    """Test error handling functionality."""
    print("\n🧪 Testing Error Handlers...")
    print("=" * 50)

    from ipo_reminder.error_handlers import safe_execute, ErrorContext

    # Test safe_execute
    result = safe_execute(lambda: "test successful")
    if result == "test successful":
        print("✅ safe_execute working correctly")
    else:
        print("❌ safe_execute failed")
        return False

    # Test ErrorContext
    try:
        with ErrorContext("test operation"):
            pass
        print("✅ ErrorContext working correctly")
    except Exception as e:
        print(f"❌ ErrorContext failed: {e}")
        return False

    return True

def main():
    """Run all tests."""
    print("🚀 IPO Reminder System Test Suite")
    print("=" * 60)

    tests = [
        test_env_configuration,
        test_imports,
        test_error_handlers
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i+1}: {test.__name__:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
