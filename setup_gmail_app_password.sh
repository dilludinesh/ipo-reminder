#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 IPO Reminder - Gmail App Password Setup${NC}"
echo -e "${BLUE}=========================================${NC}\n"

echo -e "${YELLOW}📋 Step-by-Step Gmail App Password Setup:${NC}"
echo -e "${YELLOW}=========================================${NC}\n"

echo -e "${GREEN}Step 1: Enable 2-Factor Authentication${NC}"
echo "   • Go to: https://myaccount.google.com/security"
echo "   • Sign in with your Gmail account"
echo "   • Navigate to 'Security'"
echo "   • Enable '2-Step Verification'"
echo "   • Follow the setup process"
echo ""

echo -e "${GREEN}Step 2: Generate App Password${NC}"
echo "   • Go to: https://myaccount.google.com/apppasswords"
echo "   • Sign in again if prompted"
echo "   • Click 'Select app' dropdown → Choose 'Mail'"
echo "   • Click 'Select device' dropdown → Choose 'Other (custom name)'"
echo "   • Enter 'IPO Reminder' as the custom name"
echo "   • Click 'Generate'"
echo "   • Copy the 16-character password (e.g., abcd-efgh-ijkl-mnop)"
echo ""

echo -e "${GREEN}Step 3: Configure Your System${NC}"
echo "   • Update your .env file with real credentials:"
echo "     SENDER_EMAIL=your-gmail@gmail.com"
echo "     SENDER_PASSWORD=your-16-char-app-password"
echo "     RECIPIENT_EMAIL=your-email@gmail.com"
echo ""
echo "   • Update GitHub secrets (if using workflows):"
echo "     - Go to GitHub repo Settings → Secrets and variables → Actions"
echo "     - Update SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL"
echo ""

echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "   • App Password is different from your regular Gmail password"
echo "   • Each app needs its own App Password"
echo "   • App Passwords are 16 characters with dashes"
echo "   • Never share your App Password"
echo ""

echo -e "${BLUE}🔍 Troubleshooting:${NC}"
echo "   • If 'App passwords' option isn't visible, ensure 2FA is enabled"
echo "   • Make sure you're signed into the correct Google account"
echo "   • App passwords work only with Gmail addresses"
echo ""

echo -e "${GREEN}✅ After Setup:${NC}"
echo "   • Run: python test_email_direct.py"
echo "   • Check if you receive the test email"
echo "   • Your GitHub Actions will send real IPO reminders!"
echo ""

read -p "Press Enter when you've completed the Gmail App Password setup..."
