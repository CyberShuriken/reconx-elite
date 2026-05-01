"""Phase 10: Professional Report Generation.

Per Master Prompt Section 3 - Phase 10:
- GPT_OSS_120B for High/Critical findings
- GPT_OSS_20B for Low/Medium findings
- HackerOne-format reports
- CVSS/CWE/OWASP auto-mapping
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Phase 10: Report Generation Service.

    Generates professional HackerOne-format vulnerability reports.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def generate_hackerone_report(
        self, finding: dict[str, Any], target: str
    ) -> dict[str, Any]:
        """Generate HackerOne-format report for a finding.

        Per Master Prompt - GPT_OSS_120B for Critical/High, GPT_OSS_20B for Low/Medium

        Report sections:
        - Title
        - Severity (CVSS 3.1 Score and Vector)
        - CWE Classification
        - OWASP Top 10 Category
        - Summary
        - Impact
        - Steps to Reproduce
        - Proof of Concept
        - Remediation
        - Estimated Bounty Range

        Args:
            finding: Finding dict with all details
            target: Target domain

        Returns:
            Complete HackerOne-format report
        """
        severity = finding.get("severity", "Low").lower()

        # Select model based on severity
        if severity in ["critical", "high"]:
            role = "critical_reporter"
        else:
            role = "standard_reporter"

        system_prompt = """You are a professional vulnerability report writer for ReconX-Elite.

Generate a HackerOne-format vulnerability report with ALL of these sections:

## Title
[VulnType] in [parameter/endpoint] on [host] — [one-line impact]

## Severity
CVSS 3.1 Score: X.X ([Critical|High|Medium|Low])
CVSS Vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H

## CWE Classification
CWE-XXX: [Vulnerability Name]

## OWASP Top 10 Category
A##:2021 – [Category Name]

## Summary
[3 sentences: what was found, where, why it matters to the business]

## Impact
[Business impact: data breach, financial loss, reputational damage, regulatory exposure — specific to this vulnerability]

## Steps to Reproduce
1. [Atomic step]
2. [Atomic step]
3. [Atomic step]
4. [Atomic step]
5. [Atomic step]
[Every step must be atomic and reproduce from zero state]

## Proof of Concept
[Full HTTP request]
Response:
[Actual response showing vulnerability]

## Remediation
[Specific, actionable fix — not generic advice]
Primary: [Primary fix]
Secondary: [Secondary fix]

## Estimated Bounty Range
$[min] – $[max] based on [program]'s historical payouts for this class

All reports must be marked: "AI-assisted — manual validation required"

Respond in Markdown format.
"""

        user_message = f"""Generate a HackerOne-format report for this vulnerability:

Target: {target}
Vulnerability Type: {finding.get('type', 'Unknown')}
Endpoint: {finding.get('endpoint', 'Unknown')}
Host: {finding.get('host', 'Unknown')}
Severity: {finding.get('severity', 'Low')}
Description: {finding.get('description', 'N/A')}
Payload: {finding.get('payload', {})}
CVSS Vector: {finding.get('cvss_vector', 'CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N')}
Proof of Concept: {finding.get('poc', 'N/A')}
Expected Behavior: {finding.get('expected_behavior', 'N/A')}
Vulnerable Behavior: {finding.get('vulnerable_behavior', 'N/A')}

Provide your report in Markdown format.
"""

        result = await self.ai_client.call_model_by_role(
            role=role,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=3000,
        )

        if result["success"]:
            report_content = result["content"]
            logger.info(f"Report generated for {finding.get('type')} using {role}")
        else:
            # Fallback: generate basic report
            report_content = self._generate_fallback_report(finding, target)

        return {
            "finding_id": finding.get("id"),
            "target": target,
            "severity": finding.get("severity"),
            "report_content": report_content,
            "model_used": role,
        }

    def _generate_fallback_report(self, finding: dict[str, Any], target: str) -> str:
        """Generate fallback report without AI.

        Args:
            finding: Finding dict
            target: Target domain

        Returns:
            Basic report in Markdown format
        """
        vuln_type = finding.get("type", "Unknown")
        endpoint = finding.get("endpoint", "Unknown")
        host = finding.get("host", target)
        severity = finding.get("severity", "Low")

        # CVSS mapping
        cvss_map = {
            "critical": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"),
            "high": ("7.5", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N"),
            "medium": ("5.4", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N"),
            "low": ("3.1", "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N"),
        }

        cvss_score, cvss_vector = cvss_map.get(severity.lower(), cvss_map["low"])

        # CWE mapping (simplified)
        cwe_map = {
            "ssrf": "CWE-918: Server-Side Request Forgery (SSRF)",
            "xss": "CWE-79: Cross-site Scripting (XSS)",
            "sqli": "CWE-89: SQL Injection",
            "idor": "CWE-639: Insecure Direct Object Reference",
            "cors": "CWE-942: Permissive Cross-domain Policy",
        }

        cwe = cwe_map.get(vuln_type.lower(), "CWE-79: Cross-site Scripting (XSS)")

        # OWASP mapping
        owasp_map = {
            "ssrf": "A10:2021 – Server-Side Request Forgery",
            "xss": "A03:2021 – Cross-site Scripting (XSS)",
            "sqli": "A03:2021 – Injection",
            "idor": "A01:2021 – Broken Access Control",
            "cors": "A05:2021 – Security Misconfiguration",
        }

        owasp = owasp_map.get(vuln_type.lower(), "A03:2021 – Cross-site Scripting (XSS)")

        report = f"""## {vuln_type.capitalize()} in {endpoint} on {host}

