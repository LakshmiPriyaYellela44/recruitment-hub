#!/usr/bin/env python
"""
Migration runner for PostgreSQL database
Executes SQL migration scripts in the migrations/ directory
"""

import asyncio
import sys
from pathlib import Path
import asyncpg
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "recruitment"

async def run_migrations():
    """Execute all pending SQL migrations"""
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...")
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        logger.info("✓ Connected to PostgreSQL")
        
        # Read and execute migration
        script_dir = Path(__file__).parent
        migration_file = script_dir / "migrations" / "0003_add_is_active_to_resumes.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            logger.info(f"Looking in: {migration_file.parent}")
            logger.info(f"Files present: {list(migration_file.parent.glob('*.sql')) if migration_file.parent.exists() else 'N/A'}")
            await conn.close()
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info(f"Executing migration: {migration_file.name}")
        
        # Execute the migration
        try:
            await conn.execute(migration_sql)
            logger.info(f"✓ Migration {migration_file.name} completed successfully")
        except asyncpg.exceptions.DuplicateObjectError as e:
            # Column or index already exists - this is okay for idempotent operations
            if "already exists" in str(e) or "duplicate key" in str(e):
                logger.warning(f"⚠ Migration already applied (column or index exists): {e}")
            else:
                raise
        
        await conn.close()
        logger.info("✓ Migration complete")
        return True
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migrations())
    sys.exit(0 if success else 1)
