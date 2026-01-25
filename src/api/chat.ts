import { post, ApiResponse } from './client';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequestData {
  content: string;
  role: 'assistant';
  timestamp: string;
  action?: string;
  view?: string;
}

export interface ChatRequest {
  message: string;
  history: ChatMessage[];
}

// Send chat message to backend service
export async function sendChatMessage(
  message: string, 
  history: ChatMessage[] = []
): Promise<ApiResponse<ChatRequestData>> {
  return post<ChatRequestData>('/api/chat', {
    message,
    history
  });
}

