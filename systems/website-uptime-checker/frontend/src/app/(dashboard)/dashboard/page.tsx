'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Wrench, Workflow } from 'lucide-react';

const TOOLS = [
    {
        "href": "/dashboard/log-results/",
        "label": "Log Results",
        "description": "CSV logging tool for uptime check results."
    },
    {
        "href": "/dashboard/monitor/",
        "label": "Monitor",
        "description": "Website uptime monitor tool."
    },
    {
        "href": "/dashboard/telegram-alert/",
        "label": "Telegram Alert",
        "description": "Telegram alert tool for website downtime notifications."
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
      <h1 className="font-heading text-3xl font-bold mb-2">Website Uptime Checker — Operating Instructions</h1>
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
