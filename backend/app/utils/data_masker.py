"""Data Masker for ReconX Elite.

Implements PII detection and redaction before AI prompts.
Ensures sensitive data is not sent to external AI services.
"""

from __future__ import annotations

import re
from typing import Pattern

# PII Detection Patterns
PII_PATTERNS: dict[str, Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "api_key": re.compile(r"\b(?:api[_-]?key|apikey)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]{16,})['\"]?", re.IGNORECASE),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "jwt": re.compile(r"\beyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\b"),
    "bearer_token": re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.]+\b", re.IGNORECASE),
    "password": re.compile(r"\b(?:password|passwd|pwd)[\s]*[:=][\s]*['\"]?([^'\"\s]{8,})['\"]?", re.IGNORECASE),
}

# Redaction placeholder
REDACTED_PLACEHOLDER = "[REDACTED]"


def redact_pii(text: str, patterns: list[str] | None = None) -> str:
    """Redact PII from text.

    Args:
        text: Input text potentially containing PII
        patterns: Specific patterns to redact (redacts all if None)

    Returns:
        Text with PII redacted
    """
    if not text:
        return text

    redacted = text
    patterns_to_check = patterns if patterns else list(PII_PATTERNS.keys())

    for pattern_name in patterns_to_check:
        pattern = PII_PATTERNS.get(pattern_name)
        if pattern:
            redacted = pattern.sub(REDACTED_PLACEHOLDER, redacted)

    return redacted


def redact_for_ai_prompt(text: str) -> str:
    """Redact sensitive data before sending to AI services.

    This is the primary function to use before AI API calls.

    Args:
        text: Raw text from tool output or other sources

    Returns:
        Sanitized text safe for AI processing
    """
    # Redact all PII types
    redacted = redact_pii(text)

    # Additional security: redact potential credentials in URLs
    redacted = re.sub(r"https?://[^:]+:[^@]+@", "https://[CREDENTIALS_REDACTED]@", redacted)

    return redacted


def redact_report_output(report_text: str, keep_structure: bool = True) -> str:
    """Sanitize report output for external sharing.

    Args:
        report_text: Raw report content
        keep_structure: If True, preserves structure with placeholders

    Returns:
        Sanitized report content
    """
    if keep_structure:
        return redact_pii(report_text)
    else:
        # Aggressive redaction - remove entire lines containing PII
        lines = report_text.split("\n")
        safe_lines = []
        for line in lines:
            has_pii = any(pattern.search(line) for pattern in PII_PATTERNS.values())
            if not has_pii:
                safe_lines.append(line)
        return "\n".join(safe_lines)


def detect_pii(text: str) -> dict[str, list[str]]:
    """Detect PII in text and return matches by type.

    Args:
        text: Text to analyze

    Returns:
        Dict mapping PII type to list of detected values
    """
    if not text:
        return {}

    findings = {}
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            findings[pattern_name] = matches[:10]  # Limit to first 10 matches

    return findings


def has_pii(text: str) -> bool:
    """Quick check if text contains any PII.

    Args:
        text: Text to check

    Returns:
        True if PII detected
    """
    if not text:
        return False

    return any(pattern.search(text) for pattern in PII_PATTERNS.values())


class DataMasker:
    """Stateful data masker for tracking and redacting PII."""

    def __init__(self):
        self.redaction_count = 0
        self.detection_log: list[dict] = []

    def mask(self, text: str, context: str = "") -> str:
        """Mask PII in text and log detection.

        Args:
            text: Text to mask
            context: Context for logging (e.g., 'ai_prompt', 'report')

        Returns:
            Masked text
        """
        detections = detect_pii(text)

        if detections:
            self.detection_log.append(
                {
                    "context": context,
                    "types_found": list(detections.keys()),
                    "count": sum(len(v) for v in detections.values()),
                }
            )
            self.redaction_count += sum(len(v) for v in detections.values())

        return redact_for_ai_prompt(text)

    def get_stats(self) -> dict:
        """Get masking statistics."""
        return {
            "total_redactions": self.redaction_count,
            "detection_count": len(self.detection_log),
            "recent_detections": self.detection_log[-10:],  # Last 10
        }


def sanitize_tool_output(stdout: str, stderr: str = "") -> tuple[str, str]:
    """Sanitize tool output before AI processing.

    Args:
        stdout: Tool standard output
        stderr: Tool standard error

    Returns:
        Tuple of (sanitized_stdout, sanitized_stderr)
    """
    return redact_for_ai_prompt(stdout), redact_for_ai_prompt(stderr)
