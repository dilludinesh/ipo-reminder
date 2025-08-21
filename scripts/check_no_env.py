#!/usr/bin/env python3
"""Pre-commit hook: fail if .env or secrets are staged."""
import sys
import subprocess

# Check staged files
p = subprocess.run(["git", "diff", "--name-only", "--cached"], capture_output=True, text=True)
files = p.stdout.splitlines()
for f in files:
    if f == '.env' or f.startswith('.env.'):
        print("Refusing to commit .env or dotenv files. Move secrets to GitHub Actions secrets or local environment.")
        sys.exit(1)

# Quick scan for common secret keywords in staged diffs
p = subprocess.run(["git", "diff", "--cached", "-G", "CLIENT_SECRET|SECRET|PASSWORD|TOKEN|AWS_SECRET_ACCESS_KEY"], capture_output=True, text=True)
if p.stdout:
    print("Potential secret found in staged changes. Please remove secrets before committing.")
    print(p.stdout)
    sys.exit(1)

sys.exit(0)
