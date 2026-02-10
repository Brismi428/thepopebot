---
name: n8n-performance
description: "Expert knowledge for optimizing n8n workflow performance, reducing execution time, and scaling workflows. Activates when: workflows are slow, need optimization, handling large data, scaling issues."
version: 1.0.0
---

# n8n Performance Skill

## Overview

Optimize workflow performance for speed, efficiency, and scale. This skill covers bottleneck identification, optimization techniques, and scaling strategies.

---

## Performance Metrics

### Targets by Workflow Type

| Type | Good | Acceptable | Needs Work |
|------|------|------------|------------|
| Simple (3-5 nodes) | <1s | 1-3s | >3s |
| Medium (5-10 nodes) | <5s | 5-15s | >15s |
| Complex (10+ nodes) | <30s | 30-60s | >60s |
| Data Processing | <1min | 1-5min | >5min |
| Batch Jobs | <10min | 10-30min | >30min |

### Key Metrics to Monitor
- **Execution Time**: Total workflow duration
- **Node Time**: Time per node
- **Memory Usage**: Peak memory consumption
- **API Calls**: External request count
- **Data Volume**: Items processed

---

## Optimization Patterns

### Pattern 1: Parallel Execution

**Before** (Sequential):
```
API 1 → wait → API 2 → wait → API 3 → Merge
Total: ~9 seconds (3s each)
```

**After** (Parallel):
```
┌→ API 1 ─┐
├→ API 2 ─┼→ Merge
└→ API 3 ─┘
Total: ~3 seconds
```

**Implementation**:
```json
{
  "nodes": [
    {"name": "Start", "type": "n8n-nodes-base.manualTrigger"},
    {"name": "API 1", "type": "n8n-nodes-base.httpRequest"},
    {"name": "API 2", "type": "n8n-nodes-base.httpRequest"},
    {"name": "API 3", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Merge", "type": "n8n-nodes-base.merge", 
     "parameters": {"mode": "combine", "combinationMode": "mergeByPosition"}}
  ],
  "connections": {
    "Start": {"main": [[
      {"node": "API 1"}, {"node": "API 2"}, {"node": "API 3"}
    ]]},
    "API 1": {"main": [[{"node": "Merge", "index": 0}]]},
    "API 2": {"main": [[{"node": "Merge", "index": 1}]]},
    "API 3": {"main": [[{"node": "Merge", "index": 2}]]}
  }
}
```

---

### Pattern 2: Batch Processing

**Before** (All at once - memory overflow):
```javascript
// Process 100,000 items at once
return items.map(processItem);
```

**After** (Batched - controlled memory):
```json
{
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 100,
    "options": {
      "reset": false
    }
  }
}
```

**Batch Size Guidelines**:
| Data Type | Recommended Batch Size |
|-----------|----------------------|
| Simple JSON | 500-1000 |
| Complex Objects | 100-200 |
| With API Calls | 10-50 |
| File Processing | 1-10 |

---

### Pattern 3: Early Filtering

**Before** (Filter Late):
```
Fetch 10,000 → Transform All → Filter to 100
Time: 30 seconds
```

**After** (Filter Early):
```
Fetch 10,000 → Filter to 100 → Transform 100
Time: 3 seconds
```

**Implementation**:
```json
{
  "type": "n8n-nodes-base.filter",
  "parameters": {
    "conditions": {
      "boolean": [{
        "value1": "={{ $json.status }}",
        "value2": "active",
        "operation": "equals"
      }]
    }
  }
}
```

---

### Pattern 4: Caching

**Before** (Redundant calls):
```javascript
// Same API called for each item
for (item of items) {
  const config = await fetchConfig(); // Called N times
  process(item, config);
}
```

**After** (Cached):
```javascript
// Use workflow static data for caching
const cache = $getWorkflowStaticData('global');
const cacheKey = 'config';
const cacheTTL = 300000; // 5 minutes

if (!cache[cacheKey] || Date.now() > cache[`${cacheKey}_expiry`]) {
  cache[cacheKey] = await $helpers.httpRequest({
    url: 'https://api.example.com/config'
  });
  cache[`${cacheKey}_expiry`] = Date.now() + cacheTTL;
}

return { config: cache[cacheKey], ...$json };
```

---

### Pattern 5: Bulk API Operations

**Before** (N API calls):
```javascript
// 100 items = 100 API calls
for (const item of items) {
  await createRecord(item);
}
```

**After** (1 bulk call):
```javascript
// 100 items = 1 API call
await createRecordsBulk(items);
```

**HTTP Request for Bulk**:
```json
{
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/bulk",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify($input.all().map(i => i.json)) }}"
  }
}
```

---

### Pattern 6: Lazy Loading

**Before** (Load everything):
```javascript
// Fetch all related data upfront
const users = await fetchUsers();
const orders = await fetchOrdersForAll(users);
const products = await fetchProductsForAll(orders);
```

**After** (Load on demand):
```javascript
// Fetch only what's needed
const activeUsers = await fetchUsers({ status: 'active' });
// Only fetch orders for users that need them
```

