import { useState, useRef, useEffect } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Send, Loader2, Bot, User, Sparkles, ArrowRight, Activity, Users, BarChart3 } from "lucide-react";
import { sendChatMessage } from "../api/chat";
import { useApp } from "../context/AppContext";

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  actions?: { label: string; view?: string; onClick?: () => void }[];
  error?: boolean;
  data?: any;
}

interface WelcomeScreenProps {
  onNavigate: (view: string) => void;
  patientData?: any;
}

export function WelcomeScreen({ onNavigate, patientData }: WelcomeScreenProps) {
  const appContext = useApp();
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
      // Try real API call first
      const response = await sendChatMessage(
        currentInput,
        messages.map(m => ({ role: m.role, content: m.content }))
      );

      if (response.success && response.data?.content) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.content,
          timestamp: new Date(),
          actions: generateResponse(response.data.content).actions,
          data: response.data
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Handle navigation if response contains view directive
        if (response.data.action === 'navigate' && response.data.view) {
          setTimeout(() => {
            if (appContext?.navigateToView) {
              appContext.navigateToView(response.data!.view as any);
            } else if (response.data?.view) {
              onNavigate(response.data.view);
            }
          }, 1000);
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.warn('API call failed, falling back to local response:', error);
      
      // Fallback to local response generation
      const fallbackResponse = generateResponse(currentInput);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: fallbackResponse.content,
        timestamp: new Date(),
        actions: fallbackResponse.actions
      };

      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
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
                    <p className="whitespace-pre-wrap">{message.content}</p>
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

            {/* Loading Indicator */}
            {isLoading && (
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
