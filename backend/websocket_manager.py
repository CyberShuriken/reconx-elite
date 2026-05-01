import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.connections.setdefault(session_id, []).append(websocket)
        logger.info("WebSocket connected for session %s", session_id)

    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        if session_id not in self.connections:
            return
        try:
            self.connections[session_id].remove(websocket)
        except ValueError:
            pass
        if not self.connections[session_id]:
            del self.connections[session_id]
        logger.info("WebSocket disconnected for session %s", session_id)

    async def _safe_send(self, websocket: WebSocket, message: str) -> None:
        try:
            await websocket.send_text(message)
        except (WebSocketDisconnect, RuntimeError, ConnectionResetError):
            logger.debug("WebSocket client disconnected during send")

    async def broadcast(self, session_id: str, message_type: str, data: Any) -> None:
        message = json.dumps(
            {
                "type": message_type,
                "data": data,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        if session_id not in self.connections:
            return
        for websocket in list(self.connections.get(session_id, [])):
            await self._safe_send(websocket, message)

    async def send_log(
        self,
        session_id: str,
        level: str,
        message: str,
        model_role: str | None = None,
        phase: str | None = None,
    ) -> None:
        await self.broadcast(
            session_id,
            "log",
            {
                "level": level,
                "message": message,
                "model_role": model_role,
                "phase": phase,
            },
        )

    async def send_finding(self, session_id: str, finding_dict: dict) -> None:
        """Send finding update to connected clients."""
        await self.broadcast(session_id, "finding", finding_dict)

    async def send_model_activity(
        self, session_id: str, model: str, action: str, scan_id: str | None = None, tokens_used: int = 0
    ) -> None:
        """Send AI model activity update.

        Args:
            session_id: The session identifier
            model: Model role (e.g., 'orchestrator', 'primary_analyst')
            action: Action being performed (e.g., 'exploit_chain', 'poc_generation')
            scan_id: Optional scan ID
            tokens_used: Tokens consumed in the call
        """
        await self.broadcast(
            session_id,
            "model_activity",
            {
                "model_role": model,
                "action": action,
                "scan_id": scan_id,
                "tokens_used": tokens_used,
            },
        )

    async def send_tool_log(
        self, session_id: str, tool: str, hosts: int = 0, status: str = "running", output: str = ""
    ) -> None:
        """Send tool execution log.

        Args:
            session_id: The session identifier
            tool: Tool name (e.g., 'nuclei', 'subfinder')
            hosts: Number of hosts processed
            status: Tool status (running, completed, error)
            output: Tool output (truncated)
        """
        await self.broadcast(
            session_id,
            "tool_log",
            {
                "event": "tool_log",
                "tool": tool,
                "hosts": hosts,
                "status": status,
                "output": output[:500],  # Truncate for WebSocket
            },
        )

    async def send_phase_update(self, session_id: str, phase: str, status: str) -> None:
        await self.broadcast(session_id, "phase_update", {"phase": phase, "status": status})

    async def send_phase_update_detailed(
        self, session_id: str, phase: int, status: str, progress: int, message: str = "", model: str | None = None
    ) -> None:
        """Send detailed phase update for 10-phase pipeline.

        Args:
            session_id: The session/scan identifier
            phase: Phase number (0-10)
            status: Phase status (running, completed, error)
            progress: Progress percentage (0-100)
            message: Optional status message
            model: AI model role used in this phase
        """
        await self.broadcast(
            session_id,
            "phase_update",
            {
                "phase": phase,
                "phase_name": self._get_phase_name(phase),
                "status": status,
                "progress": progress,
                "message": message,
                "model": model,
            },
        )

    def _get_phase_name(self, phase: int) -> str:
        """Get phase name from phase number."""
        phase_names = {
            0: "orchestrator_init",
            1: "recursive_recon",
            2: "context_profiling",
            3: "port_scanning",
            4: "javascript_analysis",
            5: "parameter_discovery",
            6: "vulnerability_testing",
            7: "ai_deep_analysis",
            8: "business_logic",
            9: "intelligence_correlation",
            10: "report_generation",
        }
        return phase_names.get(phase, f"phase_{phase}")

    async def send_stats(self, session_id: str, stats_dict: dict) -> None:
        await self.broadcast(session_id, "stats_update", stats_dict)

    async def send_complete(self, session_id: str, summary_dict: dict) -> None:
        await self.broadcast(session_id, "scan_complete", summary_dict)
