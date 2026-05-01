"""Phase 8: Business Logic and Manual Testing Guidance.

Per Master Prompt Section 3 - Phase 8:
- Workflow bypass tests
- Race condition tests
- IDOR test patterns
- AI-generated manual testing checklist
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class BusinessLogicService:
    """Phase 8: Business Logic Testing Service.

    Generates manual testing guidance and checklists based on
    discovered application functionality.
    """

    def __init__(self):
        self.ai_client = get_openrouter_client()

    async def generate_manual_testing_checklist(
        self, endpoints: list[str], tech_stack: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate structured manual testing checklist.

        Per Master Prompt - PRIMARY_ANALYST for business logic:
        - Workflow bypass tests
        - Race condition tests
        - IDOR test patterns
        - JWT manipulation tests

        Args:
            endpoints: List of discovered API endpoints
            tech_stack: Optional tech stack information

        Returns:
            Testing checklist with test cases
        """
        if not endpoints:
            return {"workflow_tests": [], "race_condition_tests": [], "idor_tests": [], "jwt_tests": []}

        # Prepare endpoint summary for AI
        endpoint_summary = self._format_endpoints_for_ai(endpoints)

        system_prompt = """You are a business logic testing specialist for ReconX-Elite.

Generate a structured manual testing checklist based on the discovered endpoints.

Provide:

WORKFLOW BYPASS TESTS:
- What if I call /api/checkout before /api/add-to-cart?
- What if I submit negative quantity values?
- What if I replay a single-use token?
- What if I change role:user to role:admin in the JWT payload?

RACE CONDITION TESTS:
- Identify endpoints that modify balances or apply coupons
- Generate Turbo Intruder script suggestions for parallel request testing

IDOR TESTS:
- Generate sequential ID test patterns
- Generate UUID prediction tests
- Test horizontal privilege escalation between accounts

For each test, provide:
- test_name
- endpoint
- payload
- expected_behavior
- vulnerable_behavior
- severity
- cvss

Respond in JSON format:
{
    "workflow_tests": [
        {
            "test_name": "Cart negative quantity",
            "endpoint": "POST /api/cart/update",
            "payload": {"item_id": 123, "quantity": -999},
            "expected_behavior": "Server rejects negative values",
            "vulnerable_behavior": "Total price becomes negative or zero",
            "severity": "HIGH",
            "cvss": "7.5"
        }
    ],
    "race_condition_tests": [...],
    "idor_tests": [...],
    "jwt_tests": [...]
}
"""

        user_message = f"""Generate a manual testing checklist for these endpoints:

Endpoints:
{endpoint_summary}

Tech Stack:
{self._format_tech_stack(tech_stack)}

Provide your testing checklist in JSON format.
"""

        result = await self.ai_client.call_model_by_task(
            task="business_logic",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json_object",
        )

        if result["success"]:
            try:
                import json

                checklist_data = json.loads(result["content"])
                logger.info(
                    f"Manual testing checklist generated: {len(checklist_data.get('workflow_tests', []))} workflow tests"
                )
                return checklist_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse manual testing checklist response")

        # Fallback: heuristic checklist
        return self._generate_heuristic_checklist(endpoints)

    def _format_endpoints_for_ai(self, endpoints: list[str]) -> str:
        """Format endpoints for AI input.

        Args:
            endpoints: List of endpoint strings

        Returns:
            Formatted string
        """
        lines = []
        for ep in endpoints[:50]:  # Limit to 50
            lines.append(f"- {ep}")
        return "\n".join(lines)

    def _format_tech_stack(self, tech_stack: dict[str, Any] | None) -> str:
        """Format tech stack for AI input.

        Args:
            tech_stack: Tech stack dict

        Returns:
            Formatted string
        """
        if not tech_stack:
            return "Not detected"

        lines = []
        for key, value in tech_stack.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _generate_heuristic_checklist(self, endpoints: list[str]) -> dict[str, Any]:
        """Generate heuristic checklist without AI.

        Args:
            endpoints: List of endpoint strings

        Returns:
            Checklist dict
        """
        workflow_tests = []
        race_condition_tests = []
        idor_tests = []
        jwt_tests = []

        # Identify endpoints by pattern
        cart_endpoints = [ep for ep in endpoints if "cart" in ep.lower()]
        checkout_endpoints = [ep for ep in endpoints if "checkout" in ep.lower()]
        user_endpoints = [ep for ep in endpoints if "user" in ep.lower() or "account" in ep.lower()]
        payment_endpoints = [ep for ep in endpoints if "payment" in ep.lower() or "pay" in ep.lower()]

        # Workflow bypass tests
        if cart_endpoints:
            workflow_tests.append(
                {
                    "test_name": "Negative quantity in cart",
                    "endpoint": f"POST {cart_endpoints[0]}",
                    "payload": {"item_id": 1, "quantity": -1},
                    "expected_behavior": "Server rejects negative quantity",
                    "vulnerable_behavior": "Cart accepts negative quantity, reducing total price",
                    "severity": "HIGH",
                    "cvss": "7.5",
                }
            )

        if checkout_endpoints:
            workflow_tests.append(
                {
                    "test_name": "Skip add-to-cart",
                    "endpoint": f"POST {checkout_endpoints[0]}",
                    "payload": {"items": [{"id": 123, "quantity": 1}]},
                    "expected_behavior": "Requires items to be in cart first",
                    "vulnerable_behavior": "Direct checkout bypasses cart validation",
                    "severity": "MEDIUM",
                    "cvss": "5.3",
                }
            )

        # Race condition tests
        if payment_endpoints:
            race_condition_tests.append(
                {
                    "test_name": "Coupon double-spend",
                    "endpoint": f"POST {payment_endpoints[0]}",
                    "payload": {"coupon": "SAVE10"},
                    "expected_behavior": "Coupon can only be used once",
                    "vulnerable_behavior": "Coupon applied multiple times in parallel requests",
                    "severity": "HIGH",
                    "cvss": "6.5",
                    "tool_suggestion": "Turbo Intruder with 50 parallel requests",
                }
            )

        # IDOR tests
        if user_endpoints:
            for ep in user_endpoints[:3]:
                idor_tests.append(
                    {
                        "test_name": f"Sequential ID enumeration on {ep}",
                        "endpoint": ep,
                        "payload": {"id": 1},
                        "expected_behavior": "403 or only returns own data",
                        "vulnerable_behavior": "Returns data for different user ID",
                        "severity": "CRITICAL",
                        "cvss": "9.1",
                        "test_pattern": "Try IDs 1-100 sequentially",
                    }
                )

        # JWT tests
        jwt_tests.append(
            {
                "test_name": "JWT role manipulation",
                "endpoint": "Any authenticated endpoint",
                "payload": {"role": "admin"},
                "expected_behavior": "Role claim ignored or validated",
                "vulnerable_behavior": "Role change grants admin privileges",
                "severity": "CRITICAL",
                "cvss": "9.8",
                "test_steps": [
                    "Decode JWT token",
                    "Change role claim from 'user' to 'admin'",
                    "Re-sign if possible (none algorithm, weak secret)",
                    "Use modified token",
                ],
            }
        )

        return {
            "workflow_tests": workflow_tests,
            "race_condition_tests": race_condition_tests,
            "idor_tests": idor_tests,
            "jwt_tests": jwt_tests,
        }

    async def generate_turbo_intruder_script(self, endpoint: str, payload: dict[str, Any]) -> str:
        """Generate Turbo Intruder script for race condition testing.

        Args:
            endpoint: Target endpoint
            payload: Payload to send

        Returns:
            Turbo Intruder Python script
        """
        script = f"""def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target,
                           concurrentConnections=5,
                           requestsPerConnection=100,
                           pipeline=False
                           )

    # Race condition test for {endpoint}
    for i in range(50):
        engine.queue(target, [{payload}])

def handleResponse(req, interesting):
    if interesting:
        table.add(req)
"""

        return script
