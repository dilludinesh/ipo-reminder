# IPO Reminder Bot - Email Setup Options

## Current Issue
Microsoft has disabled basic authentication (username/password) for Outlook.com personal accounts.
The bot cannot send emails using traditional SMTP with your personal Outlook account.

## Solution Options

### Option 1: Gmail SMTP (Recommended - Easiest)
Gmail still supports "App Passwords" for SMTP access.

#### Steps:
1. Create a Gmail account (or use existing)
2. Enable 2-Factor Authentication
3. Generate an App Password for Mail
4. Update .env file with Gmail credentials

#### Gmail SMTP Settings:
```
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### To get Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App passwords
4. Generate password for "Mail"
5. Use that password in SENDER_PASSWORD

### Option 2: Keep Outlook with OAuth2 SMTP
More complex - requires OAuth2 for SMTP (not just Graph API).

### Option 3: Use Email Service Provider
SendGrid, Mailgun, etc. - requires signup but very reliable.

## Quick Test
If you want to try Gmail, I can help you set it up quickly.
Just let me know a Gmail address you'd like to use!
