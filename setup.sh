#!/bin/bash
# Complete setup script for IPO Reminder Bot

echo "🚀 Setting up IPO Reminder Bot..."

# Create .env with template
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << 'EOF'
# Replace with your real Outlook credentials
SENDER_EMAIL=your_outlook_email@outlook.com
SENDER_PASSWORD=your_app_password_here
RECIPIENT_EMAIL=recipient@example.com

# Optional settings (defaults work fine)
REQUEST_TIMEOUT=30
REQUEST_RETRIES=3
REQUEST_DELAY=1.0
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
EOF
    echo "✅ Created .env file"
else
    echo "📄 .env file already exists"
fi

echo ""
echo "📧 To get your Outlook App Password:"
echo "1. Go to: https://account.microsoft.com/security"
echo "2. Click 'Advanced security options'"
echo "3. Under 'App passwords', click 'Create a new app password'"
echo "4. Select 'Mail' and copy the generated password"
echo "5. Edit .env and replace 'your_app_password_here' with that password"
echo "6. Replace 'your_outlook_email@outlook.com' with your actual email"
echo ""

echo "🧪 Test commands:"
echo "# Test without sending (safe):"
echo "./venv/bin/python -m ipo_reminder.ipo_reminder --dry-run"
echo ""
echo "# Send real email (after configuring .env):"
echo "./venv/bin/python -m ipo_reminder.ipo_reminder"
echo ""

echo "🎯 GitHub Actions setup:"
echo "Add these repository secrets in GitHub:"
echo "- SENDER_EMAIL (or OUTLOOK_EMAIL)"
echo "- SENDER_PASSWORD (or OUTLOOK_APP_PASSWORD)" 
echo "- RECIPIENT_EMAIL"
echo ""

echo "✅ Setup complete! Edit .env with your credentials and test with --dry-run"
