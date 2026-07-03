import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, Award, BarChart3, Shield, Lightbulb, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

const summaryCards = [
  { label: 'Total Tests', value: '10', icon: BarChart3, color: 'text-primary' },
  { label: 'Passed', value: '8', icon: CheckCircle, color: 'text-success' },
  { label: 'Failed', value: '1', icon: XCircle, color: 'text-error' },
  { label: 'Warnings', value: '1', icon: AlertTriangle, color: 'text-warning' },
  { label: 'Pass Rate', value: '80%', icon: TrendingUp, color: 'text-success' },
];

const evaluationCards = [
  { label: 'Functional', score: 92, maxScore: 100, status: 'pass' as const },
  { label: 'Quality', score: 88, maxScore: 100, status: 'pass' as const },
  { label: 'Safety', score: 95, maxScore: 100, status: 'pass' as const },
  { label: 'Security', score: 90, maxScore: 100, status: 'pass' as const },
  { label: 'Robustness', score: 75, maxScore: 100, status: 'warning' as const },
  { label: 'Performance', score: 85, maxScore: 100, status: 'pass' as const },
  { label: 'Context', score: 82, maxScore: 100, status: 'pass' as const },
  { label: 'RAGAS', score: 78, maxScore: 100, status: 'warning' as const },
];

const ragasMetrics = [
  { label: 'Faithfulness', score: 0.92, percentage: 92 },
  { label: 'Answer Relevancy', score: 0.88, percentage: 88 },
  { label: 'Context Precision', score: 0.85, percentage: 85 },
  { label: 'Context Recall', score: 0.79, percentage: 79 },
];

function CircularProgress({ percentage, size = 80 }: { percentage: number; size?: number }) {
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color = percentage >= 90 ? '#22C55E' : percentage >= 75 ? '#F59E0B' : '#EF4444';

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="rgba(255,255,255,0.06)" strokeWidth="6" fill="none" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>
      <span className="absolute text-sm font-bold" style={{ color }}>{percentage}%</span>
    </div>
  );
}

function AnimatedProgressBar({ label, value, percentage }: { label: string; value: number; percentage: number }) {
  const color = percentage >= 90 ? 'bg-success' : percentage >= 75 ? 'bg-warning' : 'bg-primary';
  return (
    <div>
      <div className="mb-1.5 flex justify-between text-sm">
        <span className="text-text-secondary">{label}</span>
        <span className="text-white font-medium">{value.toFixed(2)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-background">
        <motion.div
          className={cn('h-full rounded-full', color)}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

export default function Evaluation() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white">Evaluation Dashboard</h1>
        <p className="mt-1 text-text-secondary">Comprehensive evaluation of chatbot performance across multiple dimensions</p>
      </motion.div>

      {/* Summary Cards */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {summaryCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass glass-hover rounded-xl p-4"
            >
              <div className="flex items-center gap-3">
                <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl bg-card', card.color)}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-text-secondary">{card.label}</p>
                  <p className="text-xl font-bold text-white">{card.value}</p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Evaluation Cards Grid */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-white">Dimension Scores</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {evaluationCards.map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="glass rounded-xl p-5 text-center"
            >
              <CircularProgress percentage={card.score} size={100} />
              <h3 className="mt-3 text-sm font-medium text-white">{card.label}</h3>
              <span className={cn(
                'mt-1 inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
                card.status === 'pass' ? 'bg-success/10 text-success border border-success/30' :
                card.status === 'warning' ? 'bg-warning/10 text-warning border border-warning/30' :
                'bg-error/10 text-error border border-error/30'
              )}>
                {card.status === 'pass' ? 'Pass' : card.status === 'warning' ? 'Warning' : 'Fail'}
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* RAGAS Metrics */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-white">RAGAS Metrics</h2>
        <div className="glass rounded-xl p-6">
          <div className="grid gap-6 md:grid-cols-2">
            {ragasMetrics.map((metric, i) => (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <AnimatedProgressBar label={metric.label} value={metric.score} percentage={metric.percentage} />
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-8 rounded-xl border border-warning/30 bg-warning/5 p-6"
      >
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-warning/10">
            <Lightbulb className="h-5 w-5 text-warning" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Recommendation</h3>
            <p className="mt-1 text-sm text-text-secondary">
              <strong>Weakest Dimension:</strong> Robustness (75%) — The model shows inconsistency when handling varied phrasings of the same question.
            </p>
            <p className="mt-1 text-sm text-text-secondary">
              <strong>Recommended Fix:</strong> Expand the training data with diverse paraphrased questions and improve context retrieval with better chunking strategies.
            </p>
            <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 px-3 py-1.5 text-sm font-medium text-success">
              <Award className="h-4 w-4" />
              Overall Grade: A+
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}