## Severity
CVSS 3.1 Score: {cvss_score} ({severity.capitalize()})
CVSS Vector: {cvss_vector}

## CWE Classification
{cwe}

## OWASP Top 10 Category
{owasp}

## Summary
A {vuln_type} vulnerability was discovered at {endpoint} on {host}. This vulnerability allows attackers to exploit the application by manipulating the {vuln_type} functionality. Immediate remediation is required to prevent potential security breaches.

## Impact
This vulnerability could lead to data exposure, unauthorized access, or system compromise depending on the specific exploitation scenario. The business impact includes potential regulatory fines, reputational damage, and financial loss.

## Steps to Reproduce
1. Navigate to https://{host}{endpoint}
2. Intercept the request in a proxy tool (Burp Suite)
3. Modify the {vuln_type} parameter with the provided payload
4. Forward the request
5. Observe the vulnerable response

## Proof of Concept
```
{finding.get('poc', 'N/A')}
```

## Remediation
Primary: Implement proper input validation and sanitization for {vuln_type} parameters.
Secondary: Use security headers and content security policies to mitigate exploitation.

## Estimated Bounty Range
${100 if severity == 'low' else 500 if severity == 'medium' else 2000 if severity == 'high' else 5000} – ${500 if severity == 'low' else 2000 if severity == 'medium' else 5000 if severity == 'high' else 15000} based on program historical payouts

*AI-assisted — manual validation required*
"""

        return report

    async def generate_executive_summary(
        self, findings: list[dict[str, Any]], stats: dict[str, Any]
    ) -> str:
        """Generate executive summary for the scan.

        Per Master Prompt - GPT_OSS_120B for executive summaries

        Args:
            findings: List of all findings
            stats: Scan statistics

        Returns:
            Executive summary string
        """
        critical = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
        high = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        medium = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
        low = sum(1 for f in findings if f.get("severity", "").lower() == "low")

        system_prompt = """You are an executive summary writer for ReconX-Elite.

Generate a professional executive summary for a security scan report.

Include:
- Overview of scan scope and methodology
- Summary of findings by severity
- Key security concerns
- Recommended remediation priorities
- Business impact assessment

Keep it concise (2-3 paragraphs) and suitable for executive stakeholders.
"""

        user_message = f"""Generate an executive summary for this security scan:

Scan Statistics:
- Total Subdomains: {stats.get('total_subdomains', 0)}
- Live Hosts: {stats.get('total_live_hosts', 0)}
- Total Findings: {len(findings)}

Findings by Severity:
- Critical: {critical}
- High: {high}
- Medium: {medium}
- Low: {low}

Target: {stats.get('target', 'Unknown')}

Provide your executive summary.
"""

        result = await self.ai_client.call_model_by_role(
            role="critical_reporter",
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1000,
        )

        if result["success"]:
            return result["content"]

        # Fallback summary
        return f"""ReconX-Elite completed a comprehensive security scan of {stats.get('target', 'the target')}, discovering {len(findings)} vulnerabilities across {stats.get('total_live_hosts', 0)} live hosts. The scan identified {critical} critical, {high} high, {medium} medium, and {low} low severity issues requiring immediate attention.

Key security concerns include potential data exposure, authentication bypasses, and configuration misconfigurations that could be exploited by attackers. Immediate remediation of critical and high-severity findings is strongly recommended to reduce the risk of security incidents.
"""
