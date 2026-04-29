from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit_event(
    db: AsyncSession,
    *,
    action: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    metadata_json: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            metadata_json=metadata_json or {},
        )
    )
    await db.commit()
