"""
Generate Frontend — Reads system_interface.json and frontend_design.json to produce a Next.js app.

Generates project scaffolding with route groups: (marketing), (dashboard).
For each tool: generates an input form page with proper field types, validation, submit handler.
For the pipeline: generates a multi-step wizard UI.
Generates result viewers per output type (PDF, JSON, CSV).
Applies the design system from frontend_design_system.md.
Static export (next build && next export) — no SSR, no Next.js API routes.

Inputs:
    - system_dir (str): Path to the system directory
    - manifest (str): Path to system_interface.json (default: system_dir/system_interface.json)
    - design (str): Path to frontend_design.json (default: generates from archetype)

Outputs:
    - Complete Next.js project in frontend/

Usage:
    python generate_frontend.py --system-dir systems/invoice-generator/
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "frontend_nextjs"

# Type mapping from argparse types to form field types
ARG_TYPE_TO_FIELD = {
    "str": "text",
    "int": "number",
    "float": "number",
    "bool": "checkbox",
}


def generate_design_json(manifest: dict) -> dict:
    """Generate default frontend_design.json from the Professional SaaS archetype."""
    system_name = manifest.get("system", {}).get("system_name", "WAT System")
    description = manifest.get("system", {}).get("description", "A WAT-powered system.")
    tools = manifest.get("tools", [])

    return {
        "archetype": "professional-saas",
        "system_name": system_name,
        "system_description": description,
        "fonts": {
            "heading": "Space Grotesk",
            "body": "DM Sans",
            "mono": "JetBrains Mono",
        },
        "palette": "cool-tech",
        "hero": {
            "badge": f"{len(tools)} Tools Available",
            "title": system_name,
            "description": description,
            "code_preview": f"$ curl -X POST /api/run-pipeline\n  -d '{{\"input\": \"data\"}}'\n\n// {len(tools)} tools chained automatically",
        },
        "features_title": "Tools",
        "cta_description": f"Run {system_name} tools individually or as a complete pipeline.",
    }


def tool_to_form_fields(tool: dict) -> list[dict]:
    """Convert a tool's arguments to form field definitions."""
    fields = []
    for arg in tool.get("arguments", []):
        name = arg["name"]
        # Skip output-only args
        if name in ("output", "output_file", "output_dir", "output_path"):
            continue

        field_type = ARG_TYPE_TO_FIELD.get(arg.get("type", "str"), "text")
        if arg.get("choices"):
            field_type = "select"
        if arg.get("action") in ("store_true", "store_false"):
            field_type = "checkbox"

        field = {
            "name": name,
            "label": name.replace("_", " ").title(),
            "type": field_type,
            "required": arg.get("required", False),
            "placeholder": arg.get("help", ""),
            "help": arg.get("help", ""),
        }
        if arg.get("choices"):
            field["choices"] = arg["choices"]
        if arg.get("default") is not None:
            field["defaultValue"] = arg["default"]

        fields.append(field)
    return fields


def generate_tool_page(tool: dict, system_name: str) -> str:
    """Generate a tool form page component."""
    tool_name = tool["name"]
    display_name = tool_name.replace("_", " ").title()
    route_name = tool_name.replace("_", "-")
    docstring = tool.get("docstring", "").split("\n")[0] or f"Run the {display_name} tool."
    fields = tool_to_form_fields(tool)

    fields_json = json.dumps(fields, indent=6)

    return f"""'use client';

import {{ useState }} from 'react';
import {{ motion }} from 'framer-motion';
import {{ ArrowLeft }} from 'lucide-react';
import Link from 'next/link';
import ToolForm from '@/components/ToolForm';
import ResultViewer from '@/components/ResultViewer';

const FIELDS = {fields_json};

export default function {tool_name.title().replace("_", "")}Page() {{
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  return (
    <div className="max-w-4xl">
      <Link
        href="/dashboard/"
        className="inline-flex items-center gap-1 text-sm mb-6 transition-colors hover:opacity-80"
        style={{{{ color: 'var(--accent)' }}}}
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        Back to Dashboard
      </Link>

      <motion.div
        initial={{{{ opacity: 0, y: 8 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        transition={{{{ duration: 0.3 }}}}
      >
        <h1 className="font-heading text-3xl font-bold mb-2">{display_name}</h1>
        <p className="mb-8" style={{{{ color: 'var(--text-secondary)' }}}}>
          {docstring}
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-[1fr_1fr] gap-8">
        <div className="card">
          <h2 className="font-heading font-semibold text-lg mb-4">Input</h2>
          <ToolForm
            toolName="{display_name}"
            fields={{FIELDS}}
            apiEndpoint="/api/{route_name}"
            onResult={{(data) => {{ setError(''); setResult(data); }}}}
            onError={{(err) => {{ setResult(null); setError(err); }}}}
          />
        </div>

        <div>
          <h2 className="font-heading font-semibold text-lg mb-4">Output</h2>
          {{(result || error) ? (
            <ResultViewer result={{result}} error={{error}} />
          ) : (
            <div className="card" style={{{{ color: 'var(--text-muted)' }}}}>
              <p className="text-sm">Run the tool to see results here.</p>
            </div>
          )}}
        </div>
      </div>
    </div>
  );
}}
"""


