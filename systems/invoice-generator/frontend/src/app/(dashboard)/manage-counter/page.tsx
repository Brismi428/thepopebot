'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import ToolForm from '@/components/ToolForm';
import ResultViewer from '@/components/ResultViewer';

const FIELDS = [
      {
            "name": "counter_path",
            "label": "Counter Path",
            "type": "text",
            "required": true,
            "placeholder": "Path to counter JSON file",
            "help": "Path to counter JSON file"
      },
      {
            "name": "action",
            "label": "Action",
            "type": "select",
            "required": false,
            "placeholder": "Action to perform (default: get_next)",
            "help": "Action to perform (default: get_next)",
            "choices": [
                  "get_next",
                  "get_current"
            ],
            "defaultValue": "get_next"
      }
];

export default function ManageCounterPage() {
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
        <h1 className="font-heading text-3xl font-bold mb-2">Manage Counter</h1>
        <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
          Atomically increment invoice counter with file locking.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-[1fr_1fr] gap-8">
        <div className="card">
          <h2 className="font-heading font-semibold text-lg mb-4">Input</h2>
          <ToolForm
            toolName="Manage Counter"
            fields={FIELDS}
            apiEndpoint="/api/manage-counter"
            onResult={(data) => { setError(''); setResult(data); }}
            onError={(err) => { setResult(null); setError(err); }}
          />
        </div>

        <div>
          <h2 className="font-heading font-semibold text-lg mb-4">Output</h2>
          {(result || error) ? (
            <ResultViewer result={result} error={error} />
          ) : (
            <div className="card" style={{ color: 'var(--text-muted)' }}>
              <p className="text-sm">Run the tool to see results here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
