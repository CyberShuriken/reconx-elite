"""Celery tasks for manual testing and request replay."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import get_sessionmaker
from app.services.manual_tester import manual_tester

logger = logging.getLogger(__name__)


async def manual_request_task(user_id: int, request_data: dict, vulnerability_id: int = None) -> dict:
    """Execute manual HTTP request task."""
    db = get_sessionmaker()()
    
    try:
        # Send the request
        result = await manual_tester.send_custom_request(**request_data)
        
        # Log the request (would need a testing history model)
        logger.info(f"Manual request completed for user {user_id}: {request_data.get('url')}")
        
        return {
            "user_id": user_id,
            "success": result.get("success", False),
            "method": request_data.get("method"),
            "url": request_data.get("url"),
            "status_code": result.get("status_code"),
            "response_time_ms": result.get("response_time_ms"),
            "vulnerability_id": vulnerability_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Manual request task failed for user {user_id}: {e}")
        return {
            "user_id": user_id,
            "success": False,
            "error": str(e),
            "url": request_data.get("url"),
        }
    
    finally:
        db.close()


async def payload_testing_task(user_id: int, test_request: dict) -> dict:
    """Execute payload testing task."""
    db = get_sessionmaker()()
    
    try:
        base_request = test_request.get("base_request", {})
        payload_type = test_request.get("payload_type")
        target_param = test_request.get("target_param")
        
        # Run payload testing
        results = await manual_tester.test_payload_variations(
            base_request, payload_type, target_param
        )
        
        # Count successful detections
        detections = sum(1 for r in results if r.get("payload_detected", False))
        
        logger.info(f"Payload testing completed for user {user_id}: {payload_type}, {detections}/{len(results)} detections")
        
        return {
            "user_id": user_id,
            "payload_type": payload_type,
            "total_tests": len(results),
            "detections": detections,
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Payload testing task failed for user {user_id}: {e}")
        return {
            "user_id": user_id,
            "success": False,
            "error": str(e),
            "payload_type": test_request.get("payload_type"),
        }
    
    finally:
        db.close()
