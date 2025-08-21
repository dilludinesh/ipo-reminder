#!/bin/bash

# Script to automatically set up GitHub repository secrets for IPO Reminder Bot
# This script uses GitHub CLI to configure all required secrets

echo "� Setting up GitHub repository secrets for IPO Reminder Bot..."

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first:"
    echo "   brew install gh"
    exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI. Please run:"
    echo "   gh auth login"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your credentials first."
    exit 1
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Set the secrets using environment variables
echo "📝 Configuring repository secrets..."

gh secret set CLIENT_ID -b "$CLIENT_ID"
gh secret set CLIENT_SECRET -b "$CLIENT_SECRET"
gh secret set TENANT_ID -b "$TENANT_ID"
gh secret set SENDER_EMAIL -b "$SENDER_EMAIL"
gh secret set RECIPIENT_EMAIL -b "$RECIPIENT_EMAIL"

echo ""
echo "✅ All secrets configured!"
echo ""
echo "🎯 Your IPO Reminder Bot is now fully configured!"
echo "📧 You'll receive daily IPO alerts at 8:30 AM IST at $RECIPIENT_EMAIL"
echo ""
echo "The bot will automatically run via GitHub Actions."
echo "Check the Actions tab in your GitHub repository to monitor execution."
