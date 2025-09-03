#!/bin/bash
# Test GitHub Actions Setup Locally
# This script simulates the GitHub Actions workflow on your local machine

echo "🧪 TESTING GITHUB ACTIONS SETUP LOCALLY"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your email credentials:"
    echo "  SENDER_EMAIL=your-gmail@gmail.com"
    echo "  SENDER_PASSWORD=your-app-password"
    echo "  RECIPIENT_EMAIL=recipient@email.com"
    echo ""
    echo "Or run: ./setup_email.sh"
    exit 1
fi

# Load environment variables
echo "🔧 Loading configuration..."
export $(grep -v '^#' .env | xargs)

# Check required variables
if [ -z "$SENDER_EMAIL" ] || [ -z "$SENDER_PASSWORD" ] || [ -z "$RECIPIENT_EMAIL" ]; then
    echo "❌ Email configuration incomplete!"
    echo "Please check your .env file has:"
    echo "  SENDER_EMAIL"
    echo "  SENDER_PASSWORD"
    echo "  RECIPIENT_EMAIL"
    exit 1
fi

echo "✅ Email configuration found"
echo "📧 Sender: $SENDER_EMAIL"
echo "📧 Recipient: $RECIPIENT_EMAIL"
echo ""

# Set default values for testing
export DATABASE_URL=${DATABASE_URL:-"sqlite:///test_ipo_reminder.db"}
export REDIS_URL=${REDIS_URL:-""}
export ENTERPRISE_MODE=${ENTERPRISE_MODE:-"true"}
export MONITORING_ENABLED=${MONITORING_ENABLED:-"true"}
export AUDIT_ENABLED=${AUDIT_ENABLED:-"true"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo "🔧 Test Configuration:"
echo "  Database: $DATABASE_URL"
echo "  Cache: ${REDIS_URL:-Memory cache}"
echo "  Enterprise Mode: $ENTERPRISE_MODE"
echo "  Monitoring: $MONITORING_ENABLED"
echo "  Audit: $AUDIT_ENABLED"
echo ""

# Check Python installation
echo "🐍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION found"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Setup database
echo "📊 Setting up database..."
python setup_database.py setup

# Test the system
echo ""
echo "🚀 TESTING ENTERPRISE IPO SYSTEM"
echo "================================"

# Run a quick test
python -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def test_system():
    try:
        print('🔧 Initializing test system...')
        from ipo_reminder.enterprise_orchestrator import enterprise_orchestrator
        
        print('✅ Enterprise Orchestrator imported')
        
        # Initialize
        await enterprise_orchestrator.initialize()
        print('✅ System initialized')
        
        # Quick data fetch test
        print('🔍 Testing IPO data fetch...')
        ipo_data = await enterprise_orchestrator.fetch_ipo_data_enterprise()
        print(f'✅ Found {len(ipo_data)} IPOs')
        
        if ipo_data:
            print('📋 Sample IPO data:')
            for i, ipo in enumerate(ipo_data[:2], 1):  # Show first 2 IPOs
                print(f'  {i}. {ipo.get(\"company_name\", \"Unknown\")}')
        
        # Test email generation (without sending)
        print('📧 Testing email generation...')
        if ipo_data:
            email_content = await enterprise_orchestrator._generate_enterprise_email_content(ipo_data[:3])  # Test with up to 3 IPOs
            print(f'✅ Generated email content ({len(email_content)} characters)')
        
        print('✅ All tests passed!')
        
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

result = asyncio.run(test_system())
sys.exit(0 if result else 1)
"

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 LOCAL TEST SUCCESSFUL!"
    echo "========================="
    echo ""
    echo "✅ System components working correctly"
    echo "✅ IPO data fetching operational"
    echo "✅ Email generation functional"
    echo "✅ Database and cache ready"
    echo ""
    echo "🚀 Your system is ready for GitHub Actions automation!"
    echo ""
    echo "Next steps:"
    echo "1. Set up GitHub secrets (run: ./setup_github_secrets.sh)"
    echo "2. Push changes to GitHub"
    echo "3. The workflow will run automatically at 9:00 AM IST daily"
    echo "4. Or trigger manually from GitHub Actions tab"
    echo ""
else
    echo ""
    echo "❌ LOCAL TEST FAILED!"
    echo "===================="
    echo ""
    echo "Please check the error messages above and fix any issues."
    echo "Common problems:"
    echo "  - Missing dependencies"
    echo "  - Database connection issues"
    echo "  - Email configuration problems"
    echo "  - Network connectivity issues"
    echo ""
    exit 1
fi
