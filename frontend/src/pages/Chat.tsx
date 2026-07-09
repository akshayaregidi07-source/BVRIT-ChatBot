import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import {
  Sparkles, Send, Bot, User, FileText, MessageSquare,
  Settings, Sliders, BarChart3, Clock, Database,
  GraduationCap, Briefcase, Building2, IndianRupee, Award, Users, Hotel, Phone, Wifi,
  Calculator, CalendarDays, Percent, AlertTriangle, CheckCircle2, XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChatMessage, RetrievedDoc } from '@/types';
import { knowledgeBase, sessionStats, suggestionCards } from '@/lib/data';

// Use '/api' prefix — Vite proxies this to the backend on port 8000
const API_URL = '/api';

const iconMap: Record<string, React.ElementType> = {
  GraduationCap, Briefcase, Building2, IndianRupee,
  Award, Users, Hotel, Phone, Wifi,
};

function generateId() {
  return Math.random().toString(36).substring(2, 11);
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-2">
      <div className="typing-dot h-2 w-2 rounded-full bg-primary" />
      <div className="typing-dot h-2 w-2 rounded-full bg-primary" />
      <div className="typing-dot h-2 w-2 rounded-full bg-primary" />
    </div>
  );
}

function ToolBadge({ toolName }: { toolName: string }) {
  const toolConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    fee_calculator: { icon: Calculator, label: 'Fee Calculator', color: 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10' },
    date_checker: { icon: CalendarDays, label: 'Date Checker', color: 'text-blue-400 border-blue-400/30 bg-blue-400/10' },
    percentage_calculator: { icon: Percent, label: 'Percentage Calculator', color: 'text-green-400 border-green-400/30 bg-green-400/10' },
  };
  const config = toolConfig[toolName];
  if (!config) return null;
  const Icon = config.icon;
  return (
    <div className={cn('mt-2 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium', config.color)}>
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </div>
  );
}

function CitationCard({ citation }: { citation: { source: string; page: number; confidence: number } }) {
  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'text-green-400 border-green-400/30 bg-green-400/10';
    if (score >= 70) return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10';
    return 'text-red-400 border-red-400/30 bg-red-400/10';
  };

  return (
    <div className="mt-2 rounded-xl border border-border-glass bg-card/50 p-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-3.5 w-3.5 text-primary" />
          <span className="text-xs font-medium text-white">{citation.source}</span>
        </div>
        <span className={cn('rounded-lg border px-2 py-0.5 text-xs font-medium', getConfidenceColor(citation.confidence))}>
          {citation.confidence}%
        </span>
      </div>
      <div className="mt-0.5 flex items-center gap-2 text-xs text-text-secondary">
        <span>Page {citation.page}</span>
        <span>•</span>
        <span>Retrieved from Knowledge Base</span>
      </div>
    </div>
  );
}

function RoutingBadge({ routing }: { routing: string }) {
  if (!routing) return null;
  const config: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    rag: { icon: Database, label: 'RAG (Document Retrieval)', color: 'text-purple-400 border-purple-400/30 bg-purple-400/10' },
    conversation: { icon: MessageSquare, label: 'Conversation', color: 'text-gray-400 border-gray-400/30 bg-gray-400/10' },
  };
  if (routing.startsWith('tool:')) {
    const toolName = routing.replace('tool:', '');
    const toolConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
      fee_calculator: { icon: Calculator, label: 'Fee Calculator', color: 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10' },
      date_checker: { icon: CalendarDays, label: 'Date Checker', color: 'text-blue-400 border-blue-400/30 bg-blue-400/10' },
      percentage_calculator: { icon: Percent, label: 'Percentage Calculator', color: 'text-green-400 border-green-400/30 bg-green-400/10' },
    };
    const tc = toolConfig[toolName];
    if (tc) {
      const Icon = tc.icon;
      return (
        <div className={cn('mt-2 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium', tc.color)}>
          <Icon className="h-3.5 w-3.5" />
          {tc.label}
        </div>
      );
    }
  }
  const c = config[routing];
  if (c) {
    const Icon = c.icon;
    return (
      <div className={cn('mt-2 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium', c.color)}>
        <Icon className="h-3.5 w-3.5" />
        {c.label}
      </div>
    );
  }
  return null;
}

