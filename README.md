# IPO Reminder Bot (Free • GitHub Actions • Outlook Email)

Daily **8:30 AM IST** cloud job that emails you IPOs **closing today** with a clear **Apply / Avoid** suggestion and details (price band, lot size, GMP trend, expert view).

- ✅ **Free forever** (GitHub Actions free tier)
- 🔔 **Email notification** (Outlook)
- 🧠 **Apply/Avoid** = Chittorgarh review + GMP trend
- 🌐 Works even if your Mac/phone is off

---

## Quick Start

1. **Create a new GitHub repo** and upload these files.
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `OUTLOOK_EMAIL` — your Outlook address (e.g., `you@outlook.com`)
   - `OUTLOOK_APP_PASSWORD` — an **App Password** (recommended if 2FA enabled) or your Outlook password
   - `RECIPIENT_EMAIL` — the email to receive reminders (can be same as your Outlook)
3. Commit and push. The workflow runs daily at **8:30 AM IST**.

> App Password help: In Microsoft account security, create an app password for SMTP if 2FA is ON.

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

GitHub Actions uses UTC. The workflow cron `0 3 * * *` maps to **08:30 IST**.

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
  ./scripts/set_github_secrets.sh dilludinesh/ipo-reminder-bot
```

This will push the secrets to GitHub Actions securely.
