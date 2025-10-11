#!/usr/bin/env python3
"""Database connection test script for GitHub Actions."""

import os
import sys
from sqlalchemy import create_engine, text

def test_database_connection():
    """Test database connection and permissions."""
    test_db_url = os.environ.get('TEST_DB_URL')
    if not test_db_url:
        print("❌ TEST_DB_URL environment variable not set")
        sys.exit(1)

    try:
        # Use psycopg2 for sync connection test
        engine = create_engine(test_db_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version();'))
            version = result.fetchone()[0]
            print(f'✅ Connected to PostgreSQL: {version[:50]}...')

            # Verify user has proper permissions
            result = conn.execute(text('SELECT current_user, current_database();'))
            user, db = result.fetchone()
            print(f'🔑 Connected as user: {user} to database: {db}')

            # Check if user can create tables
            conn.execute(text('CREATE TABLE IF NOT EXISTS test_permissions (id SERIAL PRIMARY KEY, name TEXT);'))
            conn.execute(text('DROP TABLE IF EXISTS test_permissions;'))
            print('✅ Verified user has proper permissions')

    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        print(f'Connection URL used: {test_db_url}')
        sys.exit(1)

if __name__ == "__main__":
    test_database_connection()
