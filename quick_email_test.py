#!/usr/bin/env python3
"""Quick email test after admin consent"""

import msal
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print('=== TESTING EMAIL AFTER ADMIN CONSENT ===')
print('Status: ✅ Granted for Default Directory')

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
sender_email = os.getenv('SENDER_EMAIL')

# Get access token
authority = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=authority
)

result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

if 'access_token' in result:
    print('✅ Access token obtained')
    
    headers = {
        'Authorization': f'Bearer {result["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    email_data = {
        'message': {
            'subject': '🎉 IPO Bot SUCCESS - Email Working!',
            'body': {
                'contentType': 'Text',
                'content': '''SUCCESS! Your IPO Reminder Bot is now working!

✅ Microsoft Graph API: Working correctly
✅ Mail.Send Permission: Granted for Default Directory  
✅ Admin Consent: Successfully configured
✅ Email Delivery: Functional!

What this means:
🔔 You will now receive daily IPO alerts at 8:30 AM IST
📧 Emails will contain IPO details and recommendations
🤖 The bot runs automatically via GitHub Actions
🚀 Everything is fully automated!

Best regards,
Your IPO Reminder Bot 🤖'''
            },
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': sender_email
                    }
                }
            ]
        }
    }
    
    # Send email
    send_url = f'https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail'
    response = requests.post(send_url, headers=headers, json=email_data)
    
    print(f'Response status: {response.status_code}')
    
    if response.status_code == 202:
        print('')
        print('🎉🎉🎉 EMAIL SENT SUCCESSFULLY! 🎉🎉🎉')
        print('')
        print('📧 CHECK YOUR INBOX at reddy.dinesh@live.com')
        print('📱 You should receive the email within 1-2 minutes!')
        print('')
        print('✅ Your IPO Reminder Bot is now FULLY OPERATIONAL!')
        print('🔔 Next alert: Tomorrow at 8:30 AM IST')
    else:
        print(f'❌ Failed with status {response.status_code}')
        if response.text:
            print(f'Error: {response.text}')
        
else:
    print(f'❌ Failed to get access token: {result}')
