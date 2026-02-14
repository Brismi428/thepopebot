{/* Dashboard home page template — populated by generate_frontend.py */}
'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';

{TOOL_CARDS_IMPORT}

export default function DashboardPage() {
  const tools = {TOOL_CARDS};

  return (
    <div>
      <h1 className="font-heading text-3xl font-bold mb-2">{SYSTEM_NAME}</h1>
      <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
        {DASHBOARD_DESCRIPTION}
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {tools.map((tool, i) => (
          <motion.div
            key={tool.href}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: i * 0.05 }}
          >
            <Link href={tool.href} className="card block hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                {tool.icon}
                <h3 className="font-heading font-semibold">{tool.label}</h3>
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
