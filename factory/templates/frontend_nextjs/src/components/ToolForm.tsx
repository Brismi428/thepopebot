{/* Tool form component template — generates form fields from tool arguments */}
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Loader2 } from 'lucide-react';

interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'file';
  required?: boolean;
  placeholder?: string;
  choices?: string[];
  defaultValue?: string | number | boolean;
  help?: string;
}

interface ToolFormProps {
  toolName: string;
  fields: FormField[];
  apiEndpoint: string;
  onResult: (result: any) => void;
  onError: (error: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function ToolForm({ toolName, fields, apiEndpoint, onResult, onError }: ToolFormProps) {
  const [values, setValues] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    fields.forEach((f) => {
      if (f.defaultValue !== undefined) initial[f.name] = f.defaultValue;
      else if (f.type === 'checkbox') initial[f.name] = false;
      else initial[f.name] = '';
    });
    return initial;
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    fields.forEach((f) => {
      if (f.required && !values[f.name] && values[f.name] !== 0 && values[f.name] !== false) {
        newErrors[f.name] = `${f.label} is required`;
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}${apiEndpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(err.detail || err.message || `HTTP ${response.status}`);
      }

      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await response.json();
        onResult(data);
      } else if (contentType.includes('pdf') || contentType.includes('csv') || contentType.includes('octet-stream')) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = response.headers.get('content-disposition')?.match(/filename="?(.+)"?/)?.[1] || 'download';
        onResult({ _file: true, url, filename, contentType });
      } else {
        const text = await response.text();
        onResult({ _raw: true, text });
      }
    } catch (err: any) {
      onError(err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const renderField = (field: FormField) => {
    const error = errors[field.name];
    const id = `field-${field.name}`;
    const errorId = `error-${field.name}`;

    return (
      <div key={field.name} className="space-y-1">
        <label htmlFor={id} className="block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {field.label}
          {field.required && <span className="ml-1" style={{ color: 'var(--error)' }} aria-hidden="true">*</span>}
        </label>
        {field.help && (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{field.help}</p>
        )}

        {field.type === 'select' && field.choices ? (
          <select
            id={id}
            value={values[field.name] || ''}
            onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))}
            className={`input-field ${error ? 'error' : ''}`}
            aria-describedby={error ? errorId : undefined}
            aria-invalid={!!error}
          >
            <option value="">Select...</option>
            {field.choices.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        ) : field.type === 'textarea' ? (
          <textarea
            id={id}
            value={values[field.name] || ''}
            onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))}
            className={`input-field h-24 py-2 ${error ? 'error' : ''}`}
            placeholder={field.placeholder}
            aria-describedby={error ? errorId : undefined}
            aria-invalid={!!error}
          />
        ) : field.type === 'checkbox' ? (
          <div className="flex items-center gap-2">
            <input
              id={id}
              type="checkbox"
              checked={!!values[field.name]}
              onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.checked }))}
              className="w-4 h-4 rounded focus:ring-2 focus:ring-offset-2"
              style={{ accentColor: 'var(--accent)' }}
              aria-describedby={error ? errorId : undefined}
              aria-invalid={!!error}
            />
          </div>
        ) : (
          <input
            id={id}
            type={field.type === 'number' ? 'number' : 'text'}
            value={values[field.name] ?? ''}
            onChange={(e) => setValues((v) => ({
              ...v,
              [field.name]: field.type === 'number' ? (e.target.value ? Number(e.target.value) : '') : e.target.value,
            }))}
            className={`input-field ${error ? 'error' : ''}`}
            placeholder={field.placeholder}
            aria-describedby={error ? errorId : undefined}
            aria-invalid={!!error}
          />
        )}

        {error && (
          <p id={errorId} className="text-xs font-medium" style={{ color: 'var(--error)' }} role="alert">
            {error}
          </p>
        )}
      </div>
    );
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {fields.map(renderField)}
      <button
        type="submit"
        disabled={loading}
        className="btn-primary inline-flex items-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span>Running...</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4" aria-hidden="true" />
            <span>Run {toolName}</span>
          </>
        )}
      </button>
    </motion.form>
  );
}
