'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Wrench, Workflow } from 'lucide-react';

const TOOLS = [
    {
        "href": "/validate-content/",
        "label": "Validate Content",
        "description": "Validate content against Instagram requirements."
    },
    {
        "href": "/enrich-content/",
        "label": "Enrich Content",
        "description": "AI-powered content enrichment for hashtags, alt text, and captions."
    },
    {
        "href": "/instagram-create-container/",
        "label": "Create Container",
        "description": "Create Instagram media containers via the Graph API."
    },
    {
        "href": "/instagram-publish-container/",
        "label": "Publish Container",
        "description": "Publish containers to make Instagram posts live."
    },
    {
        "href": "/write-result/",
        "label": "Write Result",
        "description": "Write publish results to output directories."
    },
    {
        "href": "/generate-report/",
        "label": "Generate Report",
        "description": "Generate markdown summary reports with success rates."
    },
    {
        "href": "/git-commit/",
        "label": "Git Commit",
        "description": "Stage files, commit, and push to remote."
    },
    {
        "href": "/pipeline/",
        "label": "Run Pipeline",
        "description": "Execute all 7 tools in sequence as a complete workflow."
    }
];

export default function DashboardPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-bold mb-2">Instagram Publisher WAT System</h1>
      <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
        Select a tool to run or execute the full pipeline.
      </p>

      {/* Usage instructions */}
      <div className="card mb-8">
        <h2 className="font-heading font-semibold text-lg mb-3">How to use</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-heading font-semibold text-sm mb-2" style={{ color: 'var(--accent)' }}>Run a single tool</h3>
            <ol className="text-sm space-y-1 list-decimal list-inside" style={{ color: 'var(--text-secondary)' }}>
              <li>Click any tool card below to open it</li>
              <li>Fill in the form fields on the left</li>
              <li>Click the <strong>Run</strong> button</li>
              <li>View results on the right side</li>
            </ol>
          </div>
          <div>
            <h3 className="font-heading font-semibold text-sm mb-2" style={{ color: 'var(--accent)' }}>Run the full pipeline</h3>
            <ol className="text-sm space-y-1 list-decimal list-inside" style={{ color: 'var(--text-secondary)' }}>
              <li>Click <strong>Run Pipeline</strong> below</li>
              <li>Paste your content JSON on step 1 (caption, image_url, business_account_id)</li>
              <li>Step through to review each stage</li>
              <li>Click <strong>Run Full Pipeline</strong> on the last step</li>
            </ol>
          </div>
        </div>
        <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <p className="text-xs font-medium mb-1">Quick test: try Validate Content with this JSON</p>
          <code className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
            {`{"caption": "Hello world! #test", "image_url": "https://example.com/photo.jpg", "business_account_id": "12345"}`}
          </code>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {TOOLS.map((tool, i) => (
          <motion.div
            key={tool.href}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: i * 0.05 }}
          >
            <Link href={tool.href} className="card-interactive block">
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
