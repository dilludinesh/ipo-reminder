"""Database configuration and models for enterprise-grade IPO system."""
import os
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ipo_reminder.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=bool(os.getenv("SQL_ECHO", False))
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatabaseManager:
    """Database connection manager with proper error handling."""

    @staticmethod
    @contextmanager
    def get_session():
        """Get database session with automatic cleanup."""
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected database error: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def init_database():
        """Initialize database tables."""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

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
    metadata = Column(JSON)  # Additional context

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
def init_db():
    """Initialize database tables."""
    DatabaseManager.init_database()

if __name__ == "__main__":
    init_db()
