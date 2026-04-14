import asyncio
import os
import uuid
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from pydantic import BaseModel

from backend.ai_router import AIRouter
from backend.database import Scan, Finding, AgentLog, create_all_tables, get_db, async_session
from backend.orchestrator_7phase import SevenPhaseOrchestrator
from backend.tool_runner import ToolRunner
from backend.websocket_manager import WebSocketManager

load_dotenv()

# Pydantic models for API
class ScanRequest(BaseModel):
    target: str
    session_a_token: str | None = None
    session_b_token: str | None = None


class ScanResponse(BaseModel):
    session_id: str
    target: str
    status: str


app = FastAPI(title='ReconX-Elite - 7-Phase Autonomous Vulnerability Research Pipeline')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

ws_manager = WebSocketManager()
ai_router = AIRouter()
tool_runner = ToolRunner()


@app.on_event('startup')
async def startup_event() -> None:
    await create_all_tables()


@app.post('/api/scan/start')
async def start_scan(request: ScanRequest) -> ScanResponse:
    """Start a 7-phase autonomous vulnerability research scan."""
    session_id = str(uuid.uuid4())
    scan = Scan(
        session_id=session_id,
        target=request.target,
        status='initializing',
        total_subdomains=0,
        total_live_hosts=0,
        total_findings=0,
    )
    async with async_session() as session:
        session.add(scan)
        await session.commit()

    # Prepare session tokens if provided
    session_tokens = {}
    if request.session_a_token:
        session_tokens['session_a'] = request.session_a_token
    if request.session_b_token:
        session_tokens['session_b'] = request.session_b_token

    # Start orchestrator in background
    asyncio.create_task(_orchestrate_7phase(session_id, request.target, session_tokens))
    
    return ScanResponse(session_id=session_id, target=request.target, status='started')


async def _orchestrate_7phase(session_id: str, target: str, session_tokens: dict[str, str]) -> None:
    """Execute 7-phase pipeline."""
    try:
        orchestrator = SevenPhaseOrchestrator(
            session_id=session_id,
            target=target,
            ws_manager=ws_manager,
            ai_router=ai_router,
            tool_runner=tool_runner,
            session_tokens=session_tokens,
        )
        
        result = await orchestrator.execute()
        
        # Update scan record
        async with async_session() as session:
            stmt = select(Scan).where(Scan.session_id == session_id)
            db_scan = await session.execute(stmt)
            scan_record = db_scan.scalar_one()
            scan_record.status = result.get('status', 'complete')
            scan_record.completed_at = datetime.utcnow()
            await session.commit()
    
    except Exception as e:
        await ws_manager.send_log(session_id, 'error', f'Pipeline execution failed: {str(e)}', phase='error')
        async with async_session() as session:
            stmt = select(Scan).where(Scan.session_id == session_id)
            db_scan = await session.execute(stmt)
            scan_record = db_scan.scalar_one()
            scan_record.status = 'failed'
            scan_record.error_message = str(e)
            await session.commit()



@app.get('/api/scan/{session_id}/status')
async def scan_status(session_id: str) -> dict[str, Any]:
    async with async_session() as session:
        result = await session.execute(select(Scan).where(Scan.session_id == session_id))
        scan = result.scalar_one_or_none()
        if not scan:
            raise HTTPException(status_code=404, detail='Scan not found')
        return {
            'session_id': scan.session_id,
            'target': scan.target,
            'status': scan.status,
            'total_findings': scan.total_findings,
        }


@app.get('/api/scan/{session_id}/findings')
async def scan_findings(session_id: str) -> dict[str, Any]:
    async with async_session() as session:
        result = await session.execute(select(Finding).where(Finding.session_id == session_id))
        findings = [dict(
            id=row.id,
            vuln_type=row.vuln_type,
            severity=row.severity,
            endpoint=row.endpoint,
        ) for row in result.scalars().all()]
        return {'session_id': session_id, 'findings': findings}


@app.websocket('/ws/{session_id}')
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    try:
        await ws_manager.connect(websocket, session_id)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'version': '1.0.0', 'mode': 'Tactical Scanning'}
