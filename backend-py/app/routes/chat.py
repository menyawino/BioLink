from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.services.orchestrator import get_default_orchestrator
from app.core import limiter, RateLimits
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

orchestrator = get_default_orchestrator()

async def _run_chat(request: ChatRequest):
    try:
        from uuid import uuid4
        request_id = str(uuid4())
        history = []
        if request.history:
            for msg in request.history:
                history.append({"role": msg.role, "content": msg.content})

        result = await orchestrator.run(request.message, history, request_id=request_id)
        response_text = result.content

        logger.info(f"Chat response: {response_text[:100]}")

        from datetime import datetime
        return {
            "success": True,
            "data": {
                "content": response_text,
                "role": "assistant",
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id
            }
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@limiter.limit(RateLimits.CHAT)
async def chat(request: Request, chat_request: ChatRequest):
    """Chat endpoint using orchestrated agents."""
    return await _run_chat(chat_request)


@router.post("/sql-agent")
@limiter.limit(RateLimits.CHAT)
async def chat_sql_agent(request: Request, chat_request: ChatRequest):
    """Alias endpoint for chat (backwards compatibility)."""
    return await _run_chat(chat_request)
