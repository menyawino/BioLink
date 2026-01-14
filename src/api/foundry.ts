// Foundry Agent Integration Service
// Handles communication with Azure Foundry agents

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
    // Get API base URL from environment, default to current origin
    this.apiBaseUrl = import.meta.env.VITE_API_URL || window.location.origin;
  }

  /**
   * Parse agent response and extract different content types
   * Foundry agents can return text, code blocks, images, and reasoning steps
   */
  private parseAgentResponse(text: string): AgentResponseChunk[] {
    const chunks: AgentResponseChunk[] = [];
    let remaining = text;

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
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textAfter = text.substring(lastIndex).trim();
      if (textAfter) {
        chunks.push({
          type: 'text',
          content: textAfter
        });
      }
    }

    // If no chunks were found, treat entire response as text
    if (chunks.length === 0) {
      chunks.push({
        type: 'text',
        content: text
      });
    }

    return chunks;
  }

  /**
   * Initialize conversation thread with the agent
   * Returns thread ID for multi-turn conversations
   */
  async initializeThread(): Promise<string> {
    try {
      // Call backend to create thread
      const response = await fetch(`${this.apiBaseUrl}/api/foundry/thread`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentId: this.config.agentId
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize thread: ${response.statusText}`);
      }

      const data = await response.json();
      this.conversationThreadId = data.threadId;
      return this.conversationThreadId;
    } catch (error) {
      console.error('Error initializing thread:', error);
      throw error;
    }
  }

  /**
   * Send message to Foundry agent and get response
   * Handles streaming and different content types
   */
  async runAgent(
    userMessage: string,
    threadId?: string,
    onChunk?: (chunk: AgentResponseChunk) => void
  ): Promise<AgentRunResponse> {
    try {
      const finalThreadId = threadId || this.conversationThreadId;

      if (!finalThreadId) {
        await this.initializeThread();
      }

      // Call backend to run agent
      const response = await fetch(`${this.apiBaseUrl}/api/foundry/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentId: this.config.agentId,
          threadId: finalThreadId || this.conversationThreadId,
          userMessage: userMessage,
          stream: false // Can be true for streaming in future
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `Agent run failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Parse response into chunks
      const chunks = this.parseAgentResponse(data.text);

      // Notify on each chunk if callback provided
      if (onChunk) {
        chunks.forEach(chunk => onChunk(chunk));
      }

      return {
        id: data.id || Date.now().toString(),
        status: 'completed',
        text: data.text,
        chunks: chunks,
        raw: data
      };
    } catch (error) {
      console.error('Error running agent:', error);
      return {
        id: Date.now().toString(),
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
        chunks: [
          {
            type: 'error',
            content: error instanceof Error ? error.message : 'Failed to get response from agent'
          }
        ]
      };
    }
  }

  /**
   * Get conversation history for the current thread
   */
  async getConversationHistory(): Promise<AgentMessage[]> {
    try {
      if (!this.conversationThreadId) {
        return [];
      }

      const response = await fetch(
        `${this.apiBaseUrl}/api/foundry/history?threadId=${this.conversationThreadId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get history: ${response.statusText}`);
      }

      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error('Error getting conversation history:', error);
      return [];
    }
  }
}

// Factory function to create configured service
export function createFoundryAgentService(): FoundryAgentService {
  const config: FoundryAgentConfig = {
    agentId: import.meta.env.VITE_AZURE_AGENT_ID || 'blnk:8',
    projectEndpoint: import.meta.env.VITE_AZURE_AI_PROJECT_ENDPOINT || '',
    subscriptionId: import.meta.env.VITE_AZURE_SUBSCRIPTION_ID || '',
    resourceId: import.meta.env.VITE_AZURE_RESOURCE_ID || ''
  };

  if (!config.projectEndpoint) {
    console.warn('Azure Foundry endpoint not configured in environment variables');
  }

  return new FoundryAgentService(config);
}

export default FoundryAgentService;