def generate_pipeline_page(manifest: dict) -> str:
    """Generate the pipeline wizard page."""
    tools = manifest.get("tools", [])
    pipeline_order = manifest.get("pipeline_order", [t["name"] for t in tools])
    tool_map = {t["name"]: t for t in tools}

    steps = []
    for name in pipeline_order:
        tool = tool_map.get(name, {})
        steps.append({
            "name": name,
            "label": name.replace("_", " ").title(),
            "description": (tool.get("docstring", "") or "").split("\n")[0] or f"Run {name}",
        })

    steps_json = json.dumps(steps, indent=4)

    return f"""'use client';

import {{ useState }} from 'react';
import {{ motion }} from 'framer-motion';
import {{ ArrowLeft }} from 'lucide-react';
import Link from 'next/link';
import PipelineWizard from '@/components/PipelineWizard';
import ResultViewer from '@/components/ResultViewer';

const PIPELINE_STEPS = {steps_json};

export default function PipelinePage() {{
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  return (
    <div className="max-w-4xl">
      <Link
        href="/dashboard/"
        className="inline-flex items-center gap-1 text-sm mb-6 transition-colors hover:opacity-80"
        style={{{{ color: 'var(--accent)' }}}}
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        Back to Dashboard
      </Link>

      <motion.div
        initial={{{{ opacity: 0, y: 8 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        transition={{{{ duration: 0.3 }}}}
      >
        <h1 className="font-heading text-3xl font-bold mb-2">Run Pipeline</h1>
        <p className="mb-8" style={{{{ color: 'var(--text-secondary)' }}}}>
          Execute all tools in sequence as a complete workflow.
        </p>
      </motion.div>

      <PipelineWizard
        steps={{PIPELINE_STEPS}}
        onResult={{(data) => {{ setError(''); setResult(data); }}}}
        onError={{(err) => {{ setResult(null); setError(err); }}}}
      />

      {{(result || error) && (
        <div className="mt-8">
          <h2 className="font-heading font-semibold text-lg mb-4">Pipeline Result</h2>
          <ResultViewer result={{result}} error={{error}} />
        </div>
      )}}
    </div>
  );
}}
"""


def generate_dashboard_page(manifest: dict, design: dict) -> str:
    """Generate the dashboard home page with tool cards."""
    tools = manifest.get("tools", [])
    system_name = design.get("system_name", "Dashboard")

    tool_items = []
    for tool in tools:
        name = tool["name"]
        display = name.replace("_", " ").title()
        route = name.replace("_", "-")
        desc = (tool.get("docstring", "") or "").split("\n")[0] or f"Run {display}"
        tool_items.append({
            "href": f"/dashboard/{route}/",
            "label": display,
            "description": desc,
        })

    # Add pipeline entry
    tool_items.append({
        "href": "/dashboard/pipeline/",
        "label": "Run Pipeline",
        "description": "Execute all tools in sequence as a complete workflow.",
    })

    items_json = json.dumps(tool_items, indent=4)

    return f"""'use client';

import {{ motion }} from 'framer-motion';
import Link from 'next/link';
import {{ Wrench, Workflow }} from 'lucide-react';

const TOOLS = {items_json};

export default function DashboardPage() {{
  return (
    <div>
      <h1 className="font-heading text-3xl font-bold mb-2">{system_name}</h1>
      <p className="mb-8" style={{{{ color: 'var(--text-secondary)' }}}}>
        Select a tool to run or execute the full pipeline.
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {{TOOLS.map((tool, i) => (
          <motion.div
            key={{tool.href}}
            initial={{{{ opacity: 0, y: 4 }}}}
            animate={{{{ opacity: 1, y: 0 }}}}
            transition={{{{ duration: 0.2, delay: i * 0.05 }}}}
          >
            <Link href={{tool.href}} className="card block hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                {{tool.href.includes('pipeline') ? (
                  <Workflow className="w-5 h-5" style={{{{ color: 'var(--accent)' }}}} />
                ) : (
                  <Wrench className="w-5 h-5" style={{{{ color: 'var(--accent)' }}}} />
                )}}
                <h2 className="font-heading font-semibold text-base">{{tool.label}}</h2>
              </div>
              <p className="text-sm" style={{{{ color: 'var(--text-secondary)' }}}}>
                {{tool.description}}
              </p>
            </Link>
          </motion.div>
        ))}}
      </div>
    </div>
  );
}}
"""


