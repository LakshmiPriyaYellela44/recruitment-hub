import logging
from datetime import datetime
from app.core.models import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


async def log_audit(
    db: AsyncSession,
    user_id: Optional[UUID],
    action: str,
    entity_type: str,
    entity_id: str,
    changes: Optional[dict] = None
):
    """Log audit event."""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")
        await db.rollback()
