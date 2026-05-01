"""Phase 7: AI Deep Analysis and Exploit Chaining.

Per Master Prompt Section 3 - Phase 7:
- NEMOTRON_SUPER for exploit chaining analysis
- Chain opportunities: SSRF+Redis, subdomain takeover+XSS, IDOR+JWT
- CVSS 3.1 vector string generation
- QWEN_CODER for PoC scripts (Python + curl + nuclei template)
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class DeepAnalysisService:
    """Phase 7: AI Deep Analysis Service.

    Performs deep chain reasoning on high-severity findings
    and generates PoC scripts.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def analyze_finding_chains(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze exploit chains between findings.

        Per Master Prompt - NEMOTRON_SUPER for exploit chaining:
        - SSRF + internal Redis access → RCE?
        - Subdomain takeover + XSS → account takeover?
        - IDOR + JWT weak signing → privilege escalation?

        Args:
            findings: List of confirmed findings from Phase 6

        Returns:
            Chain analysis with attack paths and combined severity
        """
        if not findings:
            return {"chains": [], "combined_findings": [], "escalation_opportunities": []}

        # Filter for high-severity findings
        high_severity = [f for f in findings if f.get("severity", "").lower() in ["critical", "high"]]

        if not high_severity:
            return {"chains": [], "combined_findings": [], "escalation_opportunities": []}

        # Prepare findings summary for AI
        findings_summary = self._format_findings_for_ai(high_severity)

        system_prompt = """You are a deep security analyst for ReconX-Elite, specializing in exploit chaining.

Analyze the provided vulnerability findings and identify:
1. Potential attack chains between findings
2. Combined business impact of chaining vulnerabilities
3. Escalation paths from lower to higher severity
4. Specific step-by-step exploitation chains
5. Actual business impact (data breach, financial fraud, auth bypass, etc.)

For each chain, provide:
- Chain ID and description
- Findings involved
- Combined severity (CVSS ≥ 7.0 for critical chains)
- Step-by-step exploitation path
- Business impact assessment
- CVSS 3.1 vector string for the combined attack

Respond in JSON format:
{
    "chains": [
        {
            "chain_id": 1,
            "description": "SSRF to Redis RCE",
            "findings": ["finding_id_1", "finding_id_2"],
            "combined_severity": "Critical",
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            "exploit_path": [
                "1. Discover SSRF in /api/proxy?url=",
                "2. Use SSRF to access internal Redis on 127.0.0.1:6379",
                "3. Execute Redis commands via SSRF payload",
                "4. Achieve RCE via Redis module loading"
            ],
            "business_impact": "Full system compromise, data exfiltration, lateral movement",
            "validation_steps": ["Test SSRF to 127.0.0.1:6379", "Check Redis module loading capability"]
        }
    ],
    "escalation_opportunities": [
        {
            "from": "IDOR in /api/user/{id}",
            "to": "Privilege Escalation",
            "steps": ["Enumerate user IDs", "Modify role parameter in JWT", "Access admin endpoints"]
        }
    ]
}
"""

        user_message = f"""Analyze the following high-severity findings for exploit chaining opportunities:

Findings:
{findings_summary}

Provide your chain analysis in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="exploit_chain",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                chain_data = json.loads(result["content"])
                logger.info(f"AI chain analysis completed: {len(chain_data.get('chains', []))} chains identified")
                return chain_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse chain analysis response")

        # Fallback: simple heuristic chaining
        return self._heuristic_chain_analysis(high_severity)

    def _format_findings_for_ai(self, findings: list[dict[str, Any]]) -> str:
        """Format findings for AI input.

        Args:
            findings: List of finding dicts

        Returns:
            Formatted string
        """
        lines = []
        for i, finding in enumerate(findings):
            lines.append(
                f"{i+1}. [{finding.get('severity', 'Unknown')}] {finding.get('type', 'Unknown')} at {finding.get('endpoint', 'Unknown')}"
            )
            lines.append(f"   Description: {finding.get('description', 'N/A')}")
            lines.append("")
        return "\n".join(lines)

    def _heuristic_chain_analysis(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Fallback heuristic chain analysis.

        Args:
            findings: List of finding dicts

        Returns:
            Chain analysis dict
        """
        chains = []
        escalations = []

        # Simple heuristic: SSRF + database = potential RCE
        ssrf_findings = [f for f in findings if "ssrf" in f.get("type", "").lower()]
        db_findings = [
            f
            for f in findings
            if any(db in f.get("type", "").lower() for db in ["redis", "mongodb", "mysql", "postgresql"])
        ]

        if ssrf_findings and db_findings:
            chains.append(
                {
                    "chain_id": 1,
                    "description": "SSRF to Database Access",
                    "findings": [f.get("id", "") for f in ssrf_findings[:1] + db_findings[:1]],
                    "combined_severity": "High",
                    "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:H",
                    "exploit_path": [
                        "1. Exploit SSRF to access internal database",
                        "2. Attempt database authentication bypass",
                        "3. Extract sensitive data",
                    ],
                    "business_impact": "Data breach, credential exposure",
                    "validation_steps": ["Test SSRF to internal DB ports", "Check for default credentials"],
                }
            )

        return {
            "chains": chains,
            "combined_findings": findings,
            "escalation_opportunities": escalations,
        }

    async def generate_poc(self, finding: dict[str, Any], base_url: str) -> dict[str, Any]:
        """Generate PoC script for a finding.

        Per Master Prompt - QWEN_CODER for PoC generation:
        - Self-contained Python PoC script
        - Captures full HTTP request/response
        - Prints clear success/failure output
        - Includes safety checks (confirm scope before firing)
        - Curl one-liner for manual verification
        - Nuclei template YAML

        Args:
            finding: Finding dict to generate PoC for
            base_url: Base URL for target

        Returns:
            PoC dict with python_script, curl_command, nuclei_template
        """
        system_prompt = """You are a PoC generator for ReconX-Elite.

Generate a Proof of Concept for the given vulnerability.

Provide:
1. A self-contained Python PoC script that:
   - Reproduces the vulnerability
   - Captures the full HTTP request/response
   - Prints clear success/failure output
   - Includes safety checks (confirm scope before firing)
   - Uses httpx or requests library

2. A curl one-liner for quick manual verification

3. A nuclei template YAML for the specific finding

Respond in JSON format:
{
    "python_script": "import httpx\\n...",
    "curl_command": "curl -X POST ...",
    "nuclei_template": "id: poc-template\\n...",
    "safety_checks": ["Check target is in scope", "Confirm before sending"]
}
"""

        user_message = f"""Generate a PoC for this vulnerability:

Vulnerability Type: {finding.get('type', 'Unknown')}
Endpoint: {finding.get('endpoint', 'Unknown')}
Base URL: {base_url}
Severity: {finding.get('severity', 'Unknown')}
Description: {finding.get('description', 'N/A')}
Payload: {finding.get('payload', {})}
Expected Behavior: {finding.get('expected_behavior', 'N/A')}
Vulnerable Behavior: {finding.get('vulnerable_behavior', 'N/A')}

Provide your PoC in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="poc_generation",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                poc_data = json.loads(result["content"])
                logger.info(f"PoC generated for {finding.get('type')}")
                return poc_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse PoC generation response")

        # Fallback: basic PoC template
        return self._generate_fallback_poc(finding, base_url)

    def _generate_fallback_poc(self, finding: dict[str, Any], base_url: str) -> dict[str, Any]:
        """Generate fallback PoC template.

        Args:
            finding: Finding dict
            base_url: Base URL

        Returns:
            Basic PoC dict
        """
        endpoint = finding.get("endpoint", "/")
        vuln_type = finding.get("type", "unknown")

        python_script = f'''#!/usr/bin/env python3
"""PoC for {vuln_type} at {endpoint}"""

import sys
import httpx

def check_scope(url):
    """Check if target is in scope before testing."""
    target = input(f"Target to test: {{url}}\\nContinue? [y/N]: ")
    return target.lower() == 'y'

async def test_vulnerability():
    """Test the vulnerability."""
    if not check_scope("{base_url}{endpoint}"):
        print("Aborted by user")
        sys.exit(0)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("{base_url}{endpoint}")
            print(f"Status: {{response.status_code}}")
            print(f"Response: {{response.text[:500]}}")

            # Add vulnerability-specific check here
            if response.status_code == 200:
                print("SUCCESS: Vulnerability confirmed")
            else:
                print("FAILED: Could not confirm vulnerability")

    except Exception as e:
        print(f"ERROR: {{e}}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_vulnerability())
'''

        curl_command = f'curl -X GET "{base_url}{endpoint}" -v'

        nuclei_template = f"""id: {vuln_type}-poc
info:
  name: {vuln_type} PoC
  severity: {finding.get("severity", "medium")}
  author: ReconX-Elite

requests:
  - method: GET
    path:
      - "{endpoint}"

    matchers:
      - type: status
        status:
          - 200
"""

        return {
            "python_script": python_script,
            "curl_command": curl_command,
            "nuclei_template": nuclei_template,
            "safety_checks": ["Check target is in scope", "Confirm before sending"],
        }

    async def generate_cvss_vector(self, finding: dict[str, Any]) -> str:
        """Generate CVSS 3.1 vector string for a finding.

        Args:
            finding: Finding dict with severity and impact info

        Returns:
            CVSS 3.1 vector string
        """
        severity = finding.get("severity", "Low").lower()

        # Simple CVSS mapping
        cvss_vectors = {
            "critical": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            "high": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N",
            "medium": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
            "low": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        }

        return cvss_vectors.get(severity, cvss_vectors["low"])
