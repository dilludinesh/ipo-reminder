"""Database configuration and models for enterprise-grade IPO system with async support."""
import os
import asyncio
from datetime import datetime, date
from functools import wraps
from typing import List, Optional, Dict, Any, AsyncGenerator, Type, TypeVar, cast
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Float, Boolean, JSON, ForeignKey, select, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, DBAPIError, IntegrityError, OperationalError
from contextlib import asynccontextmanager

from .exceptions import (
    DatabaseError, ConnectionError as DBConnectionError, 
    TimeoutError as DBTimeoutError, ConstraintViolationError,
    ValidationError, NotFoundError
)
from .error_handlers import handle_errors, retry_on_failure
from .logging_config import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///ipo_reminder.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Type variables for better type hints
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound='Base')

# Create async engine with SQLite-compatible configuration
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_ECHO", False)),
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=10,       # Number of connections to keep open
    max_overflow=20,    # Max number of connections to create beyond pool_size
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create async session factory with better defaults
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True,  # Enable 2.0 style API
    twophase=False,
    enable_baked_queries=True
)

# Base class for all models
Base = declarative_base()

def handle_db_errors(func):
    """Decorator to handle common database errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NoResultFound:
            logger.warning("No results found in database query")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class DatabaseManager:
    """Database connection manager with proper async error handling and CRUD operations."""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.engine = engine
            self.async_session_factory = async_session_factory
            self._initialized = True
            logger.info("DatabaseManager initialized with engine: %s", str(engine.url))
    
    @asynccontextmanager
    @retry_on_failure(max_retries=3, initial_delay=1.0, max_delay=10.0, 
                     exceptions=(DBAPIError, OperationalError))
    @handle_errors(log_errors=True, reraise=True)
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with proper error handling and retry logic."""
        session = self.async_session_factory()
        try:
            # Test the connection first
            await session.connection()
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error in session: %s", str(e), exc_info=True)
            if isinstance(e, OperationalError):
                raise DBConnectionError("Failed to connect to the database") from e
            elif isinstance(e, IntegrityError):
                # Extract constraint name from the error if possible
                constraint = str(e.orig).split("DETAIL:  ")[-1].split("=")[0].strip()
                table = str(e.statement).split(" ")[2] if hasattr(e, 'statement') else "unknown"
                raise ConstraintViolationError(constraint=constraint, table=table) from e
            else:
                raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            await session.rollback()
            logger.error("Unexpected error in database session: %s", str(e), exc_info=True)
            raise DatabaseError(f"Unexpected database error: {str(e)}") from e
        finally:
            await session.close()
    
    @handle_errors(log_errors=True, reraise=True)
    async def initialize(self):
        """Initialize the database by creating all tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to initialize database: %s", str(e), exc_info=True)
            raise DBConnectionError(f"Failed to initialize database: {str(e)}") from e
    
    @handle_errors(log_errors=True, reraise=True)
    async def close(self):
        """Close all database connections."""
        try:
            await self.engine.dispose()
            logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error("Error closing database connections: %s", str(e), exc_info=True)
            raise DBConnectionError(f"Error closing database connections: {str(e)}") from e
    
    # CRUD Operations
    
    @handle_errors(log_errors=True, reraise=True)
    async def get(self, model: Type[ModelType], id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        async with self.get_session() as session:
            result = await session.get(model, id)
            if not result:
                raise NotFoundError(
                    resource_type=model.__name__,
                    resource_id=id
                )
            return result
    
    @handle_errors(log_errors=True, reraise=True)
    async def get_all(self, model: Type[ModelType], **filters: Any) -> List[ModelType]:
        """Get all records matching the filters."""
        async with self.get_session() as session:
            stmt = select(model)
            for key, value in filters.items():
                stmt = stmt.where(getattr(model, key) == value)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @handle_errors(log_errors=True, reraise=True)
    async def create(self, model: Type[ModelType], **data: Any) -> ModelType:
        """Create a new record."""
        async with self.get_session() as session:
            instance = model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
    
    @handle_errors(log_errors=True, reraise=True)
    async def update(self, instance: ModelType, **data: Any) -> ModelType:
        """Update an existing record."""
        async with self.get_session() as session:
            for key, value in data.items():
                setattr(instance, key, value)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
    
    @handle_errors(log_errors=True, reraise=True)
    async def delete(self, instance: ModelType) -> bool:
        """Delete a record."""
        async with self.get_session() as session:
            await session.delete(instance)
            await session.commit()
            return True
            
    @handle_errors(log_errors=True, reraise=True)
    async def _initialize_config(self):
        """Initialize system configuration if not exists."""
        from .config import (
            SYSTEM_VERSION, DATABASE_VERSION, MONITORING_ENABLED,
            CACHE_ENABLED, AUDIT_ENABLED, CIRCUIT_BREAKER_ENABLED,
            MAX_RETRY_ATTEMPTS, CACHE_TTL_SECONDS, ALERT_COOLDOWN_MINUTES,
            DATA_RETENTION_DAYS
        )
        
        # Default configuration values
        configs = [
            ("system_version", SYSTEM_VERSION, "Current system version"),
            ("database_version", DATABASE_VERSION, "Database schema version"),
            ("monitoring_enabled", str(MONITORING_ENABLED).lower(), "Enable system monitoring"),
            ("cache_enabled", str(CACHE_ENABLED).lower(), "Enable caching"),
            ("audit_enabled", str(AUDIT_ENABLED).lower(), "Enable audit logging"),
            ("circuit_breaker_enabled", str(CIRCUIT_BREAKER_ENABLED).lower(), "Enable circuit breaker"),
            ("max_retry_attempts", str(MAX_RETRY_ATTEMPTS), "Maximum retry attempts for failed operations"),
            ("cache_ttl_seconds", str(CACHE_TTL_SECONDS), "Default cache TTL in seconds"),
            ("alert_cooldown_minutes", str(ALERT_COOLDOWN_MINUTES), "Alert cooldown period in minutes"),
            ("data_retention_days", str(DATA_RETENTION_DAYS), "Data retention period in days")
        ]
        
        async with self.get_session() as session:
            # Check if config already exists
            result = await session.execute(select(SystemConfig).limit(1))
            if result.scalar_one_or_none() is not None:
                logger.info("System configuration already exists, skipping initialization")
                return
                
            # Insert default configuration
            for key, value, description in configs:
                # Check if config already exists
                result = await session.execute(
                    select(SystemConfig).where(SystemConfig.key == key)
                )
                if not result.scalars().first():
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=description
                    )
                    session.add(config)
            
            await session.commit()
            logger.info("System configuration initialized successfully")

    @handle_errors(log_errors=True, reraise=True)
    async def shutdown(self):
        """Shutdown database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")

    @handle_errors(log_errors=True, reraise=True)
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        pool = self.engine.pool
        stats = {
            "status": "operational",
            "connection_count": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
            "pool_size": pool.size() if hasattr(pool, 'size') else 0,
            "pool_overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "pool_timeout": pool.timeout() if hasattr(pool, 'timeout') else 0,
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
            "dialect": self.engine.dialect.name,
            "driver": self.engine.driver,
            "url": str(self.engine.url).split('@')[-1]  # Hide credentials in logs
        }
        return stats

    @handle_db_errors
    async def execute_query(self, query, params: Optional[Dict] = None) -> Any:
        """Execute a raw SQL query with parameters."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            return result

    @handle_db_errors
    async def get_all(self, model: Type[ModelType]) -> List[ModelType]:
        """Get all records of a model."""
        async with self.get_session() as session:
            result = await session.execute(select(model))
            return result.scalars().all()

    @handle_db_errors
    async def get_by_id(self, model: Type[ModelType], id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        async with self.get_session() as session:
            result = await session.get(model, id)
            return result

    @handle_db_errors
    async def create(self, model: Type[ModelType], **kwargs) -> ModelType:
        """Create a new record."""
        async with self.get_session() as session:
            instance = model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @handle_db_errors
    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update an existing record."""
        async with self.get_session() as session:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @handle_db_errors
    async def delete(self, instance: ModelType) -> bool:
        """Delete a record."""
        async with self.get_session() as session:
            await session.delete(instance)
            await session.commit()
            return True



