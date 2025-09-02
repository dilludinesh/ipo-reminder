# IPO Reminder

Daily **9:00 AM IST** cloud job that emails you IPOs **closing today** with a clear **Apply / Avoid** suggestion and details (price band, lot size, GMP trend, expert view).

- ✅ **Free forever** (GitHub Actions free tier)
- 🔔 **Email notification** (Gmail/Outlook)
- 🧠 **Apply/Avoid** = Chittorgarh review + GMP trend
- 🌐 **100% Cloud-based** - No local setup required

---

## 🚀 **Enhanced Features (v2.0)**

### Security & Validation
- ✅ **Input Sanitization**: All scraped data is sanitized to prevent XSS attacks
- ✅ **Email Validation**: Robust email address validation and format checking
- ✅ **HTML Escaping**: Safe HTML content generation
- ✅ **Request Validation**: Enhanced error handling for network requests

### Advanced Analysis
- 🧠 **Enhanced Deep Analyzer**: More sophisticated financial analysis with sector-specific metrics
- 📊 **Risk Assessment**: Comprehensive risk scoring with multiple factors
- 🎯 **Investment Thesis**: Automated investment thesis generation
- 📈 **Price Validation**: Robust price band parsing and validation

### Improved Email System
- 📧 **Rich HTML Emails**: Professional email templates with enhanced formatting
- 📱 **Mobile Responsive**: Emails optimized for mobile viewing
- 🔒 **Secure Sending**: Enhanced SMTP security with proper authentication
- 📝 **Detailed Analysis**: Comprehensive IPO analysis in email content

### Better Data Processing
- 🛡️ **Utility Functions**: Centralized utility functions for common operations
- 📊 **Market Summary**: Automated market summary generation
- 🎯 **Smart Categorization**: Enhanced IPO categorization with risk-based analysis
- 🔄 **Fallback Systems**: Improved fallback mechanisms for data sources

### Development Tools
- 🧪 **Enhanced Testing**: Comprehensive test suite with utilities
- 📏 **Code Formatting**: Black and isort configuration for consistent code style
- 📊 **Coverage Reports**: Detailed test coverage reporting
- 🔧 **Development Dependencies**: Added tools for better development experience

---

## Quick Start

### Cloud Setup (GitHub Actions)
1. **Fork this repo** to your GitHub account
2. **Add repository secrets** in your forked repo:
   - Go to Settings → Secrets and variables → Actions
   - Add these secrets:
     - `SENDER_EMAIL` — your Gmail/Outlook address  
     - `SENDER_PASSWORD` — your app password
     - `RECIPIENT_EMAIL` — email to receive reminders
3. **Get App Password**:
   - **Gmail**: Enable 2FA → https://myaccount.google.com/apppasswords
   - **Outlook**: https://account.microsoft.com/security → Create app password
4. **Activate workflow**:
   - Go to Actions tab → Enable workflows
   - The system will automatically send daily emails at 9:00 AM IST

### Option 2: Microsoft Graph API (Production)
1. **Create Azure App Registration**
2. **Add these repository secrets**:
   - `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`
   - `SENDER_EMAIL`, `RECIPIENT_EMAIL`
3. **Grant Mail.Send permission** and admin consent

---

## How It Works

The system runs automatically via **GitHub Actions** (cloud) at 9:00 AM IST daily:

1. **Fetches IPO data** from multiple sources (SEBI, BSE, NSE, Chittorgarh)
2. **Filters IPOs** closing today with Apply/Avoid recommendations  
3. **Sends email** with formatted IPO details and analysis
4. **Logs results** for monitoring and debugging

**No local setup required** - everything runs in GitHub's cloud!

---

## What you'll receive

An email like:

```
Subject: IPO Reminder • 19 Aug 2025 (Last-day alerts)

Hello! 👋

These IPO(s) close today:

• Mangal Electrical Industries
  - Price Band: ₹533 – ₹561
  - Lot Size: 26 shares
  - Issue Size: ₹400 Cr
  - GMP: ₹40 (steady)
  - Expert View: APPLY ✅ (Chittorgarh: Subscribe)
  - Reason: Positive reviews + non-negative GMP
  - Close Date: 19-Aug-2025
```

---

## How it works

- Scrapes **Chittorgarh** for upcoming/active IPOs and filters those with **close date = today**.
- Visits each IPO’s page to extract **price band, lot size, issue size, reviews**.
- Tries to fetch **GMP page** and derive a simple **trend** (rising/steady/falling).
- Decision rules:
  - If Chittorgarh says **Subscribe/Apply** and GMP is **≥ 0 or rising** → **APPLY** ✅
  - If Review says **Avoid** or GMP **negative & falling** → **AVOID** ❌
  - Else → **NEUTRAL** ⚖ (apply only for listing gains)

> Notes: Websites sometimes change structure. The scraper is built to be tolerant, but if a selector changes, adjust `ipo_reminder/sources/chittorgarh.py`.

---

## Timezone

GitHub Actions uses UTC. The workflow cron `30 3 * * *` maps to **09:00 IST**.

## Secrets and CI (important)

Never commit secrets or credentials to the repository. This project runs 100% in the cloud using GitHub Actions.

For GitHub Actions to work, store sensitive values as repository secrets and reference them in workflows. Example secrets to add in the repository settings:

- `SENDER_EMAIL` (your Gmail address)
- `SENDER_PASSWORD` (Gmail App Password)
- `RECIPIENT_EMAIL` (where to send IPO reminders)

Do not copy secret values into files in the repo.

Automate setting GitHub secrets (optional)

If you use the GitHub CLI (`gh`), there's a helper script to set the required repository secrets:

```bash
# make it executable once
chmod +x scripts/set_github_secrets.sh
# then run (replace owner/repo)
CLIENT_ID=... CLIENT_SECRET=... TENANT_ID=... OUTLOOK_EMAIL=... OUTLOOK_APP_PASSWORD=... RECIPIENT_EMAIL=... \
  ./scripts/set_github_secrets.sh dilludinesh/ipo-reminder
```

This will push the secrets to GitHub Actions securely.
