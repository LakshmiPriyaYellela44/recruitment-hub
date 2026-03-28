from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import inspect, text
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Create async engine with proper config for SQLite vs PostgreSQL
connect_args = {}
if "postgresql" in settings.DATABASE_URL:
    # PostgreSQL-specific settings
    connect_args = {
        "server_settings": {"application_name": settings.APP_NAME}
    }
# SQLite doesn't need additional connect_args

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    connect_args=connect_args
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database with all models.
    
    This function:
    - Retries connection if DB not available
    - Creates all tables if they don't exist
    - Seeds test data if DB is empty
    - Enables migration-friendly structure
    """
    retries = 0
    max_retries = settings.DB_CONNECTION_RETRIES
    retry_delay = settings.DB_CONNECTION_RETRY_DELAY
    
    while retries < max_retries:
        try:
            logger.info(f"Attempting to connect to database (attempt {retries + 1}/{max_retries})...")
            
            # Test connection
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✓ Database connection successful")
            
            # Create all tables
            logger.info("Creating database tables...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ All database tables created successfully")
            
            # Seed test data if database is empty
            await seed_test_data()
            
            return
            
        except Exception as e:
            retries += 1
            if retries < max_retries:
                logger.warning(
                    f"✗ Database connection failed: {str(e)}. "
                    f"Retrying in {retry_delay}s... ({retries}/{max_retries})"
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"✗ Failed to connect to database after {max_retries} attempts. "
                    f"Error: {str(e)}"
                )
                raise


async def seed_test_data():
    """Seed test data if database is empty."""
    try:
        from app.core.models import User, UserRole
        from app.core.security import get_password_hash
        from app.core.seed_data import seed_email_templates
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as session:
            # Check if any users exist
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar() or 0
            
            if user_count == 0:
                logger.info("Database is empty, seeding test data...")
                
                # Create test recruiter (John)
                recruiter = User(
                    email="recruiter@example.com",
                    password_hash=get_password_hash("password123"),
                    first_name="John",
                    last_name="Recruiter",
                    role=UserRole.RECRUITER,
                    is_active=True
                )
                
                # Create test candidate
                candidate = User(
                    email="candidate@example.com",
                    password_hash=get_password_hash("password123"),
                    first_name="Jane",
                    last_name="Candidate",
                    role=UserRole.CANDIDATE,
                    is_active=True
                )
                
                # Create bob (recruiter)
                bob = User(
                    email="bob@example.com",
                    password_hash=get_password_hash("password123"),
                    first_name="Bob",
                    last_name="Smith",
                    role=UserRole.RECRUITER,
                    is_active=True
                )
                
                # Create default admin user
                admin = User(
                    email="admin@example.com",
                    password_hash=get_password_hash("admin123"),
                    first_name="Admin",
                    last_name="User",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                
                session.add(recruiter)
                session.add(candidate)
                session.add(bob)
                session.add(admin)
                await session.commit()
                
                logger.info("✓ Test data seeded successfully")
                logger.info("  - Recruiter (John): recruiter@example.com / password123")
                logger.info("  - Candidate (Jane): candidate@example.com / password123")
                logger.info("  - Recruiter (Bob): bob@example.com / password123")
                logger.info("  - Admin (User): admin@example.com / admin123")
            else:
                logger.info(f"Database already has {user_count} users, skipping user seed")
            
            # Seed email templates (independent of user count)
            await seed_email_templates(session)
                
    except Exception as e:
        logger.warning(f"Could not seed test data: {str(e)}")


async def close_db():
    """Close database engine connection pool."""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("✓ Database connections closed")
