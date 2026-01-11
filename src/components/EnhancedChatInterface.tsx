/**
 * Redesigned ChatInterface - Modern, Minimalist Design
 * Features: Split view, card-based layout, enhanced interactions
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Avatar } from "./ui/avatar";
import { Textarea } from "./ui/textarea";
import { 
  Send, 
  Loader2, 
  Bot, 
  User,
  Users,
  Sparkles, 
  Database, 
  Search,
  Filter,
  BarChart3,
  CheckCircle2,
  Clock,
  Zap,
  Trash2,
  Copy,
  AlertCircle,
  Download,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  MessageSquare,
  TrendingUp,
  Activity,
  Plus,
  MoreVertical,
  Star,
  Share2
} from "lucide-react";
import { sendChatMessage } from "../api/chat";
import { useApp } from "../context/AppContext";

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  data?: any;
  reasoning?: ReasoningStep[];
  error?: string;
  feedback?: 'positive' | 'negative';
  starred?: boolean;
}

interface ReasoningStep {
  id: string;
  type: 'thinking' | 'tool_call' | 'database' | 'analysis' | 'complete';
  tool?: string;
  description: string;
  result?: string;
  timestamp: Date;
}

const QUICK_ACTIONS = [
  { icon: Users, label: "Patient Stats", query: "Show patient statistics", color: "from-blue-500 to-cyan-500" },
  { icon: TrendingUp, label: "Trends", query: "Show health trends", color: "from-purple-500 to-pink-500" },
  { icon: Activity, label: "Analytics", query: "Show analytics dashboard", color: "from-green-500 to-emerald-500" },
  { icon: Search, label: "Advanced Search", query: "Help me search patients", color: "from-orange-500 to-red-500" },
];

const STARTER_PROMPTS = [
  "How many patients have diabetes?",
  "Show males over 60 with hypertension",
  "What's the average age in the registry?",
  "Create a cohort for cardiovascular research",
];

function LoadingDots() {
  return (
    <div className="flex space-x-1.5 py-2">
      <div className="h-2.5 w-2.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="h-2.5 w-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="h-2.5 w-2.5 bg-gradient-to-r from-pink-500 to-red-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  );
}

export function ChatInterface() {
  const appContext = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentReasoning, setCurrentReasoning] = useState<ReasoningStep[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showStarters, setShowStarters] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentReasoning]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const addReasoningStep = useCallback((step: Omit<ReasoningStep, 'id' | 'timestamp'>) => {
    setCurrentReasoning(prev => [...prev, {
      ...step,
      id: Date.now().toString(),
      timestamp: new Date()
    }]);
  }, []);

  const copyToClipboard = (text: string, messageId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(messageId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearMessages = () => {
    if (window.confirm('Clear all messages?')) {
      setMessages([]);
      setCurrentReasoning([]);
      setShowStarters(true);
    }
  };

  const exportConversation = () => {
    const conversationText = messages
      .map(m => `[${m.role.toUpperCase()}] ${m.timestamp.toLocaleString()}\n${m.content}\n`)
      .join('\n---\n\n');
    
    const blob = new Blob([conversationText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `biolink-chat-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFeedback = (messageId: string, feedback: 'positive' | 'negative') => {
    setMessages(prev => prev.map(m => 
      m.id === messageId ? { ...m, feedback } : m
    ));
  };

  const toggleStar = (messageId: string) => {
    setMessages(prev => prev.map(m => 
      m.id === messageId ? { ...m, starred: !m.starred } : m
    ));
  };

  const handleQuickAction = (query: string) => {
    setInput(query);
    setShowStarters(false);
    setTimeout(() => handleSendMessage(), 100);
  };

  const handleStarterClick = (prompt: string) => {
    setInput(prompt);
    setShowStarters(false);
    inputRef.current?.focus();
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    setShowStarters(false);
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
    setCurrentReasoning([]);

    try {
      addReasoningStep({
        type: 'thinking',
        description: 'Processing your request...'
      });

      await new Promise(resolve => setTimeout(resolve, 400));

      addReasoningStep({
        type: 'database',
        description: 'Querying patient database...'
      });

      await new Promise(resolve => setTimeout(resolve, 300));

      const response = await sendChatMessage(
        currentInput,
        messages.map(m => ({ role: m.role, content: m.content }))
      );

      if (response.success && response.data?.content) {
        addReasoningStep({
          type: 'complete',
          description: 'Response ready',
          result: 'Done'
        });

        await new Promise(resolve => setTimeout(resolve, 300));

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.content,
          timestamp: new Date(),
          data: response.data,
          reasoning: [...currentReasoning]
        };

        setMessages(prev => [...prev, assistantMessage]);
        setCurrentReasoning([]);

        if (response.data.action === 'navigate' && response.data.view) {
          setTimeout(() => {
            appContext.navigateToView(response.data!.view as any);
          }, 1000);
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setCurrentReasoning([]);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Unable to process request. Please check:\n• Backend server is running\n• Database connection is active\n• Try a simpler query',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        setUseLineBreaks(true);
      } else {
        e.preventDefault();
        handleSendMessage();
      }
    }
  };

  const getReasoningIcon = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'thinking': return <Sparkles className="h-3 w-3" />;
      case 'tool_call': return <Zap className="h-3 w-3" />;
      case 'database': return <Database className="h-3 w-3" />;
      case 'analysis': return <BarChart3 className="h-3 w-3" />;
      case 'complete': return <CheckCircle2 className="h-3 w-3" />;
      default: return <Clock className="h-3 w-3" />;
    }
  };

  const getReasoningColor = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'thinking': return 'text-purple-500';
      case 'tool_call': return 'text-blue-500';
      case 'database': return 'text-green-500';
      case 'analysis': return 'text-orange-500';
      case 'complete': return 'text-emerald-500';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Compact Header */}
      <div className="flex-shrink-0 border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 flex items-center justify-center shadow-lg">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full border-2 border-white dark:border-slate-900 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 dark:text-white">BioLink AI</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">669 patients • Real-time insights</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="gap-2" onClick={exportConversation}>
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Export</span>
            </Button>
            <Button variant="ghost" size="sm" className="gap-2" onClick={clearMessages}>
              <Trash2 className="h-4 w-4" />
              <span className="hidden sm:inline">Clear</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col max-w-6xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto px-6 py-8">
          {/* Empty State / Welcome */}
          {messages.length === 0 && showStarters && (
            <div className="h-full flex flex-col items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="text-center mb-12 max-w-2xl">
                <div className="inline-flex items-center justify-center h-20 w-20 rounded-3xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 mb-6 shadow-2xl">
                  <Bot className="h-10 w-10 text-white" />
                </div>
                <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
                  Welcome to BioLink AI
                </h2>
                <p className="text-lg text-slate-600 dark:text-slate-300 mb-8">
                  Your intelligent assistant for cardiovascular research data
                </p>
                
                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-3 mb-8">
                  {QUICK_ACTIONS.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuickAction(action.query)}
                      className="group relative overflow-hidden rounded-2xl p-6 text-left border-2 border-slate-200 dark:border-slate-700 hover:border-transparent transition-all duration-300 bg-white dark:bg-slate-800 hover:shadow-2xl hover:scale-105"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                      <action.icon className={`h-8 w-8 mb-3 bg-gradient-to-br ${action.color} bg-clip-text text-transparent`} />
                      <div className="text-sm font-semibold text-slate-900 dark:text-white">{action.label}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">{action.query}</div>
                    </button>
                  ))}
                </div>

                {/* Starter Prompts */}
                <div className="space-y-2">
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">Or try these:</p>
                  {STARTER_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleStarterClick(prompt)}
                      className="block w-full text-left px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-sm text-slate-700 dark:text-slate-200 transition-all duration-200 border border-transparent hover:border-blue-500 dark:hover:border-blue-400"
                    >
                      "{prompt}"
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.map((message, idx) => (
              <div
                key={message.id}
                className={`animate-in fade-in slide-in-from-bottom-3 duration-500 ${
                  message.role === 'user' ? 'flex justify-end' : 'flex justify-start'
                }`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                {message.role === 'user' ? (
                  <div className="flex items-start gap-3 max-w-[80%]">
                    <div className="flex-1 rounded-2xl rounded-tr-md bg-gradient-to-br from-blue-600 to-purple-600 px-5 py-4 shadow-lg">
                      <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      <div className="flex items-center gap-2 mt-3 text-xs text-blue-100">
                        <Clock className="h-3 w-3" />
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                    <Avatar className="h-10 w-10 ring-2 ring-blue-500/20">
                      <div className="h-full w-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                        <User className="h-5 w-5 text-white" />
                      </div>
                    </Avatar>
                  </div>
                ) : (
                  <div className="flex items-start gap-3 max-w-[85%]">
                    <Avatar className="h-10 w-10 ring-2 ring-purple-500/20">
                      <div className="h-full w-full bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                    </Avatar>
                    <div className="flex-1 space-y-2">
                      {/* Reasoning Steps */}
                      {message.reasoning && message.reasoning.length > 0 && (
                        <div className="space-y-1 mb-3">
                          {message.reasoning.map((step) => (
                            <div
                              key={step.id}
                              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs"
                            >
                              <span className={getReasoningColor(step.type)}>
                                {getReasoningIcon(step.type)}
                              </span>
                              <span className="flex-1 text-slate-600 dark:text-slate-300">{step.description}</span>
                              {step.result && (
                                <CheckCircle2 className="h-3 w-3 text-green-500" />
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Message Content */}
                      <div className="rounded-2xl rounded-tl-md bg-white dark:bg-slate-800 px-5 py-4 shadow-lg border border-slate-200 dark:border-slate-700">
                        {message.error ? (
                          <div className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400">
                            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <span>{message.content}</span>
                          </div>
                        ) : (
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            {message.content.split('\n').map((line, i) => (
                              <p key={i} className="text-slate-700 dark:text-slate-200 leading-relaxed my-2">
                                {line || '\u00A0'}
                              </p>
                            ))}
                          </div>
                        )}
                        
                        {/* Message Actions */}
                        <div className="flex items-center gap-1 mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={() => copyToClipboard(message.content, message.id)}
                          >
                            {copiedId === message.id ? (
                              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                            ) : (
                              <Copy className="h-3.5 w-3.5" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 px-2 ${message.feedback === 'positive' ? 'text-green-600' : ''}`}
                            onClick={() => handleFeedback(message.id, 'positive')}
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 px-2 ${message.feedback === 'negative' ? 'text-red-600' : ''}`}
                            onClick={() => handleFeedback(message.id, 'negative')}
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 px-2 ${message.starred ? 'text-yellow-500' : ''}`}
                            onClick={() => toggleStar(message.id)}
                          >
                            <Star className={`h-3.5 w-3.5 ${message.starred ? 'fill-current' : ''}`} />
                          </Button>
                          <div className="flex-1" />
                          <span className="text-xs text-slate-400">
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Loading State */}
            {isLoading && (
              <div className="flex items-start gap-3 animate-in fade-in">
                <Avatar className="h-10 w-10 ring-2 ring-purple-500/20">
                  <div className="h-full w-full bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white animate-pulse" />
                  </div>
                </Avatar>
                <div className="rounded-2xl rounded-tl-md bg-white dark:bg-slate-800 px-5 py-3 shadow-lg border border-slate-200 dark:border-slate-700">
                  {currentReasoning.length > 0 ? (
                    <div className="space-y-2">
                      {currentReasoning.map((step) => (
                        <div key={step.id} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                          <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
                          <span>{step.description}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <LoadingDots />
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="flex-shrink-0 border-t bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <Textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask anything about your patients..."
                  disabled={isLoading}
                  className="min-h-[56px] max-h-[200px] resize-none rounded-2xl border-2 border-slate-200 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-400 bg-white dark:bg-slate-800 px-4 py-3 pr-12 text-sm shadow-lg"
                  autoFocus
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !input.trim()}
                  size="icon"
                  className="absolute right-2 bottom-2 h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg disabled:opacity-50"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 text-center">
              Press Enter to send • Shift+Enter for new line • {messages.length} messages
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
