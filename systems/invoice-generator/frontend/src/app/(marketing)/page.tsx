'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Workflow } from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <main id="main-content" className="min-h-screen">
      {/* Hero */}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          >
            <div className="badge mb-6">
              <Workflow className="w-4 h-4 mr-2" />
              5 Tools Available
            </div>
            <h1 className="font-heading text-5xl md:text-6xl font-bold tracking-tight mb-6"
                style={{ color: 'var(--text-primary)' }}>
              Invoice Generator WAT System
            </h1>
            <p className="text-lg mb-8 max-w-prose" style={{ color: 'var(--text-secondary)' }}>
              - **No API calls** (all local processing)
- **No secrets required** (for basic operation)
- **Sequential execution** (clear, predictable flow)
- **Atomic operations** (file locking prevents race conditions)
- **Graceful degradation** (continues with degraded output rather than crashing)
- **Full audit trail** (every invoice logged)
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#features" className="btn-secondary inline-flex items-center">
                See Features
              </a>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut', delay: 0.1 }}
            className="hidden lg:block"
          >
            <div className="card p-8">
              <pre className="font-mono text-sm whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>
$ curl -X POST /api/run-pipeline
  -d '{"input": "data"}'

// 5 tools chained automatically
              </pre>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-24 md:px-8 lg:px-12" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="font-heading text-3xl font-bold mb-12 text-center">
            Tools
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">

            <div className="card">
              <h3 className="font-heading font-semibold mb-2">Generate Invoice Pdf</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Generate professional PDF invoice with ReportLab.</p>
            </div>

            <div className="card">
              <h3 className="font-heading font-semibold mb-2">Load Config</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Load company branding and tax configuration with sensible defaults.</p>
            </div>

            <div className="card">
              <h3 className="font-heading font-semibold mb-2">Manage Counter</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Atomically increment invoice counter with file locking.</p>
            </div>

            <div className="card">
              <h3 className="font-heading font-semibold mb-2">Parse Invoice Input</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Parse and validate invoice JSON input with business rule checks.</p>
            </div>

            <div className="card">
              <h3 className="font-heading font-semibold mb-2">Save Invoice</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Save PDF to output directory with standardized filename and append audit log.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-4xl mx-auto text-center">
        <h2 className="font-heading text-3xl font-bold mb-4">Ready to start?</h2>
        <p className="text-lg mb-8" style={{ color: 'var(--text-secondary)' }}>
          Run Invoice Generator WAT System tools individually or as a complete pipeline.
        </p>
        <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2">
          Open Dashboard <ArrowRight className="w-4 h-4" />
        </Link>
      </section>
    </main>
  );
}
