from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.scan import Scan
from app.models.target import Target
from app.schemas.scan import ScanConfigRequest
from app.models.user import User
from app.tasks.scan_tasks import scan_target
from app.routers.auth import limiter
from app.services.audit import log_audit_event

router = APIRouter(tags=["scans"])

DEFAULT_SCAN_CONFIG = {
    "selected_templates": ["cves", "exposures", "misconfiguration"],
    "severity_filter": ["medium", "high", "critical"],
}


@router.post("/scan/{target_id}", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("12/minute")
def trigger_scan(
    target_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = db.query(Target).filter(Target.id == target_id, Target.owner_id == user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    running = (
        db.query(Scan)
        .filter(Scan.target_id == target.id, Scan.status.in_(["pending", "running"]))
        .order_by(Scan.created_at.desc())
        .first()
    )
    if running:
        raise HTTPException(status_code=409, detail="Scan already in progress for this target")
    recent_threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.scan_throttle_seconds)
    recent = (
        db.query(Scan)
        .join(Target, Target.id == Scan.target_id)
        .filter(Target.owner_id == user.id, Scan.created_at >= recent_threshold)
        .order_by(Scan.created_at.desc())
        .first()
    )
    if recent:
        raise HTTPException(status_code=429, detail="Scan throttled. Please wait before starting another scan.")

    scan = Scan(
        target_id=target.id,
        status="pending",
        metadata_json={"step": "queued"},
        scan_config_json=DEFAULT_SCAN_CONFIG,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    scan_target.delay(scan.id)
    log_audit_event(
        db,
        action="scan_triggered",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        metadata_json={"target_id": target.id, "scan_id": scan.id, "mode": "default"},
    )
    return {"scan_id": scan.id, "status": "pending"}


@router.post("/scan/{target_id}/config", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("12/minute")
def trigger_scan_with_config(
    target_id: int,
    request: Request,
    payload: ScanConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = db.query(Target).filter(Target.id == target_id, Target.owner_id == user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    running = (
        db.query(Scan)
        .filter(Scan.target_id == target.id, Scan.status.in_(["pending", "running"]))
        .order_by(Scan.created_at.desc())
        .first()
    )
    if running:
        raise HTTPException(status_code=409, detail="Scan already in progress for this target")
    recent_threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.scan_throttle_seconds)
    recent = (
        db.query(Scan)
        .join(Target, Target.id == Scan.target_id)
        .filter(Target.owner_id == user.id, Scan.created_at >= recent_threshold)
        .order_by(Scan.created_at.desc())
        .first()
    )
    if recent:
        raise HTTPException(status_code=429, detail="Scan throttled. Please wait before starting another scan.")

    scan = Scan(
        target_id=target.id,
        status="pending",
        metadata_json={"step": "queued"},
        scan_config_json={
            "selected_templates": payload.selected_templates,
            "severity_filter": payload.severity_filter,
        },
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    scan_target.delay(scan.id)
    log_audit_event(
        db,
        action="scan_triggered",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        metadata_json={"target_id": target.id, "scan_id": scan.id, "mode": "configured"},
    )
    return {"scan_id": scan.id, "status": "pending"}
