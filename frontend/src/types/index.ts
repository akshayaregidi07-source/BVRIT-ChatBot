export interface NavLink {
  label: string;
  path: string;
  icon: string;
}

export interface TopicChip {
  label: string;
  icon: string;
  color: string;
}

export interface SuggestionCard {
  label: string;
  icon: string;
  query: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
}

export interface Citation {
  source: string;
  page: number;
  confidence: number;
}

export interface RetrievedDoc {
  title: string;
  similarity: number;
  preview: string;
}

export interface EvaluationMetric {
  label: string;
  score: number;
  maxScore: number;
  status: 'pass' | 'fail' | 'warning';
}

export interface RAGASMetric {
  label: string;
  score: number;
  percentage: number;
}

export interface SessionStats {
  questionsAsked: number;
  avgResponseTime: number;
  tokensUsed: number;
}

export interface KnowledgeBaseInfo {
  filename: string;
  pages: number;
  chunks: number;
  indexed: boolean;
}