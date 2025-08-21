#!/usr/bin/env python3

import msal
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

print('=== TESTING CORRECT GRAPH API ENDPOINT ===')

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
sender_email = os.getenv('SENDER_EMAIL')

# Get token
authority = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(client_id=client_id, client_credential=client_secret, authority=authority)
result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

if 'access_token' in result:
    headers = {
        'Authorization': f'Bearer {result["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    # The correct endpoint for application permissions is /users/{user-id}/sendMail
    send_mail_url = f'https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail'
    
    # Simple test email
    email_data = {
        'message': {
            'subject': 'IPO Bot Test - Graph API Working!',
            'body': {
                'contentType': 'HTML',
                'content': '<h2>Great News!</h2><p>Your IPO reminder bot is now working correctly with Microsoft Graph API!</p><p><strong>Test Status:</strong> SUCCESS</p><p><strong>Time:</strong> August 21, 2025</p><hr><p><em>This confirms that the Mail.Send permission is properly configured and working.</em></p>'
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
    
    print(f'Sending test email to: {sender_email}')
    print(f'Using endpoint: {send_mail_url}')
    
    response = requests.post(send_mail_url, headers=headers, json=email_data)
    
    print(f'Response Status: {response.status_code}')
    print(f'Response Headers: {dict(response.headers)}')
    print(f'Response Body: {response.text}')
    
    if response.status_code == 202:
        print('\n🎉 SUCCESS! Email sent successfully!')
        print('Check your inbox for the test email.')
    elif response.status_code == 401:
        print('\n❌ Still getting 401. This might be a permission propagation delay.')
        print('Wait 5-10 minutes and try again.')
    else:
        print(f'\n⚠️  Unexpected status code: {response.status_code}')
        
else:
    print('❌ Failed to get access token')
