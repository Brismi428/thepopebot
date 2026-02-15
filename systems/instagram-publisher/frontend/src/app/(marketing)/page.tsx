'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Workflow, Zap, Shield, FileText, Camera, Send, GitBranch } from 'lucide-react';
import Link from 'next/link';

const TOOLS = [
  { name: 'Validate Content', desc: 'Validate content against Instagram requirements including caption length, hashtags, and image accessibility.', icon: Shield },
  { name: 'Enrich Content', desc: 'AI-powered content enrichment for hashtags, alt text, and caption optimization.', icon: Zap },
  { name: 'Create Container', desc: 'Create Instagram media containers via the Graph API for image posts.', icon: Camera },
  { name: 'Publish Container', desc: 'Publish containers to make Instagram posts live with retry logic.', icon: Send },
  { name: 'Write Result', desc: 'Write publish results to output directories with automatic status routing.', icon: FileText },
  { name: 'Generate Report', desc: 'Generate markdown summary reports with success rates and recommendations.', icon: FileText },
  { name: 'Git Commit', desc: 'Stage files, commit changes, and push to remote with auto-generated messages.', icon: GitBranch },
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
              7 Tools Available
            </div>
            <h1 className="font-heading text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6"
                style={{ color: 'var(--text-primary)' }}>
              Instagram Publisher
              <span className="block" style={{ color: 'var(--accent)' }}>WAT System</span>
            </h1>
            <p className="text-lg md:text-xl mb-10 max-w-prose leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Publish content to Instagram with validation, AI enrichment, and a full audit trail. Automated pipeline from content to published post.
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
  -d '{"caption": "Hello world!",
       "image_url": "https://example.com/photo.jpg"}'

✓ validate_content      ... valid
✓ enrich_content        ... 15 hashtags
✓ create_container      ... container ready
✓ publish_container     ... published
✓ write_result          ... saved
✓ generate_report       ... report ready
✓ git_commit            ... pushed

→ Post published successfully`}
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
              Seven tools, one pipeline
            </h2>
            <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
              Each tool handles one step of the Instagram publishing workflow. Run them individually or chain them together.
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

      {/* How It Works */}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
            How to use
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Three ways to publish content to Instagram.
          </p>
        </motion.div>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              step: '1',
              title: 'Run the full pipeline',
              desc: 'Click "Get Started", then select "Run Pipeline" from the dashboard. Paste your content as JSON with caption, image_url, and business_account_id fields. Step through the wizard and click "Run Full Pipeline" on the last step.',
            },
            {
              step: '2',
              title: 'Run tools individually',
              desc: 'From the dashboard, click any tool card to open it. Fill in the form fields on the left side and click "Run". Results appear on the right. Start with "Validate Content" to check your post before publishing.',
            },
            {
              step: '3',
              title: 'Use the API directly',
              desc: 'Every tool is available as a POST endpoint at /api/{tool-name}. Send JSON in the request body. Use /api/run-pipeline to execute all 7 steps at once, or /api/health to check the server status.',
            },
          ].map((item, i) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.1 }}
              className="card"
            >
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center mb-4 text-white font-bold"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                {item.step}
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">{item.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{item.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Quick start example */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mt-12"
        >
          <div className="card max-w-2xl mx-auto">
            <h3 className="font-heading font-semibold text-lg mb-3">Quick start: try Validate Content</h3>
            <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
              Go to the dashboard, click <strong>Validate Content</strong>, paste the JSON below into the content field, and click <strong>Run</strong>.
            </p>
            <pre
              className="font-mono text-sm p-4 rounded-lg overflow-x-auto"
              style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
            >
{`{
  "caption": "Beautiful sunset today! #photography #nature",
  "image_url": "https://example.com/sunset.jpg",
  "business_account_id": "17841405309211844"
}`}
            </pre>
          </div>
        </motion.div>
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
