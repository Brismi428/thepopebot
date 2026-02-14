'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Wrench, Workflow } from 'lucide-react';

const TOOLS = [
    {
        "href": "/dashboard/generate-invoice-pdf/",
        "label": "Generate Invoice Pdf",
        "description": "Generate professional PDF invoice with ReportLab."
    },
    {
        "href": "/dashboard/load-config/",
        "label": "Load Config",
        "description": "Load company branding and tax configuration with sensible defaults."
    },
    {
        "href": "/dashboard/manage-counter/",
        "label": "Manage Counter",
        "description": "Atomically increment invoice counter with file locking."
    },
    {
        "href": "/dashboard/parse-invoice-input/",
        "label": "Parse Invoice Input",
        "description": "Parse and validate invoice JSON input with business rule checks."
    },
    {
        "href": "/dashboard/save-invoice/",
        "label": "Save Invoice",
        "description": "Save PDF to output directory with standardized filename and append audit log."
    },
    {
        "href": "/dashboard/pipeline/",
        "label": "Run Pipeline",
        "description": "Execute all tools in sequence as a complete workflow."
    }
];

export default function DashboardPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-bold mb-2">Invoice Generator WAT System</h1>
      <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
        Select a tool to run or execute the full pipeline.
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {TOOLS.map((tool, i) => (
          <motion.div
            key={tool.href}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: i * 0.05 }}
          >
            <Link href={tool.href} className="card block hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                {tool.href.includes('pipeline') ? (
                  <Workflow className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                ) : (
                  <Wrench className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                )}
                <h2 className="font-heading font-semibold text-base">{tool.label}</h2>
              </div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {tool.description}
              </p>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
