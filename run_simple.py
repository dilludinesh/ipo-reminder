#!/usr/bin/env python3
"""
Enterprise IPO Reminder - Simple Runner
Runs the IPO reminder system with a simple configuration
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

async def run_ipo_reminder():
    """Run the IPO reminder system."""
    try:
        # Import here to avoid circular imports
        from ipo_reminder.enterprise_orchestrator import enterprise_orchestrator
        
        print("✅ Enterprise Orchestrator imported successfully")
        
        print("🔧 Initializing system components...")
        await enterprise_orchestrator.initialize()
        print("✅ System initialization complete")
        
        print("\n🔍 FETCHING IPO DATA...")
        print("=" * 60)
        
        await enterprise_orchestrator.run_enterprise_cycle()
        
        print("\n✅ ENTERPRISE CYCLE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📧 Email sent (if IPOs were found)")
        print("📊 System logs saved to logs/ directory")
        print("🔍 IPO data stored in database")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise

def main():
    """Main entry point."""
    print("🏢 ENTERPRISE IPO REMINDER SYSTEM")
    print("==================================")
    print(f"⏰ Execution time: {os.popen('date').read().strip()}")
    print()
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Run the async function
    try:
        asyncio.run(run_ipo_reminder())
        print("\n🎉 EXECUTION COMPLETE!")
        print("======================")
        print("🏆 Enterprise IPO Reminder System ran successfully!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
