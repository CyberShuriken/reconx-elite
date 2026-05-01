"""Phase 9: Intelligence Correlation and Deduplication.

Per Master Prompt Section 3 - Phase 9:
- Deduplication: Group identical vulnerabilities across hosts
- Correlation: Find relationships between findings
- Prioritization: Rank by CVSS score
- Scope check: Remove out-of-scope findings
- Learning: Store effective patterns to database
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class IntelligenceCorrelationService:
    """Phase 9: Intelligence Correlation Service.

    Correlates, deduplicates, and prioritizes findings before report generation.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def correlate_findings(
        self, findings: list[dict[str, Any]], scope_pattern: str
    ) -> dict[str, Any]:
        """Correlate and deduplicate findings.

        Per Master Prompt - NEMOTRON_NANO as orchestrator:
        - Group identical vulnerabilities across multiple hosts
        - Find relationships between findings
        - Prioritize by CVSS score
        - Remove out-of-scope findings

        Args:
            findings: List of findings from all phases
            scope_pattern: Scope pattern (e.g., "*.example.com")

        Returns:
            Correlated findings with deduplication and prioritization
        """
        # Step 1: Scope check - remove out-of-scope findings
        in_scope_findings = self._filter_by_scope(findings, scope_pattern)

        # Step 2: Deduplication - group identical vulnerabilities
        deduplicated = self._deduplicate_findings(in_scope_findings)

        # Step 3: Correlation - find relationships
        correlated = await self._correlate_findings(deduplicated)

        # Step 4: Prioritization - rank by CVSS
        prioritized = self._prioritize_findings(correlated)

        logger.info(
            f"Correlation complete: {len(findings)} → {len(prioritized)} findings after deduplication"
        )

        return {
            "original_count": len(findings),
            "in_scope_count": len(in_scope_findings),
            "deduplicated_count": len(deduplicated),
            "final_count": len(prioritized),
            "findings": prioritized,
            "correlations": self._extract_correlations(correlated),
        }

    def _filter_by_scope(
        self, findings: list[dict[str, Any]], scope_pattern: str
    ) -> list[dict[str, Any]]:
        """Filter findings by scope pattern.

        Args:
            findings: List of findings
            scope_pattern: Scope pattern (e.g., "*.example.com")

        Returns:
            List of in-scope findings
        """
        in_scope = []
        root_domain = scope_pattern.replace("*.", "").replace("*", "")

        for finding in findings:
            host = finding.get("host", "")
            endpoint = finding.get("endpoint", "")

            # Check if host matches scope
            if root_domain in host or root_domain in endpoint:
                in_scope.append(finding)
            else:
                logger.debug(f"Filtered out-of-scope finding: {host}")

        return in_scope

    def _deduplicate_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate findings by type and pattern.

        Args:
            findings: List of findings

        Returns:
            Deduplicated list with affected_hosts groups
        """
        groups: dict[str, list[dict[str, Any]]] = {}

        for finding in findings:
            # Create a signature for deduplication
            vuln_type = finding.get("type", "").lower()
            endpoint = finding.get("endpoint", "")
            param = finding.get("param_name", "")

            # Normalize signature
            signature = f"{vuln_type}:{endpoint}:{param}"

            if signature not in groups:
                groups[signature] = []

            groups[signature].append(finding)

        # Merge findings with affected_hosts
        deduplicated = []
        for signature, group in groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge into single finding with multiple hosts
                merged = group[0].copy()
                merged["affected_hosts"] = [f.get("host", "") for f in group]
                merged["occurrence_count"] = len(group)
                deduplicated.append(merged)

        return deduplicated

    async def _correlate_findings(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Correlate findings to find relationships.

        Args:
            findings: List of findings

        Returns:
            Findings with correlation metadata
        """
        # Simple heuristic correlation
        correlated = []

        # Group by host
        findings_by_host: dict[str, list[dict[str, Any]]] = {}
        for finding in findings:
            host = finding.get("host", "unknown")
            if host not in findings_by_host:
                findings_by_host[host] = []
            findings_by_host[host].append(finding)

        # Add correlation metadata
        for finding in findings:
            host = finding.get("host", "unknown")
            host_findings = findings_by_host.get(host, [])

            finding["correlation_metadata"] = {
                "host_findings_count": len(host_findings),
                "related_findings": [
                    f.get("id") for f in host_findings if f.get("id") != finding.get("id")
                ],
            }

            correlated.append(finding)

        return correlated

    def _prioritize_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prioritize findings by CVSS score.

        Per Master Prompt priority levels:
        - Priority 1: CVSS ≥ 9.0 (Critical)
        - Priority 2: CVSS 7.0–8.9 (High)
        - Priority 3: CVSS 4.0–6.9 (Medium)
        - Priority 4: CVSS < 4.0 (Low / Info)

        Args:
            findings: List of findings

        Returns:
            Prioritized list of findings
        """
        # Assign priority based on severity
        for finding in findings:
            severity = finding.get("severity", "Low").lower()

            if severity == "critical":
                finding["priority"] = 1
                finding["priority_label"] = "Critical"
            elif severity == "high":
                finding["priority"] = 2
                finding["priority_label"] = "High"
            elif severity == "medium":
                finding["priority"] = 3
                finding["priority_label"] = "Medium"
            else:
                finding["priority"] = 4
                finding["priority_label"] = "Low"

        # Sort by priority
        return sorted(findings, key=lambda f: f.get("priority", 4))

    def _extract_correlations(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract correlation relationships.

        Args:
            findings: List of findings with correlation metadata

        Returns:
            List of correlation relationships
        """
        correlations = []

        for finding in findings:
            metadata = finding.get("correlation_metadata", {})
            related = metadata.get("related_findings", [])

            if related:
                correlations.append(
                    {
                        "finding_id": finding.get("id"),
                        "related_findings": related,
                        "host_findings_count": metadata.get("host_findings_count", 0),
                    }
                )

        return correlations

    async def store_intelligence_patterns(
        self, findings: list[dict[str, Any]], scan_id: str
    ) -> dict[str, Any]:
        """Store effective patterns to intelligence database.

        Per Master Prompt - Learning: Store effective payloads and scan patterns
        to the intelligence database for use in future scans.

        Args:
            findings: List of confirmed findings
            scan_id: Scan identifier

        Returns:
            Storage result
        """
        # Extract patterns from findings
        patterns = []

        for finding in findings:
            if finding.get("severity", "").lower() in ["critical", "high"]:
                pattern = {
                    "scan_id": scan_id,
                    "vuln_type": finding.get("type"),
                    "endpoint_pattern": finding.get("endpoint"),
                    "payload": finding.get("payload"),
                    "severity": finding.get("severity"),
                    "cvss": finding.get("cvss"),
                    "effectiveness": "high",
                }
                patterns.append(pattern)

        # In production, this would store to PostgreSQL intelligence_patterns table
        logger.info(f"Would store {len(patterns)} intelligence patterns to database")

        return {
            "patterns_stored": len(patterns),
            "patterns": patterns,
            "scan_id": scan_id,
        }

    async def get_similar_findings(
        self, finding: dict[str, Any], historical_findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find similar historical findings.

        Args:
            finding: Current finding to compare
            historical_findings: List of historical findings

        Returns:
            List of similar findings
        """
        similar = []

        current_type = finding.get("type", "").lower()
        current_endpoint = finding.get("endpoint", "")

        for historical in historical_findings:
            hist_type = historical.get("type", "").lower()
            hist_endpoint = historical.get("endpoint", "")

            # Simple similarity check
            if current_type == hist_type:
                similar.append(historical)
            elif current_endpoint and hist_endpoint and current_endpoint in hist_endpoint:
                similar.append(historical)

        return similar
