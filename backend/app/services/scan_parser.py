import json
from typing import Any


def parse_subfinder_output(stdout: str) -> list[str]:
    return sorted({line.strip().lower() for line in stdout.splitlines() if line.strip()})


def parse_httpx_live_output(stdout: str) -> list[str]:
    hosts: set[str] = set()
    for line in stdout.splitlines():
        row = line.strip()
        if not row:
            continue
        try:
            payload = json.loads(row)
        except json.JSONDecodeError:
            continue
        host = (payload.get("input") or "").strip().lower()
        if host:
            hosts.add(host)
    return sorted(hosts)


def parse_gau_output(stdout: str) -> list[str]:
    return sorted({line.strip() for line in stdout.splitlines() if line.strip()})


def parse_nuclei_output(stdout: str) -> list[dict[str, Any]]:
    vulns: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for line in stdout.splitlines():
        row = line.strip()
        if not row:
            continue
        try:
            data = json.loads(row)
        except json.JSONDecodeError:
            continue
        info = data.get("info") or {}
        host = data.get("host") or ""
        matched_url = data.get("matched-at") or data.get("url") or host
        template_id = data.get("template-id", "unknown-template")
        matcher_name = data.get("matcher-name") or ""
        key = (template_id, matched_url or "", matcher_name)
        if key in seen:
            continue
        seen.add(key)
        vulns.append(
            {
                "template_id": template_id,
                "severity": info.get("severity", "unknown"),
                "matcher_name": matcher_name or None,
                "matched_url": matched_url or None,
                "host": host or None,
                "description": info.get("description"),
            }
        )
    return vulns


def parse_httpx_headers_output(stdout: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in stdout.splitlines():
        row = line.strip()
        if not row:
            continue
        try:
            data = json.loads(row)
        except json.JSONDecodeError:
            continue
        headers = {k.lower(): v for k, v in (data.get("header") or {}).items()}
        missing = [k for k in ("content-security-policy", "x-frame-options", "strict-transport-security") if k not in headers]
        if not missing:
            continue
        host = data.get("url") or data.get("input") or ""
        if host in seen:
            continue
        seen.add(host)
        findings.append(
            {
                "template_id": "reconx-missing-security-headers",
                "severity": "info",
                "matcher_name": "missing-headers",
                "host": host or None,
                "description": f"Missing security headers: {', '.join(missing)}",
            }
        )
    return findings
