from typing import Optional, List, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

class AgentFrameworkService:
    """Azure AI Foundry Agent service using v2 Agents API"""
    
    def __init__(self):
        self.endpoint = settings.azure_existing_aiproject_endpoint
        self.agent_id = settings.azure_existing_agent_id
        self.api_version = settings.azure_foundry_api_version
        
        if not self.endpoint:
            raise ValueError("AZURE_EXISTING_AIPROJECT_ENDPOINT is not configured")
        
        # Initialize Azure credential and project client
        try:
            credential = DefaultAzureCredential()
            self.project_client = AIProjectClient(
                endpoint=self.endpoint,
                credential=credential
            )
            logger.info(f"AIProjectClient initialized: endpoint={self.endpoint}, agent_id={self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AIProjectClient: {e}")
            raise
    
    async def create_conversation(self, first_message: Optional[str] = None) -> str:
        """Create a new conversation with the agent"""
        try:
            logger.info(f"Creating conversation")
            
            # Create conversation with optional title from first message
            conversation_options = {}
            if first_message:
                title = first_message[:50] + "..." if len(first_message) > 50 else first_message
                conversation_options["metadata"] = {"title": title}
            
            # New SDKs may not expose create_conversation; fall back to local thread id
            create_fn = getattr(self.project_client.agents, "create_conversation", None)
            if callable(create_fn):
                conversation = await create_fn(**conversation_options)
                conversation_id = conversation.id
                logger.info(f"Created conversation: {conversation_id}")
                return conversation_id

            # Fallback: generate in-memory conversation id to keep UI flowing
            conversation_id = str(uuid.uuid4())
            logger.warning("agents.create_conversation unavailable; using local thread id %s", conversation_id)
            return conversation_id
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def stream_message(
        self,
        conversation_id: str,
        message: str,
        image_data_uris: Optional[List[str]] = None,
        file_data_uris: Optional[List[str]] = None
    ):
        """Stream agent response for a message"""
        try:
            logger.info(f"Streaming message to conversation: {conversation_id}")
            
            # Get responses client for this agent and conversation
            responses_fn = getattr(
                self.project_client.agents,
                "get_project_responses_client_for_agent",
                None
            )

            if not callable(responses_fn):
                logger.warning("agents.get_project_responses_client_for_agent unavailable; returning stub response")
                yield "Agent streaming is not available in this environment."
                return

            responses_client = responses_fn(self.agent_id, conversation_id)
            
            # Build request
            request_options = {
                "messages": [{"role": "user", "content": message}]
            }
            
            # Stream responses
            async for response in responses_client.stream_message(**request_options):
                if hasattr(response, "delta") and response.delta:
                    yield response.delta
                elif hasattr(response, "message"):
                    yield response.message
        except Exception as e:
            logger.error(f"Failed to stream message: {e}")
            raise
    
    async def get_agent_metadata(self) -> Dict[str, Any]:
        """Get agent metadata from Azure AI Foundry"""
        try:
            logger.info(f"Getting agent metadata: {self.agent_id}")
            
            agent = await self.project_client.agents.get_agent(self.agent_id)
            
            return {
                "id": agent.id,
                "name": agent.name or "AI Assistant",
                "description": getattr(agent, "description", None),
                "model": getattr(agent, "model", ""),
                "metadata": getattr(agent, "metadata", {})
            }
        except Exception as e:
            logger.error(f"Failed to get agent metadata: {e}")
            raise

# Initialize service (singleton)
try:
    agent_service = AgentFrameworkService()
except Exception as e:
    logger.error(f"AgentFrameworkService initialization deferred: {e}")
    agent_service = None
