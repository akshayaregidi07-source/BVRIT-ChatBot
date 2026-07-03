import { motion } from 'framer-motion';
import { Sparkles, BookOpen, Search, Brain, BarChart3, Shield, Code2, Cpu, Database, Globe, Clock, User } from 'lucide-react';
import { cn } from '@/lib/utils';

const timelineSteps = [
  { year: 'Step 1', title: 'Data Collection', description: 'Information collected from the official BVRIT website is compiled into a structured PDF document.', icon: Globe },
  { year: 'Step 2', title: 'Document Processing', description: 'The PDF is loaded, parsed, and split into manageable text chunks using RecursiveCharacterTextSplitter.', icon: BookOpen },
  { year: 'Step 3', title: 'Vector Embeddings', description: 'Each chunk is converted into vector embeddings using OpenAI text-embedding-3-small model.', icon: Database },
  { year: 'Step 4', title: 'Vector Storage', description: 'Embeddings are stored in ChromaDB, a persistent vector database for efficient similarity search.', icon: Cpu },
  { year: 'Step 5', title: 'Retrieval', description: 'User queries are embedded and matched against the vector store to find the most relevant chunks.', icon: Search },
  { year: 'Step 6', title: 'Generation', description: 'The LLM (GPT-4o-mini) generates grounded responses using the retrieved context with citations.', icon: Brain },
  { year: 'Step 7', title: 'Evaluation', description: 'Performance is evaluated using RAGAS metrics and LLM-as-a-judge across 8 dimensions.', icon: BarChart3 },
];

const technologies = [
  { name: 'React', description: 'Frontend framework', icon: Code2 },
  { name: 'TypeScript', description: 'Type-safe JavaScript', icon: Shield },
  { name: 'LangChain', description: 'LLM orchestration', icon: Brain },
  { name: 'ChromaDB', description: 'Vector database', icon: Database },
  { name: 'OpenRouter', description: 'API gateway for LLMs', icon: Globe },
  { name: 'Streamlit', description: 'Python web framework', icon: Code2 },
];

export default function About() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-blue-600 shadow-glow">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white">About the Project</h1>
        <p className="mt-2 text-text-secondary max-w-2xl mx-auto">
          RAG-Powered College FAQ Chatbot with Automated Evaluation — A production-ready AI assistant for BVRIT Hyderabad.
        </p>
      </motion.div>

      {/* Problem Statement */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-10 glass rounded-xl p-6"
      >
        <h2 className="text-lg font-semibold text-white">Problem Statement</h2>
        <p className="mt-2 text-sm text-text-secondary leading-relaxed">
          Students and prospective applicants often struggle to find accurate and up-to-date information about their college,
          such as admission procedures, fee structures, placement statistics, departments, campus facilities, and contact details.
          Although this information is available on the college website, navigating multiple webpages to locate specific answers
          is time-consuming and inconvenient. Traditional chatbots frequently generate responses based on pre-trained knowledge,
          which may be outdated or inaccurate for institution-specific queries.
        </p>
      </motion.div>

      {/* Solution */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-6 glass rounded-xl p-6"
      >
        <h2 className="text-lg font-semibold text-white">Solution Architecture</h2>
        <p className="mt-2 text-sm text-text-secondary leading-relaxed">
          The system follows a Retrieval-Augmented Generation (RAG) architecture. Information from the college website
          is converted into a structured PDF, split into chunks, embedded, and stored in ChromaDB. User queries retrieve
          the most relevant chunks via semantic search, which are provided as context to an LLM to generate grounded
          responses with source citations.
        </p>
      </motion.div>

      {/* RAG Pipeline Timeline */}
      <div className="mt-10">
        <h2 className="mb-6 text-xl font-bold text-white">RAG Pipeline</h2>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 h-full w-px bg-border-glass" />
          
          <div className="space-y-6">
            {timelineSteps.map((step, i) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="relative flex gap-6"
                >
                  <div className="relative z-10 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-blue-600 shadow-glow">
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <div className="glass flex-1 rounded-xl p-4">
                    <span className="text-xs font-medium text-primary">{step.year}</span>
                    <h3 className="text-sm font-semibold text-white">{step.title}</h3>
                    <p className="mt-1 text-xs text-text-secondary">{step.description}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Technologies */}
      <div className="mt-10">
        <h2 className="mb-6 text-xl font-bold text-white">Technologies Used</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {technologies.map((tech, i) => {
            const Icon = tech.icon;
            return (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass glass-hover rounded-xl p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{tech.name}</h3>
                    <p className="text-xs text-text-secondary">{tech.description}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Developer Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-10 glass rounded-xl p-6 text-center"
      >
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary to-blue-600">
          <User className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-lg font-semibold text-white">Developed By</h2>
        <p className="mt-1 text-text-secondary">BVRIT Hyderabad College of Engineering for Women</p>
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-text-secondary">
          <Clock className="h-4 w-4" />
          <span>Built with ❤️ using LangChain, ChromaDB, OpenRouter & Streamlit</span>
        </div>
      </motion.div>
    </div>
  );
}