export default function Chat() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [stats, setStats] = useState(sessionStats);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const queryParam = searchParams.get('q');

  // Check if API is available
  useEffect(() => {
    fetch(`${API_URL}/`)
      .then(res => res.json())
      .then(() => setApiAvailable(true))
      .catch(() => setApiAvailable(false));
  }, []);

  useEffect(() => {
    if (queryParam) {
      const key = queryParam.toLowerCase();
      const suggestion = suggestionCards.find(s => s.label.toLowerCase() === key);
      if (suggestion) {
        handleRealQuery(suggestion.query);
      }
    }
  }, [queryParam]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleRealQuery = async (queryText: string) => {
    const userMsg: ChatMessage = { id: generateId(), role: 'user', content: queryText, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setStats(prev => ({ ...prev, questionsAsked: prev.questionsAsked + 1 }));

    try {
      const startTime = Date.now();
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText }),
      });
      const data = await response.json();
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer || 'No response generated.',
        timestamp: new Date(),
        citations: data.citations || [],
        routing: data.routing,
        tool_called: data.tool_called || undefined,
        tool_arguments: data.tool_arguments || undefined,
        tool_result: data.tool_result || undefined,
      };

      setIsTyping(false);
      setMessages(prev => [...prev, assistantMsg]);
      setStats(prev => ({
        ...prev,
        avgResponseTime: parseFloat(elapsed),
        tokensUsed: prev.tokensUsed + 150,
      }));
      setApiAvailable(true);
    } catch (err) {
      setIsTyping(false);
      setApiAvailable(false);
      const errorMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: "⚠️ Could not connect to the backend API. Make sure the API server is running (`python api_server.py`). Falling back to offline mode.",
        timestamp: new Date(),
        routing: 'error',
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    handleRealQuery(input.trim());
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left Sidebar */}
      <AnimatePresence>
        {showLeftSidebar && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 300, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="hidden border-r border-border-glass bg-card/30 lg:block overflow-y-auto flex-shrink-0"
          >
            <div className="p-4 space-y-4">
              {/* API Status */}
              <div className="rounded-xl border border-border-glass bg-card/50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-white">API Status</h3>
                </div>
                {apiAvailable === null ? (
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <div className="h-2 w-2 rounded-full bg-yellow-400 animate-pulse" />
                    Checking...
                  </div>
                ) : apiAvailable ? (
                  <div className="flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Connected
                    <span className="text-text-secondary ml-1">(port 8000)</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <XCircle className="h-3.5 w-3.5" />
                    Offline
                  </div>
                )}
              </div>

              {/* Knowledge Base */}
              <div className="rounded-xl border border-border-glass bg-card/50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-white">Knowledge Base</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">File</span>
                    <span className="text-white truncate ml-2">{knowledgeBase.filename}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">Pages</span>
                    <span className="text-white">{knowledgeBase.pages}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">Chunks</span>
                    <span className="text-white">{knowledgeBase.chunks}</span>
                  </div>
                  <div className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-green-400/30 bg-green-400/10 px-2.5 py-1 text-xs text-green-400">
                    <div className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                    Indexed
                  </div>
                </div>
              </div>

              {/* Available Tools */}
              <div className="rounded-xl border border-border-glass bg-card/50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Settings className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-white">Available Tools</h3>
                </div>
                <div className="space-y-2">
                  {[
                    { name: 'Fee Calculator', icon: Calculator, desc: 'Compute fees, scholarships, combined costs', color: 'text-yellow-400' },
                    { name: 'Date Checker', icon: CalendarDays, desc: 'Check deadlines, days remaining', color: 'text-blue-400' },
                    { name: 'Percentage Calc', icon: Percent, desc: 'Scholarship %, placement rates', color: 'text-green-400' },
                  ].map(tool => {
                    const Icon = tool.icon;
                    return (
                      <div key={tool.name} className="flex items-center gap-2.5 rounded-lg bg-background/50 p-2.5">
                        <div className={cn('flex h-7 w-7 items-center justify-center rounded-lg bg-opacity-10', tool.color.replace('text', 'bg') + '/10')}>
                          <Icon className={cn('h-3.5 w-3.5', tool.color)} />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-white">{tool.name}</p>
                          <p className="text-xs text-text-secondary">{tool.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session Stats */}
              <div className="rounded-xl border border-border-glass bg-card/50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-white">Session Statistics</h3>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {[
                    { label: 'Questions Asked', value: stats.questionsAsked, icon: MessageSquare },
                    { label: 'Response Time', value: `${stats.avgResponseTime}s`, icon: Clock },
                    { label: 'Tokens Used', value: stats.tokensUsed.toLocaleString(), icon: Sliders },
                  ].map(stat => {
                    const StatIcon = stat.icon;
                    return (
                      <div key={stat.label} className="flex items-center gap-3 rounded-lg bg-background/50 p-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                          <StatIcon className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="text-xs text-text-secondary">{stat.label}</p>
                          <p className="text-sm font-semibold text-white">{stat.value}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Center Chat */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Toggle Sidebar Buttons + API Status Bar */}
        <div className="flex items-center gap-2 border-b border-border-glass px-4 py-2">
          <button
            onClick={() => setShowLeftSidebar(!showLeftSidebar)}
            className={cn(
              'flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition-all',
              showLeftSidebar
                ? 'border-primary/30 text-primary bg-primary/10'
                : 'border-border-glass text-text-secondary hover:text-white'
            )}
          >
            <Database className="h-3.5 w-3.5" />
            KB
          </button>
          <button
            onClick={() => setShowRightSidebar(!showRightSidebar)}
            className={cn(
              'flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition-all',
              showRightSidebar
                ? 'border-primary/30 text-primary bg-primary/10'
                : 'border-border-glass text-text-secondary hover:text-white'
            )}
          >
            <FileText className="h-3.5 w-3.5" />
            Docs
          </button>
          <div className="flex-1" />
          {apiAvailable === false && (
            <div className="flex items-center gap-1.5 rounded-lg border border-red-400/30 bg-red-400/10 px-2.5 py-1 text-xs text-red-400">
              <AlertTriangle className="h-3 w-3" />
              API Offline — run `python api_server.py`
            </div>
          )}
          {apiAvailable === true && (
            <div className="flex items-center gap-1.5 rounded-lg border border-green-400/30 bg-green-400/10 px-2.5 py-1 text-xs text-green-400">
              <CheckCircle2 className="h-3 w-3" />
              Tools Active
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 ? (
            /* Welcome Screen */
            <div className="flex h-full items-center justify-center">
              <div className="max-w-lg text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                  className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-blue-600/20 border border-primary/20"
                >
                  <Bot className="h-10 w-10 text-primary" />
                </motion.div>
                <h2 className="mb-2 text-2xl font-bold text-white">BVRIT Tool-Enabled Chatbot</h2>
                <p className="mb-2 text-text-secondary">Ask questions about admissions, placements, fees, departments, and more.</p>
                <p className="mb-6 text-xs text-text-muted">The AI can use <span className="text-yellow-400">Fee Calculator</span>, <span className="text-blue-400">Date Checker</span>, and <span className="text-green-400">Percentage Calculator</span> tools.</p>
                
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {suggestionCards.map((card, i) => {
                    const Icon = iconMap[card.icon] || Sparkles;
                    return (
                      <motion.button
                        key={card.label}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => handleRealQuery(card.query)}
                        className="glass glass-hover flex flex-col items-center gap-1.5 rounded-xl p-3 text-xs font-medium text-text-secondary"
                      >
                        {Icon && <Icon className="h-5 w-5 text-primary" />}
                        {card.label}
                      </motion.button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Messages */
            <div className="mx-auto max-w-3xl space-y-4">
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-blue-600">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  
                  <div className={cn('max-w-[80%]', msg.role === 'user' && 'order-first')}>
                    {msg.role === 'user' ? (
                      <div className="rounded-2xl bg-primary px-4 py-2.5 text-sm text-white">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-border-glass bg-card/50 p-4">
                        {/* Routing Badge */}
                        <RoutingBadge routing={msg.routing || ''} />
                        
                        {/* Tool Called Badge */}
                        {msg.tool_called && (
                          <ToolBadge toolName={msg.tool_called} />
                        )}
                        
                        {/* Tool Arguments (collapsible) */}
                        {msg.tool_arguments && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-xs text-text-secondary hover:text-white">
                              Tool Arguments
                            </summary>
                            <pre className="mt-1 rounded-lg bg-background/50 p-2 text-xs text-text-secondary overflow-x-auto">
                              {msg.tool_arguments}
                            </pre>
                          </details>
                        )}
                        
                        {/* Main Answer */}
                        <p className="mt-2 text-sm text-white leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        
                        {/* Tool Result (if present and different from answer) */}
                        {msg.tool_result && !msg.content.includes(msg.tool_result) && (
                          <div className="mt-2 rounded-lg bg-background/50 p-2.5 border border-border-glass">
                            <p className="text-xs font-medium text-primary mb-1">Tool Result:</p>
                            <p className="text-xs text-white whitespace-pre-wrap">{msg.tool_result}</p>
                          </div>
                        )}
                        
                        {/* Citations */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-3 space-y-1.5">
                            {msg.citations.map((cit, i) => (
                              <CitationCard key={i} citation={cit} />
                            ))}
                          </div>
                        )}
                        
                        <div className="mt-2 flex items-center gap-2 text-xs text-text-muted">
                          <Clock className="h-3 w-3" />
                          {msg.timestamp.toLocaleTimeString()}
                          {msg.routing && (
                            <>
                              <span>•</span>
                              <span className="capitalize">{msg.routing.replace('tool:', 'Tool: ')}</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-card border border-border-glass">
                      <User className="h-4 w-4 text-text-secondary" />
                    </div>
                  )}
                </motion.div>
              ))}

              {isTyping && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-blue-600">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="rounded-2xl border border-border-glass bg-card/50 px-4 py-3">
                    <TypingIndicator />
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border-glass bg-card/30 p-4">
          <div className="mx-auto max-w-3xl">
            <div className="group flex items-center gap-2 rounded-2xl border border-border-glass bg-card/80 px-4 py-2 transition-all focus-within:border-primary/50 focus-within:shadow-glow">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything about BVRIT (fee calc, date checks, etc.)..."
                className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-text-muted"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-lg transition-all',
                  input.trim()
                    ? 'bg-primary text-white shadow-glow hover:bg-primary-dark'
                    : 'bg-card text-text-muted'
                )}
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-text-muted">
              Responses generated using RAG + Tool Calling (fee_calculator, date_checker, percentage_calculator)
            </p>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Retrieved Documents */}
      <AnimatePresence>
        {showRightSidebar && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="hidden border-l border-border-glass bg-card/30 xl:block overflow-y-auto flex-shrink-0"
          >
            <div className="p-4">
              <div className="mb-4 flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-white">Routing Info</h3>
              </div>
              {messages.length > 0 ? (
                <div className="space-y-3">
                  {messages.filter(m => m.role === 'assistant').slice(-3).reverse().map((msg, i) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="rounded-xl border border-border-glass bg-card/50 p-3"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {msg.routing?.startsWith('tool:') ? (
                          <Calculator className="h-3.5 w-3.5 text-yellow-400" />
                        ) : msg.routing === 'rag' ? (
                          <Database className="h-3.5 w-3.5 text-purple-400" />
                        ) : (
                          <MessageSquare className="h-3.5 w-3.5 text-gray-400" />
                        )}
                        <span className="text-xs font-medium text-white capitalize">
                          {msg.routing?.replace('tool:', 'Tool: ') || 'Response'}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary line-clamp-3">{msg.content}</p>
                      {msg.tool_called && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-yellow-400">
                          <Calculator className="h-3 w-3" />
                          {msg.tool_called}
                        </div>
                      )}
                    </motion.div>
                  ))}
                  <div className="rounded-xl border border-border-glass bg-card/50 p-3">
                    <h4 className="text-xs font-medium text-white mb-2">Response Routing Legend</h4>
                    <div className="space-y-1.5 text-xs">
                      <div className="flex items-center gap-2 text-purple-400">
                        <Database className="h-3 w-3" /> RAG — Document lookup
                      </div>
                      <div className="flex items-center gap-2 text-yellow-400">
                        <Calculator className="h-3 w-3" /> Tool — Fee calculation
                      </div>
                      <div className="flex items-center gap-2 text-blue-400">
                        <CalendarDays className="h-3 w-3" /> Tool — Date check
                      </div>
                      <div className="flex items-center gap-2 text-green-400">
                        <Percent className="h-3 w-3" /> Tool — Percentage
                      </div>
                      <div className="flex items-center gap-2 text-gray-400">
                        <MessageSquare className="h-3 w-3" /> Conversation
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 py-12 text-text-muted">
                  <FileText className="h-8 w-8" />
                  <p className="text-sm">Ask a question to see routing info</p>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}