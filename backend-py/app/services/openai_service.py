from typing import Optional, List
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    """Azure OpenAI service for chat completions"""
    
    def __init__(self):
        self.endpoint = settings.azure_openai_endpoint
        self.api_key = settings.azure_openai_api_key
        self.deployment = settings.azure_openai_deployment
        
        if self.endpoint and self.api_key:
            try:
                self.client = ChatCompletionsClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.api_key)
                )
                logger.info("Azure OpenAI client initialized")
            except Exception as e:
                logger.error(f"Fa   iled to initialize Azure OpenAI: {e}")
                self.client = None
        else:
            logger.warning("Azure OpenAI credentials not configured")
            self.client = None
    
    async def get_chat_completion(self, messages: List[dict]) -> str:
        """Get chat completion from Azure OpenAI"""
        if not self.client:
            raise ValueError("Azure OpenAI is not configured")
        
        try:
            response = self.client.complete(
                model=self.deployment,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            raise

# Initialize service
try:
    openai_service = AzureOpenAIService()
except Exception as e:
    logger.error(f"AzureOpenAIService initialization failed: {e}")
    openai_service = None