def generate_dashboard_layout(manifest: dict, design: dict) -> str:
    """Generate the dashboard layout with sidebar navigation."""
    tools = manifest.get("tools", [])
    system_name = design.get("system_name", "Dashboard")

    nav_items = []
    for tool in tools:
        name = tool["name"]
        display = name.replace("_", " ").title()
        route = name.replace("_", "-")
        nav_items.append({"href": f"/dashboard/{route}/", "label": display})
    nav_items.append({"href": "/dashboard/pipeline/", "label": "Pipeline"})

    nav_json = json.dumps(nav_items, indent=4)

    return f"""'use client';

import Link from 'next/link';
import {{ usePathname }} from 'next/navigation';
import {{ Workflow, Wrench, Moon, Sun, Home }} from 'lucide-react';
import {{ useState, useEffect }} from 'react';
import clsx from 'clsx';

const NAV_ITEMS = {nav_json};

export default function DashboardLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  const pathname = usePathname();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {{
    const stored = localStorage.getItem('theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(stored as 'light' | 'dark');
  }}, []);

  const toggleTheme = () => {{
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  }};

  return (
    <div className="min-h-screen flex">
      {{/* Sidebar */}}
      <aside
        className="hidden lg:flex flex-col w-60 border-r p-4 shrink-0"
        style={{{{ borderColor: 'var(--border)', backgroundColor: 'var(--bg-secondary)' }}}}
      >
        <Link href="/dashboard/" className="flex items-center gap-2 px-2 mb-8">
          <Workflow className="w-6 h-6" style={{{{ color: 'var(--accent)' }}}} />
          <span className="font-heading font-bold text-lg">{system_name}</span>
        </Link>
        <nav className="flex-1 space-y-1" aria-label="Dashboard navigation">
          <Link
            href="/dashboard/"
            className={{clsx(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              pathname === '/dashboard/' || pathname === '/dashboard'
                ? 'bg-[var(--accent-subtle)] text-[var(--accent)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
            )}}
          >
            <Home className="w-4 h-4" />
            Overview
          </Link>
          {{NAV_ITEMS.map((item) => (
            <Link
              key={{item.href}}
              href={{item.href}}
              className={{clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                pathname === item.href || pathname === item.href.replace(/\\/$/, '')
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              )}}
            >
              {{item.href.includes('pipeline') ? (
                <Workflow className="w-4 h-4" />
              ) : (
                <Wrench className="w-4 h-4" />
              )}}
              {{item.label}}
            </Link>
          ))}}
        </nav>
        <button
          onClick={{toggleTheme}}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-[var(--bg-tertiary)]"
          style={{{{ color: 'var(--text-secondary)' }}}}
          aria-label={{`Switch to ${{theme === 'light' ? 'dark' : 'light'}} mode`}}
        >
          {{theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}}
          {{theme === 'light' ? 'Dark mode' : 'Light mode'}}
        </button>
      </aside>

      {{/* Main content */}}
      <main id="main-content" className="flex-1 p-6 md:p-8 lg:p-12 overflow-auto">
        {{children}}
      </main>
    </div>
  );
}}
"""


