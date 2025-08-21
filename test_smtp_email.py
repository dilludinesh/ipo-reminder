#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/dinesh/ipo-reminder-bot')

from ipo_reminder.emailer import send_email
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=== TESTING UPDATED EMAILER (SMTP FIRST FOR PERSONAL ACCOUNTS) ===")

# Test email
subject = "🎉 IPO Bot is Working - SMTP Test Success!"
body = """Great news! Your IPO reminder bot is now working correctly.

✅ SMTP Configuration: Working
✅ Email Delivery: Success
✅ System Status: Ready for automation

This test confirms that your bot can now send email notifications for IPO reminders.

Time: August 21, 2025
Method: SMTP (Personal Account Compatible)
"""

html_body = """
<h2>🎉 IPO Bot is Working - SMTP Test Success!</h2>
<p><strong>Great news!</strong> Your IPO reminder bot is now working correctly.</p>

<ul>
<li>✅ <strong>SMTP Configuration:</strong> Working</li>
<li>✅ <strong>Email Delivery:</strong> Success</li>
<li>✅ <strong>System Status:</strong> Ready for automation</li>
</ul>

<p>This test confirms that your bot can now send email notifications for IPO reminders.</p>

<hr>
<p><small><strong>Time:</strong> August 21, 2025<br>
<strong>Method:</strong> SMTP (Personal Account Compatible)</small></p>
"""

try:
    success = send_email(
        subject=subject,
        body=body,
        html_body=html_body
    )
    
    if success:
        print("\n🎉 EMAIL SENT SUCCESSFULLY!")
        print("Check your inbox for the test email.")
        print("\nYour IPO reminder bot is now fully functional!")
    else:
        print("\n❌ Email sending failed")
        print("Check the logs above for error details")
        
except Exception as e:
    print(f"\n❌ Error during email test: {e}")
    import traceback
    traceback.print_exc()
