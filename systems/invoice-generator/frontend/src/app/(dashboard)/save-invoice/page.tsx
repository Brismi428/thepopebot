'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import ToolForm from '@/components/ToolForm';
import ResultViewer from '@/components/ResultViewer';

const FIELDS = [
      {
            "name": "pdf_path",
            "label": "Pdf Path",
            "type": "text",
            "required": true,
            "placeholder": "Path to source PDF file",
            "help": "Path to source PDF file"
      },
      {
            "name": "client_name",
            "label": "Client Name",
            "type": "text",
            "required": true,
            "placeholder": "Client name for filename",
            "help": "Client name for filename"
      },
      {
            "name": "invoice_date",
            "label": "Invoice Date",
            "type": "text",
            "required": true,
            "placeholder": "Invoice date (YYYY-MM-DD)",
            "help": "Invoice date (YYYY-MM-DD)"
      },
      {
            "name": "invoice_number",
            "label": "Invoice Number",
            "type": "text",
            "required": true,
            "placeholder": "Invoice number",
            "help": "Invoice number"
      },
      {
            "name": "total",
            "label": "Total",
            "type": "text",
            "required": true,
            "placeholder": "Total invoice amount",
            "help": "Total invoice amount"
      }
];

export default function SaveInvoicePage() {
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
        <h1 className="font-heading text-3xl font-bold mb-2">Save Invoice</h1>
        <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
          Save PDF to output directory with standardized filename and append audit log.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-[1fr_1fr] gap-8">
        <div className="card">
          <h2 className="font-heading font-semibold text-lg mb-4">Input</h2>
          <ToolForm
            toolName="Save Invoice"
            fields={FIELDS}
            apiEndpoint="/api/save-invoice"
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
