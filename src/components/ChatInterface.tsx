import { useState, useRef, useEffect } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Send, Loader2, Bot, User, Sparkles, ArrowRight, Activity, Users, BarChart3, Copy, Check } from "lucide-react";
import { useApp } from "../context/AppContext";
import { chatWithAgent, callTool, chatWithSqlAgent, chatWithOrchestrator, AgentResponseChunk, ChatMessage, ToolCall } from "../api/agent";

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  actions?: { label: string; view?: string; onClick?: () => void }[];
  error?: boolean;
  data?: any;
  chunks?: AgentResponseChunk[];
  isStreaming?: boolean; // New: indicates if message is currently streaming
  streamingChunks?: AgentResponseChunk[]; // New: chunks received during streaming
}

interface WelcomeScreenProps {
  onNavigate: (view: string) => void;
  patientData?: any;
}

// Helper function to parse simple markdown
const parseMarkdown = (text: string) => {
  // Handle images first: ![alt](url)
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; height: auto;" />');
  
  // Split by bold markers and process each part
  const parts = text.split(/(\*\*.*?\*\*)/g);
  
  return parts.map(part => {
    if (part.startsWith('**') && part.endsWith('**')) {
      // This is bold text
      const content = part.slice(2, -2);
      return `<strong>${content}</strong>`;
    } else {
      // This is regular text, apply italic parsing
      return part.replace(/\*([^*]+?)\*/g, '<em>$1</em>');
    }
  }).join('');
};

// Component to render different content types from the assistant
function ChunkRenderer({ chunk, isStreaming = false }: { chunk: AgentResponseChunk; isStreaming?: boolean }) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (chunk.type === 'text' || chunk.type === 'reasoning') {
      if (isStreaming) {
        setIsTyping(true);
        // Split by spaces but preserve newlines by treating them as separate tokens
        const tokens = chunk.content.split(/(\s+)/).filter(token => token.length > 0);
        let currentIndex = 0;
        
        const typeToken = () => {
          if (currentIndex < tokens.length) {
            setDisplayedText(prev => prev + tokens[currentIndex]);
            currentIndex++;
            setTimeout(typeToken, tokens[currentIndex - 1].includes('\n') ? 100 : 50); // Slower for lines with newlines
          } else {
            setIsTyping(false);
          }
        };
        
        // Start typing after a brief delay
        setTimeout(typeToken, 100);
      } else {
        setDisplayedText(chunk.content);
      }
    } else {
      setDisplayedText(chunk.content);
    }
  }, [chunk.content, chunk.type, isStreaming]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  switch (chunk.type) {
    case 'text':
      const textContent = isStreaming ? displayedText : chunk.content;
      const htmlContent = parseMarkdown(textContent) + (isStreaming && isTyping ? '<span class="animate-pulse text-primary">|</span>' : '');
      
      return (
        <span className="whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: htmlContent }} />
      );

    case 'code':
      return (
        <div className="bg-muted/80 rounded-lg p-4 my-2 border border-muted-foreground/20">
          <div className="flex justify-between items-center mb-2">
            <Badge variant="secondary" className="text-xs">
              {chunk.language || 'code'}
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              className="h-6 w-6 p-0"
              onClick={() => copyToClipboard(chunk.content)}
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
          <pre className="text-sm overflow-x-auto">
            <code>{chunk.content}</code>
          </pre>
        </div>
      );

    case 'image':
      return (
        <div className="my-4">
          <img 
            src={chunk.content} 
            alt="Generated visualization" 
            className="max-w-full h-auto rounded-lg border border-muted/20 shadow-sm"
          />
        </div>
      );

    case 'reasoning':
      return (
        <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg p-4 my-2 border border-blue-200/50 dark:border-blue-900/50">
          <div className="flex items-start">
            <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-sm text-blue-900 dark:text-blue-100 mb-1">Reasoning</p>
              <span className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap" dangerouslySetInnerHTML={{ 
                __html: (isStreaming ? parseMarkdown(displayedText) : parseMarkdown(chunk.content)) + (isStreaming && isTyping ? '<span class="animate-pulse text-blue-600">|</span>' : '')
              }} />
            </div>
          </div>
        </div>
      );

    case 'error':
      return (
        <div className="bg-red-50 dark:bg-red-950/20 rounded-lg p-3 my-2 border border-red-200/50 dark:border-red-900/50">
          <p className="text-sm text-red-800 dark:text-red-200">{chunk.content}</p>
        </div>
      );

    default:
      return <p className="text-muted-foreground">{chunk.content}</p>;
  }
}

