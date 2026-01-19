// Foundry Agent Integration Service
// Handles communication with Azure Foundry agents

import { API_BASE_URL } from './client';

export interface AgentResponseChunk {
  type: 'text' | 'code' | 'image' | 'reasoning' | 'error';
  content: string;
  language?: string; // For code blocks
  metadata?: Record<string, any>;
}

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chunks?: AgentResponseChunk[];
  timestamp: Date;
}

export interface FoundryAgentConfig {
  agentId: string;
  projectEndpoint: string;
  subscriptionId: string;
  resourceId: string;
}

export interface AgentRunResponse {
  id: string;
  status: 'completed' | 'failed' | 'streaming';
  text?: string;
  chunks?: AgentResponseChunk[];
  error?: string;
  raw?: any;
}

class FoundryAgentService {
  private config: FoundryAgentConfig;
  private conversationThreadId: string = '';
  private apiBaseUrl: string;

  constructor(config: FoundryAgentConfig) {
    this.config = config;
    // Use the shared API base URL so all API calls are consistent.
    this.apiBaseUrl = API_BASE_URL;
  }

  /**
   * Parse agent response and extract different content types
   * Foundry agents can return text, code blocks, images, and reasoning steps
   */
  private parseAgentResponse(text: string): AgentResponseChunk[] {
    const chunks: AgentResponseChunk[] = [];

    // Pattern for code blocks: ```language\ncode\n```
    const codePattern = /```(\w+)?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codePattern.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textBefore = text.substring(lastIndex, match.index).trim();
        if (textBefore) {
          chunks.push({
            type: 'text',
            content: textBefore
          });
        }
      }

      // Add code block
      chunks.push({
        type: 'code',
        content: match[2].trim(),
        language: match[1] || 'text'
      });

      lastIndex = match.index + match[0].length;
    // Deprecated: Foundry backend client removed in favor of direct frontend calls.

