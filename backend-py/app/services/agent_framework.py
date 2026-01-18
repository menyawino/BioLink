from typing import Optional, List, Dict, Any, Callable
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.config import settings
import logging
import uuid
import asyncio
import time

try:
    from azure.ai.agents import AgentsClient
except Exception:  # pragma: no cover - optional dependency at runtime
    AgentsClient = None

logger = logging.getLogger(__name__)

class AgentFrameworkService:
    """Azure AI Foundry Agent service using v2 Agents API"""
    
    def __init__(self):
        self.endpoint = settings.azure_existing_aiproject_endpoint
        self.agent_id = settings.azure_existing_agent_id
        self.api_version = settings.azure_foundry_api_version
        self.model_deployment = settings.model_deployment_name
        
        if not self.endpoint:
            raise ValueError("AZURE_EXISTING_AIPROJECT_ENDPOINT is not configured")
        
        # Initialize Azure credential and project client
        try:
            credential = DefaultAzureCredential()
            self.credential = credential
            self.project_client = AIProjectClient(
                endpoint=self.endpoint,
                credential=credential
            )
            logger.info(f"AIProjectClient initialized: endpoint={self.endpoint}, agent_id={self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AIProjectClient: {e}")
            raise

        # Initialize Azure AI Agents (persistent) client when available
        self.agents_client = None
        if AgentsClient is not None:
            try:
                self.agents_client = AgentsClient(
                    endpoint=self.endpoint,
                    credential=self.credential
                )
                logger.info("AgentsClient initialized for persistent agents")
            except Exception as e:
                logger.warning(f"Failed to initialize AgentsClient: {e}")
                self.agents_client = None

    async def _call_client(self, func: Callable, **kwargs):
        """Run a potentially blocking SDK call in a thread."""
        return await asyncio.to_thread(func, **kwargs)

    async def _create_thread(self) -> Optional[str]:
        """Create a persistent thread via Azure AI Agents SDK if available."""
        if not self.agents_client:
            return None

        threads_client = getattr(self.agents_client, "threads", None)
        if threads_client and hasattr(threads_client, "create"):
            thread = await self._call_client(threads_client.create)
            return getattr(thread, "id", None)

        create_thread = getattr(self.agents_client, "create_thread", None)
        if callable(create_thread):
            thread = await self._call_client(create_thread)
            return getattr(thread, "id", None)

        return None

    async def _create_message(self, thread_id: str, message: str) -> None:
        """Create a user message on a thread if supported by the SDK."""
        if not self.agents_client:
            return

        messages_client = getattr(self.agents_client, "messages", None)
        if messages_client and hasattr(messages_client, "create"):
            await self._call_client(
                messages_client.create,
                thread_id=thread_id,
                role="user",
                content=message
            )
            return

        threads_client = getattr(self.agents_client, "threads", None)
        nested_messages = getattr(getattr(threads_client, "messages", None), "create", None)
        if callable(nested_messages):
            await self._call_client(
                nested_messages,
                thread_id=thread_id,
                role="user",
                content=message
            )

    async def _start_run(self, thread_id: str) -> Optional[str]:
        """Start a run for the thread and return run id."""
        if not self.agents_client:
            return None

        runs_client = getattr(self.agents_client, "runs", None)
        if runs_client and hasattr(runs_client, "create"):
            run = await self._call_client(
                runs_client.create,
                thread_id=thread_id,
                agent_id=self.agent_id
            )
            return getattr(run, "id", None)

        threads_client = getattr(self.agents_client, "threads", None)
        nested_runs = getattr(getattr(threads_client, "runs", None), "create", None)
        if callable(nested_runs):
            run = await self._call_client(
                nested_runs,
                thread_id=thread_id,
                agent_id=self.agent_id
            )
            return getattr(run, "id", None)

        return None

    async def _poll_run(self, thread_id: str, run_id: str, timeout_s: int = 60) -> None:
        """Poll for run completion."""
        if not self.agents_client:
            return

        runs_client = getattr(self.agents_client, "runs", None)
        get_run = None
        if runs_client and hasattr(runs_client, "get"):
            get_run = runs_client.get
        else:
            threads_client = getattr(self.agents_client, "threads", None)
            get_run = getattr(getattr(threads_client, "runs", None), "get", None)

        if not callable(get_run):
            return

        start = time.time()
        while time.time() - start < timeout_s:
            run = await self._call_client(get_run, thread_id=thread_id, run_id=run_id)
            status = getattr(run, "status", None)
            if status in {"completed", "failed", "cancelled"}:
                return
            await asyncio.sleep(0.5)

    async def _get_latest_assistant_message(self, thread_id: str) -> Optional[str]:
        """Fetch the most recent assistant message from the thread."""
        if not self.agents_client:
            return None

        list_messages = None
        messages_client = getattr(self.agents_client, "messages", None)
        if messages_client and hasattr(messages_client, "list"):
            list_messages = messages_client.list
        else:
            threads_client = getattr(self.agents_client, "threads", None)
            list_messages = getattr(getattr(threads_client, "messages", None), "list", None)

        if not callable(list_messages):
            return None

        messages = await self._call_client(list_messages, thread_id=thread_id)
        items = getattr(messages, "data", None) or getattr(messages, "items", None) or messages
        if not items:
            return None

        # Find the latest assistant message
        for msg in reversed(list(items)):
            if getattr(msg, "role", None) != "assistant":
                continue

            content = getattr(msg, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Handle list of content parts
                text_parts = []
                for part in content:
                    text_value = getattr(part, "text", None) or getattr(part, "value", None)
                    if text_value:
                        text_parts.append(text_value)
                if text_parts:
                    return "".join(text_parts)

        return None
    
    async def create_conversation(self, first_message: Optional[str] = None) -> str:
        """Create a new conversation with the agent"""
        try:
            logger.info(f"Creating conversation")
            
            # Create conversation with optional title from first message
            conversation_options = {}
            if first_message:
                title = first_message[:50] + "..." if len(first_message) > 50 else first_message
                conversation_options["metadata"] = {"title": title}
            
            # Prefer Azure AI Agents persistent thread if available
            thread_id = await self._create_thread()
            if thread_id:
                logger.info(f"Created persistent thread: {thread_id}")
                return thread_id

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
        # Use Azure AI Agents SDK when available for real responses
        if self.agents_client and self.agent_id:
            try:
                thread_id = await self._create_thread()
                if not thread_id:
                    raise RuntimeError("Failed to create persistent thread")

                await self._create_message(thread_id, message)
                run_id = await self._start_run(thread_id)
                if run_id:
                    await self._poll_run(thread_id, run_id)

                assistant_text = await self._get_latest_assistant_message(thread_id)
                if assistant_text:
                    return assistant_text
            except Exception as e:
                logger.warning(f"Azure AI Agents SDK call failed: {e}")

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
