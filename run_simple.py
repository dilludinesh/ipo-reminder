#!/usr/bin/env python3
"""
Enterprise IPO Reminder - Simple Runner
Changes to the ipo_reminder directory and runs the orchestrator
"""

import os
import sys
import subprocess

def main():
    """Main entry point."""
    print("🏢 ENTERPRISE IPO REMINDER SYSTEM")
    print("==================================")
    print(f"⏰ Execution time: {os.popen('date').read().strip()}")
    print()

    # Change to the ipo_reminder directory
    ipo_dir = os.path.join(os.path.dirname(__file__), 'ipo_reminder')
    os.chdir(ipo_dir)

    print(f"📁 Changed directory to: {ipo_dir}")

    # Run the enterprise orchestrator directly
    cmd = [sys.executable, '-c', '''
import asyncio
import sys
sys.path.insert(0, ".")

async def main():
    from enterprise_orchestrator import enterprise_orchestrator
    print("✅ Enterprise Orchestrator imported successfully")

    print("🔧 Initializing system components...")
    await enterprise_orchestrator.initialize()
    print("✅ System initialization complete")

    print()
    print("🔍 FETCHING IPO DATA...")
    print("=" * 60)

    await enterprise_orchestrator.run_enterprise_cycle()

    print()
    print("✅ ENTERPRISE CYCLE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("📧 Email sent (if IPOs were found)")
    print("📊 System logs saved to logs/ directory")
    print("🔍 IPO data stored in database")

    status = await enterprise_orchestrator.get_system_status()
    print()
    print("📈 SYSTEM STATUS:")
    print("-" * 30)
    print(f"Overall Status: {status.get(\"overall_status\", \"UNKNOWN\")}")
    print(f"Uptime: {status.get(\"uptime\", \"N/A\")}")
    print(f"Database: {status.get(\"components\", {}).get(\"database\", {}).get(\"status\", \"UNKNOWN\")}")
    print(f"Cache: {status.get(\"components\", {}).get(\"cache\", {}).get(\"status\", \"UNKNOWN\")}")

asyncio.run(main())
''']

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        print()
        print("🎉 EXECUTION COMPLETE!")
        print("======================")
        print("🏆 Enterprise IPO Reminder System ran successfully!")
    else:
        print("❌ ERROR:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
