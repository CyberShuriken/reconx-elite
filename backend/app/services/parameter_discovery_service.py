"""Phase 5: Parameter Discovery and URL Collection.

Per Master Prompt Section 3 - Phase 5:
- Historical URL mining (gau, waybackurls)
- Filter for parameters
- Hidden parameter fuzzing (arjun)
- Pattern filtering with gf (xss, sqli, ssrf, redirect, rce, idor)
- AI classification (GEMMA_JSON)
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class ParameterDiscoveryService:
    """Phase 5: Parameter Discovery Service.

    Discovers parameters from historical URLs and classifies
    them by vulnerability class using AI.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def discover_parameters(
        self, root_domain: str, live_hosts: list[str] | None = None
    ) -> dict[str, Any]:
        """Perform complete parameter discovery.

        Args:
            root_domain: Root domain to discover parameters for
            live_hosts: Optional list of live hosts to focus on

        Returns:
            Dictionary with urls_with_params, parameters, classified_params
        """
        results = {
            "all_urls": [],
            "urls_with_params": [],
            "parameters": [],
            "classified_params": [],
            "gf_patterns": {
                "xss": [],
                "sqli": [],
                "ssrf": [],
                "redirect": [],
                "rce": [],
                "idor": [],
            },
        }

        # Step 1: Historical URL mining
        all_urls = await self._mine_historical_urls(root_domain)
        results["all_urls"] = all_urls

        # Step 2: Filter for parameters
        urls_with_params = [url for url in all_urls if "?" in url]
        results["urls_with_params"] = urls_with_params

        # Step 3: Extract parameters
        parameters = self._extract_parameters(urls_with_params)
        results["parameters"] = parameters

        # Step 4: Pattern filtering with gf patterns
        for vuln_type in ["xss", "sqli", "ssrf", "redirect", "rce", "idor"]:
            pattern_urls = self._filter_by_pattern(urls_with_params, vuln_type)
            results["gf_patterns"][vuln_type] = pattern_urls

        # Step 5: AI classification of parameters
        if parameters:
            classified = await self._classify_parameters(parameters)
            results["classified_params"] = classified

        logger.info(
            f"Parameter discovery completed: {len(urls_with_params)} URLs with params, {len(parameters)} parameters"
        )

        return results

    async def _mine_historical_urls(self, root_domain: str) -> list[str]:
        """Mine historical URLs using gau and waybackurls.

        Args:
            root_domain: Root domain to mine

        Returns:
            List of discovered URLs
        """
        urls = []

        # Try gau (GetAllUrls)
        gau_urls = await self._fetch_gau(root_domain)
        urls.extend(gau_urls)

        # Try waybackurls
        wayback_urls = await self._fetch_waybackurls(root_domain)
        urls.extend(wayback_urls)

        # Deduplicate
        return list(set(urls))

    async def _fetch_gau(self, domain: str) -> list[str]:
        """Fetch URLs using gau (GetAllUrls).

        Args:
            domain: Domain to query

        Returns:
            List of URLs
        """
        # For now, implement a simple HTTP-based approach
        # In production, this would use the gau CLI tool
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Using wayback machine API as fallback
                response = await client.get(
                    f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
                )
                if response.status_code == 200:
                    import json

                    data = response.json()
                    # Skip header row
                    return [row[0] for row in data[1:] if row[0]]
        except Exception as e:
            logger.warning(f"Failed to fetch gau URLs: {e}")

        return []

    async def _fetch_waybackurls(self, domain: str) -> list[str]:
        """Fetch URLs using waybackurls.

        Args:
            domain: Domain to query

        Returns:
            List of URLs
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
                )
                if response.status_code == 200:
                    import json

                    data = response.json()
                    # Skip header row
                    return [row[0] for row in data[1:] if row[0]]
        except Exception as e:
            logger.warning(f"Failed to fetch wayback URLs: {e}")

        return []

    def _extract_parameters(self, urls_with_params: list[str]) -> list[dict[str, Any]]:
        """Extract parameters from URLs.

        Args:
            urls_with_params: List of URLs with query parameters

        Returns:
            List of parameter info dicts
        """
        parameters = []
        seen = set()

        for url in urls_with_params:
            try:
                # Parse query string
                query_part = url.split("?")[1] if "?" in url else ""
                params = query_part.split("&")

                for param in params:
                    if "=" in param:
                        param_name = param.split("=")[0]
                        key = (url.split("?")[0], param_name)

                        if key not in seen:
                            seen.add(key)
                            parameters.append(
                                {
                                    "url": url.split("?")[0],
                                    "param_name": param_name,
                                    "full_url": url,
                                    "method": "GET",  # Default for historical URLs
                                }
                            )
            except Exception as e:
                logger.debug(f"Failed to parse URL {url}: {e}")

        return parameters

    def _filter_by_pattern(self, urls: list[str], vuln_type: str) -> list[str]:
        """Filter URLs by vulnerability pattern (gf patterns).

        Args:
            urls: List of URLs to filter
            vuln_type: Vulnerability type (xss, sqli, ssrf, redirect, rce, idor)

        Returns:
            List of matching URLs
        """
        # Pattern definitions based on gf patterns
        patterns = {
            "xss": [r"[?&](q|search|query|input|callback|redirect|url|file)=.*"],
            "sqli": [r"[?&](id|user|uid|cat|page|view|search|query|filter)=.*\d+"],
            "ssrf": [r"[?&](url|uri|redirect|next|target|link|file|feed)=.*https?://"],
            "redirect": [r"[?&](redirect|next|url|target|link|return|goto)=.*"],
            "rce": [r"[?&](cmd|exec|command|file|path)=.*"],
            "idor": [r"[?&](id|user_id|uid|account_id|profile_id|order_id)=\d+"],
        }

        matching_urls = []

        for url in urls:
            for pattern in patterns.get(vuln_type, []):
                if re.search(pattern, url, re.IGNORECASE):
                    matching_urls.append(url)
                    break

        return matching_urls

    async def _classify_parameters(
        self, parameters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Classify parameters by vulnerability class using AI.

        Per Master Prompt - GEMMA_JSON for parameter classification.

        Args:
            parameters: List of parameter info dicts

        Returns:
            List of classified parameter dicts
        """
        if not parameters:
            return []

        # Limit to top 50 parameters for AI processing
        sample_params = parameters[:50]

        # Build parameter summary for AI
        param_summary = []
        for param in sample_params:
            param_summary.append(
                {
                    "url": param["url"],
                    "param_name": param["param_name"],
                    "method": param["method"],
                }
            )

        system_prompt = """You are a parameter classification specialist for ReconX-Elite.

Classify each parameter by its vulnerability class based on the parameter name and context.

Vulnerability classes:
- XSS: Parameters that reflect user input without sanitization
- SQLi: Parameters used in database queries
- SSRF: Parameters that accept URLs or external resources
- OpenRedirect: Parameters used for redirects
- IDOR: Parameters that reference database IDs
- PathTraversal: Parameters used in file paths
- Info: Low-risk or informational parameters

Respond in JSON format:
{
    "classifications": [
        {
            "url": "https://example.com/search",
            "param_name": "q",
            "type": "user_input",
            "vuln_class": ["XSS", "SQLi"],
            "priority": "HIGH"
        }
    ]
}
"""

        user_message = f"""Classify the following parameters by vulnerability class:

Parameters:
{self._format_params_for_ai(param_summary)}

Provide your classification in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="parameter_classification",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                classification_data = json.loads(result["content"])
                return classification_data.get("classifications", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse parameter classification response")

        # Fallback: heuristic classification
        return self._heuristic_classification(parameters)

    def _format_params_for_ai(self, parameters: list[dict[str, Any]]) -> str:
        """Format parameters for AI input.

        Args:
            parameters: List of parameter dicts

        Returns:
            Formatted string
        """
        lines = []
        for param in parameters[:50]:  # Limit to 50
            lines.append(f"- {param['method']} {param['url']}?{param['param_name']}=...")
        return "\n".join(lines)

    def _heuristic_classification(
        self, parameters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Fallback heuristic classification without AI.

        Args:
            parameters: List of parameter dicts

        Returns:
            List of classified parameter dicts
        """
        classifications = []

        for param in parameters:
            param_name = param["param_name"].lower()
            vuln_classes = []
            priority = "LOW"

            # Heuristic rules
            if param_name in ["q", "query", "search", "input", "callback", "msg"]:
                vuln_classes.extend(["XSS"])
                priority = "MEDIUM"
            elif param_name in ["id", "user_id", "uid", "account_id", "profile_id"]:
                vuln_classes.extend(["IDOR"])
                priority = "HIGH"
            elif param_name in ["url", "uri", "redirect", "next", "target", "link"]:
                vuln_classes.extend(["SSRF", "OpenRedirect"])
                priority = "HIGH"
            elif param_name in ["file", "path", "document", "page"]:
                vuln_classes.extend(["PathTraversal"])
                priority = "MEDIUM"
            elif param_name in ["cat", "category", "filter", "sort"]:
                vuln_classes.extend(["SQLi"])
                priority = "MEDIUM"

            classifications.append(
                {
                    "url": param["url"],
                    "param_name": param["param_name"],
                    "type": "user_input" if priority != "LOW" else "unknown",
                    "vuln_class": vuln_classes if vuln_classes else ["Info"],
                    "priority": priority,
                }
            )

        return classifications

    async def fuzz_hidden_parameters(
        self, endpoint: str, method: str = "GET"
    ) -> list[dict[str, Any]]:
        """Fuzz for hidden parameters on an endpoint.

        Per Master Prompt - arjun for hidden parameter fuzzing.

        Args:
            endpoint: Target endpoint URL
            method: HTTP method

        Returns:
            List of discovered hidden parameters
        """
        # Common parameter names to test
        common_params = [
            "id",
            "user_id",
            "uid",
            "email",
            "username",
            "password",
            "token",
            "api_key",
            "key",
            "secret",
            "redirect",
            "next",
            "url",
            "file",
            "path",
            "page",
            "limit",
            "offset",
            "sort",
            "order",
            "filter",
            "search",
            "query",
            "q",
            "callback",
            "format",
            "output",
            "debug",
            "test",
            "admin",
            "role",
        ]

        discovered = []

        # For now, return the common params as potential candidates
        # In production, this would use arjun or similar tool
        for param in common_params:
            discovered.append(
                {
                    "endpoint": endpoint,
                    "method": method,
                    "param_name": param,
                    "status": "candidate",
                    "confidence": "low",
                }
            )

        return discovered
