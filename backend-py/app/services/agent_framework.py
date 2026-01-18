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
        """Stream agent response for a message - simulated streaming for now"""
        try:
            logger.info(f"Streaming message to conversation: {conversation_id}")
            
            # For now, we'll simulate streaming by getting the full response and chunking it
            # In a future SDK version, this will use real streaming
            
            # Get the full response first
            full_response = await self._get_full_response(message)
            
            # Simulate streaming by yielding chunks with small delays
            # Chunk by characters but preserve newlines
            chars = list(full_response)
            current_chunk = ""
            
            for char in chars:
                current_chunk += char
                if len(current_chunk) >= 50 and (char == ' ' or char == '\n' or char == '.'):
                    yield current_chunk
                    current_chunk = ""
                    # Small delay to simulate streaming
                    import asyncio
                    await asyncio.sleep(0.03)
            
            # Send remaining chunk
            if current_chunk:
                yield current_chunk
            if current_chunk:
                yield current_chunk.strip()
                
        except Exception as e:
            logger.error(f"Failed to stream message: {e}")
            yield f"Error: {str(e)}"
    
    async def _get_full_response(self, message: str) -> str:
        """Get full response from agent (fallback method)"""
        # For demonstration purposes, return sample responses
        # In production, this would integrate with Azure AI Foundry agents
        
        if "cardiovascular" in message.lower() or "heart" in message.lower() or "cardiac" in message.lower():
            return """Cardiovascular research encompasses the study of heart and blood vessel diseases, which remain the leading cause of death worldwide. Key focus areas include:

**Coronary Artery Disease**: Investigating atherosclerosis mechanisms, novel stent technologies, and regenerative approaches to restore blood flow.

**Heart Failure**: Research into cardiac remodeling, biomarker discovery, and advanced device therapies like left ventricular assist devices.

**Arrhythmias**: Developing better understanding of electrical conduction abnormalities and improving ablation techniques and implantable devices.

**Hypertension**: Studying the renin-angiotensin system, vascular biology, and personalized treatment approaches.

**Cardiovascular Imaging**: Advancing MRI, CT, echocardiography, and molecular imaging techniques for early detection and monitoring.

**Preventive Cardiology**: Large-scale population studies examining risk factors, lifestyle interventions, and genetic predispositions.

Modern cardiovascular research heavily incorporates AI for risk prediction, drug discovery, and personalized medicine approaches."""
        else:
            return """I'm BioLink's AI research assistant, specializing in cardiovascular medicine and clinical data analysis. I can help you with:

• Patient registry exploration and cohort building
• Clinical data analysis and visualization  
• Research protocol design and statistical analysis
• Genomic and biomarker data interpretation
• Medical literature review and evidence synthesis

How can I assist with your cardiovascular research today?"""
    
    async def get_agent_metadata(self) -> Dict[str, Any]:
        """Get agent metadata from Azure AI Foundry"""
        try:
            logger.info(f"Getting agent metadata: {self.agent_id}")
            
            agent = self.project_client.agents.get(self.agent_id)
            
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
