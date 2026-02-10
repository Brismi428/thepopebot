---
name: n8n-error-recovery
description: "Expert knowledge for handling runtime errors, implementing retry logic, and building resilient n8n workflows. Activates when: workflow fails, needs retry logic, error handling, graceful degradation."
version: 1.0.0
---

# n8n Error Recovery Skill

## Overview

Build resilient workflows that handle failures gracefully. This skill covers error detection, retry strategies, fallback patterns, and recovery mechanisms.

---

## Error Handling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Error Handling Layers                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Node-Level         │ retryOnFail, continueOnFail  │
│  Layer 2: Branch-Level       │ IF node error routing        │
│  Layer 3: Workflow-Level     │ Error Trigger workflow       │
│  Layer 4: System-Level       │ Monitoring & alerting        │
└─────────────────────────────────────────────────────────────┘
```

---

## Node-Level Error Handling

### Retry on Failure

```json
{
  "name": "HTTP Request",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {...},
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 1000
}
```

**Best Practices**:
- Use for transient failures (network, rate limits)
- Exponential backoff for APIs: 1s → 2s → 4s
- Set reasonable maxTries (3-5)

### Continue on Fail

```json
{
  "name": "Optional API Call",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {...},
  "continueOnFail": true
}
```

**When to Use**:
- Non-critical operations
- Enrichment that can be skipped
- Parallel branches where one can fail

**Accessing Error Data**:
```javascript
// When continueOnFail: true, check for error
if ($json.error) {
  // Error occurred
  const errorMessage = $json.error.message;
  const errorCode = $json.error.code;
}
```

---

## Branch-Level Error Handling

### Error Detection Pattern

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Risky Node   │────▶│   IF Node   │────▶│ Success Path │
│ (continue=T) │     │ (check err) │     └──────────────┘
└──────────────┘     └──────┬──────┘
                           │ error
                           ▼
                    ┌──────────────┐
                    │  Error Path  │
                    └──────────────┘
```

### IF Node Error Check

```json
{
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "boolean": [{
        "value1": "={{ $json.error !== undefined }}",
        "value2": true
      }]
    }
  }
}
```

### Error Router Pattern

```javascript
// Code node to categorize errors
const error = $json.error;

if (!error) {
  return { success: true, data: $json };
}

// Categorize error
let errorType = 'unknown';
let recoverable = false;

if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
  errorType = 'network';
  recoverable = true;
} else if (error.httpCode === 429) {
  errorType = 'rate_limit';
  recoverable = true;
} else if (error.httpCode === 401 || error.httpCode === 403) {
  errorType = 'auth';
  recoverable = false;
} else if (error.httpCode >= 500) {
  errorType = 'server';
  recoverable = true;
}

return {
  success: false,
  errorType,
  recoverable,
  originalError: error
};
```

---

## Workflow-Level Error Handling

### Error Trigger Workflow

Create a separate workflow triggered by errors:

```json
{
  "name": "Error Handler",
  "nodes": [
    {
      "name": "Error Trigger",
      "type": "n8n-nodes-base.errorTrigger",
      "parameters": {}
    },
    {
      "name": "Process Error",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Error data available in $json\nconst workflow = $json.workflow;\nconst execution = $json.execution;\nconst error = $json.execution.error;\n\nreturn {\n  workflowName: workflow.name,\n  executionId: execution.id,\n  errorMessage: error.message,\n  timestamp: new Date().toISOString()\n};"
      }
    },
    {
      "name": "Send Alert",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#alerts",
        "text": "🚨 Workflow Error\n*Workflow*: {{ $json.workflowName }}\n*Error*: {{ $json.errorMessage }}"
      }
    }
  ]
}
```

### Error Data Structure

```javascript
// Data available in Error Trigger
{
  "workflow": {
    "id": "workflow-id",
    "name": "Workflow Name"
  },
  "execution": {
    "id": "execution-id",
    "url": "https://n8n.example.com/execution/...",
    "error": {
      "message": "Error message",
      "stack": "Stack trace..."
    },
    "lastNodeExecuted": "Node Name"
  }
}
```

---

## Retry Strategies

### Strategy 1: Immediate Retry
```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 0
}
```
Use for: Flaky operations with instant recovery

### Strategy 2: Fixed Interval
```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 5000
}
```
Use for: Rate-limited APIs with known cooldown

### Strategy 3: Exponential Backoff (Code Node)
```javascript
// Store retry count in workflow static data
const staticData = $getWorkflowStaticData('node');
staticData.retryCount = (staticData.retryCount || 0) + 1;

const baseDelay = 1000; // 1 second
const maxDelay = 60000; // 1 minute
const delay = Math.min(baseDelay * Math.pow(2, staticData.retryCount - 1), maxDelay);

// Add jitter to prevent thundering herd
const jitter = Math.random() * 1000;

await new Promise(resolve => setTimeout(resolve, delay + jitter));

return $json;
```

