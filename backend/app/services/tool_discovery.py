"""Tool Discovery Service for ReconX Elite.

Dynamically detects available security tools and adapts pipeline execution.
Caches results in Redis for quick lookup during scans.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any

import redis.asyncio as redis
from app.core.tool_registry import (
    ToolAvailabilityReport,
    get_all_tools,
    get_install_hint,
    get_required_tools,
    get_tools_for_phase,
    is_tool_required,
)

logger = logging.getLogger(__name__)

# Redis key for caching tool availability
TOOL_AVAILABILITY_KEY = "reconx:tool_availability"
TOOL_AVAILABILITY_TTL = 3600  # 1 hour cache


class ToolDiscoveryService:
    """Service for discovering and tracking tool availability."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self._cache: dict[str, bool] | None = None

    async def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool binary is available in PATH.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is available, False otherwise
        """
        return shutil.which(tool_name) is not None

    async def discover_tools(self, use_cache: bool = True) -> ToolAvailabilityReport:
        """Discover all available tools.

        Checks all tools in the registry and returns availability report.
        Results are cached in Redis for 1 hour.

        Args:
            use_cache: Whether to use cached results if available

        Returns:
            ToolAvailabilityReport with availability status
        """
        # Try to get from cache first
        if use_cache and self.redis:
            cached = await self._get_cached_availability()
            if cached:
                logger.debug("Using cached tool availability")
                return self._build_report_from_cache(cached)

        # Discover all tools concurrently
        tools = get_all_tools()
        tasks = [self._check_tool_available(tool["name"]) for tool in tools]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build availability map
        availability: dict[str, bool] = {}
        for tool, result in zip(tools, results):
            if isinstance(result, Exception):
                logger.warning(f"Error checking {tool['name']}: {result}")
                availability[tool["name"]] = False
            else:
                availability[tool["name"]] = result

        # Cache results
        if self.redis:
            await self._cache_availability(availability)

        self._cache = availability

        return self._build_report_from_cache(availability)

    async def _get_cached_availability(self) -> dict[str, bool] | None:
        """Get cached tool availability from Redis.

        Returns:
            Dict mapping tool name to availability, or None if not cached
        """
        if not self.redis:
            return None

        try:
            data = await self.redis.get(TOOL_AVAILABILITY_KEY)
            if data:
                import json

                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get cached tool availability: {e}")

        return None

    async def _cache_availability(self, availability: dict[str, bool]) -> None:
        """Cache tool availability to Redis.

        Args:
            availability: Dict mapping tool name to availability
        """
        if not self.redis:
            return

        try:
            import json

            await self.redis.setex(
                TOOL_AVAILABILITY_KEY,
                TOOL_AVAILABILITY_TTL,
                json.dumps(availability),
            )
        except Exception as e:
            logger.warning(f"Failed to cache tool availability: {e}")

    def _build_report_from_cache(self, cache: dict[str, bool]) -> ToolAvailabilityReport:
        """Build ToolAvailabilityReport from cache data.

        Args:
            cache: Dict mapping tool name to availability

        Returns:
            ToolAvailabilityReport
        """
        available = [name for name, is_avail in cache.items() if is_avail]
        missing = [name for name, is_avail in cache.items() if not is_avail]

        missing_required = [name for name in missing if is_tool_required(name)]
        missing_optional = [name for name in missing if not is_tool_required(name)]

        return ToolAvailabilityReport(
            available=available,
            missing_required=missing_required,
            missing_optional=missing_optional,
            total=len(cache),
            available_count=len(available),
            missing_count=len(missing),
        )

    async def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if available, False otherwise
        """
        # Check cache first
        if self._cache and tool_name in self._cache:
            return self._cache[tool_name]

        # Check live
        return await self._check_tool_available(tool_name)

    async def get_availability_report(self) -> ToolAvailabilityReport:
        """Get current tool availability report.

        Returns:
            ToolAvailabilityReport
        """
        if self._cache:
            return self._build_report_from_cache(self._cache)

        return await self.discover_tools()

    async def invalidate_cache(self) -> None:
        """Invalidate the tool availability cache."""
        self._cache = None
        if self.redis:
            try:
                await self.redis.delete(TOOL_AVAILABILITY_KEY)
            except Exception as e:
                logger.warning(f"Failed to invalidate tool cache: {e}")

    async def can_execute_phase(self, phase: str) -> tuple[bool, list[str]]:
        """Check if a phase can be executed with available tools.

        Args:
            phase: Phase name (e.g., 'phase_1')

        Returns:
            Tuple of (can_execute, missing_tools_list)
        """
        report = await self.get_availability_report()
        can_execute = report.is_phase_executable(phase)
        missing = report.get_missing_tools_for_phase(phase)

        return can_execute, missing

    def adapt_command_for_tools(self, base_command: list[str], available_tools: list[str]) -> list[str] | None:
        """Adapt a command based on available tools.

        If the primary tool is not available, tries to find alternatives.

        Args:
            base_command: Original command list
            available_tools: List of available tool names

        Returns:
            Modified command or None if no suitable tool available
        """
        if not base_command:
            return None

        primary_tool = base_command[0]

        # If primary tool is available, use as-is
        if primary_tool in available_tools:
            return base_command

        # Tool-specific fallbacks
        fallbacks: dict[str, list[str]] = {
            "subfinder": ["sublist3r", "findomain"],
            "httpx": ["httprobe"],
            "katana": ["hakrawler"],
            "gau": ["waybackurls"],
            "dalfox": ["kxss"],
            "sqlmap": ["ghauri"],
        }

        # Try fallbacks
        for fallback in fallbacks.get(primary_tool, []):
            if fallback in available_tools:
                # Adapt command for fallback tool
                return self._adapt_command_for_fallback(base_command, primary_tool, fallback)

        # No suitable tool found
        return None

    def _adapt_command_for_fallback(self, original: list[str], original_tool: str, fallback_tool: str) -> list[str]:
        """Adapt command arguments for a fallback tool.

        Args:
            original: Original command
            original_tool: Original tool name
            fallback_tool: Fallback tool name

        Returns:
            Modified command for fallback tool
        """
        # Tool-specific argument mappings
        adaptations: dict[tuple[str, str], dict[str, str]] = {
            ("subfinder", "sublist3r"): {"-d": "-d", "-silent": ""},
            ("httpx", "httprobe"): {},  # Different output format, just pass through
            ("katana", "hakrawler"): {"-js-crawl": "-js", "-u": "-url"},
            ("gau", "waybackurls"): {},  # Similar usage
            ("dalfox", "kxss"): {"file": ""},  # kxss expects stdin
        }

        mapping = adaptations.get((original_tool, fallback_tool), {})

        # Build new command
        new_cmd = [fallback_tool]

        i = 1  # Skip original tool name
        while i < len(original):
            arg = original[i]

            # Check if this arg has a mapping
            if arg in mapping:
                if mapping[arg]:  # Only add if not empty
                    new_cmd.append(mapping[arg])
            else:
                new_cmd.append(arg)

            i += 1

        return new_cmd


