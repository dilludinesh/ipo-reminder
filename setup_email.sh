#!/bin/bash
# Email Configuration Setup Script
# This script helps you configure email settings for the Enterprise IPO Reminder

echo "🚀 ENTERPRISE IPO REMINDER - EMAIL SETUP"
echo "=========================================="
echo ""

# Check if running on macOS (for pbcopy)
if [[ "$OSTYPE" == "darwin"* ]]; then
    HAS_CLIPBOARD=true
else
    HAS_CLIPBOARD=false
fi

echo "📧 EMAIL CONFIGURATION REQUIRED"
echo "-------------------------------"
echo ""
echo "To send emails, you need to configure these environment variables:"
echo ""
echo "1. SENDER_EMAIL    - Your Gmail address"
echo "2. SENDER_PASSWORD - Your Gmail App Password (NOT your regular password)"
echo "3. RECIPIENT_EMAIL - Email address to receive IPO reminders"
echo ""

# Gmail App Password Instructions
echo "🔐 GMAIL APP PASSWORD SETUP:"
echo "----------------------------"
echo "1. Go to: https://myaccount.google.com/security"
echo "2. Enable 2-Factor Authentication (if not already enabled)"
echo "3. Go to: https://myaccount.google.com/apppasswords"
echo "4. Select 'Mail' and 'Other (custom name)'"
echo "5. Enter 'IPO Reminder' as the custom name"
echo "6. Copy the 16-character password"
echo ""

# Create .env file
echo "📝 CREATING .env FILE..."
cat > .env << 'EOF'
# Enterprise IPO Reminder - Email Configuration
# Replace these values with your actual credentials

# Email Configuration (REQUIRED)
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=your-16-character-app-password
RECIPIENT_EMAIL=recipient@email.com

# Database Configuration (for Enterprise features)
DATABASE_URL=postgresql://user:password@localhost:5432/ipo_reminder

# Redis Cache Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# API Keys (optional but recommended)
BSE_API_KEY=your-bse-api-key
NSE_API_KEY=your-nse-api-key

# Security (generate random keys)
ENCRYPTION_KEY=your-32-character-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key

# Enterprise Features
ENTERPRISE_MODE=true
MONITORING_ENABLED=true
AUDIT_ENABLED=true
EOF

echo "✅ Created .env file with template configuration"
echo ""

# Show next steps
echo "🎯 NEXT STEPS:"
echo "-------------"
echo ""
echo "1. 📧 Configure Gmail App Password:"
echo "   • Visit: https://myaccount.google.com/apppasswords"
echo "   • Generate password for 'IPO Reminder'"
echo ""
echo "2. ✏️  Edit the .env file:"
echo "   • Open .env in your text editor"
echo "   • Replace placeholder values with your actual credentials"
echo ""
echo "3. 🧪 Test email functionality:"
echo "   python3 test_email.py"
echo ""
echo "4. 🚀 Run the enterprise system:"
echo "   python3 -m ipo_reminder.enterprise_orchestrator"
echo ""

# Show example configuration
echo "📋 EXAMPLE CONFIGURATION:"
echo "------------------------"
echo ""
echo "# Replace these in your .env file:"
echo "SENDER_EMAIL=john.doe@gmail.com"
echo "SENDER_PASSWORD=abcd-efgh-ijkl-mnop"
echo "RECIPIENT_EMAIL=john.doe@gmail.com"
echo ""

echo "⚠️  SECURITY NOTES:"
echo "------------------"
echo "• Never commit .env file to version control"
echo "• Keep your App Password secure"
echo "• Use strong encryption keys for production"
echo ""

echo "🎉 SETUP COMPLETE!"
echo "=================="
echo "Your Enterprise IPO Reminder is ready to send emails!"
echo "Configure your credentials and run: python3 test_email.py"
