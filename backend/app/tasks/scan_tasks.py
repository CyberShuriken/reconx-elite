from datetime import datetime, timezone
import shlex

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.endpoint import Endpoint
from app.models.scan import Scan
from app.models.scan_log import ScanLog
from app.models.subdomain import Subdomain
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.services.scan_runner import check_headers, run_gau, run_httpx, run_nuclei, run_subfinder
from app.services.tool_executor import ToolExecutionResult
from app.tasks.celery_app import celery_app


def _update_scan(scan: Scan, db: Session, **kwargs) -> None:
    for key, value in kwargs.items():
        setattr(scan, key, value)
    db.add(scan)
    db.commit()
    db.refresh(scan)


def _log_step(
    db: Session,
    scan_id: int,
    step: str,
    status: str,
    details: dict,
    result: ToolExecutionResult | None = None,
) -> None:
    if result:
        row = ScanLog(
            scan_id=scan_id,
            step=step,
            status=status,
            started_at=result.started_at,
            ended_at=result.ended_at,
            duration_ms=result.duration_ms,
            attempts=result.attempts,
            stdout=result.stdout,
            stderr=result.stderr,
            details_json=details | result.to_json(),
        )
    else:
        now = datetime.now(timezone.utc)
        row = ScanLog(
            scan_id=scan_id,
            step=step,
            status=status,
            started_at=now,
            ended_at=now,
            duration_ms=0,
            attempts=1,
            stdout="",
            stderr="",
            details_json=details,
        )
    db.add(row)
    db.commit()


@celery_app.task(name="scan_target")
def scan_target(scan_id: int) -> dict:
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"error": "scan not found"}
        target = db.query(Target).filter(Target.id == scan.target_id).first()
        if not target:
            _update_scan(scan, db, status="failed", error="target not found")
            return {"error": "target not found"}
        scan_config = scan.scan_config_json or {}

        _update_scan(scan, db, status="running", metadata_json={"step": "subfinder", "started": True})

        subdomains, sub_result = run_subfinder(target.domain)
        _log_step(
            db,
            scan.id,
            "subfinder",
            sub_result.status,
            {"count": len(subdomains), "parsed_json": {"subdomains": subdomains}},
            sub_result,
        )
        if sub_result.status != "success":
            _update_scan(scan, db, status="failed", error=sub_result.error, metadata_json={"step": "subfinder"})
            return {"error": sub_result.error}

        for host in subdomains:
            db.add(Subdomain(scan_id=scan.id, hostname=host, is_live=0))
        db.commit()

        _update_scan(scan, db, metadata_json={"step": "httpx"})
        live_hosts, httpx_result = run_httpx(subdomains)
        if httpx_result:
            _log_step(
                db,
                scan.id,
                "httpx",
                httpx_result.status,
                {"count": len(live_hosts), "parsed_json": {"live_hosts": live_hosts}},
                httpx_result,
            )
        if httpx_result and httpx_result.status != "success":
            _update_scan(scan, db, status="failed", error=httpx_result.error, metadata_json={"step": "httpx"})
            return {"error": httpx_result.error}

        live_set = set(live_hosts)
        for row in db.query(Subdomain).filter(Subdomain.scan_id == scan.id).all():
            if row.hostname in live_set:
                row.is_live = 1
        db.commit()

        _update_scan(scan, db, metadata_json={"step": "gau"})
        urls, gau_result = run_gau(target.domain)
        _log_step(
            db,
            scan.id,
            "gau",
            gau_result.status,
            {"count": len(urls), "parsed_json": {"endpoints": urls}},
            gau_result,
        )
        if gau_result.status != "success":
            _update_scan(scan, db, status="failed", error=gau_result.error, metadata_json={"step": "gau"})
            return {"error": gau_result.error}

        deduped_urls = sorted(set(urls))
        for url in deduped_urls:
            db.add(Endpoint(scan_id=scan.id, url=url))
        db.commit()

        _update_scan(scan, db, metadata_json={"step": "nuclei"})
        nuclei_vulns, nuclei_result = run_nuclei(deduped_urls[:300], scan_config)
        if nuclei_result:
            command_preview = " ".join(shlex.quote(part) for part in nuclei_result.command)
            _log_step(
                db,
                scan.id,
                "nuclei",
                nuclei_result.status,
                {
                    "count": len(nuclei_vulns),
                    "scan_config": scan_config,
                    "effective_nuclei_command": command_preview,
                    "effective_nuclei_flags": {
                        "tags": scan_config.get("selected_templates", []),
                        "severity": scan_config.get("severity_filter", []),
                    },
                    "parsed_json": {"vulnerabilities": nuclei_vulns},
                },
                nuclei_result,
            )
        if nuclei_result and nuclei_result.status != "success":
            _update_scan(scan, db, status="failed", error=nuclei_result.error, metadata_json={"step": "nuclei"})
            return {"error": nuclei_result.error}
        for vuln in nuclei_vulns:
            db.add(Vulnerability(scan_id=scan.id, **vuln))

        _update_scan(scan, db, metadata_json={"step": "headers"})
        header_findings, headers_result = check_headers(deduped_urls[:50])
        if headers_result:
            _log_step(
                db,
                scan.id,
                "headers",
                headers_result.status,
                {"count": len(header_findings), "parsed_json": {"header_findings": header_findings}},
                headers_result,
            )
        if headers_result and headers_result.status != "success":
            _update_scan(scan, db, status="failed", error=headers_result.error, metadata_json={"step": "headers"})
            return {"error": headers_result.error}
        for finding in header_findings:
            db.add(Vulnerability(scan_id=scan.id, **finding))
        db.commit()

        _update_scan(scan, db, status="completed", metadata_json={"step": "done"})
        return {"status": "completed", "scan_id": scan_id}
    except Exception as exc:  # noqa: BLE001
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            _update_scan(scan, db, status="failed", error=str(exc))
        return {"error": str(exc)}
    finally:
        db.close()
