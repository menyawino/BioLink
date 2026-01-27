export type ChatMessage = {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
};

export type ToolCall = {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
};

export type AgentResponseChunk = {
  type: 'text' | 'code' | 'image' | 'reasoning' | 'error' | 'tool_call';
  content: string;
  language?: string;
  metadata?: Record<string, any>;
  tool_call?: ToolCall;
};

export async function chatWithAgent(
  messages: ChatMessage[],
  options?: { tools?: boolean; stream?: boolean; toolModelOverride?: string }
) {
  const baseUrl = import.meta.env.VITE_OLLAMA_BASE_URL || 'http://localhost:11434';
  const defaultModel = import.meta.env.VITE_OLLAMA_MODEL || 'alibayram/medgemma:4b';
  const toolModel = options?.toolModelOverride || import.meta.env.VITE_OLLAMA_TOOL_MODEL || defaultModel;
  const model = options?.tools ? toolModel : defaultModel;
  const stream = options?.stream ?? true;

  const url = `${baseUrl.replace(/\/$/, '')}/api/chat`;

  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      messages,
      stream,
      ...(options?.tools
        ? {
            tools: [
              {
                type: "function",
                function: {
                  name: "query_sql",
                  description: "Execute SQL queries against the EHVol patient database",
                  parameters: {
                    type: "object",
                    properties: {
                      sql: {
                        type: "string",
                        description: "The SQL query to execute"
                      },
                      limit: {
                        type: "number",
                        description: "Maximum number of rows to return (default: 500)"
                      }
                    },
                    required: ["sql"]
                  }
                }
              },
              {
                type: "function",
                function: {
                  name: "search_patients",
                  description: "Search for patients with specific criteria",
                  parameters: {
                    type: "object",
                    properties: {
                      search: {
                        type: "string",
                        description: "Search term for patient name or MRN"
                      },
                      gender: {
                        type: "string",
                        description: "Filter by gender (male/female)"
                      },
                      age_min: {
                        type: "number",
                        description: "Minimum age"
                      },
                      age_max: {
                        type: "number",
                        description: "Maximum age"
                      },
                      limit: {
                        type: "number",
                        description: "Maximum number of results"
                      }
                    }
                  }
                }
              },
              {
                type: "function",
                function: {
                  name: "build_cohort",
                  description: "Build a patient cohort with specific criteria",
                  parameters: {
                    type: "object",
                    properties: {
                      age_min: { type: "number", description: "Minimum age" },
                      age_max: { type: "number", description: "Maximum age" },
                      gender: { type: "string", description: "Gender filter" },
                      has_diabetes: { type: "boolean", description: "Has diabetes" },
                      has_hypertension: { type: "boolean", description: "Has hypertension" },
                      has_echo: { type: "boolean", description: "Has echocardiogram" },
                      has_mri: { type: "boolean", description: "Has MRI" },
                      limit: { type: "number", description: "Maximum results" }
                    }
                  }
                }
              },
              {
                type: "function",
                function: {
                  name: "chart_from_sql",
                  description: "Create charts from SQL query results",
                  parameters: {
                    type: "object",
                    properties: {
                      sql: { type: "string", description: "SQL query for chart data" },
                      mark: { type: "string", enum: ["line", "bar", "point", "area"], description: "Chart type" },
                      x: { type: "string", description: "X-axis field" },
                      y: { type: "string", description: "Y-axis field" },
                      color: { type: "string", description: "Color field for grouping" },
                      title: { type: "string", description: "Chart title" }
                    },
                    required: ["sql", "x", "y"]
                  }
                }
              },
              {
                type: "function",
                function: {
                  name: "registry_overview",
                  description: "Get overview statistics of the patient registry",
                  parameters: {
                    type: "object",
                    properties: {}
                  }
                }
              }
            ]
          }
        : {})
    })
  });
}

export async function chatWithOrchestrator(
  message: string,
  history: ChatMessage[] = []
) {
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3001';
  const response = await fetch(`${backendUrl.replace(/\/$/, '')}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      history
    })
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  return response.json();
}

export async function callTool(toolName: string, args: any): Promise<string> {
  // Call backend API endpoint for tools
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3001';
  const response = await fetch(`${backendUrl.replace(/\/$/, '')}/api/tools/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tool: toolName,
      arguments: args
    })
  });

  if (!response.ok) {
    throw new Error(`Tool call failed: ${response.status}`);
  }

  const result = await response.json();
  return JSON.stringify(result, null, 2);
}

export async function chatWithSqlAgent(
  message: string,
  history: ChatMessage[] = []
) {
  return chatWithOrchestrator(message, history);
}