def generate_landing_page(manifest: dict, design: dict) -> str:
    """Generate the marketing landing page."""
    tools = manifest.get("tools", [])
    hero = design.get("hero", {})
    system_name = design.get("system_name", "WAT System")

    feature_cards = []
    for tool in tools:
        name = tool["name"]
        display = name.replace("_", " ").title()
        desc = (tool.get("docstring", "") or "").split("\n")[0] or f"Run {display}"
        feature_cards.append(f"""
            <div className="card">
              <h3 className="font-heading font-semibold mb-2">{display}</h3>
              <p className="text-sm" style={{{{ color: 'var(--text-secondary)' }}}}>{desc}</p>
            </div>""")

    features_block = "\n".join(feature_cards)

    return f"""'use client';

import {{ motion }} from 'framer-motion';
import {{ ArrowRight, Workflow }} from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {{
  return (
    <main id="main-content" className="min-h-screen">
      {{/* Hero */}}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-12 items-center">
          <motion.div
            initial={{{{ opacity: 0, y: 8 }}}}
            animate={{{{ opacity: 1, y: 0 }}}}
            transition={{{{ duration: 0.3, ease: 'easeOut' }}}}
          >
            <div className="badge mb-6">
              <Workflow className="w-4 h-4 mr-2" />
              {hero.get("badge", f"{len(tools)} Tools Available")}
            </div>
            <h1 className="font-heading text-5xl md:text-6xl font-bold tracking-tight mb-6"
                style={{{{ color: 'var(--text-primary)' }}}}>
              {hero.get("title", system_name)}
            </h1>
            <p className="text-lg mb-8 max-w-prose" style={{{{ color: 'var(--text-secondary)' }}}}>
              {hero.get("description", design.get("system_description", ""))}
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
            initial={{{{ opacity: 0, y: 8 }}}}
            animate={{{{ opacity: 1, y: 0 }}}}
            transition={{{{ duration: 0.3, ease: 'easeOut', delay: 0.1 }}}}
            className="hidden lg:block"
          >
            <div className="card p-8">
              <pre className="font-mono text-sm whitespace-pre-wrap" style={{{{ color: 'var(--text-secondary)' }}}}>
{hero.get("code_preview", "$ curl -X POST /api/run-pipeline")}
              </pre>
            </div>
          </motion.div>
        </div>
      </section>

      {{/* Features */}}
      <section id="features" className="px-6 py-24 md:px-8 lg:px-12" style={{{{ backgroundColor: 'var(--bg-secondary)' }}}}>
        <div className="max-w-6xl mx-auto">
          <h2 className="font-heading text-3xl font-bold mb-12 text-center">
            {design.get("features_title", "Tools")}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
{features_block}
          </div>
        </div>
      </section>

      {{/* CTA */}}
      <section className="px-6 py-24 md:px-8 lg:px-12 max-w-4xl mx-auto text-center">
        <h2 className="font-heading text-3xl font-bold mb-4">Ready to start?</h2>
        <p className="text-lg mb-8" style={{{{ color: 'var(--text-secondary)' }}}}>
          {design.get("cta_description", f"Run {system_name} tools from your browser.")}
        </p>
        <Link href="/dashboard/" className="btn-primary inline-flex items-center gap-2">
          Open Dashboard <ArrowRight className="w-4 h-4" />
        </Link>
      </section>
    </main>
  );
}}
"""


def generate_root_layout(design: dict) -> str:
    """Generate the root layout.tsx."""
    system_name = design.get("system_name", "WAT System")
    description = design.get("system_description", "A WAT-powered system.")

    return f"""import type {{ Metadata }} from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {{
  title: '{system_name}',
  description: '{description}',
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{{{
            __html: `
              (function() {{
                const theme = localStorage.getItem('theme') ||
                  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                document.documentElement.setAttribute('data-theme', theme);
                if (theme === 'dark') document.documentElement.classList.add('dark');
              }})();
            `,
          }}}}
        />
      </head>
      <body className="font-body antialiased">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        {{children}}
      </body>
    </html>
  );
}}
"""


