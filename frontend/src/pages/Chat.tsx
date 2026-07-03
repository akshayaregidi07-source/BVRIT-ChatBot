import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import {
  Sparkles, Send, Paperclip, Mic, Bot, User, FileText, MessageSquare,
  Settings, Sliders, BarChart3, Clock, Database, X,
  GraduationCap, Briefcase, Building2, IndianRupee, Award, Users, Hotel, Phone, Wifi,
  ChevronDown, ChevronUp, Search, AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChatMessage, RetrievedDoc } from '@/types';
import { knowledgeBase, sessionStats, retrievedDocs, suggestionCards, placeholderMessages } from '@/lib/data';

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

function CitationCard({ citation }: { citation: { source: string; page: number; confidence: number } }) {
  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'text-success border-success/30 bg-success/10';
    if (score >= 70) return 'text-warning border-warning/30 bg-warning/10';
    return 'text-error border-error/30 bg-error/10';
  };

  return (
    <div className="mt-3 rounded-xl border border-border-glass bg-card/50 p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-white">{citation.source}</span>
        </div>
        <span className={cn('rounded-lg border px-2 py-0.5 text-xs font-medium', getConfidenceColor(citation.confidence))}>
          {citation.confidence}%
        </span>
      </div>
      <div className="mt-1 flex items-center gap-2 text-xs text-text-secondary">
        <span>Page {citation.page}</span>
        <span>•</span>
        <span>Retrieved from Knowledge Base</span>
      </div>
    </div>
  );
}

function RetrievedDocCard({ doc }: { doc: RetrievedDoc }) {
  const progressColor = doc.similarity >= 0.9 ? 'bg-success' : doc.similarity >= 0.7 ? 'bg-warning' : 'bg-primary';
  return (
    <div className="rounded-xl border border-border-glass bg-card/50 p-3 transition-all hover:bg-card/80">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-white">{doc.title}</span>
        <span className="text-xs text-text-secondary">{Math.round(doc.similarity * 100)}%</span>
      </div>
      <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-background">
        <div
          className={cn('h-full rounded-full transition-all duration-1000', progressColor)}
          style={{ width: `${doc.similarity * 100}%` }}
        />
      </div>
      <p className="text-xs text-text-secondary line-clamp-2">{doc.preview}</p>
    </div>
  );
}

export default function Chat() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [stats, setStats] = useState(sessionStats);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const queryParam = searchParams.get('q');

  useEffect(() => {
    if (queryParam) {
      const key = queryParam.toLowerCase();
      const response = placeholderMessages[key]?.[0];
      if (response) {
        setMessages([
          { id: generateId(), role: 'user', content: suggestionCards.find(s => s.label.toLowerCase() === key)?.query || `Tell me about ${key}`, timestamp: new Date() },
          { ...response, id: generateId(), timestamp: new Date() },
        ]);
        setStats(prev => ({ ...prev, questionsAsked: prev.questionsAsked + 1 }));
      }
    }
  }, [queryParam]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { id: generateId(), role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setStats(prev => ({ ...prev, questionsAsked: prev.questionsAsked + 1 }));

    setTimeout(() => {
      const lower = input.toLowerCase();
      let response = placeholderMessages.admissions[0];
      if (lower.includes('placement') || lower.includes('package')) response = placeholderMessages.placements[0];
      else if (lower.includes('department') || lower.includes('cse')) response = placeholderMessages.departments[0];
      else if (lower.includes('image') || lower.includes('campus') || lower.includes('photo') || lower.includes('facilities')) {
        response = {
          id: generateId(), role: 'assistant',
          content: 'BVRIT Hyderabad campus features modern infrastructure with state-of-the-art facilities. Here are some images from the campus.',
          timestamp: new Date(),
          citations: [{ source: 'Campus Facilities', page: 4, confidence: 92 }],
        };
      } else {
        response = {
          id: generateId(), role: 'assistant',
          content: "I'm sorry, but I don't have enough information in my knowledge base to answer this question. Please contact the college administration for more details.",
          timestamp: new Date(),
          citations: [],
        };
      }
      setIsTyping(false);
      setMessages(prev => [...prev, { ...response, id: generateId(), timestamp: new Date() }]);
    }, 2000);
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
                  <div className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-success/30 bg-success/10 px-2.5 py-1 text-xs text-success">
                    <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                    Indexed
                  </div>
                </div>
              </div>

              {/* Retrieval Settings */}
              <div className="rounded-xl border border-border-glass bg-card/50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Settings className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-white">Retrieval Settings</h3>
                </div>
                <div className="space-y-3">
                  {[
                    { label: 'Chunk Size', value: '500' },
                    { label: 'Chunk Overlap', value: '100' },
                    { label: 'Top K', value: '4' },
                  ].map(item => (
                    <div key={item.label}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="text-text-secondary">{item.label}</span>
                        <span className="text-white">{item.value}</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-background">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: item.label === 'Chunk Size' ? '70%' : item.label === 'Chunk Overlap' ? '30%' : '40%' }}
                        />
                      </div>
                    </div>
                  ))}
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
                    { label: 'Avg Response Time', value: `${stats.avgResponseTime}s`, icon: Clock },
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
        {/* Toggle Sidebar Buttons */}
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
            <Search className="h-3.5 w-3.5" />
            Docs
          </button>
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
                <h2 className="mb-2 text-2xl font-bold text-white">Welcome to BVRIT College FAQ Assistant</h2>
                <p className="mb-8 text-text-secondary">Ask me anything about admissions, placements, faculty, fees, and campus facilities.</p>
                
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {suggestionCards.map((card, i) => {
                    const Icon = iconMap[card.icon] || Sparkles;
                    return (
                      <motion.button
                        key={card.label}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => {
                          setMessages([{ id: generateId(), role: 'user', content: card.query, timestamp: new Date() }]);
                          setIsTyping(true);
                          setStats(prev => ({ ...prev, questionsAsked: prev.questionsAsked + 1 }));
                          setTimeout(() => {
                            const key = card.label.toLowerCase();
                            const resp = placeholderMessages[key === 'fee structure' ? 'admissions' : key]?.[0] || placeholderMessages.admissions[0];
                            setIsTyping(false);
                            setMessages(prev => [...prev, { ...resp, id: generateId(), timestamp: new Date() }]);
                          }, 2000);
                        }}
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
                        <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        
                        {/* Citations */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-3 space-y-2">
                            {msg.citations.map((cit, i) => (
                              <CitationCard key={i} citation={cit} />
                            ))}
                          </div>
                        )}
                        
                        <div className="mt-2 flex items-center gap-2 text-xs text-text-muted">
                          <Clock className="h-3 w-3" />
                          {msg.timestamp.toLocaleTimeString()}
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
              <button className="flex h-8 w-8 items-center justify-center rounded-lg text-text-secondary hover:text-white transition-colors">
                <Paperclip className="h-4 w-4" />
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything about BVRIT..."
                className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-text-muted"
              />
              <button className="flex h-8 w-8 items-center justify-center rounded-lg text-text-secondary hover:text-white transition-colors">
                <Mic className="h-4 w-4" />
              </button>
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
              Responses are generated using Retrieval-Augmented Generation
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
                <Search className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-white">Retrieved Documents</h3>
              </div>
              {messages.length > 0 ? (
                <div className="space-y-3">
                  {retrievedDocs.map((doc, i) => (
                    <motion.div
                      key={doc.title}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <RetrievedDocCard doc={doc} />
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 py-12 text-text-muted">
                  <Search className="h-8 w-8" />
                  <p className="text-sm">Ask a question to see retrieved documents</p>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}

