#!/bin/bash

echo "=== IPO BOT GMAIL SETUP SCRIPT ==="
echo "This script will update your .env file with Gmail configuration"
echo ""

# Get current directory
SCRIPT_DIR="/Users/dinesh/ipo-reminder-bot"
ENV_FILE="$SCRIPT_DIR/.env"

echo "📧 Gmail Configuration Required:"
echo "1. Gmail address (e.g., yourname@gmail.com)"
echo "2. Gmail app password (16-character code from Google)"
echo ""
echo "To get Gmail app password:"
echo "• Go to https://myaccount.google.com/security"
echo "• Enable 2-Step Verification"
echo "• Generate App Password for 'Mail'"
echo ""

read -p "Enter your Gmail address: " GMAIL_ADDRESS
read -p "Enter your Gmail app password: " GMAIL_APP_PASSWORD

echo ""
echo "🔄 Updating configuration..."

# Backup current .env
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backed up current .env file"

# Update .env file
sed -i '' "s/SENDER_EMAIL=.*/SENDER_EMAIL=$GMAIL_ADDRESS/" "$ENV_FILE"
sed -i '' "s/SENDER_PASSWORD=.*/SENDER_PASSWORD=$GMAIL_APP_PASSWORD/" "$ENV_FILE"
sed -i '' "s/RECIPIENT_EMAIL=.*/RECIPIENT_EMAIL=$GMAIL_ADDRESS/" "$ENV_FILE"
sed -i '' "s/SMTP_SERVER=.*/SMTP_SERVER=smtp.gmail.com/" "$ENV_FILE"
sed -i '' "s/SMTP_PORT=.*/SMTP_PORT=587/" "$ENV_FILE"

echo "✅ Updated .env file with Gmail configuration"
echo ""
echo "📋 New Configuration:"
echo "SENDER_EMAIL=$GMAIL_ADDRESS"
echo "RECIPIENT_EMAIL=$GMAIL_ADDRESS"
echo "SMTP_SERVER=smtp.gmail.com"
echo "SMTP_PORT=587"
echo ""
echo "🧪 Running test email..."
python3 "$SCRIPT_DIR/test_gmail_smtp.py"
