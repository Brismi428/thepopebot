'use client';
// Result viewer component — renders JSON, PDF, CSV, or file downloads

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Copy, CheckCircle, FileText, Braces, AlertCircle } from 'lucide-react';

interface ResultViewerProps {
  result: any;
  error?: string;
}

export default function ResultViewer({ result, error }: ResultViewerProps) {
  const [copied, setCopied] = useState(false);

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="card border-l-4"
        style={{ borderLeftColor: 'var(--error)' }}
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" style={{ color: 'var(--error)' }} />
          <div>
            <h3 className="font-heading font-semibold mb-1">Error</h3>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{error}</p>
          </div>
        </div>
      </motion.div>
    );
  }

  if (!result) return null;

  // File download result
  if (result._file) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div className="flex items-center gap-3 mb-4">
          <FileText className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <h3 className="font-heading font-semibold">Generated File</h3>
        </div>
        {result.contentType?.includes('pdf') && (
          <div className="mb-4 rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
            <iframe
              src={result.url}
              className="w-full h-96"
              title="PDF Preview"
            />
          </div>
        )}
        <a
          href={result.url}
          download={result.filename}
          className="btn-primary inline-flex items-center gap-2"
        >
          <Download className="w-4 h-4" aria-hidden="true" />
          Download {result.filename}
        </a>
      </motion.div>
    );
  }

  // Raw text result
  if (result._raw) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <pre className="font-mono text-sm whitespace-pre-wrap" style={{ color: 'var(--text-primary)' }}>
          {result.text}
        </pre>
      </motion.div>
    );
  }

  // JSON result
  const jsonString = JSON.stringify(result, null, 2);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Braces className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <h3 className="font-heading font-semibold">Result</h3>
          {result.status && (
            <span
              className="badge"
              style={{
                backgroundColor: result.status === 'success' ? 'var(--success)' : 'var(--error)',
                color: 'white',
              }}
            >
              {result.status}
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="btn-ghost p-2 rounded-lg"
          aria-label="Copy to clipboard"
        >
          {copied ? (
            <CheckCircle className="w-4 h-4" style={{ color: 'var(--success)' }} />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>
      </div>
      <pre
        className="font-mono text-sm overflow-x-auto p-4 rounded-lg max-h-96 overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
      >
        {jsonString}
      </pre>
    </motion.div>
  );
}
