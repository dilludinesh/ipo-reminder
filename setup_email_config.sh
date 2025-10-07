#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📧 IPO Reminder - Email Configuration Setup${NC}"
echo -e "${YELLOW}======================================${NC}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    chmod 600 .env  # Restrict permissions for security
else
    echo -e "${YELLOW}.env file already exists. Backing up as .env.bak...${NC}"
    cp .env .env.bak
fi

# Function to prompt for email config
setup_email_config() {
    echo -e "\n${YELLOW}📩 Email Configuration${NC}"
    echo -e "${YELLOW}====================${NC}"
    
    # Sender Email
    while true; do
        read -p "Enter sender email address (e.g., your-email@gmail.com): " SENDER_EMAIL
        if [[ "$SENDER_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
            break
        else
            echo -e "${RED}❌ Invalid email format. Please try again.${NC}"
        fi
    done

    # Password/App Password
    echo -e "\n${YELLOW}🔑 Email Password/App Password${NC}"
    echo -e "For Gmail with 2FA, you need to generate an App Password:"
    echo -e "1. Go to your Google Account Settings"
    echo -e "2. Navigate to Security > App passwords"
    echo -e "3. Generate a new app password and paste it below\n"
    
    read -s -p "Enter your email password or app password: " SENDER_PASSWORD
    echo ""  # New line after password input

    # Recipient Email
    while true; do
        read -p "\nEnter recipient email address (press Enter to use $SENDER_EMAIL): " RECIPIENT_EMAIL
        if [ -z "$RECIPIENT_EMAIL" ]; then
            RECIPIENT_EMAIL="$SENDER_EMAIL"
            break
        elif [[ "$RECIPIENT_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
            break
        else
            echo -e "${RED}❌ Invalid email format. Please try again.${NC}"
        fi
    done

    # Update .env file
    echo -e "\n${GREEN}Updating .env file...${NC}"
    
    # Remove existing email config if any
    sed -i '' '/^SENDER_EMAIL=.*/d' .env
    sed -i '' '/^SENDER_PASSWORD=.*/d' .env
    sed -i '' '/^RECIPIENT_EMAIL=.*/d' .env
    
    # Add new email config
    echo "SENDER_EMAIL=$SENDER_EMAIL" >> .env
    echo "SENDER_PASSWORD=$SENDER_PASSWORD" >> .env
    echo "RECIPIENT_EMAIL=$RECIPIENT_EMAIL" >> .env
    
    echo -e "\n${GREEN}✅ Email configuration saved to .env file${NC}"
    echo -e "${YELLOW}Note: The .env file contains sensitive information. Do not commit it to version control!${NC}"
}

# Function to test email configuration
test_email_config() {
    echo -e "\n${YELLOW}✉️  Testing Email Configuration${NC}"
    echo -e "${YELLOW}============================${NC}"
    
    # Source the .env file to get the variables
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo -e "${RED}❌ .env file not found. Please run the setup first.${NC}"
        exit 1
    fi
    
    # Check if required variables are set
    if [ -z "$SENDER_EMAIL" ] || [ -z "$SENDER_PASSWORD" ] || [ -z "$RECIPIENT_EMAIL" ]; then
        echo -e "${RED}❌ Email configuration is incomplete. Please run the setup first.${NC}"
        exit 1
    fi
    
    echo -e "Sending test email from ${GREEN}$SENDER_EMAIL${NC} to ${GREEN}$RECIPIENT_EMAIL${NC}"
    echo -e "${YELLOW}This might take a moment...${NC}"
    
    # Run the test email script
    python3 check_email.py
    
    echo -e "\n${YELLOW}📨 Check your email inbox (and spam folder) for the test email.${NC}"
}

# Main menu
while true; do
    echo -e "\n${YELLOW}📧 Email Configuration Menu${NC}"
    echo -e "${YELLOW}========================${NC}"
    echo "1. Setup Email Configuration"
    echo "2. Test Email Configuration"
    echo "3. Exit"
    echo -n "\nEnter your choice (1-3): "
    
    read choice
    case $choice in
        1) setup_email_config ;;
        2) test_email_config ;;
        3) echo -e "${GREEN}Goodbye! 👋${NC}"; exit 0 ;;
        *) echo -e "${RED}❌ Invalid choice. Please try again.${NC}" ;;
    esac
done
