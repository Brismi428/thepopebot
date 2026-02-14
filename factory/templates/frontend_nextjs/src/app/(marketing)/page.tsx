{/* Marketing landing page template — populated by generate_frontend.py */}
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
              {SYSTEM_BADGE}
            </div>
            <h1 className="font-heading text-5xl md:text-6xl font-bold tracking-tight mb-6"
                style={{ color: 'var(--text-primary)' }}>
              {HERO_TITLE}
            </h1>
            <p className="text-lg mb-8 max-w-prose" style={{ color: 'var(--text-secondary)' }}>
              {HERO_DESCRIPTION}
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
              <div className="font-mono text-sm" style={{ color: 'var(--text-secondary)' }}>
                {HERO_CODE_PREVIEW}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-24 md:px-8 lg:px-12" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="font-heading text-3xl font-bold mb-12 text-center">
            {FEATURES_TITLE}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURE_CARDS}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-4xl mx-auto text-center">
        <h2 className="font-heading text-3xl font-bold mb-4">Ready to start?</h2>
        <p className="text-lg mb-8" style={{ color: 'var(--text-secondary)' }}>
          {CTA_DESCRIPTION}
        </p>
        <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2">
          Open Dashboard <ArrowRight className="w-4 h-4" />
        </Link>
      </section>
    </main>
  );
}
