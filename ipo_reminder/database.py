"""Database configuration and models for enterprise-grade IPO system with async support."""
import os
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///ipo_reminder.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create async engine with SQLite-compatible configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_ECHO", False)),
    # SQLite in-memory database requires special handling
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

class DatabaseManager:
    """Database connection manager with proper async error handling."""

    def __init__(self):
        """Initialize the database manager."""
        self.engine = engine
        self.async_session_factory = async_session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with proper error handling."""
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()

    async def initialize(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")

    async def shutdown(self):
        """Shutdown database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with self.get_session() as session:
            # Get connection pool status
            pool = self.engine.pool
            stats = {
                "connection_count": pool.checkedin(),
                "pool_size": pool.size(),
                "pool_overflow": pool.overflow(),
                "pool_timeout": pool.timeout(),
                "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0
            }
            return stats

# Database Models
class IPOData(Base):
    """Main IPO data model."""
    __tablename__ = "ipo_data"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    symbol = Column(String(50), index=True)
    platform = Column(String(20), nullable=False, default="Mainboard")  # Mainboard or SME
    price_band = Column(String(100))
    min_price = Column(Float)
    max_price = Column(Float)
    lot_size = Column(Integer)
    issue_size = Column(Float)  # in crores
    fresh_issue = Column(Float)
    offer_for_sale = Column(Float)
    open_date = Column(Date)
    close_date = Column(Date, index=True)
    listing_date = Column(Date)
    subscription_status = Column(String(50))
    anchor_investor_allocation = Column(Float)
    lead_managers = Column(JSON)  # List of lead managers
    registrar = Column(String(255))
    sector = Column(String(100), index=True)
    industry = Column(String(100))

    # Metadata
    source = Column(String(50), nullable=False)  # zerodha, moneycontrol, etc.
    source_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendations = relationship("IPORecommendation", back_populates="ipo")
    audit_logs = relationship("AuditLog", back_populates="ipo")

class IPORecommendation(Base):
    """IPO investment recommendations."""
    __tablename__ = "ipo_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    ipo_id = Column(Integer, ForeignKey("ipo_data.id"), nullable=False)

    # Recommendation data
    recommendation = Column(String(20), nullable=False)  # STRONG_BUY, BUY, HOLD, AVOID, STRONG_AVOID
    confidence_score = Column(Integer, nullable=False)  # 1-100
    risk_score = Column(Integer, nullable=False)  # 1-100
    fair_value_estimate = Column(Float)
    upside_potential = Column(Float)  # percentage

    # Analysis details
    key_strengths = Column(JSON)  # List of strengths
    key_risks = Column(JSON)  # List of risks
    financial_health = Column(String(20))
    valuation_assessment = Column(String(20))
    management_quality = Column(String(20))
    business_model_strength = Column(String(20))
    competitive_position = Column(String(20))

    # Metadata
    analysis_version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ipo = relationship("IPOData", back_populates="recommendations")

class AuditLog(Base):
    """Compliance and audit logging."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ipo_id = Column(Integer, ForeignKey("ipo_data.id"))

    # Audit information
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, ANALYZE, EMAIL_SENT
    user_id = Column(String(100))  # For future multi-user support
    ip_address = Column(String(45))  # IPv4/IPv6 support
    user_agent = Column(String(500))

    # Action details
    old_values = Column(JSON)  # Previous state for updates
    new_values = Column(JSON)  # New state
    context_data = Column(JSON)  # Additional context (renamed from metadata)

    # Compliance fields
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_id = Column(String(100))
    compliance_flags = Column(JSON)  # Regulatory compliance markers

    # Relationships
    ipo = relationship("IPOData", back_populates="audit_logs")

class SystemMetrics(Base):
    """System performance and health metrics."""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(20), nullable=False)  # COUNTER, GAUGE, HISTOGRAM
    labels = Column(JSON)  # Additional labels/tags

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class EmailLog(Base):
    """Enhanced email delivery tracking."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)  # SENT, FAILED, BOUNCED, etc.
    provider = Column(String(50))  # gmail, outlook, etc.
    message_id = Column(String(255))  # SMTP message ID

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timing
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)

    # Metadata
    ipo_count = Column(Integer)
    processing_time = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)

class CircuitBreakerState(Base):
    """Circuit breaker state tracking."""
    __tablename__ = "circuit_breaker_states"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False, unique=True)
    state = Column(String(20), nullable=False)  # CLOSED, OPEN, HALF_OPEN
    failure_count = Column(Integer, default=0)
    last_failure_time = Column(DateTime)
    last_success_time = Column(DateTime)
    next_retry_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize database on import
async def init_db():
    """Initialize database tables asynchronously."""
    db_manager = DatabaseManager()
    await db_manager.initialize()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
