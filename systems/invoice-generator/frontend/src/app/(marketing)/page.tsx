'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Workflow, Zap, Shield, FileText } from 'lucide-react';
import Link from 'next/link';

const TOOLS = [
  { name: 'Generate Invoice Pdf', desc: 'Generate professional PDF invoice with ReportLab.', icon: FileText },
  { name: 'Load Config', desc: 'Load company branding and tax configuration with sensible defaults.', icon: Shield },
  { name: 'Manage Counter', desc: 'Atomically increment invoice counter with file locking.', icon: Zap },
  { name: 'Parse Invoice Input', desc: 'Parse and validate invoice JSON input with business rule checks.', icon: Shield },
  { name: 'Save Invoice', desc: 'Save PDF to output directory with standardized filename and append audit log.', icon: FileText },
];

export default function HomePage() {
  return (
    <main id="main-content" className="min-h-screen">
      {/* Hero */}
      <section className="relative px-6 py-32 md:px-8 lg:px-12 max-w-6xl mx-auto hero-gradient">
        <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            <div className="badge mb-6">
              <Workflow className="w-3.5 h-3.5 mr-1.5" />
              5 Tools Available
            </div>
            <h1 className="font-heading text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6"
                style={{ color: 'var(--text-primary)' }}>
              Invoice Generator
              <span className="block" style={{ color: 'var(--accent)' }}>WAT System</span>
            </h1>
            <p className="text-lg md:text-xl mb-10 max-w-prose leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Generate professional invoices with local processing, atomic operations, and a full audit trail. No API calls or secrets required.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2 text-base">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#features" className="btn-secondary inline-flex items-center text-base">
                See Features
              </a>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut', delay: 0.15 }}
            className="hidden lg:block"
          >
            <div className="card p-8" style={{ boxShadow: 'var(--shadow-lg)' }}>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }} />
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F59E0B' }} />
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10B981' }} />
              </div>
              <pre className="font-mono text-sm whitespace-pre-wrap leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
{`$ curl -X POST /api/run-pipeline \\
  -d '{"client": "Acme Corp",
       "items": [{"desc": "Consulting", "qty": 40, "rate": 150}]}'

✓ parse_invoice_input  ... validated
✓ load_config          ... loaded
✓ manage_counter       ... INV-2024-0042
✓ generate_invoice_pdf ... 2 pages
✓ save_invoice         ... saved

→ output/INV-2024-0042-acme-corp.pdf`}
              </pre>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-24 md:px-8 lg:px-12 section-alt">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="text-center mb-16"
          >
            <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
              Five tools, one pipeline
            </h2>
            <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
              Each tool handles one step of the invoice workflow. Run them individually or chain them together.
            </p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {TOOLS.map((tool, i) => {
              const Icon = tool.icon;
              return (
                <motion.div
                  key={tool.name}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: i * 0.08 }}
                >
                  <div className="card h-full">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                         style={{ backgroundColor: 'var(--accent-subtle)' }}>
                      <Icon className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                    </div>
                    <h3 className="font-heading font-semibold text-base mb-2">{tool.name}</h3>
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{tool.desc}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-4xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
        >
          <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">Ready to start?</h2>
          <p className="text-lg mb-10" style={{ color: 'var(--text-secondary)' }}>
            Run tools individually or execute the full pipeline with one click.
          </p>
          <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2 text-base">
            Open Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </section>
    </main>
  );
}
