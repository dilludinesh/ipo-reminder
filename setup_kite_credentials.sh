#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📈 Kite Connect Setup for IPO Reminder${NC}"
echo -e "${YELLOW}==================================${NC}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    chmod 600 .env  # Restrict permissions for security
else
    echo -e "${YELLOW}.env file already exists. Backing up as .env.bak...${NC}"
    cp .env .env.bak
fi

# Function to prompt for Kite API credentials
setup_kite_credentials() {
    echo -e "\n${YELLOW}🔑 Kite Connect API Credentials${NC}"
    echo -e "${YELLOW}============================${NC}"
    
    # Kite API Key
    while true; do
        read -p "Enter your Kite API Key: " KITE_API_KEY
        if [ -n "$KITE_API_KEY" ]; then
            break
        else
            echo -e "${RED}❌ API Key cannot be empty. Please try again.${NC}"
        fi
    done
    
    # Kite API Secret
    while true; do
        read -s -p "Enter your Kite API Secret: " KITE_API_SECRET
        echo ""  # New line after password input
        if [ -n "$KITE_API_SECRET" ]; then
            break
        else
            echo -e "${RED}❌ API Secret cannot be empty. Please try again.${NC}"
        fi
    done

    # Redirect URL (with default)
    read -p "Enter redirect URL [http://localhost:5000/callback]: " KITE_REDIRECT_URL
    KITE_REDIRECT_URL=${KITE_REDIRECT_URL:-'http://localhost:5000/callback'}

    # Update .env file
    echo -e "\n${GREEN}Updating .env file...${NC}"
    
    # Remove existing Kite config if any
    sed -i '' '/^KITE_/d' .env
    
    # Add new Kite config
    echo "# Kite Connect Configuration" >> .env
    echo "KITE_API_KEY=$KITE_API_KEY" >> .env
    echo "KITE_API_SECRET=$KITE_API_SECRET" >> .env
    echo "KITE_REDIRECT_URL=$KITE_REDIRECT_URL" >> .env
    echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" >> .env
    
    echo -e "\n${GREEN}✅ Kite Connect configuration saved to .env file${NC}"
    echo -e "${YELLOW}Note: The .env file contains sensitive information. Do not commit it to version control!${NC}"
}

# Function to test Kite connection
test_kite_connection() {
    echo -e "\n${YELLOW}🔌 Testing Kite Connect Connection${NC}"
    echo -e "${YELLOW}==============================${NC}"
    
    # Source the .env file
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo -e "${RED}❌ .env file not found. Please run the setup first.${NC}"
        return 1
    fi
    
    # Check if required variables are set
    if [ -z "$KITE_API_KEY" ] || [ -z "$KITE_API_SECRET" ]; then
        echo -e "${RED}❌ Kite API credentials not found. Please run the setup first.${NC}"
        return 1
    fi
    
    echo -e "Starting Kite Connect web server..."
    echo -e "Open this URL in your browser to authenticate: ${GREEN}http://localhost:5000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server when done.${NC}"
    
    # Run the Kite integration script
    python3 kite_integration.py
}

# Main menu
while true; do
    echo -e "\n${YELLOW}📡 Kite Connect Menu${NC}"
    echo -e "${YELLOW}==================${NC}"
    echo "1. Setup Kite API Credentials"
    echo "2. Test Kite Connection"
    echo "3. Exit"
    echo -n "\nEnter your choice (1-3): "
    
    read choice
    case $choice in
        1) setup_kite_credentials ;;
        2) test_kite_connection ;;
        3) echo -e "${GREEN}Goodbye! 👋${NC}"; exit 0 ;;
        *) echo -e "${RED}❌ Invalid choice. Please try again.${NC}" ;;
    esac
done
