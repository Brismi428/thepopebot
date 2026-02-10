---
name: n8n-webhook-patterns
description: "Expert knowledge for webhook security, validation, and patterns in n8n. Activates when: creating webhooks, securing endpoints, handling external integrations, validating payloads."
version: 1.0.0
---

# n8n Webhook Patterns Skill

## Overview

Build secure, reliable webhook endpoints in n8n. This skill covers authentication, validation, rate limiting, and common webhook patterns.

---

## Webhook Node Configuration

### Basic Webhook
```json
{
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "path": "my-webhook",
    "httpMethod": "POST",
    "responseMode": "onReceived",
    "responseCode": 200,
    "responseData": "allEntries"
  }
}
```

### Webhook Parameters

| Parameter | Options | Use Case |
|-----------|---------|----------|
| `httpMethod` | GET, POST, PUT, DELETE, PATCH, HEAD | Match sender's method |
| `responseMode` | `onReceived`, `lastNode`, `responseNode` | When to respond |
| `authentication` | `none`, `basicAuth`, `headerAuth` | Auth method |

---

## Authentication Patterns

### Header Authentication (Recommended)
```json
{
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "authentication": "headerAuth",
    "options": {}
  },
  "credentials": {
    "httpHeaderAuth": {
      "id": "1",
      "name": "Webhook Auth"
    }
  }
}
```

Configure credential with:
- Header Name: `X-Webhook-Secret`
- Header Value: Your secret key

### Basic Auth
```json
{
  "parameters": {
    "authentication": "basicAuth"
  },
  "credentials": {
    "httpBasicAuth": {
      "id": "2",
      "name": "Basic Auth"
    }
  }
}
```

### HMAC Signature Verification (Code Node)
```javascript
// Verify webhook signature (e.g., Stripe, GitHub)
const crypto = require('crypto');

const payload = JSON.stringify($json.body);
const signature = $json.headers['x-webhook-signature'];
const secret = $env.WEBHOOK_SECRET;

// GitHub style (sha256)
const expectedSignature = 'sha256=' + crypto
  .createHmac('sha256', secret)
  .update(payload)
  .digest('hex');

if (signature !== expectedSignature) {
  throw new Error('Invalid webhook signature');
}

return $json;
```

### Stripe Signature Verification
```javascript
const crypto = require('crypto');

const payload = $json.body;
const signature = $json.headers['stripe-signature'];
const secret = $env.STRIPE_WEBHOOK_SECRET;

// Parse Stripe signature header
const parts = signature.split(',').reduce((acc, part) => {
  const [key, value] = part.split('=');
  acc[key] = value;
  return acc;
}, {});

const signedPayload = `${parts.t}.${JSON.stringify(payload)}`;
const expectedSignature = crypto
  .createHmac('sha256', secret)
  .update(signedPayload)
  .digest('hex');

if (parts.v1 !== expectedSignature) {
  throw new Error('Invalid Stripe signature');
}

return $json;
```

---

## Data Access (CRITICAL)

### ⚠️ Webhook Data Location
```javascript
// ❌ WRONG - Data is NOT at $json directly
const email = $json.email;

// ✅ CORRECT - Webhook data is under .body
const email = $json.body.email;

// Headers
const apiKey = $json.headers['x-api-key'];

// Query parameters
const userId = $json.query.userId;
```

### Available Webhook Data
```javascript
{
  body: {},           // POST/PUT body
  headers: {},        // Request headers
  query: {},          // URL query parameters
  params: {},         // URL path parameters
  webhookUrl: "",     // Full webhook URL
  executionMode: ""   // test/production
}
```

---

## Input Validation

### Schema Validation (Code Node)
```javascript
// Validate required fields
const body = $json.body;
const required = ['email', 'name', 'amount'];

for (const field of required) {
  if (!body[field]) {
    throw new Error(`Missing required field: ${field}`);
  }
}

// Validate types
if (typeof body.email !== 'string') {
  throw new Error('email must be a string');
}

if (typeof body.amount !== 'number' || body.amount < 0) {
  throw new Error('amount must be a positive number');
}

// Validate format
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(body.email)) {
  throw new Error('Invalid email format');
}

return { validated: true, data: body };
```

### Sanitization
```javascript
// Sanitize string inputs
const sanitize = (str) => {
  if (typeof str !== 'string') return str;
  return str
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML
    .substring(0, 1000);   // Limit length
};

const sanitized = {
  name: sanitize($json.body.name),
  email: sanitize($json.body.email),
  message: sanitize($json.body.message)
};

return { json: sanitized };
```

---

## Response Patterns

### Immediate Response
```json
{
  "parameters": {
    "responseMode": "onReceived",
    "responseCode": 200,
    "responseData": "allEntries"
  }
}
```

