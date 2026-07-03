import { TopicChip, SuggestionCard, ChatMessage, RetrievedDoc, KnowledgeBaseInfo, SessionStats } from '@/types';

export const topicChips: TopicChip[] = [
  { label: 'Admissions', icon: 'GraduationCap', color: '#3B82F6' },
  { label: 'Placements', icon: 'Briefcase', color: '#22C55E' },
  { label: 'Departments', icon: 'Building2', color: '#A855F7' },
  { label: 'Fees', icon: 'IndianRupee', color: '#F59E0B' },
  { label: 'Scholarships', icon: 'Award', color: '#EC4899' },
  { label: 'Faculty', icon: 'Users', color: '#06B6D4' },
  { label: 'Hostel', icon: 'Hotel', color: '#F97316' },
  { label: 'Contact', icon: 'Phone', color: '#10B981' },
];

export const suggestionCards: SuggestionCard[] = [
  { label: 'Admissions', icon: 'GraduationCap', query: 'What are the admission criteria for B.Tech programs?' },
  { label: 'Placements', icon: 'Briefcase', query: 'What is the highest placement package in 2026?' },
  { label: 'Departments', icon: 'Building2', query: 'What departments are offered at BVRIT?' },
  { label: 'Fee Structure', icon: 'IndianRupee', query: 'What are the B.Tech fees at BVRIT?' },
  { label: 'Campus Facilities', icon: 'Wifi', query: 'What facilities are available on campus?' },
  { label: 'Scholarships', icon: 'Award', query: 'What scholarship opportunities are available?' },
  { label: 'Faculty', icon: 'Users', query: 'Who is the principal of BVRIT?' },
  { label: 'Contact', icon: 'Phone', query: 'What is the college email address?' },
];

export const placeholderMessages: Record<string, ChatMessage[]> = {
  admissions: [
    {
      id: '1',
      role: 'assistant',
      content: 'BVRIT HYDERABAD offers undergraduate programs (B.Tech) in CSE, IT, ECE, and EEE. Candidates must qualify in TG EAPCET or TS ECET examinations followed by web-based counseling conducted by the state government.',
      timestamp: new Date(),
      citations: [
        { source: 'Admissions Section', page: 2, confidence: 94 },
        { source: 'Academic Programs', page: 1, confidence: 89 },
      ],
    },
  ],
  placements: [
    {
      id: '1',
      role: 'assistant',
      content: 'The highest placement package offered in 2026 is Rs 59 LPA. The average package for the top 10% of students is Rs 20.56 LPA. The college has a strong placement record with top recruiters including Google, Microsoft, Amazon, and Infosys.',
      timestamp: new Date(),
      citations: [
        { source: 'Placements Section', page: 3, confidence: 96 },
        { source: 'Training & Placements', page: 3, confidence: 91 },
      ],
    },
  ],
  departments: [
    {
      id: '1',
      role: 'assistant',
      content: 'BVRIT HYDERABAD offers the following departments: Computer Science & Engineering (CSE), Information Technology (IT), Electronics & Communication Engineering (ECE), Electrical & Electronics Engineering (EEE), and Basic Sciences & Humanities.',
      timestamp: new Date(),
      citations: [
        { source: 'Departments Section', page: 1, confidence: 95 },
      ],
    },
  ],
};

export const knowledgeBase: KnowledgeBaseInfo = {
  filename: 'BVRIT HYDERABAD Institutional Overview.pdf',
  pages: 4,
  chunks: 15,
  indexed: true,
};

export const sessionStats: SessionStats = {
  questionsAsked: 0,
  avgResponseTime: 1.2,
  tokensUsed: 0,
};

export const retrievedDocs: RetrievedDoc[] = [
  { title: 'Admissions', similarity: 0.94, preview: 'Admission to undergraduate programs is based on TG EAPCET or TS ECET scores...' },
  { title: 'Placements', similarity: 0.89, preview: 'The Training & Placement Cell provides comprehensive training programs...' },
  { title: 'Fee Structure', similarity: 0.81, preview: 'B.Tech program fees are approximately Rs 5.14 Lakhs cumulative...' },
];