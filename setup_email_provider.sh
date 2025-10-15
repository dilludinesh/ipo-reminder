#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}📧 IPO Reminder - Email Provider Setup Guide${NC}"
echo -e "${BLUE}===========================================${NC}\n"

echo -e "${PURPLE}🎯 Choose Your Email Provider:${NC}"
echo -e "${PURPLE}============================${NC}\n"

echo -e "${GREEN}📧 Option 1: Gmail (Recommended)${NC}"
echo -e "   → Most reliable for automation"
echo -e "   → Best deliverability rates"
echo -e "   → Comprehensive documentation"
echo ""

echo -e "${YELLOW}📧 Option 2: Outlook/Hotmail${NC}"
echo -e "   → Good alternative option"
echo -e "   → Works well for automation"
echo -e "   → Microsoft ecosystem integration"
echo ""

echo -e "${BLUE}🔑 Gmail Setup (Step-by-Step):${NC}"
echo -e "${BLUE}=============================${NC}\n"

echo -e "${GREEN}Step 1: Enable 2-Factor Authentication${NC}"
echo "   • Go to: https://myaccount.google.com/security"
echo "   • Sign in with your Gmail account"
echo "   • Navigate to 'Security' → '2-Step Verification'"
echo "   • Click 'Get started' and follow the setup"
echo ""

echo -e "${GREEN}Step 2: Generate App Password${NC}"
echo "   • Go to: https://myaccount.google.com/apppasswords"
echo "   • Sign in again if prompted"
echo "   • Click 'Select app' → 'Mail'"
echo "   • Click 'Select device' → 'Other (custom name)'"
echo "   • Enter 'IPO Reminder' as the name"
echo "   • Click 'Generate'"
echo "   • Copy the 16-character password (abcd-efgh-ijkl-mnop)"
echo ""

echo -e "${BLUE}🔑 Outlook Setup (Step-by-Step):${NC}"
echo -e "${BLUE}==============================${NC}\n"

echo -e "${YELLOW}Step 1: Enable 2-Factor Authentication${NC}"
echo "   • Go to: https://account.microsoft.com/security"
echo "   • Sign in with your Outlook account"
echo "   • Navigate to 'Security' → 'More security options'"
echo "   • Set up two-step verification"
echo ""

echo -e "${YELLOW}Step 2: Generate App Password${NC}"
echo "   • Go to: https://account.microsoft.com/security/app-passwords"
echo "   • Sign in again if prompted"
echo "   • Click 'Create a new app password'"
echo "   • Enter 'IPO Reminder' as the app name"
echo "   • Copy the generated password"
echo ""

echo -e "${PURPLE}⚙️  After Getting Your App Password:${NC}"
echo -e "${PURPLE}=================================${NC}\n"

echo -e "${GREEN}Update your .env file:${NC}"
echo "   SENDER_EMAIL=your-email@gmail.com    # or outlook.com"
echo "   SENDER_PASSWORD=your-app-password    # 16-char for Gmail, varies for Outlook"
echo "   RECIPIENT_EMAIL=your-email@gmail.com # or outlook.com"
echo ""

echo -e "${GREEN}Update GitHub Secrets (for workflow automation):${NC}"
echo "   • Go to GitHub repo Settings → Secrets and variables → Actions"
echo "   • Set SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL"
echo ""

echo -e "${BLUE}🧪 Test Your Setup:${NC}"
echo "   • Run: python test_email_direct.py"
echo "   • Check if you receive the test email"
echo ""

echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo -e "${YELLOW}=================${NC}\n"

echo -e "${PURPLE}Gmail:${NC}"
echo "   • App passwords are 16 characters with dashes"
echo "   • Format: abcd-efgh-ijkl-mnop"
echo "   • Use exactly as generated (case-sensitive)"
echo ""

echo -e "${PURPLE}Outlook:${NC}"
echo "   • Password length varies (usually 16-24 characters)"
echo "   • May contain letters, numbers, and special characters"
echo "   • Use exactly as generated"
echo ""

echo -e "${RED}Common Issues:${NC}"
echo "   • 'App passwords not available' → Ensure 2FA is fully enabled"
echo "   • 'Authentication failed' → Double-check the generated password"
echo "   • 'Invalid credentials' → Make sure you're using App password, not regular password"
echo ""

echo -e "${GREEN}✅ What Happens Next:${NC}"
echo "   • Your IPO Reminder will send real emails"
echo "   • GitHub Actions will automate daily reminders"
echo "   • You'll receive professional IPO notifications"
echo ""

read -p "Which email provider would you like to use? (gmail/outlook): " email_provider

if [ "$email_provider" = "gmail" ]; then
    echo -e "\n${GREEN}🔗 Gmail Setup Links:${NC}"
    echo "   2FA Setup: https://myaccount.google.com/security"
    echo "   App Password: https://myaccount.google.com/apppasswords"
elif [ "$email_provider" = "outlook" ]; then
    echo -e "\n${YELLOW}🔗 Outlook Setup Links:${NC}"
    echo "   2FA Setup: https://account.microsoft.com/security"
    echo "   App Password: https://account.microsoft.com/security/app-passwords"
else
    echo -e "\n${RED}❌ Please choose 'gmail' or 'outlook'${NC}"
fi

echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Complete the App Password setup for your chosen provider"
echo "2. Copy the generated password"
echo "3. Let me know when you're ready and I'll configure everything!"
echo ""

read -p "Press Enter when you've completed the App Password setup..."
