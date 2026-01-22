from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_agent import rag_agent_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class RagRequest(BaseModel):
    question: str


@router.post("")
async def rag_ask(request: RagRequest):
    """Hybrid RAG endpoint (SQL filters + pgvector notes)."""
    try:
        if not rag_agent_service:
            raise HTTPException(status_code=500, detail="RAG agent is not configured")

        answer = await rag_agent_service.run(request.question)
        return {"success": True, "data": {"answer": answer}}
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
