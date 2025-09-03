#!/usr/bin/env python3
"""
Enterprise IPO Reminder - Direct Runner
Runs the enterprise system directly to send real daily emails
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def run_enterprise_system():
    """Run the enterprise IPO reminder system."""
    try:
        print("🚀 INITIALIZING ENTERPRISE IPO REMINDER SYSTEM...")
        print("=" * 60)

        # Import after path setup
        from ipo_reminder.enterprise_orchestrator import enterprise_orchestrator

        print("✅ Enterprise Orchestrator imported successfully")

        # Initialize the system
        print("🔧 Initializing system components...")
        await enterprise_orchestrator.initialize()
        print("✅ System initialization complete")

        print()
        print("🔍 FETCHING IPO DATA...")
        print("=" * 60)

        # Run the enterprise cycle
        await enterprise_orchestrator.run_enterprise_cycle()

        print()
        print("✅ ENTERPRISE CYCLE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📧 Email sent (if IPOs were found)")
        print("📊 System logs saved to logs/ directory")
        print("🔍 IPO data stored in database")

        # Get system status
        print()
        print("📈 SYSTEM STATUS:")
        print("-" * 30)
        status = await enterprise_orchestrator.get_system_status()
        print(f"Overall Status: {status.get('overall_status', 'UNKNOWN')}")
        print(f"Uptime: {status.get('uptime', 'N/A')}")
        print(f"Database: {status.get('components', {}).get('database', {}).get('status', 'UNKNOWN')}")
        print(f"Cache: {status.get('components', {}).get('cache', {}).get('status', 'UNKNOWN')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            await enterprise_orchestrator.shutdown()
            print("🔄 System shutdown complete")
        except:
            pass

if __name__ == "__main__":
    print("🏢 ENTERPRISE IPO REMINDER SYSTEM")
    print("==================================")
    print(f"⏰ Execution time: {os.popen('date').read().strip()}")
    print()

    # Load environment variables if .env exists
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded from .env")
        except ImportError:
            print("⚠️  python-dotenv not installed, using system environment variables")
    else:
        print("⚠️  No .env file found, using system environment variables")

    print()
    asyncio.run(run_enterprise_system())

    print()
    print("🎉 EXECUTION COMPLETE!")
    print("======================")
    print("🏆 Enterprise IPO Reminder System ran successfully!")
