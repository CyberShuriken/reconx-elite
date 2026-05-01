"""Report Service for ReconX Elite.

Generates professional HackerOne-quality vulnerability reports.
Features:
- CVSS 3.1 calculator
- CWE/OWASP mapping
- HackerOne format
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.model_registry import get_model_config, get_task_role
from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


# CVSS 3.1 score to severity mapping
def cvss_to_severity(score: float) -> str:
    """Convert CVSS score to severity rating."""
    if score >= 9.0:
        return "critical"
    elif score >= 7.0:
        return "high"
    elif score >= 4.0:
        return "medium"
    else:
        return "low"


# CWE to OWASP mapping
CWE_TO_OWASP: dict[str, str] = {
    "CWE-79": "A03:2021 - Injection",
    "CWE-89": "A03:2021 - Injection",
    "CWE-200": "A01:2021 - Broken Access Control",
    "CWE-287": "A07:2021 - Identification and Authentication Failures",
    "CWE-352": "A01:2021 - Broken Access Control",
    "CWE-434": "A04:2021 - Insecure Design",
    "CWE-502": "A08:2021 - Software and Data Integrity Failures",
    "CWE-798": "A07:2021 - Identification and Authentication Failures",
    "CWE-918": "A10:2021 - Server-Side Request Forgery (SSRF)",
    "CWE-22": "A01:2021 - Broken Access Control",
}


def get_owasp_category(cwe_id: str | None) -> str:
    """Get OWASP category for CWE ID."""
    if not cwe_id:
        return "Unknown"
    return CWE_TO_OWASP.get(cwe_id, "A04:2021 - Insecure Design")


# Template path
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def load_report_template(template_name: str = "hackerone_report.md") -> str:
    """Load report template from file."""
    template_path = TEMPLATES_DIR / template_name
    if template_path.exists():
        return template_path.read_text()
    # Fallback to basic template
    return """# {title}

**Severity:** {severity}
**CVSS:** {cvss_score}

## Summary
{summary}

## Remediation
{remediation}
"""


def render_template(template: str, data: dict[str, Any]) -> str:
    """Simple template rendering with {{variable}} syntax."""
    result = template
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value) if value is not None else "N/A")
    return result


class ReportService:
    """Service for generating vulnerability reports."""

    def __init__(self):
        self.openrouter = get_openrouter_client()
        self.template = load_report_template()

    async def generate_hackerone_report(self, finding: dict[str, Any], model_role: str | None = None) -> dict[str, Any]:
        """Generate HackerOne-format report for a finding.

        Args:
            finding: Vulnerability finding data
            model_role: AI model role to use for generation

        Returns:
            Dict with report data and metadata
        """
        # Determine model based on severity
        severity = finding.get("severity", "medium").lower()
        if severity in ["critical", "high"]:
            role = model_role or "critical_reporter"
        else:
            role = model_role or "standard_reporter"

        # Calculate CVSS
        cvss_score = finding.get("cvss_score", 5.0)
        if not finding.get("cvss_score"):
            cvss_score = await self._calculate_cvss(finding)

        # Generate report sections using AI
        summary = finding.get("description") or await self._generate_summary(finding, role)
        impact = finding.get("impact") or await self._generate_impact(finding, role)
        remediation = finding.get("remediation") or await self._generate_remediation(finding, role)
        reproduction = await self._generate_reproduction_steps(finding, role)

        # Build report data
        cwe_id = finding.get("cwe_id") or finding.get("cwe") or "CWE-未知"
        report_data = {
            "title": finding.get("name") or finding.get("title") or "Security Vulnerability",
            "severity": severity.upper(),
            "cvss_score": f"{cvss_score:.1f}",
            "cwe_id": cwe_id,
            "owasp_category": get_owasp_category(cwe_id),
            "summary": summary,
            "impact": impact,
            "reproduction_steps": reproduction,
            "poc_request": finding.get("poc_request") or "N/A",
            "poc_response": finding.get("poc_response") or "N/A",
            "remediation": remediation,
            "references": finding.get("references") or "- Nuclei Template Documentation",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "template_id": finding.get("template_id") or "custom",
        }

        # Render report
        report_text = render_template(self.template, report_data)

        return {
            "report_text": report_text,
            "report_data": report_data,
            "model_role": role,
            "format": "hackerone",
        }

    async def _calculate_cvss(self, finding: dict[str, Any]) -> float:
        """Calculate CVSS 3.1 score from finding data."""
        # Simplified calculation - would use proper CVSS calculator in production
        severity = finding.get("severity", "medium").lower()

        base_scores = {
            "critical": 9.5,
            "high": 7.5,
            "medium": 5.5,
            "low": 3.5,
            "info": 0.0,
        }

        return base_scores.get(severity, 5.0)

    async def _generate_summary(self, finding: dict[str, Any], role: str) -> str:
        """Generate vulnerability summary using AI."""
        system_prompt = "You are a security researcher writing a vulnerability summary for a bug bounty report. Be concise and professional."

        user_message = f"""
