"""Phase 4: JavaScript Analysis and Secret Extraction.

Per Master Prompt Section 3 - Phase 4:
- Crawl and collect JS files (katana, hakrawler)
- Download and analyze JS files
- Secret scanning (trufflehog, grep patterns)
- Endpoint extraction (linkfinder)
- AI analysis (MINIMAX for large files, QWEN_CODER for payloads)
"""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from pathlib import Path
from typing import Any

import httpx

from app.core.tool_registry import get_tools_for_phase
from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class JSAnalysisService:
    """Phase 4: JavaScript Analysis Service.

    Crawls, downloads, and analyzes JavaScript files for secrets,
    endpoints, and hidden functionality.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def analyze_domain_js(self, live_hosts: list[str]) -> dict[str, Any]:
        """Perform complete JS analysis for a domain.

        Args:
            live_hosts: List of live host URLs to analyze

        Returns:
            Analysis results with js_files, secrets, endpoints, findings
        """
        results = {
            "js_files": [],
            "secrets": [],
            "endpoints": [],
            "findings": [],
            "js_analyzed_count": 0,
        }

        # Step 1: Crawl and collect JS URLs
        js_urls = await self._collect_js_urls(live_hosts)
        logger.info(f"Collected {len(js_urls)} JavaScript URLs")

        # Step 2: Download and analyze JS files
        js_files_data = await self._download_js_files(js_urls)
        results["js_files"] = [f["url"] for f in js_files_data]
        results["js_analyzed_count"] = len(js_files_data)

        # Step 3: Secret scanning
        secrets = await self._scan_secrets(js_files_data)
        results["secrets"] = secrets

        # Step 4: Endpoint extraction
        endpoints = await self._extract_endpoints(js_files_data)
        results["endpoints"] = endpoints

        # Step 5: AI analysis for large files (>50KB)
        for js_file in js_files_data:
            if len(js_file.get("content", "")) > 50000:
                ai_analysis = await self._analyze_large_js(js_file)
                if ai_analysis:
                    results["findings"].extend(ai_analysis["findings"])
                    results["secrets"].extend(ai_analysis["secrets"])

        return results

    async def _collect_js_urls(self, live_hosts: list[str]) -> list[str]:
        """Collect JS file URLs from live hosts.

        Uses katana and hakrawler if available.

        Args:
            live_hosts: List of host URLs

        Returns:
            List of JS file URLs
        """
        js_urls = []

        # Try katana if available
        katana_available = True  # TODO: Check with tool discovery
        if katana_available:
            for host in live_hosts:
                try:
                    # katana -u {host} -js-crawl -o katana_urls.txt
                    # For now, use httpx to fetch and parse HTML
                    urls = await self._fetch_js_via_httpx(host)
                    js_urls.extend(urls)
                except Exception as e:
                    logger.warning(f"Katana failed for {host}: {e}")

        # Try hakrawler if available
        hakrawler_available = False  # TODO: Check with tool discovery
        if hakrawler_available:
            for host in live_hosts:
                try:
                    urls = await self._fetch_js_via_httpx(host)
                    js_urls.extend(urls)
                except Exception as e:
                    logger.warning(f"Hakrawler failed for {host}: {e}")

        # Fallback: simple HTTP fetch for .js files
        if not js_urls:
            for host in live_hosts:
                try:
                    urls = await self._fetch_js_via_httpx(host)
                    js_urls.extend(urls)
                except Exception as e:
                    logger.warning(f"HTTP fetch failed for {host}: {e}")

        # Deduplicate
        return list(set(js_urls))

    async def _fetch_js_via_httpx(self, host: str) -> list[str]:
        """Fetch JS URLs via HTTPX by parsing HTML.

        Args:
            host: Host URL to crawl

        Returns:
            List of JS file URLs
        """
        js_urls = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(host)
                html = response.text

                # Find all .js references
                js_pattern = r'(?:src|href)=["\']([^"\']+\.js(?:\?[^"\']*)?)["\']'
                matches = re.findall(js_pattern, html, re.IGNORECASE)

                for match in matches:
                    # Convert relative URLs to absolute
                    if match.startswith("/"):
                        base = host.rstrip("/")
                        js_urls.append(f"{base}{match}")
                    elif match.startswith("http"):
                        js_urls.append(match)
                    else:
                        base = host.rstrip("/")
                        js_urls.append(f"{base}/{match}")

        except Exception as e:
            logger.warning(f"Failed to fetch {host}: {e}")

        return js_urls

    async def _download_js_files(self, js_urls: list[str]) -> list[dict[str, Any]]:
        """Download JS file contents.

        Args:
            js_urls: List of JS file URLs

        Returns:
            List of dicts with url, content, and size
        """
        js_files = []
        semaphore = asyncio.Semaphore(10)  # Limit concurrent downloads

        async def fetch_js(url: str) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url)
                        return {
                            "url": url,
                            "content": response.text,
                            "size": len(response.text),
                        }
                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    return None

        tasks = [fetch_js(url) for url in js_urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        for result in results:
            if result:
                js_files.append(result)

        return js_files

    async def _scan_secrets(self, js_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Scan JS files for secrets and credentials.

        Args:
            js_files: List of JS file dicts with content

        Returns:
            List of secret findings
        """
        secrets = []

        # Secret patterns from master prompt
        secret_patterns = [
            r'(api[_-]?key|secret|token|password|aws_|AKIA)[\'"]?\s*[:=]\s*[\'"]?([A-Za-z0-9+/]{16,})',
            r"(Bearer|Basic)\s+([A-Za-z0-9+/=]{20,})",
            r"(sk_|pk_|live_|test_)[a-zA-Z0-9]{32,}",  # Stripe-like
            r"(AIza[A-Za-z0-9_-]{35})",  # Google API key
            r"(xox[baprs]-\d{10,}-\d{10,}-\d{10,}-[a-zA-Z0-9]{32})",  # Slack
            r"(ghp_[a-zA-Z0-9]{36})",  # GitHub PAT
            r"(glpat-[a-zA-Z0-9_-]{20})",  # GitLab PAT
        ]

        for js_file in js_files:
            content = js_file.get("content", "")
            url = js_file.get("url", "")

            for pattern in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Mask the actual secret value
                    secret_value = match.group(2) if len(match.groups()) > 1 else match.group(0)
                    masked_value = secret_value[:4] + "*" * (len(secret_value) - 8) + secret_value[-4:]

                    secrets.append(
                        {
                            "type": match.group(1) if len(match.groups()) > 0 else "credential",
                            "masked_value": masked_value,
                            "url": url,
                            "line": content[: match.start()].count("\n") + 1,
                            "severity": "critical" if "api_key" in match.group(0).lower() else "high",
                        }
                    )

        return secrets

    async def _extract_endpoints(self, js_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract API endpoints from JS files.

        Args:
            js_files: List of JS file dicts with content

        Returns:
            List of endpoint findings
        """
        endpoints = []

        # Endpoint patterns
        endpoint_patterns = [
            r'["\']/(api/v?\d?/[^"\']+)["\']',  # REST API endpoints
            r'["\']/(graphql)["\']',  # GraphQL
            r'fetch\(["\']([^"\']+)["\']',  # fetch() calls
            r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',  # axios calls
            r'\.post\(["\']([^"\']+)["\']',  # .post() calls
        ]

        for js_file in js_files:
            content = js_file.get("content", "")
            url = js_file.get("url", "")

            for pattern in endpoint_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    endpoint = match.group(1) if len(match.groups()) > 0 else match.group(0)

                    # Skip common non-endpoint patterns
                    if any(skip in endpoint for skip in [".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ttf"]):
                        continue

                    endpoints.append(
                        {
                            "endpoint": endpoint,
                            "url": url,
                            "method": "GET",  # Default, could be refined
                            "interesting": any(
                                keyword in endpoint.lower()
                                for keyword in ["api", "admin", "user", "auth", "login", "internal"]
                            ),
                        }
                    )

        # Deduplicate
        seen = set()
        unique_endpoints = []
        for ep in endpoints:
            key = (ep["endpoint"], ep["method"])
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)

        return unique_endpoints

    async def _analyze_large_js(self, js_file: dict[str, Any]) -> dict[str, Any] | None:
        """Analyze large JS file using AI (MINIMAX).

        Per Master Prompt - MINIMAX for files > 50KB:
        - Hidden API endpoints not in HTML
        - Hardcoded credentials, tokens, API keys
        - Internal domain names or IP addresses
        - GraphQL schema hints or REST patterns
        - Feature flags or debug modes

        Args:
            js_file: JS file dict with content

        Returns:
            Analysis results with findings and secrets
        """
        content = js_file.get("content", "")
        url = js_file.get("url", "")

        if len(content) <= 50000:
            return None

        # Truncate content if too large for model context
        max_content = 10000  # Limit for AI input
        truncated_content = content[:max_content] + "\n... [truncated]"

        system_prompt = """You are a JavaScript security analyst for ReconX-Elite.

Analyze the provided JavaScript code and identify:
1. Hidden API endpoints not visible in HTML
2. Hardcoded credentials, tokens, or API keys
3. Internal domain names or IP addresses referenced in comments
4. GraphQL schema hints or REST API contract patterns
5. Feature flags or debug modes that could be enabled

Respond in JSON format:
{
    "endpoints": [{"path": "/api/endpoint", "method": "GET", "interesting": true}],
    "secrets": [{"type": "api_key", "context": "description"}],
    "internal_refs": [{"type": "domain|ip", "value": "10.0.0.1", "context": "comment"}],
    "feature_flags": [{"name": "DEBUG_MODE", "value": "true"}],
    "findings": [{"type": "hidden_endpoint", "severity": "medium", "description": "..."}]
}
"""

        user_message = f"""Analyze this JavaScript file for security-relevant information:

Source URL: {url}
File Size: {len(content)} bytes

JavaScript Content:
{truncated_content}

Provide your analysis in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="js_analysis",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                analysis = json.loads(result["content"])
                logger.info(f"AI analysis completed for {url}")

                # Convert AI findings to standard format
                findings = []
                for finding in analysis.get("findings", []):
                    findings.append(
                        {
                            "type": finding["type"],
                            "severity": finding["severity"],
                            "description": finding["description"],
                            "source": "js_analysis",
                            "url": url,
                        }
                    )

                secrets = []
                for secret in analysis.get("secrets", []):
                    secrets.append(
                        {
                            "type": secret["type"],
                            "context": secret["context"],
                            "url": url,
                            "severity": "high",
                        }
                    )

                return {"findings": findings, "secrets": secrets}

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI analysis for {url}")

        return None

    async def generate_test_payloads(self, endpoint_pattern: str) -> list[dict[str, Any]]:
        """Generate test payloads for discovered API endpoints using AI.

        Per Master Prompt - QWEN_CODER for payload generation:
        - IDOR (sequential IDs, UUID manipulation, negative numbers)
        - Parameter pollution
        - Type confusion attacks

        Args:
            endpoint_pattern: API endpoint pattern (e.g., /api/v1/user/{id})

        Returns:
            List of test payloads
        """
        system_prompt = """You are a payload generator for ReconX-Elite.

Generate 10 targeted test payloads for the given API endpoint pattern.

Include tests for:
- IDOR (sequential IDs, UUID manipulation, negative numbers)
- Parameter pollution
- Type confusion attacks
- Access control bypass

Respond in JSON format:
{
    "payloads": [
        {
            "test_type": "idor_sequential",
            "endpoint": "/api/v1/user/1",
            "payload": {"user_id": 1},
            "expected_behavior": "403 or owner check",
            "vulnerable_behavior": "Returns user 1 data"
        }
    ]
}
"""

        user_message = f"""Generate test payloads for this API endpoint pattern:

Endpoint Pattern: {endpoint_pattern}

Provide 10 targeted test payloads in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="payload_generation",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                payload_data = json.loads(result["content"])
                return payload_data.get("payloads", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse payload generation response")

        # Fallback payloads
        return [
            {
                "test_type": "idor_sequential",
                "endpoint": endpoint_pattern.replace("{id}", "1"),
                "payload": {"id": 1},
                "expected_behavior": "403 or owner check",
                "vulnerable_behavior": "Returns data for ID 1",
            },
            {
                "test_type": "idor_negative",
                "endpoint": endpoint_pattern.replace("{id}", "-1"),
                "payload": {"id": -1},
                "expected_behavior": "400 Bad Request",
                "vulnerable_behavior": "Returns unexpected data",
            },
        ]