def main() -> dict[str, Any]:
    """Generate Next.js frontend for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate Next.js frontend")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    parser.add_argument("--manifest", default=None, help="Path to system_interface.json")
    parser.add_argument("--design", default=None, help="Path to frontend_design.json")
    args = parser.parse_args()

    logger.info("Generating frontend for: %s", args.system_dir)

    try:
        system_dir = Path(args.system_dir)
        if not system_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {system_dir}"}

        # Load manifest
        manifest_path = args.manifest or str(system_dir / "system_interface.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        tools = manifest.get("tools", [])
        if not tools:
            return {"status": "error", "data": None, "message": "No tools found in manifest"}

        # Load or generate design
        design_path = args.design or str(system_dir / "frontend_design.json")
        if os.path.isfile(design_path):
            with open(design_path, "r", encoding="utf-8") as f:
                design = json.load(f)
        else:
            design = generate_design_json(manifest)
            with open(design_path, "w", encoding="utf-8") as f:
                json.dump(design, f, indent=2)
            logger.info("Generated default frontend_design.json")

        # Create frontend directory
        frontend_dir = system_dir / "frontend"
        if frontend_dir.is_dir():
            logger.warning("frontend/ already exists — will overwrite generated files")

        # Copy template skeleton
        if TEMPLATE_DIR.is_dir():
            for item in TEMPLATE_DIR.rglob("*"):
                if item.is_file():
                    relative = item.relative_to(TEMPLATE_DIR)
                    dest = frontend_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
            logger.info("Copied template skeleton")
        else:
            logger.warning("Template directory not found at %s — creating from scratch", TEMPLATE_DIR)
            frontend_dir.mkdir(parents=True, exist_ok=True)

        # Update package.json with system slug
        system_slug = design.get("system_name", "wat-system").lower().replace(" ", "-")
        pkg_path = frontend_dir / "package.json"
        if pkg_path.is_file():
            pkg_content = pkg_path.read_text(encoding="utf-8")
            pkg_content = pkg_content.replace("{SYSTEM_SLUG}", system_slug)
            pkg_path.write_text(pkg_content, encoding="utf-8")

        # Generate root layout
        layout_path = frontend_dir / "src" / "app" / "layout.tsx"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        layout_path.write_text(generate_root_layout(design), encoding="utf-8")
        logger.info("Generated root layout.tsx")

        # Generate marketing landing page
        marketing_dir = frontend_dir / "src" / "app" / "(marketing)"
        marketing_dir.mkdir(parents=True, exist_ok=True)
        (marketing_dir / "layout.tsx").write_text(
            "export default function MarketingLayout({ children }: { children: React.ReactNode }) {\n  return <>{children}</>;\n}\n",
            encoding="utf-8",
        )
        (marketing_dir / "page.tsx").write_text(
            generate_landing_page(manifest, design),
            encoding="utf-8",
        )
        logger.info("Generated marketing landing page")

        # Generate dashboard layout
        dashboard_dir = frontend_dir / "src" / "app" / "(dashboard)"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        (dashboard_dir / "layout.tsx").write_text(
            generate_dashboard_layout(manifest, design),
            encoding="utf-8",
        )

        # Generate dashboard home
        dashboard_home = dashboard_dir / "dashboard"
        dashboard_home.mkdir(parents=True, exist_ok=True)
        (dashboard_home / "page.tsx").write_text(
            generate_dashboard_page(manifest, design),
            encoding="utf-8",
        )
        logger.info("Generated dashboard page")

        # Generate tool pages
        pages_generated = []
        for tool in tools:
            tool_name = tool["name"]
            route_name = tool_name.replace("_", "-")
            tool_dir = dashboard_dir / route_name
            tool_dir.mkdir(parents=True, exist_ok=True)
            page_content = generate_tool_page(tool, design.get("system_name", ""))
            (tool_dir / "page.tsx").write_text(page_content, encoding="utf-8")
            pages_generated.append(f"(dashboard)/{route_name}/page.tsx")
            logger.info("Generated tool page: %s", route_name)

        # Generate pipeline page
        pipeline_dir = dashboard_dir / "pipeline"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / "page.tsx").write_text(
            generate_pipeline_page(manifest),
            encoding="utf-8",
        )
        pages_generated.append("(dashboard)/pipeline/page.tsx")
        logger.info("Generated pipeline page")

        # Ensure components are present
        components_dir = frontend_dir / "src" / "components"
        components_dir.mkdir(parents=True, exist_ok=True)

        # Ensure lib and styles are present
        (frontend_dir / "src" / "lib").mkdir(parents=True, exist_ok=True)
        (frontend_dir / "src" / "styles").mkdir(parents=True, exist_ok=True)

        # Ensure public dir exists
        (frontend_dir / "public").mkdir(parents=True, exist_ok=True)

        file_count = sum(1 for _ in frontend_dir.rglob("*") if _.is_file())
        logger.info("Frontend generation complete: %d files", file_count)

        return {
            "status": "success",
            "data": {
                "pages_generated": pages_generated,
                "file_count": file_count,
                "design_file": design_path,
            },
            "message": f"Frontend generated with {len(pages_generated)} pages",
        }

    except Exception as e:
        logger.error("Frontend generation failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