Generate a 2-3 sentence summary for this vulnerability:

Title: {finding.get('name') or finding.get('title')}
Severity: {finding.get('severity')}
Template: {finding.get('template_id')}
Description: {finding.get('description')}

Summary:
"""

        try:
            result = await self.openrouter.call_model_by_role(
                role=role,
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=200,
            )
            return result.get("content", finding.get("description") or "No description available")
        except Exception as e:
            logger.error("Failed to generate summary: %s", e)
            return finding.get("description") or "No description available"

    async def _generate_impact(self, finding: dict[str, Any], role: str) -> str:
        """Generate impact section using AI."""
        system_prompt = "Describe the security impact of a vulnerability in 1-2 sentences for a bug bounty report."

        user_message = f"""
What is the security impact of this {finding.get('severity')} severity vulnerability:
{finding.get('name') or finding.get('title')}

Impact:
"""

        try:
            result = await self.openrouter.call_model_by_role(
                role=role,
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=150,
            )
            return result.get("content", "This vulnerability could compromise the security of the application.")
        except Exception as e:
            logger.error("Failed to generate impact: %s", e)
            return "This vulnerability could compromise the security of the application."

    async def _generate_remediation(self, finding: dict[str, Any], role: str) -> str:
        """Generate remediation advice using AI."""
        system_prompt = (
            "Provide specific, actionable remediation steps for a security vulnerability. Be concrete, not generic."
        )

        user_message = f"""
Provide specific remediation steps for:

Vulnerability: {finding.get('name') or finding.get('title')}
Severity: {finding.get('severity')}
Template ID: {finding.get('template_id')}

Remediation:
"""

        try:
            result = await self.openrouter.call_model_by_role(
                role=role,
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=300,
            )
            return result.get(
                "content", "1. Implement proper input validation\n2. Apply security patches\n3. Review access controls"
            )
        except Exception as e:
            logger.error("Failed to generate remediation: %s", e)
            return "1. Implement proper input validation\n2. Apply security patches\n3. Review access controls"

    async def _generate_reproduction_steps(self, finding: dict[str, Any], role: str) -> str:
        """Generate reproduction steps."""
        endpoint = finding.get("matched_url") or finding.get("endpoint") or "Target URL"
        template_id = finding.get("template_id") or "N/A"

        return f"""1. Access the target: {endpoint}
2. Observe the behavior described in the vulnerability
3. Verify using the detection template: {template_id}
"""

    async def generate_pdf_report(
        self, scan_id: int, findings: list[dict[str, Any]], include_details: bool = True
    ) -> bytes:
        """Generate PDF report for scan findings.

        Note: This is a placeholder. In production, use WeasyPrint or ReportLab.

        Args:
            scan_id: The scan ID
            findings: List of findings
            include_details: Whether to include full details

        Returns:
            PDF bytes
        """
        # Placeholder - would integrate with PDF library
        logger.info("PDF generation requested for scan %s with %s findings", scan_id, len(findings))

        # Return placeholder content
        content = f"""
ReconX Elite Report
===================
Scan ID: {scan_id}
Findings: {len(findings)}
Generated: {datetime.now(timezone.utc).isoformat()}

Summary:
- Critical: {sum(1 for f in findings if f.get('severity') == 'critical')}
- High: {sum(1 for f in findings if f.get('severity') == 'high')}
- Medium: {sum(1 for f in findings if f.get('severity') == 'medium')}
- Low: {sum(1 for f in findings if f.get('severity') == 'low')}
"""
        return content.encode()


# Global instance
_report_service: ReportService | None = None


def get_report_service() -> ReportService:
    """Get or create global ReportService instance."""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
