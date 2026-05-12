"""Centralized OpenRouter Client for ReconX Elite.

Implements the exact call pattern from the Master Prompt Section 2.
All AI calls go through this client with proper retry logic,
rate limiting, and Gemini fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import google.generativeai as genai
import httpx
import redis.asyncio as redis
from app.core.model_registry import (
    GEMINI_CONFIG,
    MODEL_REGISTRY,
    RATE_LIMIT_CONFIG,
    get_model_config,
)

logger = logging.getLogger(__name__)

# OpenRouter API endpoint
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class RateLimiter:
    """Redis-based token bucket rate limiter for AI calls."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.max_calls = RATE_LIMIT_CONFIG["max_calls_per_minute"]
        self.prefix = RATE_LIMIT_CONFIG["token_bucket_key_prefix"]

    async def check_rate_limit(self, scan_id: str) -> bool:
        """Check if scan is within rate limit.

        Args:
            scan_id: The scan identifier

        Returns:
            True if allowed, False if rate limited
        """
        if not self.redis:
            return True

        key = f"{self.prefix}:{scan_id}"
        pipe = self.redis.pipeline()

        # Get current count
        pipe.get(key)
        # Increment with 60s expiry if not exists
        pipe.incr(key)
        pipe.expire(key, 60)

        results = await pipe.execute()
        current_count = int(results[0] or 0)

        return current_count < self.max_calls

    async def get_remaining_calls(self, scan_id: str) -> int:
        """Get remaining calls for scan in current window.

        Args:
            scan_id: The scan identifier

        Returns:
            Number of remaining allowed calls
        """
        if not self.redis:
            return self.max_calls

        key = f"{self.prefix}:{scan_id}"
        current = await self.redis.get(key)
        current_count = int(current or 0)

        return max(0, self.max_calls - current_count)


