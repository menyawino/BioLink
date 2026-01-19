"""
BioLink Agent Integration with Microsoft Foundry
Connects your existing Azure agent with BioLink API tools
"""

import os
import asyncio
import httpx
from typing import Annotated

# =============================================================================
# CONFIGURATION - Update these with your Azure/Foundry details
# =============================================================================
RESPONSES_ENDPOINT = os.environ.get(
    "FOUNDRY_RESPONSES_ENDPOINT",
    "https://omar-ahmed-abdelhamiid-resource.services.ai.azure.com/api/projects/abdelhamiid-1153/applications/blnk/protocols/openai/responses?api-version=2025-11-15-preview",
)

# BioLink API base URL (local development)
BIOLINK_API = "http://localhost:3001/api"

# =============================================================================
# MAIN AGENT SETUP
# =============================================================================

async def main():
    """Invoke existing BioLink agent via Foundry project endpoint."""

    print("🚀 Connecting to existing BioLink agent...")
    responses_endpoint = RESPONSES_ENDPOINT.strip()
    print(f"📍 Responses API: {responses_endpoint}")
    print("🤖 Agent: blnk (published)")
    print(f"🔗 API: {BIOLINK_API}\n")

    api_key = os.environ.get("AZURE_AI_PROJECT_API_KEY")
    if not api_key:
        print("❌ Missing AZURE_AI_PROJECT_API_KEY in the environment.")
        print("   Set it before running this script.")
        return

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    agent_url = responses_endpoint

    print("✅ Ready! Type your query (or 'quit' to exit):")
    print("=" * 60)

    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue

        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are BioLink, the AI assistant for the Magdi Yacoub Heart Foundation's cardiovascular research registry (EHVol).
                    Respond conversationally but call tools when research queries need data.""",
                },
                {"role": "user", "content": user_input},
            ]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    agent_url,
                    headers=headers,
                    json={"input": messages, "stream": False},
                )
                response.raise_for_status()

            result = response.json()
            assistant_reply = result.get("output_text")
            if not assistant_reply:
                assistant_reply = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "No response")
                )

            print(f"\n🤖 BioLink: {assistant_reply}")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
