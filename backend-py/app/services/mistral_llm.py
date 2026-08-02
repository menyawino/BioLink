"""Native LangChain-compatible ChatMistralAI provider for BioLink backend services.
"""

from __future__ import annotations

import json
import logging
import ssl
import urllib.request
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

logger = logging.getLogger(__name__)


class ChatMistralAI(BaseChatModel):
    api_key: str
    model: str = "mistral-small-latest"
    temperature: float = 0.1
    timeout: float = 30.0

    @property
    def _llm_type(self) -> str:
        return "mistral-ai"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                role = "user"
            payload_messages.append({"role": role, "content": str(msg.content)})

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": self.temperature,
        }
        if stop:
            payload["stop"] = stop

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=req_data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            content = data["choices"][0]["message"]["content"]
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        except Exception as exc:
            logger.error("Mistral API call failed: %s", exc)
            raise RuntimeError(f"Mistral API request failed: {exc}") from exc