// Component to render streaming text chunks as a single flowing paragraph
function StreamingTextRenderer({ chunks, isStreaming }: { chunks: AgentResponseChunk[]; isStreaming: boolean }) {
  const fullContent = chunks.map(c => c.content).join('');
  
  // Add line breaks for better readability
  const formattedContent = fullContent
    .replace(/(\*\*.*?\*\*)\s*\*/g, '$1\n') // Add line break after bold items in lists
    .replace(/([.!?])\s+/g, '$1\n') // Add line breaks after sentences
    .replace(/\n\s*\n/g, '\n') // Remove extra blank lines
    .trim();
  
  const htmlContent = parseMarkdown(formattedContent) + (isStreaming ? '<span class="animate-pulse text-primary">|</span>' : '');
  
  return (
    <span className="whitespace-pre-line" dangerouslySetInnerHTML={{ __html: htmlContent }} />
  );
}


export function WelcomeScreen({ onNavigate, patientData }: WelcomeScreenProps) {
  const appContext = useApp();
  const toolModelFallback = import.meta.env.VITE_OLLAMA_TOOL_MODEL_FALLBACK as string | undefined;
  const sqlAgentEnabled = (import.meta.env.VITE_SQL_AGENT_ENABLED as string | undefined) === 'true';
  const orchestratorEnabled = (import.meta.env.VITE_AGENT_ORCHESTRATOR_ENABLED as string | undefined) !== 'false';
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to BioLink. I\'m your AI research assistant. I have access to the entire patient registry, analytics engine, and cohort builder.\n\nHow can I assist you with your research today?',
      timestamp: new Date(),
      actions: [
        { label: "View Patient Registry", view: "registry" },
        { label: "Build New Cohort", view: "cohort" },
        { label: "Analyze Demographics", view: "analytics" },
      ]
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const systemPrompt = `You are BioLink, an AI assistant for cardiovascular research.
Rules:
1) ZERO chit-chat for data requests. Use tools immediately with reasonable defaults (limit 10, age ranges, latest records).
2) Ask a follow-up only if the request is ambiguous or unsafe.
3) For non-data chat, respond briefly in 1-2 sentences.
4) Never stall or ask to confirm obvious parameters.`;

  const isLikelyToolPayload = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return false;
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      try {
        const parsed = JSON.parse(trimmed);
        if (parsed?.tool_calls || parsed?.tool || parsed?.name || parsed?.parameters) return true;
      } catch {
        // ignore
      }
    }
    return /"name"\s*:\s*"[a-zA-Z0-9_]+"\s*,\s*"parameters"/i.test(trimmed);
  };

  const sanitizeAssistantText = (text: string) => {
    let cleaned = text;
    cleaned = cleaned.replace(/\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{[^}]*\}\s*\}/gi, '').trim();
    cleaned = cleaned.replace(/\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}/gi, '').trim();
    cleaned = cleaned.replace(/^select\s+.*$/gim, '').trim();
    return cleaned;
  };

  const shouldUseTools = (text: string) => {
    const normalized = text.trim().toLowerCase();
    if (!normalized) return false;
    const keywords = [
      "patient", "patients", "registry", "cohort", "sql", "query", "count", "list",
      "show", "find", "search", "chart", "plot", "graph", "analytics", "stats",
      "age", "gender", "ef", "ejection fraction", "hypertension", "diabetes",
      "echo", "mri", "biomarker", "protein"
    ];
    return keywords.some(keyword => normalized.includes(keyword));
  };

  const isLikelySqlOnly = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return false;
    return /^select\s+/i.test(trimmed) && !/[a-z]\s*:\s*/i.test(trimmed);
  };

  const generateResponse = (text: string): { content: string, actions: { label: string; view?: string }[] } => {
    const lowerInput = text.toLowerCase();
    let content = "";
    let actions: { label: string; view: string }[] = [];

    if (lowerInput.includes("registry") || lowerInput.includes("list") || lowerInput.includes("patients")) {
      content = "I can take you to the Patient Registry. There are currently 1,247 patients with 94% data completeness. Would you like to view the full list?";
      actions = [{ label: "Open Registry", view: "registry" }];
    } else if (lowerInput.includes("cohort") || lowerInput.includes("filter") || lowerInput.includes("group")) {
      content = "The Cohort Builder allows you to create sophisticated patient groups using multi-dimensional filtering. Shall I open the builder for you?";
      actions = [{ label: "Open Cohort Builder", view: "cohort" }];
    } else if (lowerInput.includes("analytics") || lowerInput.includes("stats") || lowerInput.includes("dashboard") || lowerInput.includes("graph")) {
      content = "Our Analytics Dashboard features UpSet plots, timeline exploration, and geographic mapping. I can open that for you.";
      actions = [{ label: "View Analytics", view: "analytics" }];
    } else if (lowerInput.includes("biomarker") || lowerInput.includes("protein")) {
      content = "We have comprehensive data on protein biomarkers. You can view this data within specific patient profiles or analyze it across the registry.";
      if (patientData && patientData.patient) {
        content += `\n\nFor example, the currently loaded patient (${patientData.patient.mrn}) has ${patientData.proteinBiomarkers?.cardiac?.length || 0} cardiac biomarkers on file.`;
      }
      actions = [
        { label: "Search Patient", view: "patient" },
        { label: "View Registry", view: "registry" }
      ];
    } else if (lowerInput.includes("search") || lowerInput.includes("find")) {
      content = "You can search for patients by MRN, name, or other identifiers in the Patient View.";
      if (patientData && patientData.patient) {
         content = `The current active patient is ${patientData.patient.name} (${patientData.patient.mrn}). Would you like to view their full profile?`;
         actions = [{ label: "View " + patientData.patient.mrn, view: "patient" }];
      } else {
         actions = [{ label: "Go to Search", view: "patient" }];
      }
    } else if (lowerInput.includes("dictionary") || lowerInput.includes("definition")) {
      content = "The Data Dictionary contains definitions for all clinical variables, including protein biomarkers and genomic data.";
      actions = [{ label: "Open Dictionary", view: "dictionary" }];
    } else {
      content = "I can help you navigate the platform. You can ask me to show the registry, build a cohort, or view analytics. What would you like to do?";
      actions = [
        { label: "View Registry", view: "registry" },
        { label: "View Analytics", view: "analytics" },
        { label: "Build Cohort", view: "cohort" }
      ];
    }
    
    return { content, actions };
  };

  const streamChatResponse = async (
    conversationMessages: ChatMessage[],
    streamingMessageId: string,
    useTools: boolean
  ) => {
    let response = await chatWithAgent(conversationMessages, { tools: useTools });
    if (!response.ok) {
      const errorText = await response.text();
      const isToolUnsupported =
        useTools &&
        response.status === 400 &&
        (errorText.includes("does not support tools") ||
          errorText.includes("does not support tool"));

      if (isToolUnsupported) {
        if (toolModelFallback) {
          response = await chatWithAgent(conversationMessages, {
            tools: true,
            toolModelOverride: toolModelFallback
          });
        } else {
          response = await chatWithAgent(conversationMessages, { tools: false });
        }
        if (!response.ok) {
          const retryErrorText = await response.text();
          throw new Error(`Ollama request failed: ${response.status} ${retryErrorText}`);
        }
      } else {
        throw new Error(`Ollama request failed: ${response.status} ${errorText}`);
      }
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Ollama response stream is unavailable');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';
    let toolCalls: ToolCall[] = [];
    let suppressText = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const data = line.trim();
        if (!data) continue;

        let parsed: any;
        try {
          parsed = JSON.parse(data);
        } catch {
          continue;
        }

        const delta = parsed?.message?.content ?? parsed?.content;
        const toolCallsDelta = parsed?.message?.tool_calls ?? parsed?.tool_calls;

        if (toolCallsDelta) {
          toolCalls = [...toolCalls, ...toolCallsDelta];
        }

        if (delta) {
          const nextText = `${fullText}${delta}`;
          if (useTools && (toolCallsDelta || isLikelyToolPayload(delta) || isLikelyToolPayload(nextText))) {
            suppressText = true;
            continue;
          }
          if (suppressText) {
            continue;
          }
          fullText += delta;
          const chunk: AgentResponseChunk = { type: 'text', content: delta };

          setMessages(prev => prev.map(msg => {
            if (msg.id === streamingMessageId) {
              const updatedChunks = [...(msg.streamingChunks || []), chunk];
              return {
                ...msg,
                streamingChunks: updatedChunks,
                content: fullText
              };
            }
            return msg;
          }));
        }
      }
    }

    if (useTools && (toolCalls.length > 0 || suppressText)) {
      fullText = '';
    }

    if (useTools && toolCalls.length === 0 && isLikelySqlOnly(fullText)) {
      fullText = '';
    }

    fullText = sanitizeAssistantText(fullText);

    setMessages(prev => prev.map(msg => {
      if (msg.id === streamingMessageId) {
        return {
          ...msg,
          chunks: [{ type: 'text', content: fullText }],
          content: fullText || (useTools && toolCalls.length > 0 ? 'Running tools...' : 'Response received'),
          isStreaming: false,
          streamingChunks: undefined
        };
      }
      return msg;
    }));

    return { fullText, toolCalls };
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      // Prefer orchestrator if enabled
      if (orchestratorEnabled) {
        const history = messages
          .filter(msg => msg.role === 'user' || msg.role === 'assistant')
          .map(msg => ({ role: msg.role, content: msg.content }));

        const response = await chatWithOrchestrator(currentInput, history);
        const content = response?.data?.content ?? response?.content ?? 'No response.';

        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + Math.random()).toString(),
            role: 'assistant',
            content,
            timestamp: new Date(),
            chunks: [{ type: 'text', content }]
          }
        ]);

        setIsLoading(false);
        inputRef.current?.focus();
        return;
      }

      // Check if this is a data query that should use the SQL agent
      const useSqlAgent = sqlAgentEnabled && shouldUseTools(currentInput);

      if (useSqlAgent) {
        const history = messages
          .filter(msg => msg.role === 'user' || msg.role === 'assistant')
          .map(msg => ({ role: msg.role, content: msg.content }));

        const response = await chatWithSqlAgent(currentInput, history);
        const content = response?.data?.content ?? response?.content ?? 'No response.';

        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + Math.random()).toString(),
            role: 'assistant',
            content,
            timestamp: new Date(),
            chunks: [{ type: 'text', content }]
          }
        ]);

        setIsLoading(false);
        inputRef.current?.focus();
        return;
      }

      // Handle non-SQL queries with regular chat
      let conversationMessages: ChatMessage[] = [
        { role: 'system', content: systemPrompt },
        ...messages
          .filter(msg => msg.role === 'user' || msg.role === 'assistant')
          .map(msg => ({ role: msg.role, content: msg.content })),
        { role: 'user', content: currentInput }
      ];

      if (isGreeting(currentInput)) {
        const streamingMessageId = (Date.now() + Math.random()).toString();
        const streamingMessage: Message = {
          id: streamingMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
          streamingChunks: []
        };
        setMessages(prev => [...prev, streamingMessage]);
        await streamChatResponse(conversationMessages, streamingMessageId, false);
        setIsLoading(false);
        inputRef.current?.focus();
        return;
      }

      // Regular chat without tools
      const streamingMessageId = (Date.now() + Math.random()).toString();
      const streamingMessage: Message = {
        id: streamingMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
        streamingChunks: []
      };
      setMessages(prev => [...prev, streamingMessage]);
      await streamChatResponse(conversationMessages, streamingMessageId, false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.warn('Chat error:', error);
      setMessages(prev => [
        ...prev.filter(msg => !msg.isStreaming),
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${message}`,
          timestamp: new Date(),
          error: true
        }
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-center space-x-3 pb-6 pt-4 border-b border-muted/20">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#00a2dd] to-[#efb01b] flex items-center justify-center flex-shrink-0">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">BioLink Agent</h1>
        <Badge variant="outline" className="text-primary border-primary/20 bg-primary/5">
          Beta
        </Badge>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col overflow-hidden shadow-sm border-muted/40 rounded-lg mt-4">
        <ScrollArea className="flex-1 p-4 md:p-6">
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <Avatar className={`h-8 w-8 flex-shrink-0 ${message.role === 'user' ? 'ml-3' : 'mr-3'}`}>
                  <AvatarFallback className={message.role === 'user' 
                    ? 'bg-muted text-muted-foreground' 
                    : 'bg-primary/10 text-primary'}>
                    {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </AvatarFallback>
                </Avatar>

                {/* Message Content */}
                <div className={`space-y-2 max-w-[80%]`}>
                  <div className={`p-3 rounded-2xl text-sm ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-tr-none'
                      : 'bg-muted/50 text-foreground rounded-tl-none'
                  }`}>
                    {/* Render chunks if available (assistant responses) */}
                    {message.isStreaming ? (
                      // Streaming message - accumulate text chunks and render others separately
                      <div className="space-y-2">
                        {(() => {
                          const textChunks = message.streamingChunks?.filter(c => c.type === 'text') || [];
                          const otherChunks = message.streamingChunks?.filter(c => c.type !== 'text') || [];
                          
                          return (
                            <>
                              {/* Render accumulated text as single paragraph */}
                              {textChunks.length > 0 && (
                                <StreamingTextRenderer 
                                  chunks={textChunks} 
                                  isStreaming={true} 
                                />
                              )}
                              
                              {/* Render other chunk types (code, reasoning, etc.) */}
                              {otherChunks.map((chunk, chunkIdx) => (
                                <ChunkRenderer 
                                  key={`other-${chunkIdx}`} 
                                  chunk={chunk} 
                                  isStreaming={false} 
                                />
                              ))}
                              
                              {/* Show typing animation if no chunks yet */}
                              {(!message.streamingChunks || message.streamingChunks.length === 0) && (
                                <div className="flex items-center space-x-2">
                                  <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                  </div>
                                  <span className="text-sm text-muted-foreground">Thinking...</span>
                                </div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    ) : message.chunks && message.chunks.length > 0 ? (
                      // Completed message - show all chunks
                      <div className="space-y-2">
                        {message.chunks.map((chunk, chunkIdx) => (
                          <ChunkRenderer key={chunkIdx} chunk={chunk} isStreaming={false} />
                        ))}
                      </div>
                    ) : (
                      <span className="whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: parseMarkdown(message.content) }} />
                    )}
                  </div>

                  {/* Action Buttons */}
                  {message.actions && message.actions.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {message.actions.map((action, idx) => (
                        <Button
                          key={idx}
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs bg-background hover:bg-accent hover:text-accent-foreground border-primary/20 text-primary"
                          onClick={() => {
                            if (action.view) {
                              onNavigate(action.view);
                            } else if (action.onClick) {
                              action.onClick();
                            }
                          }}
                        >
                          {action.label}
                          <ArrowRight className="ml-1 h-3 w-3" />
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading Indicator - only show when not streaming */}
            {isLoading && !messages.some(message => message.isStreaming) && (
              <div className="flex items-start">
                <Avatar className="h-8 w-8 mr-3 bg-primary/10">
                  <AvatarFallback className="bg-primary/10 text-primary">
                    <Bot size={16} />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-muted/50 p-3 rounded-2xl rounded-tl-none">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t bg-background/50 backdrop-blur-sm">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me to show patients, build cohorts, or analyze data..."
              disabled={isLoading}
              className="flex-1"
              autoFocus
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="bg-[#00a2dd] hover:bg-[#0081b0]"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          <div className="mt-3 flex justify-center space-x-6 text-xs text-muted-foreground px-2">
            <span className="flex items-center"><Activity className="h-3 w-3 mr-1.5" /> Clinical Data</span>
            <span className="flex items-center"><Users className="h-3 w-3 mr-1.5" /> Cohorts</span>
            <span className="flex items-center"><BarChart3 className="h-3 w-3 mr-1.5" /> Analytics</span>
          </div>
        </div>
      </Card>
    </div>
  );
}

// Export ChatInterface as an alias to WelcomeScreen for compatibility
export function ChatInterface() {
  const appContext = useApp();
  
  const handleNavigate = (view: string) => {
    if (appContext?.navigateToView) {
      appContext.navigateToView(view as any);
    }
  };
  
  return <WelcomeScreen onNavigate={handleNavigate} />;
}
