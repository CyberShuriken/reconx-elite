"""PoC Generator for ReconX Elite.

Generates safe proof-of-concept scripts with:
- Y/N confirmation prompts
- Scope verification before network requests
- Safety checks for all outputs
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.scope_guard import ScopeGuard

logger = logging.getLogger(__name__)

# Safety warning template
SAFETY_WARNING = '''
# SECURITY WARNING - READ BEFORE RUNNING
# =======================================
# This script is for authorized security testing only.
# Only run against targets you have explicit permission to test.
# Unauthorized access to computer systems is illegal.
#
# By running this script, you confirm:
# 1. You have authorization to test this target
# 2. You understand the legal implications
# 3. You will not use this for malicious purposes
#
'''

# Python script safety wrapper
PYTHON_SAFETY_WRAPPER = '''
def confirm_scope(target):
    """Confirm target is in scope before execution."""
    print(f"\\nTarget: {target}")
    print("Have you verified this target is in your authorized scope?")
    response = input("Type 'YES' to proceed: ")
    return response.strip().upper() == "YES"

def safe_request(func):
    """Decorator to add safety confirmation to requests."""
    def wrapper(*args, **kwargs):
        target = kwargs.get('url') or args[0] if args else 'unknown'
        if not confirm_scope(target):
            print("Aborted: Target scope not confirmed")
            return None
        return func(*args, **kwargs)
    return wrapper
'''

# Bash script safety wrapper
BASH_SAFETY_WRAPPER = '''
# Scope confirmation function
confirm_scope() {
    echo ""
    echo "Target: $1"
    echo "Have you verified this target is in your authorized scope?"
    read -p "Type 'YES' to proceed: " response
    if [ "$response" != "YES" ]; then
        echo "Aborted: Target scope not confirmed"
        exit 1
    fi
}
'''


def generate_python_poc(
    vulnerability_name: str,
    target_url: str,
    payload: str,
    expected_behavior: str,
    remediation: str,
    scope_pattern: str | None = None,
) -> str:
    """Generate a safe Python PoC script.

    Args:
        vulnerability_name: Name of the vulnerability
        target_url: Target URL for testing
        payload: The exploit payload
        expected_behavior: Expected behavior when vulnerability exists
        remediation: Remediation advice
        scope_pattern: Scope pattern for verification

    Returns:
        Python script as string
    """
    scope_check = f'SCOPE_PATTERN = "{scope_pattern}"' if scope_pattern else 'SCOPE_PATTERN = None'

    script = f'''#!/usr/bin/env python3
{SAFETY_WARNING}

import urllib.request
import urllib.parse
import sys

{scope_check}

{PYTHON_SAFETY_WRAPPER}

VULNERABILITY = "{vulnerability_name}"
TARGET_URL = "{target_url}"
PAYLOAD = """{payload}"""
EXPECTED_BEHAVIOR = """{expected_behavior}"""

@safe_request
def test_vulnerability(url=TARGET_URL, payload=PAYLOAD):
    """
    Test for {vulnerability_name}.
    
    Expected behavior: {expected_behavior}
    """
    print(f"Testing {{VULNERABILITY}}...")
    print(f"Target: {{url}}")
    
    try:
        # Implement the actual test here
        req = urllib.request.Request(url, data=payload.encode())
        response = urllib.request.urlopen(req, timeout=10)
        
        print(f"Response code: {{response.status}}")
        print(f"Response body preview: {{response.read()[:500]}}")
        
        # Check for vulnerability indicators
        if "VULNERABILITY_INDICATOR" in str(response.read()):
            print(f"[!] VULNERABILITY DETECTED: {{VULNERABILITY}}")
            return True
        else:
            print(f"[-] Vulnerability not detected or requires manual verification")
            return False
            
    except Exception as e:
        print(f"[!] Error during test: {{e}}")
        return False

def main():
    print("="*60)
    print("ReconX Elite - Proof of Concept Script")
    print(f"Vulnerability: {{VULNERABILITY}}")
    print("="*60)
    
    result = test_vulnerability()
    
    if result:
        print("\\n" + "="*60)
        print("REMEDIATION ADVICE:")
        print("="*60)
        print("""{remediation}""")
        print("="*60)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
'''
    return script


def generate_bash_poc(
    vulnerability_name: str,
    target_url: str,
    curl_command: str,
    expected_indicator: str,
    remediation: str,
) -> str:
    """Generate a safe Bash/curl PoC script.

    Args:
        vulnerability_name: Name of the vulnerability
        target_url: Target URL
        curl_command: The curl command to execute
        expected_indicator: String to look for in response
        remediation: Remediation advice

    Returns:
        Bash script as string
    """
    script = f'''#!/bin/bash
{SAFETY_WARNING}

{BASH_SAFETY_WRAPPER}

VULNERABILITY="{vulnerability_name}"
TARGET_URL="{target_url}"
EXPECTED_INDICATOR="{expected_indicator}"

echo "=========================================="
echo "ReconX Elite - Proof of Concept Script"
echo "Vulnerability: $VULNERABILITY"
echo "=========================================="

# Scope confirmation
confirm_scope "$TARGET_URL"

echo ""
echo "[+] Testing $VULNERABILITY..."

# Execute the test
RESPONSE=$(curl -s {curl_command} "$TARGET_URL")

# Check for vulnerability
if echo "$RESPONSE" | grep -q "$EXPECTED_INDICATOR"; then
    echo "[!] VULNERABILITY DETECTED: $VULNERABILITY"
    echo ""
    echo "=========================================="
    echo "REMEDIATION:"
    echo "=========================================="
cat << 'EOF'
{remediation}
EOF
    echo "=========================================="
    exit 0
else
    echo "[-] Vulnerability not detected or requires manual verification"
    exit 1
fi
'''
    return script


def generate_nuclei_template(
    name: str,
    severity: str,
    description: str,
    matcher_type: str,
    matcher_value: str,
    remediation: str,
) -> str:
    """Generate a safe Nuclei template.

    Args:
        name: Template name
        severity: Severity level (critical, high, medium, low)
        description: Template description
        matcher_type: Type of matcher (word, regex, status)
        matcher_value: Value to match
        remediation: Remediation advice

    Returns:
        Nuclei template YAML string
    """
    template = f'''# ReconX Elite - Nuclei Template
# {name}
# Severity: {severity}
# Auto-generated - Review before use

id: {name.lower().replace(' ', '-')}

info:
  name: {name}
  author: reconx-elite
  severity: {severity}
  description: {description}
  remediation: |
    {remediation.replace(chr(10), chr(10) + '    ')}

http:
  - method: GET
    path:
      - "{{{{BaseURL}}}}"

    matchers:
      - type: {matcher_type}
        {matcher_type}s:
          - "{matcher_value}"
'''
    return template


def validate_poc_safety(poc_script: str, scope_pattern: str | None = None) -> dict[str, Any]:
    """Validate PoC script for safety concerns.

    Args:
        poc_script: The generated PoC script
        scope_pattern: Expected scope pattern

    Returns:
        Dict with validation results
    """
    issues = []

    # Check for safety confirmation
    if "confirm_scope" not in poc_script and "Scope confirmation" not in poc_script:
        issues.append("Missing scope confirmation prompt")

    # Check for safety warning
    if "SECURITY WARNING" not in poc_script:
        issues.append("Missing security warning header")

    # Check for dangerous patterns
    dangerous_patterns = [
        "rm -rf",
        "format C:",
        "dd if=",
        "> /dev/",
        "mkfs.",
    ]

    for pattern in dangerous_patterns:
        if pattern in poc_script:
            issues.append(f"Potentially dangerous pattern detected: {pattern}")

    return {
        "is_safe": len(issues) == 0,
        "issues": issues,
        "requires_manual_review": len(issues) > 0,
    }


class SafePoCGenerator:
    """Generator for safe PoC scripts with built-in validation."""

    def __init__(self, scope_guard: ScopeGuard | None = None):
        self.scope_guard = scope_guard or ScopeGuard()
        self.generation_log: list[dict] = []

    def generate(
        self,
        vuln_type: str,
        target: str,
        details: dict,
        output_format: str = "python",
    ) -> dict[str, Any]:
        """Generate a safe PoC with validation.

        Args:
            vuln_type: Type of vulnerability
            target: Target URL/host
            details: Vulnerability details
            output_format: 'python', 'bash', or 'nuclei'

        Returns:
            Dict with script and safety info
        """
        # Pre-check scope
        if not self.scope_guard.check(target):
            return {
                "script": None,
                "error": f"Target {target} is out of scope",
                "is_safe": False,
            }

        # Generate based on format
        if output_format == "python":
            script = generate_python_poc(
                vulnerability_name=vuln_type,
                target_url=target,
                payload=details.get("payload", ""),
                expected_behavior=details.get("expected", ""),
                remediation=details.get("remediation", "Implement proper input validation."),
                scope_pattern=self.scope_guard.scope_pattern,
            )
        elif output_format == "bash":
            script = generate_bash_poc(
                vulnerability_name=vuln_type,
                target_url=target,
                curl_command=details.get("curl", "-X GET"),
                expected_indicator=details.get("indicator", ""),
                remediation=details.get("remediation", "Implement proper input validation."),
            )
        elif output_format == "nuclei":
            script = generate_nuclei_template(
                name=vuln_type,
                severity=details.get("severity", "medium"),
                description=details.get("description", ""),
                matcher_type=details.get("matcher_type", "word"),
                matcher_value=details.get("matcher", ""),
                remediation=details.get("remediation", "Implement proper input validation."),
            )
        else:
            return {"script": None, "error": f"Unknown format: {output_format}", "is_safe": False}

        # Validate
        safety_check = validate_poc_safety(script, self.scope_guard.scope_pattern)

        # Log generation
        self.generation_log.append({
            "vuln_type": vuln_type,
            "target": target,
            "format": output_format,
            "is_safe": safety_check["is_safe"],
            "issues": safety_check["issues"],
        })

        return {
            "script": script,
            "format": output_format,
            "is_safe": safety_check["is_safe"],
            "requires_manual_review": safety_check["requires_manual_review"],
            "issues": safety_check["issues"],
        }
