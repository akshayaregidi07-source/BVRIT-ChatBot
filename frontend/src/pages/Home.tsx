import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, MessageSquare, BarChart3, GraduationCap, Briefcase, Building2, IndianRupee, Award, Users, Hotel, Phone, Wifi } from 'lucide-react';
import { cn } from '@/lib/utils';
import { topicChips } from '@/lib/data';

const iconMap: Record<string, React.ElementType> = {
  GraduationCap, Briefcase, Building2, IndianRupee,
  Award, Users, Hotel, Phone, Wifi,
};

export default function Home() {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden">
      {/* Background Gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute -right-40 top-40 h-[400px] w-[400px] rounded-full bg-blue-600/10 blur-[100px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:py-20">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Left Column */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary"
            >
              <Sparkles className="h-4 w-4" />
              <span>Powered by Retrieval-Augmented AI</span>
            </motion.div>

            <h1 className="text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
              AI-Powered{' '}
              <span className="bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
                College Information
              </span>{' '}
              Assistant
            </h1>

            <p className="mt-6 text-lg text-text-secondary leading-relaxed max-w-xl">
              Ask questions about admissions, placements, departments, fees, faculty, campus facilities, scholarships, and more. Get instant answers with source citations.
            </p>

            {/* Buttons */}
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                to="/chat"
                className="group flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white shadow-glow transition-all hover:bg-primary-dark hover:shadow-glow-lg"
              >
                <MessageSquare className="h-4 w-4" />
                Start Chat
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                to="/evaluation"
                className="flex items-center gap-2 rounded-xl border border-border-glass bg-card/50 px-6 py-3 text-sm font-medium text-text-secondary transition-all hover:border-primary/30 hover:text-white hover:bg-card"
              >
                <BarChart3 className="h-4 w-4" />
                View Evaluation
              </Link>
            </div>

            {/* Topic Chips */}
            <div className="mt-10">
              <p className="mb-4 text-sm text-text-muted">Popular topics</p>
              <div className="flex flex-wrap gap-2">
                {topicChips.map((chip, i) => {
                  const Icon = iconMap[chip.icon] || Sparkles;
                  return (
                    <motion.div
                      key={chip.label}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + i * 0.05 }}
                    >
                      <Link
                        to={`/chat?q=${chip.label.toLowerCase()}`}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-border-glass bg-card/50 px-3.5 py-2 text-xs font-medium text-text-secondary transition-all hover:border-primary/30 hover:text-white hover:bg-card/80"
                      >
                        {Icon && <Icon className="h-3.5 w-3.5" style={{ color: chip.color }} />}
                        {chip.label}
                      </Link>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>

          {/* Right Column - Robot Illustration */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex items-center justify-center"
          >
            <div className="relative">
              {/* Glow */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-primary/20 via-blue-500/10 to-transparent blur-3xl" />
              
              {/* Robot Card */}
              <div className="glass relative overflow-hidden rounded-3xl p-1 shadow-card">
                <div className="rounded-2xl bg-gradient-to-br from-card to-background p-8">
                  <motion.div
                    animate={{ y: [0, -15, 0] }}
                    transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                    className="flex items-center justify-center"
                  >
                    <div className="flex h-64 w-64 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 via-blue-500/5 to-transparent border border-primary/10">
                      <div className="relative">
                        {/* Robot Face */}
                        <div className="flex h-40 w-40 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-blue-600/20 border border-primary/20">
                          <div className="text-center">
                            <Sparkles className="mx-auto h-16 w-16 text-primary" />
                            <div className="mt-2 flex items-center justify-center gap-1">
                              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                              <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.3s' }} />
                              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: '0.6s' }} />
                            </div>
                          </div>
                        </div>
                        {/* Graduation Cap */}
                        <div className="absolute -right-2 -top-2 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary to-blue-600 shadow-glow">
                          <GraduationCap className="h-5 w-5 text-white" />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                  
                  <p className="mt-4 text-center text-sm text-text-secondary">
                    AI Assistant • Ready to help
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}