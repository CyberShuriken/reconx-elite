"""Scope Guard for ReconX Elite.

Implements hard constraints from Master Prompt Section 7 - Legal & Safety.
Prevents out-of-scope traffic and ensures compliance with bug bounty scope.
"""

from __future__ import annotations

import fnmatch
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def is_in_scope(host: str, wildcard_pattern: str | None) -> bool:
    """Check if a host is within the defined scope.

    Args:
        host: The hostname to check (e.g., "api.example.com")
        wildcard_pattern: The wildcard scope pattern (e.g., "*.example.com")

    Returns:
        True if host is in scope, False otherwise

    Examples:
        >>> is_in_scope("api.example.com", "*.example.com")
        True
        >>> is_in_scope("evil.com", "*.example.com")
        False
        >>> is_in_scope("sub.api.example.com", "*.example.com")
        True
    """
    if not wildcard_pattern:
        # No scope defined - be permissive but log warning
        logger.warning("No scope pattern defined, allowing host: %s", host)
        return True

    # Normalize host
    host = host.lower().strip()
    if host.startswith("http://") or host.startswith("https://"):
        parsed = urlparse(host)
        host = parsed.netloc or parsed.path

    # Remove port if present
    if ":" in host:
        host = host.split(":")[0]

    # Handle wildcard patterns
    pattern = wildcard_pattern.lower().strip()

    # Direct match
    if host == pattern.replace("*.", ""):
        return True

    # Wildcard match
    if pattern.startswith("*."):
        root_domain = pattern[2:]  # Remove *.
        # Check if host ends with root domain or is exactly root domain
        if host == root_domain or host.endswith("." + root_domain):
            return True

    # FQDN pattern match
    if fnmatch.fnmatch(host, pattern):
        return True

    # Subdomain match for explicit subdomains
    if host.endswith("." + pattern) or host == pattern:
        return True

    logger.warning("Host %s is OUT OF SCOPE (pattern: %s)", host, wildcard_pattern)
    return False


def extract_root_domain(wildcard_pattern: str) -> str:
    """Extract root domain from wildcard pattern.

    Args:
        wildcard_pattern: The wildcard scope (e.g., "*.example.com")

    Returns:
        The root domain (e.g., "example.com")
    """
    pattern = wildcard_pattern.lower().strip()
    if pattern.startswith("*."):
        return pattern[2:]
    return pattern


def validate_urls_against_scope(urls: list[str], scope_pattern: str | None) -> tuple[list[str], list[str]]:
    """Validate a list of URLs against scope.

    Args:
        urls: List of URLs to validate
        scope_pattern: The wildcard scope pattern

    Returns:
        Tuple of (in_scope_urls, out_of_scope_urls)
    """
    in_scope = []
    out_of_scope = []

    for url in urls:
        try:
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            host = parsed.netloc or parsed.path

            if is_in_scope(host, scope_pattern):
                in_scope.append(url)
            else:
                out_of_scope.append(url)
                logger.warning("BLOCKED out-of-scope URL: %s", url)
        except Exception as e:
            logger.error("Failed to validate URL %s: %s", url, e)
            out_of_scope.append(url)

    return in_scope, out_of_scope


class ScopeGuard:
    """Scope guard to prevent out-of-scope traffic."""

    def __init__(self, scope_pattern: str | None = None):
        self.scope_pattern = scope_pattern
        self.blocked_count = 0
        self.allowed_count = 0

    def check(self, host: str) -> bool:
        """Check if host is in scope.

        Args:
            host: Hostname to check

        Returns:
            True if in scope
        """
        result = is_in_scope(host, self.scope_pattern)
        if result:
            self.allowed_count += 1
        else:
            self.blocked_count += 1
        return result

    def check_url(self, url: str) -> bool:
        """Check if URL is in scope.

        Args:
            url: URL to check

        Returns:
            True if in scope
        """
        try:
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            host = parsed.netloc or parsed.path
            return self.check(host)
        except Exception as e:
            logger.error("Failed to check URL %s: %s", url, e)
            return False

    def get_stats(self) -> dict:
        """Get scope check statistics."""
        return {
            "scope_pattern": self.scope_pattern,
            "allowed": self.allowed_count,
            "blocked": self.blocked_count,
            "total": self.allowed_count + self.blocked_count,
        }


def sanitize_scope_input(user_input: str) -> str | None:
    """Sanitize and validate user-provided scope input.

    Args:
        user_input: Raw user input for scope

    Returns:
        Sanitized scope pattern or None if invalid
    """
    if not user_input:
        return None

    # Remove dangerous characters
    sanitized = re.sub(r"[^a-zA-Z0-9.*_-]", "", user_input.lower().strip())

    # Validate format
    if ".." in sanitized or sanitized.startswith(".") or sanitized.endswith("."):
        logger.error("Invalid scope format: %s", user_input)
        return None

    # Must look like a domain
    if "." not in sanitized.replace("*.", ""):
        logger.error("Scope does not look like a domain: %s", sanitized)
        return None

    return sanitized
