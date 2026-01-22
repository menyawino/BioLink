from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services.openai_service import openai_service
from app.services.sql_agent import sql_agent_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

@router.post("")
async def chat(request: ChatRequest):
    """Chat endpoint using Azure OpenAI"""
    try:
        if not openai_service or not openai_service.client:
            raise HTTPException(status_code=500, detail="Azure OpenAI is not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        
        # Build messages list
        messages = []
        if request.history:
            for msg in request.history:
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": request.message})
        
        # Get completion
        response_text = await openai_service.get_chat_completion(messages)
        
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


@router.post("/sql-agent")
async def sql_agent_chat(request: ChatRequest):
    """Chat endpoint using LangChain SQL agent (Ollama)"""
    try:
        if not sql_agent_service:
            raise HTTPException(status_code=500, detail="SQL agent is not configured")

        history = []
        if request.history:
            for msg in request.history:
                history.append({"role": msg.role, "content": msg.content})

        response_text = await sql_agent_service.run(request.message, history)

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
        logger.error(f"SQL agent chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