class PipelineAdapter:
    """Adapts pipeline execution based on tool availability."""

    def __init__(self, tool_discovery: ToolDiscoveryService):
        self.tool_discovery = tool_discovery

    async def get_phase_execution_plan(self, phase: str) -> dict[str, Any]:
        """Get execution plan for a phase based on available tools.

        Args:
            phase: Phase name

        Returns:
            Dict with execution plan details
        """
        can_execute, missing = await self.tool_discovery.can_execute_phase(phase)
        phase_tools = get_tools_for_phase(phase)

        available_in_phase = []
        for tool in phase_tools:
            is_avail = await self.tool_discovery.is_tool_available(tool["name"])
            if is_avail:
                available_in_phase.append(tool["name"])

        return {
            "phase": phase,
            "can_execute": can_execute,
            "required_tools_available": can_execute,
            "available_tools": available_in_phase,
            "missing_tools": missing,
            "fallback_actions": self._generate_fallback_actions(phase, missing),
        }

    def _generate_fallback_actions(self, phase: str, missing_tools: list[str]) -> list[str]:
        """Generate fallback actions for missing tools.

        Args:
            phase: Phase name
            missing_tools: List of missing tool names

        Returns:
            List of fallback action descriptions
        """
        actions = []

        for tool in missing_tools:
            if is_tool_required(tool):
                actions.append(f"CRITICAL: Install {tool} - {get_install_hint(tool)}")
            else:
                actions.append(f"Optional: Install {tool} for enhanced results - {get_install_hint(tool)}")

        # Phase-specific fallbacks
        phase_fallbacks: dict[str, list[str]] = {
            "phase_1": [
                "Using alternative subdomain enumeration methods",
                "Consider manual subdomain list upload",
            ],
            "phase_2": [
                "HTTP probing may be limited",
                "Consider manual host validation",
            ],
            "phase_3": [
                "Port scanning may be limited",
                "Consider manual port scan with nmap",
            ],
            "phase_4": [
                "JS analysis will be basic without specialized tools",
                "Manual JS review recommended",
            ],
            "phase_5": [
                "Parameter discovery may be limited",
                "Consider manual endpoint enumeration",
            ],
            "phase_6": [
                "Vulnerability testing will use nuclei only",
                "Manual testing recommended for comprehensive coverage",
            ],
        }

        if phase in phase_fallbacks and missing_tools:
            actions.extend(phase_fallbacks[phase])

        return actions

    async def validate_pipeline(self, phases: list[str]) -> dict[str, Any]:
        """Validate that a pipeline can be executed.

        Args:
            phases: List of phase names to execute

        Returns:
            Validation result with executable status and recommendations
        """
        results = []
        all_can_execute = True
        critical_missing: list[str] = []

        for phase in phases:
            plan = await self.get_phase_execution_plan(phase)
            results.append(plan)

            if not plan["can_execute"]:
                all_can_execute = False
                critical_missing.extend(plan["missing_tools"])

        return {
            "executable": all_can_execute,
            "phase_plans": results,
            "critical_missing_tools": list(set(critical_missing)),
            "recommendations": (
                [f"Install: {tool}" for tool in set(critical_missing)]
                if critical_missing
                else ["All required tools available"]
            ),
        }


# Global service instance
_tool_discovery_service: ToolDiscoveryService | None = None
_pipeline_adapter: PipelineAdapter | None = None


def get_tool_discovery_service(redis_client: redis.Redis | None = None) -> ToolDiscoveryService:
    """Get or create the global ToolDiscoveryService instance.

    Args:
        redis_client: Optional Redis client for caching

    Returns:
        ToolDiscoveryService instance
    """
    global _tool_discovery_service

    if _tool_discovery_service is None:
        _tool_discovery_service = ToolDiscoveryService(redis_client)

    return _tool_discovery_service


def get_pipeline_adapter(redis_client: redis.Redis | None = None) -> PipelineAdapter:
    """Get or create the global PipelineAdapter instance.

    Args:
        redis_client: Optional Redis client for caching

    Returns:
        PipelineAdapter instance
    """
    global _pipeline_adapter

    if _pipeline_adapter is None:
        discovery = get_tool_discovery_service(redis_client)
        _pipeline_adapter = PipelineAdapter(discovery)

    return _pipeline_adapter