class IPOData(Base):
    """
    Main IPO data model with comprehensive fields for tracking IPO details.
    
    This model represents an Initial Public Offering with all relevant details
    including pricing, dates, and status information.
    """
    __tablename__ = "ipo_data"
    __table_args__ = (
        # Composite index for common query patterns
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core identification
    company_name = Column(String(255), nullable=False, index=True, comment="Full name of the company going public")
    symbol = Column(String(50), unique=True, index=True, comment="Stock exchange ticker symbol")
    isin = Column(String(20), unique=True, index=True, comment="International Securities Identification Number")
    
    # Categorization
    platform = Column(String(20), nullable=False, default="Mainboard", index=True, 
                     comment="Type of market platform (Mainboard/SME/Startup)")
    sector = Column(String(100), index=True, comment="Industry sector of the company")
    industry = Column(String(100), index=True, comment="Specific industry within the sector")
    
    # Pricing information
    price_band_low = Column(Float, comment="Lower end of the price band")
    price_band_high = Column(Float, comment="Upper end of the price band")
    lot_size = Column(Integer, comment="Number of shares per lot")
    min_investment = Column(Float, comment="Minimum investment amount required")
    
    # Date information
    open_date = Column(DateTime, index=True, comment="IPO subscription open date")
    close_date = Column(DateTime, index=True, comment="IPO subscription close date")
    basis_allotment_date = Column(DateTime, comment="Date of share allotment")
    refund_initiation_date = Column(DateTime, comment="Date when refunds are initiated")
    credit_to_demat_date = Column(DateTime, comment="Date when shares are credited to DEMAT")
    listing_date = Column(DateTime, index=True, comment="Date of stock exchange listing")
    
    # Status tracking
    status = Column(String(50), index=True, default="Upcoming", 
                   comment="Current status (Upcoming/Open/Closed/Listed/Withdrawn)")
    
    # Additional metadata
    exchange = Column(String(10), index=True, comment="Stock exchange (NSE/BSE/Both)")
    ipo_size = Column(Float, comment="Total issue size in crores")
    face_value = Column(Float, comment="Face value per share")
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    recommendations = relationship("IPORecommendation", back_populates="ipo", 
                                 cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="ipo", 
                            cascade="all, delete-orphan")
    
    # Subscription and allocation details
    subscription_status = Column(String(50), index=True, comment="Overall subscription status (Subscribed x times)")
    qib_subscription = Column(Float, comment="QIB (Qualified Institutional Buyers) subscription multiple")
    nii_subscription = Column(Float, comment="Non-Institutional Investors subscription multiple")
    retail_subscription = Column(Float, comment="Retail Individual Investors subscription multiple")
    anchor_investor_allocation = Column(Float, comment="Percentage allocated to anchor investors")
    
    # Issue management
    lead_managers = Column(JSON, comment="List of lead managers and book runners")
    registrar = Column(String(255), comment="Registrar to the issue")
    
    # Source tracking
    source = Column(String(50), nullable=False, index=True, 
                   comment="Data source (e.g., zerodha, moneycontrol, chittorgarh)")
    source_url = Column(String(500), comment="URL of the source page")
    last_updated = Column(DateTime, default=datetime.utcnow, 
                         onupdate=datetime.utcnow, nullable=False,
                         comment="Timestamp of last update")
    
    # Indexes for common query patterns
    __table_args__ = (
        # Composite index for date range queries
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<IPO {self.company_name} ({self.symbol}) - {self.platform} - {self.status}>"

class IPORecommendation(Base):
    """Comprehensive IPO investment recommendations and analysis."""
    __tablename__ = "ipo_recommendations"
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ipo_id = Column(Integer, ForeignKey("ipo_data.id", ondelete="CASCADE"), 
                  nullable=False, index=True)
    
    # Recommendation metadata
    source = Column(String(50), nullable=False, index=True, 
                  comment="Source of the recommendation")
    analyst_name = Column(String(100), comment="Name of the analyst")
    
    # Core recommendation
    recommendation = Column(String(20), nullable=False, index=True, 
                         comment="STRONG_BUY, BUY, HOLD, AVOID, STRONG_AVOID")
    target_price = Column(Float, comment="Target price for the stock")
    risk_level = Column(String(20), comment="Risk level: LOW, MODERATE, HIGH")
    confidence_score = Column(Integer, nullable=False)  # 1-100
    risk_score = Column(Integer, nullable=False)  # 1-100
    fair_value_estimate = Column(Float)
    upside_potential = Column(Float)  # percentage

    # Analysis details
    key_strengths = Column(JSON, comment="List of key strengths and competitive advantages")
    key_risks = Column(JSON, comment="List of key risks and concerns")
    financial_health = Column(String(20), comment="Assessment of company's financial health")
    valuation_assessment = Column(String(20), comment="Valuation assessment (Undervalued/Fair/Overvalued)")
    management_quality = Column(String(20), comment="Management quality assessment")
    business_model_strength = Column(String(20), comment="Strength of the business model")
    competitive_position = Column(String(20), comment="Competitive position in the industry")
    
    # Technical analysis
    technical_analysis = Column(JSON, comment="Technical analysis indicators and patterns")
    support_levels = Column(JSON, comment="Key support price levels")
    resistance_levels = Column(JSON, comment="Key resistance price levels")
    
    # Investment horizon
    investment_horizon = Column(String(20), comment="Recommended holding period (Short/Medium/Long term)")
    
    # Additional notes
    notes = Column(Text, comment="Additional analysis and notes")
    
    # Metadata
    analysis_version = Column(String(20), default="1.0", comment="Version of the analysis model")
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ipo = relationship("IPOData", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation for {self.ipo_id}: {self.recommendation} (Confidence: {self.confidence_score}%)"

class AuditLog(Base):
    """
    Comprehensive audit logging for compliance and tracking all system activities.
    
    This model captures a detailed audit trail of all significant actions
    performed within the system, including data changes, system events, and user activities.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        # Index for performance on common query patterns
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ipo_id = Column(Integer, ForeignKey("ipo_data.id", ondelete="CASCADE"), 
                  index=True, comment="Related IPO (if applicable)")
    
    # Core audit information
    action = Column(String(50), nullable=False, index=True, 
                  comment="Type of action performed (CREATE/UPDATE/DELETE/LOGIN/ANALYZE/EMAIL)")
    entity_type = Column(String(50), index=True, 
                       comment="Type of entity affected (IPO/RECOMMENDATION/USER/SYSTEM)")
    entity_id = Column(String(50), index=True, 
                     comment="ID of the affected entity (if applicable)")
    
    # User/System context
    user_id = Column(String(100), index=True, comment="ID of the user who performed the action")
    user_ip = Column(String(45), comment="IP address of the user")
    user_agent = Column(String(500), comment="User agent string from the client")
    
    # Change details
    old_values = Column(JSON, comment="Previous values before the change (for updates)")
    new_values = Column(JSON, comment="New values after the change (for updates)")
    changed_fields = Column(JSON, comment="List of fields that were changed")
    
    # Request/Response details
    request_id = Column(String(100), index=True, comment="Unique ID for the request")
    endpoint = Column(String(255), comment="API endpoint or function called")
    status = Column(String(20), index=True, comment="Status of the action (SUCCESS/FAILURE)")
    error_message = Column(Text, comment="Error message if the action failed")
    
    # System context
    service_name = Column(String(50), index=True, comment="Name of the service/module")
    hostname = Column(String(100), comment="Host where the action was performed")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True,
                      comment="When the action was performed")
    
    # Relationships
    ipo = relationship("IPOData", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.entity_type} {self.entity_id or ''}>"

class SystemMetrics(Base):
    """
    System performance, health, and operational metrics.
    
    This model stores time-series metrics for monitoring the health and performance
    of the IPO Reminder system, including resource usage, API performance,
    and business metrics.
    """
    __tablename__ = "system_metrics"
    __table_args__ = (
        # Index for time-series queries
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core metric information
    metric_name = Column(String(100), nullable=False, index=True,
                       comment="Name of the metric (e.g., 'cpu_usage', 'api_response_time')")
    metric_value = Column(Float, nullable=False,
                         comment="Numeric value of the metric")
    metric_type = Column(String(20), nullable=False, index=True,
                       comment="Type of metric: GAUGE, COUNTER, HISTOGRAM, SUMMARY")
    
    # Context and categorization
    labels = Column(JSON, comment="Key-value pairs for filtering and grouping metrics")
    service = Column(String(50), index=True, 
                    comment="Service/component that generated the metric")
    host = Column(String(100), index=True, 
                 comment="Hostname or instance where the metric was collected")
    
    # Time information
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True,
                     comment="When the metric was collected")
    interval_seconds = Column(Integer, 
                            comment="Sampling interval in seconds (for rate calculations)")
    
    # Additional metadata
    unit = Column(String(20), comment="Unit of measurement (e.g., 'ms', 'bytes', 'count')")
    description = Column(Text, comment="Human-readable description of the metric")
    
    # Retention and TTL
    retention_days = Column(Integer, default=30,
                          comment="Number of days to retain this metric")
    
    def __repr__(self):
        return f"<SystemMetrics {self.metric_name}={self.metric_value} {self.unit or ''} @ {self.timestamp}>"

class EmailLog(Base):
    """
    Comprehensive email delivery tracking and analytics.
    
    This model tracks all email communications sent by the system,
    including delivery status, open rates, and engagement metrics.
    """
    __tablename__ = "email_logs"
    __table_args__ = (
        # Index for common query patterns
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core email information
    message_id = Column(String(255), unique=True, index=True,
                      comment="Unique message ID from the email service")
    recipient = Column(String(255), nullable=False, index=True,
                     comment="Email address of the recipient")
    subject = Column(String(500), nullable=False,
                   comment="Email subject line")
    template_name = Column(String(100), index=True,
                         comment="Name of the email template used")
    
    # Sender information
    sender_email = Column(String(255), nullable=False,
                        comment="Email address of the sender")
    sender_name = Column(String(100),
                       comment="Display name of the sender")
    
    # Status tracking
    status = Column(String(20), nullable=False, index=True,
                  comment="Current status: PENDING/SENT/DELIVERED/BOUNCED/OPENED/CLICKED/FAILED")
    status_updated_at = Column(DateTime,
                             comment="When the status was last updated")
    
    # Delivery information
    sent_at = Column(DateTime, index=True,
                    comment="When the email was sent")
    delivered_at = Column(DateTime, index=True,
                        comment="When the email was delivered")
    opened_at = Column(DateTime, index=True,
                      comment="When the email was first opened")
    clicked_at = Column(DateTime, index=True,
                       comment="When a link in the email was first clicked")
    
    # Error tracking
    error_code = Column(String(50), index=True,
                       comment="Error code if delivery failed")
    error_message = Column(Text,
                         comment="Detailed error message if delivery failed")
    
    # Content and context
    ip_address = Column(String(45),
                       comment="IP address used to send the email")
    user_agent = Column(String(500),
                       comment="User agent string from the email client")
    
    # Engagement metrics
    open_count = Column(Integer, default=0,
                       comment="Number of times the email was opened")
    click_count = Column(Integer, default=0,
                        comment="Number of times links were clicked")
    
    # Metadata
    metadata = Column(JSON,
                     comment="Additional metadata and tracking information")
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<EmailLog {self.id}: {self.recipient} - {self.status} - {self.subject}>"

class CircuitBreakerState(Base):
    """
    Circuit breaker state tracking for distributed systems resilience.
    
    This model implements the Circuit Breaker pattern to detect failures and encapsulate
    the logic of preventing a service from performing operations that are likely to fail.
    """
    __tablename__ = "circuit_breaker_states"
    __table_args__ = (
        # Ensure one entry per service
        {'sqlite_autoincrement': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Service identification
    service_name = Column(String(100), nullable=False, unique=True, index=True,
                        comment="Name of the protected service/endpoint")
    
    # Circuit state
    state = Column(String(20), nullable=False, index=True,
                 comment="Current state: CLOSED, OPEN, HALF_OPEN")
    
    # Failure tracking
    failure_count = Column(Integer, default=0,
                         comment="Number of consecutive failures")
    failure_threshold = Column(Integer, default=5,
                             comment="Number of failures before opening the circuit")
    last_failure_time = Column(DateTime, index=True,
                             comment="Timestamp of the last failure")
    last_failure_error = Column(Text,
                              comment="Error message from the last failure")
    
    # Timing and recovery
    last_success_time = Column(DateTime, index=True,
                             comment="Timestamp of the last successful operation")
    open_until = Column(DateTime, index=True,
                       comment="When to attempt to close the circuit")
    reset_timeout = Column(Integer, default=60,
                         comment="Time in seconds before attempting to close the circuit")
    
    # Request tracking
    request_count = Column(Integer, default=0,
                         comment="Total number of requests")
    error_count = Column(Integer, default=0,
                       comment="Total number of failed requests")
    
    # Success rate tracking
    success_rate = Column(Float, default=100.0,
                        comment="Success rate percentage (0-100)")
    
    # Configuration
    config = Column(JSON,
                   comment="Configuration parameters for the circuit breaker")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CircuitBreaker {self.service_name}: {self.state} (Failures: {self.failure_count})>"

# Initialize database on import
async def init_db():
    """Initialize database tables asynchronously."""
    db_manager = DatabaseManager()
    await db_manager.initialize()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
