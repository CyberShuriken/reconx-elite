"""Model Registry for ReconX Elite 10-Phase Pipeline.

Maps AI model roles to environment variables and OpenRouter model IDs.
Based on the Master Prompt specification.
"""

from typing import TypedDict


class ModelConfig(TypedDict):
    """Configuration for a model role."""

    env_var: str
    model_id: str
    role_description: str
    max_tokens: int
    temperature: float


# Model Registry - Maps role to (env_var, model_id, description)
# Per Master Prompt Section 2 - Model Roster and Role Assignments
MODEL_REGISTRY: dict[str, ModelConfig] = {
    "orchestrator": {
        "env_var": "OR_KEY_NEMOTRON_NANO",
        "model_id": "nvidia/llama-3.1-nemotron-nano-8b-instruct:free",
        "role_description": "Pipeline routing, phase transitions, hard-stop logic",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "primary_analyst": {
        "env_var": "OPENROUTER_KEY",
        "model_id": "meta-llama/llama-3.3-70b-instruct:free",
        "role_description": "IDOR test gen, severity rating, finding triage",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "deep_reasoner": {
        "env_var": "OR_KEY_NEMOTRON_SUPER",
        "model_id": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "role_description": "JWT attack chains, SSRF escalation, exploit chaining",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "code_engine": {
        "env_var": "OR_KEY_QWEN_CODER",
        "model_id": "qwen/qwen3-coder-480b-a35b-instruct:free",
        "role_description": "Payload generation, PoC scripts, JS deobfuscation",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "fast_classifier": {
        "env_var": "OR_KEY_GLM_45",
        "model_id": "thudm/glm-4-9b-chat:free",
        "role_description": "Subdomain/host classification, scope filtering",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "json_extractor": {
        "env_var": "OPENROUTER_API_KEY_SECONDARY",
        "model_id": "google/gemma-3-27b-it:free",
        "role_description": "Structured output from raw tool stdout",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "header_analyst": {
        "env_var": "OPENROUTER_API_KEY_TERTIARY",
        "model_id": "google/gemma-3-12b-it:free",
        "role_description": "CORS, CSP, security header misconfiguration",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "js_analyst": {
        "env_var": "OR_KEY_MINIMAX",
        "model_id": "minimax/minimax-m1:extended",
        "role_description": "Large JS files, full file analysis (large context)",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
    "critical_reporter": {
        "env_var": "OR_KEY_GPT_OSS_120B",
        "model_id": "microsoft/phi-4-reasoning-plus:free",
        "role_description": "High/Critical severity reports, exec summaries",
        "max_tokens": 3000,
        "temperature": 0.3,
    },
    "standard_reporter": {
        "env_var": "OR_KEY_GPT_OSS_20B",
        "model_id": "microsoft/phi-4-mini-reasoning:free",
        "role_description": "Low/Medium severity report drafting",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
    "deep_reasoner_fallback": {
        "env_var": "OR_KEY_NEMOTRON_SUPER_ALT",
        "model_id": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "role_description": "FALLBACK for NEMOTRON_SUPER when rate limited",
        "max_tokens": 2000,
        "temperature": 0.3,
    },
}

# Task-to-Role mapping for the 10-phase pipeline
# Maps specific tasks to their designated model roles
TASK_ROLE_MAP: dict[str, str] = {
    # Phase 0: Orchestrator
    "orchestrate": "orchestrator",
    "route": "orchestrator",
    "pipeline_control": "orchestrator",
    # Phase 1: Recon - Subdomain Classification
    "subdomain_classification": "fast_classifier",
    "scope_filtering": "fast_classifier",
    "host_triage": "fast_classifier",
    # Phase 2: Validation - HTTP Profiling
    "httpx_parsing": "json_extractor",
    "host_metadata": "json_extractor",
    # Phase 3: Port Scan - Service Analysis
    "service_interpretation": "primary_analyst",
    "port_analysis": "primary_analyst",
    "exposure_assessment": "primary_analyst",
    # Phase 4: JS Analysis
    "js_analysis": "js_analyst",
    "js_secrets": "js_analyst",
    "payload_generation": "code_engine",
    # Phase 5: Parameter Discovery
    "parameter_classification": "json_extractor",
    "url_parsing": "json_extractor",
    # Phase 6: Vulnerability Testing
    "vuln_triage": "primary_analyst",
    "severity_rating": "primary_analyst",
    "finding_validation": "primary_analyst",
    # Phase 7: Deep Analysis
    "exploit_chain": "deep_reasoner",
    "attack_chaining": "deep_reasoner",
    "cvss_analysis": "deep_reasoner",
    "poc_generation": "code_engine",
    # Phase 8: Business Logic
    "business_logic": "primary_analyst",
    "workflow_test": "primary_analyst",
    # Phase 9: Intelligence
    "correlation": "orchestrator",
    "deduplication": "orchestrator",
    # Phase 10: Report Generation
    "critical_report": "critical_reporter",
    "high_report": "critical_reporter",
    "medium_report": "standard_reporter",
    "low_report": "standard_reporter",
    "executive_summary": "critical_reporter",
}

# Gemini fallback configuration
GEMINI_CONFIG = {
    "env_var": "GEMINI_API_KEY",
    "model_id": "gemini-1.5-pro",
    "role_description": "Global fallback when all OpenRouter calls fail",
    "max_tokens": 2000,
    "temperature": 0.3,
}


def get_model_config(role: str) -> ModelConfig | None:
    """Get configuration for a model role.

    Args:
        role: The model role (e.g., 'orchestrator', 'primary_analyst')

    Returns:
        ModelConfig dict or None if role not found
    """
    return MODEL_REGISTRY.get(role)


def get_task_role(task: str) -> str:
    """Get the model role assigned to a specific task.

    Args:
        task: The task type (e.g., 'subdomain_classification', 'vuln_triage')

    Returns:
        The model role assigned to this task, defaults to 'primary_analyst'
    """
    return TASK_ROLE_MAP.get(task, "primary_analyst")


def list_all_roles() -> list[str]:
    """List all available model roles."""
    return list(MODEL_REGISTRY.keys())


def list_all_tasks() -> list[str]:
    """List all task types."""
    return list(TASK_ROLE_MAP.keys())


# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "max_calls_per_minute": 10,
    "token_bucket_key_prefix": "ai_rate_limit",
    "timeout_seconds": 60,
    "max_retries": 3,
    "backoff_base": 2.0,
}
