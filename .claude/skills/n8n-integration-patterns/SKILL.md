---
name: n8n-integration-patterns
description: "Expert knowledge for integrating external services, APIs, and databases in n8n. Activates when: connecting services, building integrations, syncing data between systems."
version: 1.0.0
---

# n8n Integration Patterns Skill

## Overview

Connect external services effectively. This skill covers API integration, database connections, authentication patterns, and data synchronization strategies.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Hub                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │   CRM   │   │  Email  │   │  Cloud  │   │ Payment │     │
│  │ Systems │   │Services │   │ Storage │   │ Gateway │     │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘     │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                    ┌───────▼───────┐                        │
│                    │    n8n Hub    │                        │
│                    └───────┬───────┘                        │
│                            │                                 │
│       ┌─────────────┬──────┴──────┬─────────────┐           │
│       │             │             │             │           │
│  ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐     │
│  │   ERP   │   │Analytics│   │ Support │   │Marketing│     │
│  │ System  │   │Platform │   │  Desk   │   │Platform │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## HTTP Request Node Patterns

### Basic GET Request
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "GET",
    "url": "https://api.example.com/users",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth",
    "options": {
      "timeout": 30000
    }
  }
}
```

### POST with JSON Body
```json
{
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/users",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ name: $json.name, email: $json.email }) }}"
  }
}
```

### With Query Parameters
```json
{
  "parameters": {
    "method": "GET",
    "url": "https://api.example.com/search",
    "sendQuery": true,
    "queryParameters": {
      "parameters": [
        {"name": "q", "value": "={{ $json.searchTerm }}"},
        {"name": "limit", "value": "100"}
      ]
    }
  }
}
```

### With Headers
```json
{
  "parameters": {
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {"name": "X-Custom-Header", "value": "custom-value"},
        {"name": "Accept", "value": "application/json"}
      ]
    }
  }
}
```

---

## Authentication Patterns

### API Key (Header)
```json
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpHeaderAuth"
}
```
Credential: Header Name: `Authorization`, Value: `Bearer YOUR_KEY`

### API Key (Query Parameter)
```json
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpQueryAuth"
}
```

### OAuth2
```json
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "oAuth2Api"
}
```

### Custom OAuth2 (Code Node)
```javascript
// Refresh OAuth token if expired
const staticData = $getWorkflowStaticData('global');
const now = Date.now();

if (!staticData.token || now > staticData.tokenExpiry) {
  const response = await $helpers.httpRequest({
    method: 'POST',
    url: 'https://auth.example.com/oauth/token',
    body: {
      grant_type: 'client_credentials',
      client_id: $env.CLIENT_ID,
      client_secret: $env.CLIENT_SECRET
    }
  });
  
  staticData.token = response.access_token;
  staticData.tokenExpiry = now + (response.expires_in * 1000) - 60000; // 1 min buffer
}

return { token: staticData.token };
```

---

## Pagination Patterns

### Offset-Based Pagination
```javascript
// Code node for paginated API
const results = [];
let offset = 0;
const limit = 100;
let hasMore = true;

while (hasMore) {
  const response = await $helpers.httpRequest({
    method: 'GET',
    url: 'https://api.example.com/items',
    qs: { offset, limit }
  });
  
  results.push(...response.items);
  offset += limit;
  hasMore = response.items.length === limit;
  
  // Safety limit
  if (results.length > 10000) break;
}

return results.map(item => ({ json: item }));
```

### Cursor-Based Pagination
```javascript
const results = [];
let cursor = null;

do {
  const response = await $helpers.httpRequest({
    method: 'GET',
    url: 'https://api.example.com/items',
    qs: { cursor, limit: 100 }
  });
  
  results.push(...response.data);
  cursor = response.next_cursor;
  
} while (cursor);

return results.map(item => ({ json: item }));
```

### Link Header Pagination
```javascript
const results = [];
let url = 'https://api.example.com/items';

while (url) {
  const response = await $helpers.httpRequestWithAuthentication.call(
    this,
    'myCredential',
    { method: 'GET', url, returnFullResponse: true }
  );
  
  results.push(...JSON.parse(response.body));
  
  // Parse Link header for next URL
  const linkHeader = response.headers.link;
  const nextMatch = linkHeader?.match(/<([^>]+)>;\s*rel="next"/);
  url = nextMatch ? nextMatch[1] : null;
}

