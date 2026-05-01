"""Phase 0: Orchestrator Initialization for 10-Phase Pipeline.

Per Master Prompt Section 3 - Phase 0:
- Parse wildcard scope and extract root domain
- Set global scan parameters (rate limits, timeouts, concurrency)
- Initialize scan record with status=RUNNING
- Emit pipeline manifest to Redis
- Routing decision: tool selection based on scope size
- Hard-stop conditions: out-of-scope check, 0 live hosts check
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from app.core.model_registry import get_model_config, get_task_role
from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


@dataclass
class ScanConfig:
    """Scan configuration parameters."""

    target: str
    root_domain: str
    scope_pattern: str
    intensity: str = "normal"  # stealth | normal | aggressive
    rate_limit: int = 5
    timeout: int = 30
    concurrency: int = 10
    excluded_paths: list[str] = field(default_factory=list)


@dataclass
class PipelineManifest:
    """Pipeline manifest stored in Redis."""

    scan_id: str
    target: str
    root_domain: str
    phases: list[str]
    current_phase: str
    findings: list[dict[str, Any]]
    escalations: list[dict[str, Any]]
    status: str
    config: dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "scan_id": self.scan_id,
            "target": self.target,
            "root_domain": self.root_domain,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "findings": self.findings,
            "escalations": self.escalations,
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class OrchestratorService:
    """Phase 0: Orchestrator Initialization Service.

    Handles pipeline initialization, scope parsing, and routing decisions.
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.ai_client = get_openrouter_client(redis_client)
        self.manifest: PipelineManifest | None = None

    async def initialize_scan(
        self,
        target: str,
        intensity: str = "normal",
        excluded_paths: list[str] | None = None,
    ) -> PipelineManifest:
        """Initialize a new scan (Phase 0).

        Args:
            target: Target domain (e.g., "*.example.com")
            intensity: Scan intensity (stealth | normal | aggressive)
            excluded_paths: List of paths to exclude

        Returns:
            PipelineManifest with initial state
        """
        scan_id = str(uuid.uuid4())
        excluded_paths = excluded_paths or []

        # Parse scope and extract root domain
        root_domain, scope_pattern = self._parse_wildcard_scope(target)

        # Validate target is not out of scope
        if not self._validate_scope(root_domain):
            raise ValueError(f"Target {target} is out of scope")

        # Set global scan parameters based on intensity
        config = self._get_scan_config(intensity, excluded_paths)

        # Initialize pipeline manifest
        phases = [
            "phase_0",  # Orchestrator Initialization
            "phase_1",  # Subdomain Enumeration (Recon)
            "phase_2",  # Live Host Validation
            "phase_3",  # Port Scanning
            "phase_4",  # JavaScript Analysis
            "phase_5",  # Parameter Discovery
            "phase_6",  # Vulnerability Testing
            "phase_7",  # AI Deep Analysis
            "phase_8",  # Business Logic Testing
            "phase_9",  # Intelligence Correlation
            "phase_10",  # Report Generation
        ]

        now = datetime.now(timezone.utc).isoformat()

        self.manifest = PipelineManifest(
            scan_id=scan_id,
            target=target,
            root_domain=root_domain,
            phases=phases,
            current_phase="phase_0",
            findings=[],
            escalations=[],
            status="initializing",
            config=config,
            created_at=now,
            updated_at=now,
        )

        # Emit to Redis
        await self._emit_manifest()

        # Make routing decision using AI
        routing_decision = await self._make_routing_decision(root_domain)
        self.manifest.config["routing_decision"] = routing_decision
        self.manifest.updated_at = datetime.now(timezone.utc).isoformat()
        await self._emit_manifest()

        logger.info(f"Scan {scan_id} initialized for {target}")
        return self.manifest

    def _parse_wildcard_scope(self, target: str) -> tuple[str, str]:
        """Parse wildcard scope and extract root domain.

        Args:
            target: Target domain (e.g., "*.example.com" or "example.com")

        Returns:
            Tuple of (root_domain, scope_pattern)
        """
        # Remove wildcard if present
        if target.startswith("*."):
            root_domain = target[2:]
            scope_pattern = target
        else:
            root_domain = target
            scope_pattern = f"*.{target}"

        # Remove protocol if present
        root_domain = root_domain.replace("https://", "").replace("http://", "")
        scope_pattern = scope_pattern.replace("https://", "").replace("http://", "")

        # Remove path if present
        root_domain = root_domain.split("/")[0]
        scope_pattern = scope_pattern.split("/")[0]

        return root_domain, scope_pattern

    def _validate_scope(self, root_domain: str) -> bool:
        """Validate that target is in scope.

        Hard-stop condition: If target is out of scope → ABORT immediately.

        Args:
            root_domain: Root domain to validate

        Returns:
            True if in scope, False otherwise
        """
        # Basic validation: must be a valid domain
        domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$"

        if not re.match(domain_pattern, root_domain):
            logger.error(f"Invalid domain format: {root_domain}")
            return False

        # Check against known out-of-scope domains (could be configurable)
        out_of_scope_domains = [
            "google.com",
            "facebook.com",
            "microsoft.com",
            "apple.com",
            "amazon.com",
        ]

        if root_domain in out_of_scope_domains:
            logger.error(f"Target {root_domain} is in out-of-scope list")
            return False

        return True

    def _get_scan_config(self, intensity: str, excluded_paths: list[str]) -> dict[str, Any]:
        """Get scan configuration based on intensity level.

        Args:
            intensity: Scan intensity (stealth | normal | aggressive)
            excluded_paths: List of paths to exclude

        Returns:
            Configuration dictionary
        """
        intensity_configs = {
            "stealth": {
                "rate_limit": 2,
                "timeout": 60,
                "concurrency": 5,
                "max_requests_per_second": 2,
            },
            "normal": {
                "rate_limit": 5,
                "timeout": 30,
                "concurrency": 10,
                "max_requests_per_second": 5,
            },
            "aggressive": {
                "rate_limit": 50,
                "timeout": 15,
                "concurrency": 50,
                "max_requests_per_second": 50,
            },
        }

        base_config = intensity_configs.get(intensity, intensity_configs["normal"])
        base_config["excluded_paths"] = excluded_paths
        base_config["intensity"] = intensity

        return base_config

    async def _make_routing_decision(self, root_domain: str) -> dict[str, Any]:
        """Make routing decision using AI Orchestrator.

        Decision: which recon tools to run based on scope size
        - < 50 known subdomains → full brute force
        - ≥ 50 → passive + targeted brute

        Args:
            root_domain: Root domain to analyze

        Returns:
            Routing decision dict
        """
        system_prompt = """You are the Master Orchestrator for ReconX-Elite, an AI-driven bug bounty automation platform.

Your task is to make routing decisions for the reconnaissance phase based on target characteristics.

Analyze the target domain and determine:
1. Expected subdomain count (small < 50, medium 50-200, large > 200)
2. Recommended recon strategy (full_brute, passive_targeted, or passive_only)
3. Recommended tool set for subdomain enumeration

Respond in JSON format only:
{
    "expected_subdomain_count": "small|medium|large",
    "recon_strategy": "full_brute|passive_targeted|passive_only",
    "tools": ["subfinder", "sublist3r", "findomain", "massdns", "gobuster"],
    "reasoning": "Brief explanation of the decision"
}
"""

        user_message = f"""Analyze the following domain and provide routing recommendations:

Target Domain: {root_domain}

Consider:
- Domain age (if known)
- Domain popularity
- Typical subdomain structure for this type of domain
- Reconnaissance intensity requirements

Provide your routing decision in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="orchestrate",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                decision = json.loads(result["content"])
                logger.info(f"AI routing decision for {root_domain}: {decision}")
                return decision
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI routing decision, using fallback")

        # Fallback routing decision
        return {
            "expected_subdomain_count": "medium",
            "recon_strategy": "passive_targeted",
            "tools": ["subfinder", "httpx", "nuclei"],
            "reasoning": "AI routing failed, using conservative default",
        }

    async def _emit_manifest(self) -> None:
        """Emit pipeline manifest to Redis."""
        if not self.redis or not self.manifest:
            return

        key = f"scan:{self.manifest.scan_id}:manifest"

        try:
            import json

            await self.redis.set(key, json.dumps(self.manifest.to_dict()))
            # Set expiration to 24 hours
            await self.redis.expire(key, 86400)
        except Exception as e:
            logger.warning(f"Failed to emit manifest to Redis: {e}")

    async def update_phase(self, phase: str, status: str) -> None:
        """Update current phase and status.

        Args:
            phase: Phase name (e.g., "phase_1")
            status: Phase status (running, completed, failed, skipped)
        """
        if not self.manifest:
            return

        self.manifest.current_phase = phase
        self.manifest.status = status
        self.manifest.updated_at = datetime.now(timezone.utc).isoformat()
        await self._emit_manifest()

    async def add_finding(self, finding: dict[str, Any]) -> None:
        """Add a finding to the manifest.

        Args:
            finding: Finding dictionary
        """
        if not self.manifest:
            return

        self.manifest.findings.append(finding)
        self.manifest.updated_at = datetime.now(timezone.utc).isoformat()
        await self._emit_manifest()

    async def add_escalation(self, escalation: dict[str, Any]) -> None:
        """Add an escalation to the manifest.

        Args:
            escalation: Escalation dictionary
        """
        if not self.manifest:
            return

        self.manifest.escalations.append(escalation)
        self.manifest.updated_at = datetime.now(timezone.utc).isoformat()
        await self._emit_manifest()

    async def check_hard_stop_conditions(self, live_hosts_count: int = 0) -> tuple[bool, str]:
        """Check hard-stop conditions.

        Hard-stop conditions:
        - If scan produces 0 live hosts → SKIP to report with null finding

        Args:
            live_hosts_count: Number of live hosts discovered

        Returns:
            Tuple of (should_stop, reason)
        """
        if live_hosts_count == 0:
            return True, "No live hosts discovered, skipping to report"

        return False, ""

    async def get_manifest(self, scan_id: str) -> PipelineManifest | None:
        """Get pipeline manifest from Redis.

        Args:
            scan_id: Scan identifier

        Returns:
            PipelineManifest or None if not found
        """
        if not self.redis:
            return None

        key = f"scan:{scan_id}:manifest"

        try:
            import json

            data = await self.redis.get(key)
            if data:
                manifest_dict = json.loads(data)
                return PipelineManifest(**manifest_dict)
        except Exception as e:
            logger.warning(f"Failed to get manifest from Redis: {e}")

        return None


# Global service instance
_orchestrator_service: OrchestratorService | None = None


def get_orchestrator_service(redis_client: redis.Redis | None = None) -> OrchestratorService:
    """Get or create the global OrchestratorService instance.

    Args:
        redis_client: Optional Redis client

    Returns:
        OrchestratorService instance
    """
    global _orchestrator_service

    if _orchestrator_service is None:
        _orchestrator_service = OrchestratorService(redis_client)

    return _orchestrator_service
