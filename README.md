# IPO Reminder

Daily **9:00 AM IST** cloud job that emails you IPOs **closing today** with a clear **Apply / Avoid** suggestion and details (price band, lot size, GMP trend, expert view).

- ✅ **Free forever** (GitHub Actions free tier)
- 🔔 **Email notification** (Outlook)
- 🧠 **Apply/Avoid** = Chittorgarh review + GMP trend
- 🌐 Works even if your Mac/phone is off

---

## Quick Start

### Option 1: SMTP (Easiest)
1. **Fork this repo** or create a new one with these files.
2. **Copy `.env.template` to `.env`** and fill in your credentials:
   ```bash
   cp .env.template .env
   # Edit .env with your email credentials
   ```
3. **Get Outlook App Password** (if using 2FA): 
   - Go to https://account.microsoft.com/security
   - Create a new app password for "Mail"
4. **Test locally** (optional):
   ```bash
   python -m ipo_reminder.ipo_reminder --dry-run
   ```
5. **For GitHub Actions**: Add repository secrets:
   - `SENDER_EMAIL` or `OUTLOOK_EMAIL` — your Outlook address
   - `SENDER_PASSWORD` or `OUTLOOK_APP_PASSWORD` — your app password
   - `RECIPIENT_EMAIL` — email to receive reminders

### Option 2: Microsoft Graph API (Production)
1. **Create Azure App Registration**
2. **Add these repository secrets**:
   - `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`
   - `SENDER_EMAIL`, `RECIPIENT_EMAIL`
3. **Grant Mail.Send permission** and admin consent

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and edit config
cp .env.template .env
# Fill in your credentials in .env

# Test without sending email
python -m ipo_reminder.ipo_reminder --dry-run

# Run for real
python -m ipo_reminder.ipo_reminder
```

---

## What you'll receive

An email like:

```
Subject: IPO Reminder – 19 Aug 2025 (Last-day alerts)

Hello Dillu 👋

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

## Local testing (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OUTLOOK_EMAIL="you@outlook.com"
export OUTLOOK_APP_PASSWORD="your-app-password"
export RECIPIENT_EMAIL="you@outlook.com"
python ipo_reminder/main.py
```

---

## Timezone

GitHub Actions uses UTC. The workflow cron `30 3 * * *` maps to **09:00 IST**.

## Secrets and CI (important)

Never commit secrets or credentials to the repository. Use a local `.env` file for development and keep it listed in `.gitignore`.

For CI (GitHub Actions), store sensitive values as repository secrets and reference them in workflows. Example secrets to add in the repository settings:

- `CLIENT_ID`
- `CLIENT_SECRET`
- `TENANT_ID`
- `OUTLOOK_EMAIL` (or `SENDER_EMAIL`)
- `OUTLOOK_APP_PASSWORD` (if using SMTP fallback)

Do not copy secret values into files in the repo. If a secret is accidentally committed, rotate it immediately and remove it from git history.

Local developer setup (recommended):

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Install pre-commit hooks:

```bash
pre-commit install
```

This will block accidental commits of `.env` or common secret patterns.

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
