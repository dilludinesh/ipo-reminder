#!/usr/bin/env bash
# Helper to set required GitHub Actions secrets using the gh CLI.
# Usage: export values (or pass interactively) then run: ./scripts/set_github_secrets.sh <owner/repo>

set -euo pipefail

REPO="$1"

require() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Environment variable $name is not set. You will be prompted to enter it now."
    read -s -p "Enter value for $name: " val
    echo
    export $name="$val"
  fi
}

# Required secrets
require CLIENT_ID
require CLIENT_SECRET
require TENANT_ID
require OUTLOOK_EMAIL
require OUTLOOK_APP_PASSWORD
require RECIPIENT_EMAIL

# Check gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install from https://cli.github.com/ and authenticate (gh auth login)"
  exit 1
fi

echo "Setting secrets for repo: $REPO"

gh secret set CLIENT_ID --repo "$REPO" --body "$CLIENT_ID"
gh secret set CLIENT_SECRET --repo "$REPO" --body "$CLIENT_SECRET"
gh secret set TENANT_ID --repo "$REPO" --body "$TENANT_ID"

gh secret set OUTLOOK_EMAIL --repo "$REPO" --body "$OUTLOOK_EMAIL"
gh secret set OUTLOOK_APP_PASSWORD --repo "$REPO" --body "$OUTLOOK_APP_PASSWORD"
gh secret set RECIPIENT_EMAIL --repo "$REPO" --body "$RECIPIENT_EMAIL"

echo "Done. Secrets set for $REPO"