return results.map(item => ({ json: item }));
```

---

## Database Integration

### PostgreSQL Query
```json
{
  "type": "n8n-nodes-base.postgres",
  "parameters": {
    "operation": "executeQuery",
    "query": "SELECT * FROM users WHERE status = $1",
    "options": {
      "queryParams": "={{ [$json.status] }}"
    }
  }
}
```

### MySQL Insert
```json
{
  "type": "n8n-nodes-base.mySql",
  "parameters": {
    "operation": "insert",
    "table": "orders",
    "columns": "customer_id, product_id, quantity, total",
    "options": {}
  }
}
```

### MongoDB Aggregation
```json
{
  "type": "n8n-nodes-base.mongoDb",
  "parameters": {
    "operation": "aggregate",
    "collection": "sales",
    "query": "[{\"$match\": {\"date\": {\"$gte\": \"{{ $json.startDate }}\"}}}, {\"$group\": {\"_id\": \"$product\", \"total\": {\"$sum\": \"$amount\"}}}]"
  }
}
```

---

## Common Service Integrations

### Salesforce
```javascript
// Query Salesforce records
const query = `SELECT Id, Name, Email FROM Contact WHERE LastModifiedDate > ${$json.lastSync}`;

// Use Salesforce node with SOQL query
```

### HubSpot
```json
{
  "type": "n8n-nodes-base.hubspot",
  "parameters": {
    "resource": "contact",
    "operation": "create",
    "email": "={{ $json.email }}",
    "additionalFields": {
      "firstName": "={{ $json.firstName }}",
      "lastName": "={{ $json.lastName }}"
    }
  }
}
```

### Slack
```json
{
  "type": "n8n-nodes-base.slack",
  "parameters": {
    "resource": "message",
    "operation": "post",
    "channel": "#general",
    "text": "={{ $json.message }}",
    "attachments": [],
    "otherOptions": {
      "unfurlLinks": false
    }
  }
}
```

### Google Sheets
```json
{
  "type": "n8n-nodes-base.googleSheets",
  "parameters": {
    "operation": "append",
    "documentId": "your-sheet-id",
    "sheetName": "Sheet1",
    "options": {
      "valueInputMode": "USER_ENTERED"
    }
  }
}
```

---

## Data Sync Patterns

### One-Way Sync (Source → Destination)
```
┌────────────┐     ┌────────────┐     ┌────────────┐
│   Source   │────▶│  Transform │────▶│Destination │
│   System   │     │   & Map    │     │   System   │
└────────────┘     └────────────┘     └────────────┘
```

### Two-Way Sync (Bidirectional)
```
┌────────────┐                        ┌────────────┐
│  System A  │◀────── Sync ──────────▶│  System B  │
│            │        Agent           │            │
└────────────┘                        └────────────┘
```

### Change Detection
```javascript
// Track changes using timestamps
const staticData = $getWorkflowStaticData('global');
const lastSync = staticData.lastSync || '1970-01-01T00:00:00Z';

// Fetch only changed records
const response = await $helpers.httpRequest({
  url: 'https://api.source.com/records',
  qs: { modified_after: lastSync }
});

// Update last sync time
staticData.lastSync = new Date().toISOString();

return response.records.map(r => ({ json: r }));
```

### Conflict Resolution
```javascript
// Simple last-write-wins strategy
const sourceRecord = $json.source;
const destRecord = $json.destination;

// Compare timestamps
const sourceTime = new Date(sourceRecord.updatedAt);
const destTime = new Date(destRecord.updatedAt);

if (sourceTime > destTime) {
  return { winner: 'source', data: sourceRecord };
} else {
  return { winner: 'destination', data: destRecord };
}
```

---

## Error Handling for Integrations

### Retry with Backoff
```json
{
  "retryOnFail": true,
  "maxTries": 5,
  "waitBetweenTries": 2000
}
```

### API-Specific Error Handling
```javascript
try {
  const response = await $helpers.httpRequest({
    url: 'https://api.example.com/resource',
    method: 'POST',
    body: $json
  });
  return { success: true, data: response };
} catch (error) {
  const status = error.response?.status;
  
  if (status === 429) {
    // Rate limited - get retry-after
    const retryAfter = error.response.headers['retry-after'];
    return { retry: true, waitSeconds: parseInt(retryAfter) || 60 };
  }
  
  if (status === 409) {
    // Conflict - record already exists
    return { conflict: true, existingId: error.response.data.id };
  }
  
  throw error; // Re-throw unexpected errors
}
```

---

## Best Practices

1. **Use Built-in Nodes**: n8n has 500+ integrations - use them before HTTP Request
2. **Cache Tokens**: Store OAuth tokens in static data
3. **Handle Rate Limits**: Implement backoff strategies
4. **Batch Operations**: Use bulk APIs when available
5. **Idempotency**: Use unique IDs to prevent duplicates
6. **Monitor Usage**: Track API calls and costs
7. **Secure Credentials**: Never hardcode, use n8n credentials

---

## Quick Reference

### Find Integration Nodes
```javascript
// Search for service-specific nodes
search_nodes({query: 'salesforce', includeExamples: true})
search_nodes({query: 'google sheets', includeExamples: true})
```

### HTTP Request Essentials
```json
{
  "method": "POST",
  "url": "https://api.example.com",
  "sendBody": true,
  "authentication": "predefinedCredentialType",
  "options": {"timeout": 30000}
}
```