### Strategy 4: Circuit Breaker (Code Node)
```javascript
const staticData = $getWorkflowStaticData('global');
const serviceName = 'external-api';

// Initialize circuit breaker state
if (!staticData.circuits) {
  staticData.circuits = {};
}
if (!staticData.circuits[serviceName]) {
  staticData.circuits[serviceName] = {
    failures: 0,
    lastFailure: null,
    state: 'closed' // closed, open, half-open
  };
}

const circuit = staticData.circuits[serviceName];
const cooldownPeriod = 60000; // 1 minute

// Check circuit state
if (circuit.state === 'open') {
  const timeSinceFailure = Date.now() - circuit.lastFailure;
  if (timeSinceFailure > cooldownPeriod) {
    circuit.state = 'half-open';
  } else {
    throw new Error(`Circuit breaker open for ${serviceName}`);
  }
}

return { ....$json, circuitState: circuit.state };
```

---

## Recovery Patterns

### Pattern 1: Fallback Value
```javascript
// Provide default when API fails
const data = $json.error 
  ? { status: 'unknown', timestamp: new Date().toISOString() }
  : $json;

return data;
```

### Pattern 2: Alternative Service
```
┌─────────────┐     ┌─────────────┐
│ Primary API │────▶│   IF Node   │─── success ──▶ Continue
│ (continue)  │     │             │
└─────────────┘     └──────┬──────┘
                          │ failure
                          ▼
                   ┌─────────────┐
                   │ Backup API  │────────────▶ Continue
                   └─────────────┘
```

### Pattern 3: Queue for Retry
```javascript
// On failure, queue for later retry
if ($json.error) {
  return {
    action: 'queue',
    retryAt: new Date(Date.now() + 300000).toISOString(), // 5 min
    originalPayload: $json.originalData,
    attemptCount: ($json.attemptCount || 0) + 1
  };
}

return { action: 'success', data: $json };
```

### Pattern 4: Dead Letter Queue
```
┌───────────┐     ┌───────────┐     ┌───────────┐
│  Process  │────▶│  Retry 3x │────▶│   Alert   │
│           │     │           │     │           │
└───────────┘     └─────┬─────┘     └───────────┘
                       │ all failed
                       ▼
                ┌─────────────┐
                │ Dead Letter │
                │   Queue     │
                └─────────────┘
```

---

## Common Error Patterns

### HTTP Errors

| Code | Type | Recovery |
|------|------|----------|
| 400 | Bad Request | Fix input, don't retry |
| 401 | Unauthorized | Refresh credentials |
| 403 | Forbidden | Check permissions, don't retry |
| 404 | Not Found | Log and skip |
| 429 | Rate Limited | Exponential backoff |
| 500 | Server Error | Retry with backoff |
| 502/503/504 | Gateway/Timeout | Retry immediately |

### Error Classification Code
```javascript
const httpCode = $json.error?.httpCode || $json.error?.response?.status;

let strategy = 'fail';
let waitTime = 0;

switch (true) {
  case httpCode === 429:
    strategy = 'retry';
    waitTime = parseInt($json.error.headers?.['retry-after'] || '60') * 1000;
    break;
  case httpCode >= 500:
    strategy = 'retry';
    waitTime = 5000;
    break;
  case httpCode === 401:
    strategy = 'refresh_auth';
    break;
  case httpCode >= 400:
    strategy = 'fail';
    break;
  default:
    strategy = 'retry';
    waitTime = 1000;
}

return { strategy, waitTime, originalError: $json.error };
```

---

## Monitoring & Alerting

### Execution Status Check
```javascript
// Get recent failures
n8n_executions({
  action: 'list',
  workflowId: 'workflow-id',
  status: 'failed',
  limit: 10
})
```

### Alert Thresholds
```javascript
// Code node to check failure rate
const executions = $json.executions;
const failedCount = executions.filter(e => e.status === 'failed').length;
const failureRate = failedCount / executions.length;

if (failureRate > 0.1) { // > 10% failure rate
  return {
    alert: true,
    severity: 'warning',
    message: `High failure rate: ${(failureRate * 100).toFixed(1)}%`
  };
}

return { alert: false };
```

---

## Best Practices

1. **Fail Fast**: Don't retry on unrecoverable errors (auth, validation)
2. **Idempotency**: Design operations to be safely retryable
3. **Timeouts**: Set reasonable timeouts on all external calls
4. **Logging**: Log enough context to debug failures
5. **Alerts**: Alert on unusual failure patterns, not every failure
6. **Testing**: Test failure scenarios, not just happy paths

---

## Quick Reference

### Enable Retry
```json
{"retryOnFail": true, "maxTries": 3, "waitBetweenTries": 1000}
```

### Enable Continue
```json
{"continueOnFail": true}
```

### Check for Error
```javascript
if ($json.error) { /* handle error */ }
```

### Error Trigger Node
```json
{"type": "n8n-nodes-base.errorTrigger"}
```