---

### Pattern 7: Connection Reuse

**Code Node** (Connection pooling):
```javascript
// Reuse HTTP agent across requests
const staticData = $getWorkflowStaticData('global');

if (!staticData.httpAgent) {
  const https = require('https');
  staticData.httpAgent = new https.Agent({
    keepAlive: true,
    maxSockets: 10
  });
}

const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  agent: staticData.httpAgent
});

return response;
```

---

## Node-Specific Optimizations

### HTTP Request Node
```json
{
  "parameters": {
    "options": {
      "timeout": 30000,
      "response": {
        "response": {
          "neverError": true
        }
      }
    }
  }
}
```

### Code Node
```javascript
// ❌ Slow - Creates new array each iteration
let result = [];
for (const item of items) {
  result = [...result, processItem(item)];
}

// ✅ Fast - Mutates in place
const result = [];
for (const item of items) {
  result.push(processItem(item));
}

// ✅ Faster - Use map
const result = items.map(processItem);
```

### Set Node vs Code Node
- **Set Node**: Faster for simple mappings
- **Code Node**: Better for complex logic

Use Set Node when possible.

---

## Memory Optimization

### Large Data Handling
```javascript
// ❌ Bad - Loads all into memory
const allData = await fetchAllRecords();
const processed = allData.map(process);

// ✅ Good - Stream processing
async function* fetchRecords() {
  let page = 1;
  while (true) {
    const batch = await fetchPage(page++);
    if (batch.length === 0) break;
    yield* batch;
  }
}

const results = [];
for await (const record of fetchRecords()) {
  results.push(process(record));
  if (results.length >= 100) {
    await saveBatch(results);
    results.length = 0; // Clear array
  }
}
```

### Binary Data
```javascript
// ❌ Bad - Base64 in memory
const fileContent = Buffer.from(data).toString('base64');

// ✅ Good - Stream to file
const fs = require('fs');
const stream = fs.createWriteStream('/tmp/file');
stream.write(data);
stream.end();
```

---

## Database Query Optimization

### PostgreSQL
```sql
-- ❌ Slow
SELECT * FROM orders WHERE customer_id IN 
  (SELECT id FROM customers WHERE status = 'active');

-- ✅ Fast - Use JOIN
SELECT o.* FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.status = 'active';

-- ✅ Add index
CREATE INDEX idx_orders_customer ON orders(customer_id);
```

### Limit Results
```json
{
  "parameters": {
    "operation": "executeQuery",
    "query": "SELECT * FROM orders ORDER BY created_at DESC LIMIT 1000"
  }
}
```

---

## Webhook Optimization

### Fast Response Pattern
```
Webhook (responseMode: onReceived, responseCode: 202)
    │
    ├──► Immediate 202 Response to Caller
    │
    └──► Continue Processing Asynchronously
             │
             └──► Store Result / Send Notification
```

```json
{
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "responseMode": "onReceived",
    "responseCode": 202,
    "responseData": "noData"
  }
}
```

---

## Monitoring & Profiling

### Execution Time Tracking
```javascript
// Add timing to Code node
const startTime = Date.now();

// ... your processing ...

const executionTime = Date.now() - startTime;
return {
  ...$json,
  _metrics: {
    nodeExecutionTime: executionTime,
    itemCount: $input.all().length
  }
};
```

### Identify Slow Nodes
```javascript
// Use n8n execution data
n8n_executions({action: 'get', executionId: 'exec-id'})

// Analyze node timings in result
const execution = $json;
const nodeTimes = Object.entries(execution.data.resultData.runData)
  .map(([name, data]) => ({
    name,
    time: data[0].executionTime
  }))
  .sort((a, b) => b.time - a.time);

return { slowestNodes: nodeTimes.slice(0, 5) };
```

---

## Scaling Strategies

### Horizontal Scaling
- Run multiple n8n instances
- Use queue mode for workload distribution
- External database for shared state

### Workflow Splitting
```
Main Workflow (orchestrator)
    │
    ├──► Sub-workflow 1 (data fetch)
    ├──► Sub-workflow 2 (processing)
    └──► Sub-workflow 3 (output)
```

### Queue-Based Processing
```
Webhook → Add to Queue → Process Queue (separate workflow)
           │
           └──► Immediate 202 Response
```

---

## Quick Wins Checklist

- [ ] Parallel independent API calls
- [ ] Batch large data sets (100-500 items)
- [ ] Filter early, transform late
- [ ] Cache repeated lookups
- [ ] Use bulk API endpoints
- [ ] Set timeouts on all HTTP requests
- [ ] Use Set node instead of Code for simple mappings
- [ ] Limit database query results
- [ ] Respond to webhooks before processing

---

## Performance Anti-Patterns

❌ **Avoid These**:
1. Sequential API calls that could be parallel
2. Processing all items before filtering
3. Fetching full objects when you need one field
4. No timeouts on external calls
5. Large binary data in memory
6. N+1 query patterns
7. Unbounded result sets
8. Synchronous webhook responses for long operations