### Response After Processing
```json
{
  "parameters": {
    "responseMode": "lastNode"
  }
}
```

### Custom Response (Respond to Webhook Node)
```json
{
  "type": "n8n-nodes-base.respondToWebhook",
  "parameters": {
    "respondWith": "json",
    "responseBody": "={{ JSON.stringify({ success: true, id: $json.id }) }}",
    "options": {
      "responseCode": 201,
      "responseHeaders": {
        "entries": [
          {"name": "X-Request-Id", "value": "={{ $json.requestId }}"}
        ]
      }
    }
  }
}
```

### Async Pattern (Respond Immediately, Process Later)
```
Webhook (responseMode: onReceived)
    │
    ├──► Respond 202 Accepted
    │
    └──► Continue Processing ──► Store Result
```

---

## Rate Limiting Pattern

### In-Workflow Rate Limiting
```javascript
// Track requests per IP
const staticData = $getWorkflowStaticData('global');
const ip = $json.headers['x-forwarded-for'] || $json.headers['x-real-ip'] || 'unknown';
const now = Date.now();
const windowMs = 60000; // 1 minute
const maxRequests = 10;

// Initialize tracking
if (!staticData.rateLimits) {
  staticData.rateLimits = {};
}

// Clean old entries
for (const [key, data] of Object.entries(staticData.rateLimits)) {
  if (now - data.windowStart > windowMs) {
    delete staticData.rateLimits[key];
  }
}

// Check rate limit
if (!staticData.rateLimits[ip]) {
  staticData.rateLimits[ip] = { windowStart: now, count: 0 };
}

const rateData = staticData.rateLimits[ip];
if (now - rateData.windowStart > windowMs) {
  rateData.windowStart = now;
  rateData.count = 0;
}

rateData.count++;

if (rateData.count > maxRequests) {
  throw new Error('Rate limit exceeded');
}

return $json;
```

---

## Common Webhook Integrations

### GitHub Webhooks
```javascript
// Verify GitHub signature
const event = $json.headers['x-github-event'];
const delivery = $json.headers['x-github-delivery'];

// Route by event type
switch (event) {
  case 'push':
    return { event: 'push', data: $json.body };
  case 'pull_request':
    return { event: 'pr', data: $json.body };
  case 'issues':
    return { event: 'issue', data: $json.body };
  default:
    return { event: 'unknown', data: $json.body };
}
```

### Stripe Webhooks
```javascript
// Handle Stripe events
const event = $json.body;

switch (event.type) {
  case 'checkout.session.completed':
    return { action: 'fulfill_order', data: event.data.object };
  case 'invoice.paid':
    return { action: 'update_subscription', data: event.data.object };
  case 'customer.subscription.deleted':
    return { action: 'cancel_subscription', data: event.data.object };
  default:
    return { action: 'log', data: event };
}
```

### Slack Webhooks
```javascript
// Handle Slack events
const body = $json.body;

// URL verification challenge
if (body.type === 'url_verification') {
  return { challenge: body.challenge };
}

// Event handling
if (body.type === 'event_callback') {
  const event = body.event;
  return {
    eventType: event.type,
    user: event.user,
    text: event.text,
    channel: event.channel
  };
}
```

---

## Error Handling

### Error Response Pattern
```javascript
// Wrap in try-catch, return appropriate error
try {
  // Validate
  if (!$json.body.email) {
    return {
      statusCode: 400,
      error: 'Bad Request',
      message: 'email is required'
    };
  }
  
  // Process...
  return { success: true };
  
} catch (error) {
  return {
    statusCode: 500,
    error: 'Internal Server Error',
    message: 'An error occurred processing your request',
    // Don't expose internal details!
    requestId: Date.now().toString()
  };
}
```

---

## Security Best Practices

1. **Always Authenticate**: Never expose unauthenticated webhooks in production
2. **Validate Input**: Check all fields before processing
3. **Sanitize Data**: Remove potentially dangerous characters
4. **Use HTTPS**: Always (n8n cloud handles this)
5. **Rate Limit**: Protect against abuse
6. **Log Minimally**: Don't log sensitive data
7. **Timeout**: Set reasonable response timeouts
8. **Idempotency**: Handle duplicate deliveries gracefully

---

## Testing Webhooks

### Test with cURL
```bash
curl -X POST https://your-n8n.com/webhook/path \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### Test Mode vs Production
```javascript
// Check execution mode
if ($json.executionMode === 'test') {
  // Test mode - use mock data
} else {
  // Production mode - real processing
}
```

---

## Quick Reference

### Webhook URL Format
```
https://your-n8n.com/webhook/[path]
https://your-n8n.com/webhook-test/[path]  // Test mode
```

### Access Data
```javascript
$json.body          // POST body
$json.headers       // Request headers
$json.query         // Query params
$json.params        // Path params
```
