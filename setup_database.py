"""Database setup and migration script for enterprise IPO reminder system."""
import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipo_reminder.database import Base, DatabaseManager
# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://ipo_user:ipo_password@localhost:5432/ipo_reminder')
SYNC_DATABASE_URL = DATABASE_URL.replace('+asyncpg', '')  # Convert to sync URL for setup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Set up the database with all tables and initial data."""
    try:
        logger.info("Setting up enterprise database...")

        # Create sync engine for setup (Alembic operations need sync)
        engine = create_engine(SYNC_DATABASE_URL, echo=True)

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Create indexes for better performance
        with engine.connect() as conn:
            # Index for IPO data queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ipo_data_dates
                ON ipo_data (open_date, close_date);
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ipo_data_company
                ON ipo_data (company_name);
            """))

            # Index for audit logs
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
                ON audit_logs (timestamp);
            """))

            # Index for system metrics
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp
                ON system_metrics (timestamp);
            """))

            conn.commit()

        logger.info("Database tables and indexes created successfully")

        # Insert initial system configuration
        _insert_initial_data(engine)

        logger.info("Database setup completed successfully!")

    except SQLAlchemyError as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during database setup: {e}")
        sys.exit(1)

def _insert_initial_data(engine):
    """Insert initial configuration and seed data."""
    try:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with engine.connect() as conn:
            # Insert system configuration - using SQLite compatible syntax
            conn.execute(text("""
                INSERT OR IGNORE INTO system_config (key, value, description, created_at, updated_at)
                VALUES
                    ('system_version', '"enterprise-v1.0"', 'Current system version', :time, :time),
                    ('database_version', '"1.0"', 'Database schema version', :time, :time),
                    ('monitoring_enabled', 'true', 'Enable system monitoring', :time, :time),
                    ('cache_enabled', 'true', 'Enable caching system', :time, :time),
                    ('audit_enabled', 'true', 'Enable audit logging', :time, :time),
                    ('circuit_breaker_enabled', 'true', 'Enable circuit breaker pattern', :time, :time),
                    ('max_retry_attempts', '3', 'Maximum retry attempts for failed operations', :time, :time),
                    ('cache_ttl_seconds', '3600', 'Default cache TTL in seconds', :time, :time),
                    ('alert_cooldown_minutes', '60', 'Alert cooldown period in minutes', :time, :time),
                    ('data_retention_days', '365', 'Data retention period in days', :time, :time);
            """), {'time': current_time})

            # Insert initial system metrics - using SQLite compatible syntax
            conn.execute(text("""
                INSERT OR IGNORE INTO system_metrics (metric_name, metric_value, metric_type, labels, timestamp)
                VALUES
                    ('system_setup', 1.0, 'GAUGE', :labels1, :time1),
                    ('database_tables_created', 4.0, 'GAUGE', :labels2, :time2);
            """), {
                'labels1': '{"event": "initial_setup"}',
                'labels2': '{"tables": ["ipo_data", "ipo_recommendations", "audit_logs", "system_metrics"]}',
                'time1': current_time,
                'time2': current_time
            })

            conn.commit()

        logger.info("Initial data inserted successfully")

    except Exception as e:
        logger.error(f"Failed to insert initial data: {e}")
        raise

def migrate_database():
    """Run database migrations if needed."""
    try:
        logger.info("Checking for database migrations...")

        engine = create_engine(DATABASE_URL, echo=True)

        # Check current schema version
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT value FROM system_config
                WHERE key = 'database_version'
                LIMIT 1;
            """))

            current_version = result.fetchone()
            current_version = current_version[0].strip('"') if current_version else '0.0'

            logger.info(f"Current database version: {current_version}")

            # For now, we only have version 1.0
            # Future migrations would be added here
            if current_version == '1.0':
                logger.info("Database is up to date")
            else:
                logger.warning(f"Database version {current_version} may need migration")

    except Exception as e:
        logger.error(f"Migration check failed: {e}")

def verify_database_setup():
    """Verify that the database is properly set up."""
    try:
        logger.info("Verifying database setup...")

        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as session:
            # Check if tables exist
            tables = ['ipo_data', 'ipo_recommendations', 'audit_logs', 'system_metrics', 'system_config']
            for table in tables:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1;"))
                count = result.fetchone()[0]
                logger.info(f"Table '{table}': {count} records")

            # Check system configuration
            result = session.execute(text("SELECT COUNT(*) FROM system_config;"))
            config_count = result.fetchone()[0]
            logger.info(f"System configuration: {config_count} settings")

        logger.info("Database verification completed successfully")

    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

    return True

def cleanup_old_data():
    """Clean up old data based on retention policy."""
    try:
        logger.info("Cleaning up old data...")

        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        retention_days = 365  # From configuration

        with SessionLocal() as session:
            # Clean up old audit logs
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            result = session.execute(text("""
                DELETE FROM audit_logs
                WHERE timestamp < :cutoff_date;
            """), {'cutoff_date': cutoff_date})

            deleted_audit = result.rowcount

            # Clean up old system metrics (keep last 30 days)
            metrics_cutoff = datetime.utcnow() - timedelta(days=30)

            result = session.execute(text("""
                DELETE FROM system_metrics
                WHERE timestamp < :cutoff_date;
            """), {'cutoff_date': metrics_cutoff})

            deleted_metrics = result.rowcount

            session.commit()

            logger.info(f"Cleaned up {deleted_audit} old audit log entries")
            logger.info(f"Cleaned up {deleted_metrics} old system metric entries")

    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")

def main():
    """Main setup function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'setup':
            setup_database()
        elif command == 'migrate':
            migrate_database()
        elif command == 'verify':
            success = verify_database_setup()
            sys.exit(0 if success else 1)
        elif command == 'cleanup':
            cleanup_old_data()
        elif command == 'all':
            setup_database()
            migrate_database()
            verify_database_setup()
            cleanup_old_data()
        else:
            print("Usage: python setup_database.py [setup|migrate|verify|cleanup|all]")
            sys.exit(1)
    else:
        # Default: run full setup
        setup_database()
        migrate_database()
        verify_database_setup()
        cleanup_old_data()

if __name__ == "__main__":
    main()
