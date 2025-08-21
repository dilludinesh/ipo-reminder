#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/dinesh/ipo-reminder-bot')

from ipo_reminder.emailer import send_email
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== TESTING EMAIL TO LIVE.COM ADDRESS ===')
print('📧 FROM: dineshreddysalla@gmail.com (Gmail SMTP)')
print('📧 TO: reddy.dinesh@live.com (Your Live.com inbox)')
print()

# Test email
subject = '🎯 IPO Bot Configuration Test - Live.com Delivery'
body = '''Perfect! Your IPO reminder bot is now configured correctly:

✅ SENDER: Gmail account (dineshreddysalla@gmail.com)
✅ RECIPIENT: Your Live.com inbox (reddy.dinesh@live.com)
✅ METHOD: Gmail SMTP (reliable and secure)

This means:
• The bot sends emails using Gmail SMTP (which works reliably)
• You receive IPO alerts in your preferred Live.com inbox
• Best of both worlds - reliable sending + your preferred inbox

Your IPO bot will now send daily alerts to your Live.com email!

---
Configuration: Gmail SMTP → Live.com Inbox
Date: August 22, 2025
Status: Ready for automation
'''

html_body = '''
<h2>🎯 IPO Bot Configuration Test - Live.com Delivery</h2>
<p><strong>Perfect!</strong> Your IPO reminder bot is now configured correctly:</p>

<div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0;">
    <h3>✅ Configuration Summary</h3>
    <ul>
        <li>✅ <strong>SENDER:</strong> Gmail account (dineshreddysalla@gmail.com)</li>
        <li>✅ <strong>RECIPIENT:</strong> Your Live.com inbox (reddy.dinesh@live.com)</li>
        <li>✅ <strong>METHOD:</strong> Gmail SMTP (reliable and secure)</li>
    </ul>
</div>

<div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
    <h3>🎯 This means:</h3>
    <ul>
        <li>• The bot sends emails using Gmail SMTP (which works reliably)</li>
        <li>• You receive IPO alerts in your preferred Live.com inbox</li>
        <li>• Best of both worlds - reliable sending + your preferred inbox</li>
    </ul>
</div>

<p><strong>🚀 Your IPO bot will now send daily alerts to your Live.com email!</strong></p>

<hr>
<p><small><strong>Configuration:</strong> Gmail SMTP → Live.com Inbox<br>
<strong>Date:</strong> August 22, 2025<br>
<strong>Status:</strong> Ready for automation</small></p>
'''

try:
    print('Sending test email...')
    success = send_email(
        subject=subject,
        body=body,
        html_body=html_body
    )
    
    if success:
        print('\n🎉 SUCCESS! Test email sent!')
        print('📧 Check your Live.com inbox: reddy.dinesh@live.com')
        print('✅ Configuration confirmed working!')
        print('\n🤖 Your bot will now send IPO alerts to your Live.com email daily!')
    else:
        print('\n❌ Email sending failed')
        
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
