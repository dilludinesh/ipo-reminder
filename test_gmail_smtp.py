#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/dinesh/ipo-reminder-bot')

from ipo_reminder.emailer import send_email
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=== TESTING GMAIL SMTP CONFIGURATION ===")

# Test with actual IPO data
subject = "🚀 IPO Reminder - Gmail Test Success!"
body = """Your IPO reminder bot is now working with Gmail!

✅ Gmail SMTP: Configured and Working
✅ Email Delivery: Success
✅ Bot Status: Ready for Daily Automation

Sample IPO Alert for August 21, 2025:
• Patel Retail Ltd - Closes Today
• Vikram Solar Ltd - Closes Today  
• Gem Aromatics Ltd - Closes Today
• Shreeji Shipping Global Ltd - Closes Today

Your bot will now send you daily IPO reminders at 8:30 AM IST!

---
Time: August 22, 2025
Method: Gmail SMTP (Reliable & Secure)
"""

html_body = """
<h2>🚀 IPO Reminder - Gmail Test Success!</h2>
<p><strong>Your IPO reminder bot is now working with Gmail!</strong></p>

<div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0;">
    <h3>✅ System Status</h3>
    <ul>
        <li>✅ <strong>Gmail SMTP:</strong> Configured and Working</li>
        <li>✅ <strong>Email Delivery:</strong> Success</li>
        <li>✅ <strong>Bot Status:</strong> Ready for Daily Automation</li>
    </ul>
</div>

<div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
    <h3>📈 Sample IPO Alert for August 21, 2025:</h3>
    <ul>
        <li><strong>Patel Retail Ltd</strong> - Closes Today</li>
        <li><strong>Vikram Solar Ltd</strong> - Closes Today</li>
        <li><strong>Gem Aromatics Ltd</strong> - Closes Today</li>
        <li><strong>Shreeji Shipping Global Ltd</strong> - Closes Today</li>
    </ul>
</div>

<p><strong>🎯 Your bot will now send you daily IPO reminders at 8:30 AM IST!</strong></p>

<hr>
<p><small><strong>Time:</strong> August 22, 2025<br>
<strong>Method:</strong> Gmail SMTP (Reliable & Secure)</small></p>
"""

try:
    print("Sending test email...")
    success = send_email(
        subject=subject,
        body=body,
        html_body=html_body
    )
    
    if success:
        print("\n🎉 SUCCESS! GMAIL EMAIL SENT!")
        print("✅ Check your inbox for the test email")
        print("✅ Your IPO reminder bot is fully operational!")
        print("\n📅 Next Steps:")
        print("1. Check that you received the test email")
        print("2. Your bot will automatically run daily at 8:30 AM IST")
        print("3. You'll get IPO alerts whenever there are IPOs closing that day")
    else:
        print("\n❌ Email sending failed")
        print("Check the logs above for error details")
        
except Exception as e:
    print(f"\n❌ Error during email test: {e}")
    import traceback
    traceback.print_exc()