class OpenRouterClient:
    """Centralized client for OpenRouter AI calls with fallback to Gemini."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.rate_limiter = RateLimiter(redis_client)
        self.timeout = RATE_LIMIT_CONFIG["timeout_seconds"]
        self.max_retries = RATE_LIMIT_CONFIG["max_retries"]
        self.backoff_base = RATE_LIMIT_CONFIG["backoff_base"]

        # Initialize Gemini as global fallback
        gemini_key = os.environ.get(GEMINI_CONFIG["env_var"])
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(GEMINI_CONFIG["model_id"])
        else:
            self.gemini_model = None

    async def call_openrouter(
        self,
        model_env_var: str,
        model_id: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        response_format: str = "text",  # "text" or "json_object"
        scan_id: str | None = None,
    ) -> dict[str, Any]:
        """Call OpenRouter API with the exact pattern from Master Prompt.

        Args:
            model_env_var: Environment variable name for the API key
            model_id: OpenRouter model ID (e.g., "nvidia/llama-3.1-nemotron-nano-8b-instruct:free")
            system_prompt: System prompt content
            user_message: User message content
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            response_format: "text" or "json_object"
            scan_id: Optional scan ID for rate limiting

        Returns:
            Dict with 'success', 'content', 'model', 'error' keys
        """
        # Check rate limit if scan_id provided
        if scan_id and not await self.rate_limiter.check_rate_limit(scan_id):
            remaining = await self.rate_limiter.get_remaining_calls(scan_id)
            logger.warning(f"Rate limit exceeded for scan {scan_id}. Remaining: {remaining}")
            return {
                "success": False,
                "content": "",
                "model": model_id,
                "error": "rate_limit_exceeded",
                "remaining_calls": remaining,
            }

        # Get API key from environment
        api_key = os.environ.get(model_env_var)
        if not api_key:
            logger.error(f"API key not found in environment: {model_env_var}")
            return {
                "success": False,
                "content": "",
                "model": model_id,
                "error": f"missing_api_key: {model_env_var}",
            }

        # Build payload per Master Prompt Section 2
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        # Headers per Master Prompt
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/CyberShuriken/reconx-elite",
            "X-Title": "ReconX Elite",
        }

        # Execute with retry logic
        last_error: str | None = None
        delay = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        OPENROUTER_BASE_URL,
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    result = resp.json()

                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                return {
                    "success": True,
                    "content": content,
                    "model": model_id,
                    "error": None,
                }

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                logger.warning(f"OpenRouter call failed (attempt {attempt}/{self.max_retries}): {last_error}")

                # Don't retry on certain status codes
                if e.response.status_code in (400, 401, 403):
                    break

            except Exception as e:
                last_error = str(e)
                logger.warning(f"OpenRouter call failed (attempt {attempt}/{self.max_retries}): {e}")

            # Exponential backoff before retry
            if attempt < self.max_retries:
                await asyncio.sleep(delay)
                delay *= self.backoff_base

        # All retries exhausted
        return {
            "success": False,
            "content": "",
            "model": model_id,
            "error": f"max_retries_exceeded: {last_error}",
        }

    async def call_gemini_fallback(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Call Gemini as global fallback when OpenRouter fails.

        Args:
            prompt: The full prompt to send
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with 'success', 'content', 'model', 'error' keys
        """
        if not self.gemini_model:
            return {
                "success": False,
                "content": "",
                "model": GEMINI_CONFIG["model_id"],
                "error": "gemini_not_configured",
            }

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            return {
                "success": True,
                "content": response.text,
                "model": GEMINI_CONFIG["model_id"],
                "error": None,
            }

        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")
            return {
                "success": False,
                "content": "",
                "model": GEMINI_CONFIG["model_id"],
                "error": f"gemini_error: {str(e)}",
            }

    async def call_model_by_role(
        self,
        role: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format: str = "text",
        scan_id: str | None = None,
        use_fallback: bool = True,
    ) -> dict[str, Any]:
        """Call AI model by its assigned role from the registry.

        This is the primary method for making AI calls. It looks up the role
        in the MODEL_REGISTRY, gets the correct env var and model ID,
        calls OpenRouter, and falls back to Gemini if needed.

        Args:
            role: Model role from MODEL_REGISTRY (e.g., 'orchestrator')
            system_prompt: System prompt content
            user_message: User message content
            max_tokens: Override max tokens (uses registry default if None)
            temperature: Override temperature (uses registry default if None)
            response_format: "text" or "json_object"
            scan_id: Optional scan ID for rate limiting
            use_fallback: Whether to try Gemini if OpenRouter fails

        Returns:
            Dict with 'success', 'content', 'model', 'role', 'error' keys
        """
        config = get_model_config(role)
        if not config:
            return {
                "success": False,
                "content": "",
                "model": "unknown",
                "role": role,
                "error": f"unknown_role: {role}",
            }

        # Use registry defaults if not overridden
        max_tokens = max_tokens or config["max_tokens"]
        temperature = temperature or config["temperature"]

        # Call OpenRouter
        result = await self.call_openrouter(
            model_env_var=config["env_var"],
            model_id=config["model_id"],
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format,
            scan_id=scan_id,
        )

        # Add role to result
        result["role"] = role

        # Try Gemini fallback if OpenRouter failed and fallback enabled
        if not result["success"] and use_fallback:
            logger.info(f"Attempting Gemini fallback for role {role}")

            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_message}"

            fallback_result = await self.call_gemini_fallback(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Add role info to fallback result
            fallback_result["role"] = role
            fallback_result["fallback_used"] = True
            fallback_result["original_error"] = result["error"]

            return fallback_result

        return result

    async def call_model_by_task(
        self,
        task: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format: str = "text",
        scan_id: str | None = None,
        use_fallback: bool = True,
    ) -> dict[str, Any]:
        """Call AI model by task type, looking up the appropriate role.

        Args:
            task: Task type from TASK_ROLE_MAP (e.g., 'subdomain_classification')
            system_prompt: System prompt content
            user_message: User message content
            max_tokens: Override max tokens
            temperature: Override temperature
            response_format: "text" or "json_object"
            scan_id: Optional scan ID for rate limiting
            use_fallback: Whether to try Gemini if OpenRouter fails

        Returns:
            Dict with 'success', 'content', 'model', 'role', 'task', 'error' keys
        """
        from app.core.model_registry import get_task_role

        role = get_task_role(task)

        result = await self.call_model_by_role(
            role=role,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format,
            scan_id=scan_id,
            use_fallback=use_fallback,
        )

        # Add task info
        result["task"] = task

        return result


# Global client instance
_openrouter_client: OpenRouterClient | None = None


def get_openrouter_client(redis_client: redis.Redis | None = None) -> OpenRouterClient:
    """Get or create the global OpenRouter client instance.

    Args:
        redis_client: Optional Redis client for rate limiting

    Returns:
        OpenRouterClient instance
    """
    global _openrouter_client

    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient(redis_client)

    return _openrouter_client


async def call_openrouter(
    model_env_var: str,
    model_id: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    response_format: str = "text",
    scan_id: str | None = None,
) -> str:
    """Convenience function matching the exact Master Prompt signature.

    This is the standalone function as specified in Master Prompt Section 2.

    Args:
        model_env_var: Environment variable name for API key
        model_id: OpenRouter model ID
        system_prompt: System prompt content
        user_message: User message content
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        response_format: "text" or "json_object"
        scan_id: Optional scan ID for rate limiting

    Returns:
        The response content string (empty string on error)
    """
    client = get_openrouter_client()

    result = await client.call_openrouter(
        model_env_var=model_env_var,
        model_id=model_id,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
        scan_id=scan_id,
    )

    if result["success"]:
        return result["content"]

    # Try Gemini fallback
    full_prompt = f"{system_prompt}\n\n{user_message}"
    fallback = await client.call_gemini_fallback(
        prompt=full_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return fallback["content"] if fallback["success"] else ""
