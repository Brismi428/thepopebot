'use client';
// Pipeline wizard component template — multi-step form for running the full pipeline

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Loader2, CheckCircle, ArrowRight, ArrowLeft, AlertCircle } from 'lucide-react';

interface PipelineStep {
  name: string;
  label: string;
  description: string;
}

interface PipelineWizardProps {
  steps: PipelineStep[];
  onResult: (result: any) => void;
  onError: (error: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function PipelineWizard({ steps, onResult, onError }: PipelineWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [inputData, setInputData] = useState('');
  const [loading, setLoading] = useState(false);
  const [stepResults, setStepResults] = useState<Array<{ step: number; tool: string; status: string }>>([]);

  const handleRun = async () => {
    setLoading(true);
    setStepResults([]);
    try {
      let payload = {};
      if (inputData.trim()) {
        try {
          payload = JSON.parse(inputData);
        } catch {
          onError('Invalid JSON input');
          setLoading(false);
          return;
        }
      }

      const response = await fetch(`${API_BASE}/api/run-pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      if (data.steps) {
        setStepResults(data.steps);
      }
      onResult(data);
    } catch (err: any) {
      onError(err.message || 'Pipeline failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Step indicator */}
      <div className="flex items-center gap-2" role="list" aria-label="Pipeline steps">
        {steps.map((step, i) => {
          const stepResult = stepResults.find((r) => r.step === i + 1);
          const isActive = i === currentStep;
          return (
            <div key={step.name} className="flex items-center gap-2" role="listitem">
              <button
                onClick={() => setCurrentStep(i)}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-white'
                    : 'text-[var(--text-secondary)]'
                }`}
                style={{
                  backgroundColor: stepResult?.status === 'success'
                    ? 'var(--success)'
                    : stepResult?.status === 'failed'
                    ? 'var(--error)'
                    : isActive
                    ? 'var(--accent)'
                    : 'var(--bg-tertiary)',
                }}
                aria-label={`Step ${i + 1}: ${step.label}`}
                aria-current={isActive ? 'step' : undefined}
              >
                {stepResult?.status === 'success' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : stepResult?.status === 'failed' ? (
                  <AlertCircle className="w-4 h-4" />
                ) : (
                  i + 1
                )}
              </button>
              {i < steps.length - 1 && (
                <div className="w-8 h-px" style={{ backgroundColor: 'var(--border)' }} />
              )}
            </div>
          );
        })}
      </div>

      {/* Current step info */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -8 }}
          transition={{ duration: 0.2 }}
          className="card"
        >
          <h3 className="font-heading font-semibold text-lg mb-2">
            Step {currentStep + 1}: {steps[currentStep]?.label}
          </h3>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
            {steps[currentStep]?.description}
          </p>

          {currentStep === 0 && (
            <div className="space-y-2">
              <label htmlFor="pipeline-input" className="block text-sm font-medium">
                Pipeline Input (JSON)
              </label>
              <textarea
                id="pipeline-input"
                value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                className="input-field h-32 py-2 font-mono text-sm"
                placeholder='{"key": "value"}'
              />
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
          disabled={currentStep === 0}
          className="btn-ghost inline-flex items-center gap-2 disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Previous
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            onClick={() => setCurrentStep((s) => Math.min(steps.length - 1, s + 1))}
            className="btn-secondary inline-flex items-center gap-2"
          >
            Next <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </button>
        ) : (
          <button
            onClick={handleRun}
            disabled={loading}
            className="btn-primary inline-flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                Running Pipeline...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" aria-hidden="true" />
                Run Full Pipeline
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
