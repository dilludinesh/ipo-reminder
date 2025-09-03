#!/bin/bash
# Enterprise IPO Reminder - Manual Workflow Runner
# This script simulates the GitHub Actions workflow locally

echo "🚀 ENTERPRISE IPO REMINDER - MANUAL WORKFLOW"
echo "============================================"
echo ""
echo "⏰ Execution time:"
echo "  UTC: $(date -u '+%Y-%m-%d %H:%M:%S %Z')"
echo "  IST: $(TZ='Asia/Kolkata' date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please run: ./setup_email.sh"
    exit 1
fi

# Load environment variables
echo "🔧 Loading configuration..."
export $(grep -v '^#' .env | xargs)

# Check required email configuration
if [ -z "$SENDER_EMAIL" ] || [ -z "$SENDER_PASSWORD" ] || [ -z "$RECIPIENT_EMAIL" ]; then
    echo "❌ Email configuration incomplete!"
    echo "Please edit .env file with your email credentials"
    echo ""
    echo "Required:"
    echo "  SENDER_EMAIL=your-gmail@gmail.com"
    echo "  SENDER_PASSWORD=your-app-password"
    echo "  RECIPIENT_EMAIL=recipient@email.com"
    exit 1
fi

echo "✅ Email configuration found"
echo "📧 Sender: $SENDER_EMAIL"
echo "📧 Recipient: $RECIPIENT_EMAIL"
echo ""

# Install dependencies if needed
echo "📦 Checking dependencies..."
if ! python3 -c "import sqlalchemy, redis, aiohttp" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Setup database (if PostgreSQL is available)
echo "📊 Setting up database..."
if command -v psql &> /dev/null; then
    # Create database if it doesn't exist
    createdb ipo_reminder 2>/dev/null || echo "Database already exists"
    python3 setup_database.py setup
else
    echo "⚠️  PostgreSQL not found, using in-memory database"
    export DATABASE_URL="sqlite:///ipo_reminder.db"
fi

# Setup Redis (if available)
if command -v redis-server &> /dev/null; then
    echo "🔄 Redis found, using Redis cache"
else
    echo "⚠️  Redis not found, using memory cache"
    export REDIS_URL=""
fi

echo ""
echo "🏢 STARTING ENTERPRISE IPO ORCHESTRATOR..."
echo "=========================================="

# Run the enterprise system
python3 -c "
from ipo_reminder.enterprise_orchestrator import enterprise_orchestrator
import asyncio
import sys

async def main():
    try:
        print('🚀 Initializing Enterprise System...')
        await enterprise_orchestrator.initialize()
        print('✅ Enterprise System Ready')
        print()
        print('🔍 Fetching IPO Data...')
        await enterprise_orchestrator.run_enterprise_cycle()
        print()
        print('✅ Enterprise Cycle Completed Successfully!')
        print('📧 Email sent (if IPOs were found)')
    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)
    finally:
        await enterprise_orchestrator.shutdown()

asyncio.run(main())
"

echo ""
echo "🎉 WORKFLOW COMPLETED!"
echo "======================"
echo ""
echo "📧 Check your email for IPO reminders"
echo "📊 System logs saved to logs/ directory"
echo "🔍 IPO data stored in database"
echo ""
echo "🏆 Enterprise IPO Reminder System executed successfully!"
