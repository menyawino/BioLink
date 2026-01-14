from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.services.agent_framework import agent_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory thread storage (in production use database)
conversation_threads: Dict[str, Dict[str, Any]] = {}

class ThreadRequest(BaseModel):
    agent_id: Optional[str] = None

class RunRequest(BaseModel):
    agent_id: Optional[str] = None
    thread_id: str
    user_message: str
    stream: Optional[bool] = False

@router.post("/thread")
async def create_thread(request: ThreadRequest):
    """Initialize a new conversation thread with the Foundry agent"""
    try:
        if not agent_service:
            raise HTTPException(status_code=500, detail="Azure Foundry endpoint not configured")
        
        # Create conversation using agent service
        conversation_id = await agent_service.create_conversation()
        
        # Store in memory
        conversation_threads[conversation_id] = {
            "thread_id": conversation_id,
            "messages": []
        }
        
        logger.info(f"Created thread: {conversation_id} for agent: {request.agent_id or 'blnk:8'}")
        
        return {
            "success": True,
            "data": {
                "thread_id": conversation_id,
                "agent_id": request.agent_id or "blnk:8",
                "status": "initialized"
            }
        }
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def run_agent(request: RunRequest):
    """Run an agent with a message"""
    try:
        if not agent_service:
            raise HTTPException(status_code=500, detail="Azure Foundry endpoint not configured")
        
        if not request.user_message:
            raise HTTPException(status_code=400, detail="User message is required")
        
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Thread ID is required")
        
        # Get or initialize thread
        thread = conversation_threads.get(request.thread_id)
        if not thread:
            thread = {
                "thread_id": request.thread_id,
                "messages": []
            }
            conversation_threads[request.thread_id] = thread
        
        # Add user message
        thread["messages"].append({
            "role": "user",
            "content": request.user_message,
            "timestamp": str(__import__('datetime').datetime.now())
        })
        
        logger.info(f"Running agent on thread {request.thread_id} with message: {request.user_message[:50]}")
        
        # Stream message from agent
        response_text = ""
        async for chunk in agent_service.stream_message(request.thread_id, request.user_message):
            response_text += str(chunk)
        
        # Add assistant response
        thread["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": str(__import__('datetime').datetime.now())
        })
        
        return {
            "success": True,
            "data": {
                "id": f"run_{__import__('time').time()}",
                "thread_id": request.thread_id,
                "agent_id": request.agent_id or "blnk:8",
                "text": response_text,
                "status": "completed"
            }
        }
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(thread_id: str):
    """Get conversation history"""
    try:
        thread = conversation_threads.get(thread_id)
        if not thread:
            return {"success": True, "data": {"messages": []}}
        
        return {
            "success": True,
            "data": {
                "thread_id": thread_id,
                "messages": thread["messages"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for Foundry integration"""
    try:
        is_configured = bool(agent_service)
        
        return {
            "success": True,
            "data": {
                "status": "ok",
                "foundry_configured": is_configured,
                "agent_id": agent_service.agent_id if agent_service else None,
                "endpoint": "✓ configured" if agent_service else "✗ missing"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
