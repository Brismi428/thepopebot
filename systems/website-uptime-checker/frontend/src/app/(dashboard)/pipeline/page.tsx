'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import PipelineWizard from '@/components/PipelineWizard';
import ResultViewer from '@/components/ResultViewer';

const PIPELINE_STEPS = [
    {
        "name": "monitor",
        "label": "Monitor",
        "description": "Website uptime monitor tool."
    },
    {
        "name": "log_results",
        "label": "Log Results",
        "description": "CSV logging tool for uptime check results."
    },
    {
        "name": "telegram_alert",
        "label": "Telegram Alert",
        "description": "Telegram alert tool for website downtime notifications."
    }
];

export default function PipelinePage() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  return (
    <div className="max-w-4xl">
      <Link
        href="/dashboard/"
        className="inline-flex items-center gap-1 text-sm mb-6 transition-colors hover:opacity-80"
        style={{ color: 'var(--accent)' }}
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        Back to Dashboard
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="font-heading text-3xl font-bold mb-2">Run Pipeline</h1>
        <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
          Execute all tools in sequence as a complete workflow.
        </p>
      </motion.div>

      <PipelineWizard
        steps={PIPELINE_STEPS}
        onResult={(data) => { setError(''); setResult(data); }}
        onError={(err) => { setResult(null); setError(err); }}
      />

      {(result || error) && (
        <div className="mt-8">
          <h2 className="font-heading font-semibold text-lg mb-4">Pipeline Result</h2>
          <ResultViewer result={result} error={error} />
        </div>
      )}
    </div>
  );
}
