from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services.langgraph_agent import SQLAgentService
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

# Initialize LangGraph agent
sql_agent_service = SQLAgentService(
    db_url=settings.database_url,
    ollama_base_url=settings.ollama_base_url,
    model=settings.ollama_model
)

# Validate database connection
if not sql_agent_service.validate_database():
    logger.warning("Database validation failed - agent may not work properly")
else:
    logger.info("Database validation successful")

async def _run_chat(request: ChatRequest):
    try:
        history = []
        if request.history:
            for msg in request.history:
                history.append({"role": msg.role, "content": msg.content})

        response_text = await sql_agent_service.run(request.message, history)

        logger.info(f"Chat response: {response_text[:100]}")

        from datetime import datetime
        return {
            "success": True,
            "data": {
                "content": response_text,
                "role": "assistant",
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def chat(request: ChatRequest):
    """Chat endpoint using LangGraph SQL agent"""
    return await _run_chat(request)


@router.post("/sql-agent")
async def chat_sql_agent(request: ChatRequest):
    """Alias endpoint for SQL agent chat (backwards compatibility)"""
    return await _run_chat(request)
