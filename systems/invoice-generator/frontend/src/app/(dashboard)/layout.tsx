'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Workflow, Wrench, Moon, Sun, Home } from 'lucide-react';
import { useState, useEffect } from 'react';
import clsx from 'clsx';

const NAV_ITEMS = [
    {
        "href": "/dashboard/generate-invoice-pdf/",
        "label": "Generate Invoice Pdf"
    },
    {
        "href": "/dashboard/load-config/",
        "label": "Load Config"
    },
    {
        "href": "/dashboard/manage-counter/",
        "label": "Manage Counter"
    },
    {
        "href": "/dashboard/parse-invoice-input/",
        "label": "Parse Invoice Input"
    },
    {
        "href": "/dashboard/save-invoice/",
        "label": "Save Invoice"
    },
    {
        "href": "/dashboard/pipeline/",
        "label": "Pipeline"
    }
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const stored = localStorage.getItem('theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(stored as 'light' | 'dark');
  }, []);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className="hidden lg:flex flex-col w-60 border-r p-4 shrink-0"
        style={{ borderColor: 'var(--border)', backgroundColor: 'var(--bg-secondary)' }}
      >
        <Link href="/dashboard/" className="flex items-center gap-2 px-2 mb-8">
          <Workflow className="w-6 h-6" style={{ color: 'var(--accent)' }} />
          <span className="font-heading font-bold text-lg">Invoice Generator WAT System</span>
        </Link>
        <nav className="flex-1 space-y-1" aria-label="Dashboard navigation">
          <Link
            href="/dashboard/"
            className={clsx(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              pathname === '/dashboard/' || pathname === '/dashboard'
                ? 'bg-[var(--accent-subtle)] text-[var(--accent)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
            )}
          >
            <Home className="w-4 h-4" />
            Overview
          </Link>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                pathname === item.href || pathname === item.href.replace(/\/$/, '')
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              )}
            >
              {item.href.includes('pipeline') ? (
                <Workflow className="w-4 h-4" />
              ) : (
                <Wrench className="w-4 h-4" />
              )}
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-[var(--bg-tertiary)]"
          style={{ color: 'var(--text-secondary)' }}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
          {theme === 'light' ? 'Dark mode' : 'Light mode'}
        </button>
      </aside>

      {/* Main content */}
      <main id="main-content" className="flex-1 p-6 md:p-8 lg:p-12 overflow-auto">
        {children}
      </main>
    </div>
  );
}
