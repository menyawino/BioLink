export type ChatMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export type AgentResponseChunk = {
  type: 'text' | 'code' | 'image' | 'reasoning' | 'error';
  content: string;
  language?: string;
  metadata?: Record<string, any>;
};

export async function chatWithAgent(messages: ChatMessage[]) {
  const baseUrl = import.meta.env.VITE_OLLAMA_BASE_URL || 'http://localhost:11434';
  const model = import.meta.env.VITE_OLLAMA_MODEL || 'alibayram/medgemma:4b';

  const url = `${baseUrl.replace(/\/$/, '')}/api/chat`;

  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      messages,
      stream: true
    })
  });
}
