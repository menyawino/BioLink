from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter()
tool_registry = ToolRegistry()

class ToolRequest(BaseModel):
    tool: str
    arguments: Optional[dict] = None

@router.post("/")
async def call_tool(request: ToolRequest):
    """Execute a tool from the consolidated registry."""
    try:
        return tool_registry.call(request.tool, request.arguments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")