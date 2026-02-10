---
name: n8n-testing
description: "Expert knowledge for testing n8n workflows, creating test scenarios, and ensuring quality. Activates when: testing workflows, creating test cases, validating functionality, QA processes."
version: 1.0.0
---

# n8n Testing Skill

## Overview

Ensure workflow quality through systematic testing. This skill covers test design, execution strategies, and quality validation techniques.

---

## Testing Pyramid for n8n

```
                    ┌─────────────┐
                    │   E2E Tests │  ← Full workflow execution
                   ─┴─────────────┴─
                  ┌─────────────────┐
                  │Integration Tests│  ← Node combinations
                 ─┴─────────────────┴─
                ┌─────────────────────┐
                │     Unit Tests      │  ← Individual nodes
               ─┴─────────────────────┴─
              ┌─────────────────────────┐
              │   Validation Tests      │  ← Structure & config
             ─┴─────────────────────────┴─
```

---

## Test Types

### 1. Structural Validation
Verify workflow configuration is correct.

```javascript
// Validate workflow structure
validate_workflow(workflowJson)

// Validate deployed workflow
n8n_validate_workflow({id: 'workflow-id'})
```

### 2. Unit Tests
Test individual nodes in isolation.

```javascript
// Validate single node
validate_node({
  nodeType: 'nodes-base.slack',
  config: {...},
  mode: 'full',
  profile: 'runtime'
})
```

### 3. Integration Tests
Test node combinations and data flow.

```javascript
// Execute workflow with test data
n8n_test_workflow({
  workflowId: 'workflow-id',
  data: testData
})
```

### 4. End-to-End Tests
Test complete workflow from trigger to output.

---

## Test Data Patterns

### Happy Path Data
```javascript
const happyPathData = {
  body: {
    email: "valid@example.com",
    name: "John Doe",
    amount: 100,
    currency: "USD"
  }
};
```

### Edge Case Data
```javascript
const edgeCases = [
  // Empty values
  { body: { email: "", name: "", amount: 0 } },
  
  // Minimum values
  { body: { email: "a@b.co", name: "A", amount: 0.01 } },
  
  // Maximum values
  { body: { email: "a".repeat(100) + "@example.com", name: "A".repeat(1000), amount: 999999999 } },
  
  // Special characters
  { body: { email: "test+tag@example.com", name: "O'Brien & Sons", amount: 100 } },
  
  // Unicode
  { body: { email: "tëst@example.com", name: "日本語テスト", amount: 100 } }
];
```

### Error Case Data
```javascript
const errorCases = [
  // Missing required fields
  { body: { name: "Test" } },  // Missing email
  
  // Invalid types
  { body: { email: 123, name: true, amount: "hundred" } },
  
  // Invalid formats
  { body: { email: "not-an-email", name: "Test", amount: -100 } },
  
  // Injection attempts
  { body: { email: "'; DROP TABLE users; --", name: "<script>alert('xss')</script>" } }
];
```

### Boundary Data
```javascript
const boundaryTests = {
  // Numbers
  zero: { amount: 0 },
  negative: { amount: -1 },
  maxInt: { amount: Number.MAX_SAFE_INTEGER },
  decimal: { amount: 0.001 },
  
  // Strings
  empty: { name: "" },
  singleChar: { name: "A" },
  maxLength: { name: "A".repeat(10000) },
  
  // Arrays
  emptyArray: { items: [] },
  singleItem: { items: [1] },
  largeArray: { items: Array(10000).fill(1) }
};
```

---

## Test Case Template

```markdown
## TC-[ID]: [Test Name]

### Category
[Unit/Integration/E2E/Validation]

### Priority
[P0-Critical/P1-High/P2-Medium/P3-Low]

### Preconditions
- Workflow is active
- Credentials are configured
- [Other conditions]

### Test Data
```json
{
  "body": {
    "field": "value"
  }
}
```

### Steps
1. Trigger workflow with test data
2. Wait for execution to complete
3. Verify output matches expected

### Expected Result
- Status: Success
- Output: { "processed": true }

### Actual Result
[Filled after execution]

### Status
[Pass/Fail/Blocked/Skip]
```

---

## Test Matrix Template

```markdown
| ID | Category | Test Case | Input | Expected | Status |
|----|----------|-----------|-------|----------|--------|
| TC-001 | Happy Path | Valid signup | Valid JSON | User created | ⬜ |
| TC-002 | Happy Path | Valid order | Valid JSON | Order created | ⬜ |
| TC-010 | Boundary | Empty name | name: "" | Validation error | ⬜ |
| TC-011 | Boundary | Max length | name: "A"*10000 | Truncate or error | ⬜ |
| TC-020 | Error | Missing email | No email | 400 error | ⬜ |
| TC-021 | Error | Invalid type | amount: "text" | 400 error | ⬜ |
| TC-030 | Security | SQL injection | SQL in field | Sanitized | ⬜ |
| TC-031 | Security | XSS attempt | Script tag | Escaped | ⬜ |
```

---

## Automated Test Workflow

### Test Runner Workflow
```json
{
  "name": "Test Runner",
  "nodes": [
    {
      "name": "Test Cases",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Define test cases\nconst testCases = [\n  {\n    name: 'Valid signup',\n    data: { body: { email: 'test@example.com', name: 'Test' } },\n    expectedStatus: 'success'\n  },\n  {\n    name: 'Missing email',\n    data: { body: { name: 'Test' } },\n    expectedStatus: 'error'\n  }\n];\n\nreturn testCases.map(tc => ({ json: tc }));"
      }
    },
    {
      "name": "Execute Test",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://your-n8n.com/webhook-test/your-webhook",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.data) }}"
      },
      "continueOnFail": true
    },
    {
      "name": "Validate Result",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const testCase = $('Test Cases').item.json;\nconst result = $json;\n\nconst passed = result.error \n  ? testCase.expectedStatus === 'error'\n  : testCase.expectedStatus === 'success';\n\nreturn {\n  testName: testCase.name,\n  passed,\n  expected: testCase.expectedStatus,\n  actual: result.error ? 'error' : 'success',\n  details: result\n};"
      }
    },
    {
      "name": "Aggregate Results",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const results = $input.all().map(i => i.json);\nconst passed = results.filter(r => r.passed).length;\nconst failed = results.filter(r => !r.passed).length;\n\nreturn {\n  summary: {\n    total: results.length,\n    passed,\n    failed,\n    passRate: ((passed / results.length) * 100).toFixed(1) + '%'\n  },\n  results\n};"
      }
    }
  ]
}
```

---

## Testing Strategies

### Strategy 1: Smoke Testing
Quick validation that workflow works at all.

```javascript
// Single happy path test
n8n_test_workflow({
  workflowId: 'workflow-id',
  data: { body: { email: 'test@example.com' } }
})
```

### Strategy 2: Regression Testing
Ensure changes don't break existing functionality.

```javascript
// Run full test suite after changes
const testSuite = [
  { name: 'TC-001', data: {...} },
  { name: 'TC-002', data: {...} },
  // ... all tests
];

for (const test of testSuite) {
  const result = await runTest(test);
  if (!result.passed) {
    console.error(`REGRESSION: ${test.name} failed`);
  }
}
```

### Strategy 3: Exploratory Testing
Manual investigation of edge cases.

```markdown
## Exploratory Test Session

**Charter**: Find edge cases in user signup flow
**Time Box**: 30 minutes
**Tester**: @n8n-tester

### Notes
- Tried emoji in name field → Accepted ✅
- Tried 500 char email → Accepted (should reject?) ⚠️
- Tried concurrent signups → Second one failed 🐛

### Bugs Found
1. Email validation too permissive
2. Race condition on duplicate check
```

### Strategy 4: Load Testing
Test performance under volume.

```javascript
// Generate load
const items = Array(100).fill(null).map((_, i) => ({
  body: { email: `test${i}@example.com`, name: `User ${i}` }
}));

// Execute in batches
const batchSize = 10;
for (let i = 0; i < items.length; i += batchSize) {
  const batch = items.slice(i, i + batchSize);
  await Promise.all(batch.map(data => 
    n8n_test_workflow({ workflowId: 'workflow-id', data })
  ));
}
```

---

## Validation Patterns

### Pre-Deployment Validation
```javascript
// Full validation before deploy
const validation = validate_workflow(workflowJson);

if (validation.errors.length > 0) {
  throw new Error('Workflow has errors: ' + JSON.stringify(validation.errors));
}

// Deploy only if valid
n8n_create_workflow(workflowJson);
```

### Post-Deployment Validation
```javascript
// Validate after deploy
n8n_validate_workflow({id: 'workflow-id'})

// Run smoke test
n8n_test_workflow({
  workflowId: 'workflow-id',
  data: smokeTestData
})
```

### Continuous Validation
```javascript
// Scheduled workflow to test critical workflows
const criticalWorkflows = ['wf-1', 'wf-2', 'wf-3'];

for (const id of criticalWorkflows) {
  const result = await n8n_test_workflow({ workflowId: id, data: testData });
  if (result.status !== 'success') {
    // Send alert
    await sendSlackAlert(`Workflow ${id} health check failed!`);
  }
}
```

---

## Test Report Template

```markdown
# Test Report: [Workflow Name]

## Summary
| Metric | Value |
|--------|-------|
| Total Tests | 50 |
| Passed | 47 |
| Failed | 2 |
| Blocked | 1 |
| Pass Rate | 94% |
| Test Duration | 5m 32s |

## Environment
- n8n Version: 1.x.x
- Instance: [URL]
- Date: [Date]

## Results by Category

### Happy Path (15/15) ✅
All passed

### Boundary (12/13) ⚠️
- TC-011 Failed: Max length not truncated

### Error Handling (10/11) ⚠️
- TC-025 Failed: 500 error instead of 400

### Security (10/10) ✅
All passed

## Failed Tests

### TC-011: Maximum length handling
**Expected**: Truncate to 1000 chars or return error
**Actual**: Accepted full 10000 char input
**Impact**: Medium - could cause DB issues
**Action**: Add length validation

### TC-025: Invalid JSON response code
**Expected**: 400 Bad Request
**Actual**: 500 Internal Server Error
**Impact**: Low - still fails but wrong code
**Action**: Add input validation before processing

## Recommendations
1. [P1] Add input length validation
2. [P2] Improve error handling for malformed JSON
3. [P3] Add rate limiting for API endpoints

## Sign-off
- [ ] All P0/P1 issues addressed
- [ ] Test report reviewed
- [ ] Ready for production
```

---

## Quick Reference

### Execute Test
```javascript
n8n_test_workflow({
  workflowId: 'id',
  data: { body: {...} }
})
```

### Validate Structure
```javascript
validate_workflow(workflowJson)
```

### Validate Deployed
```javascript
n8n_validate_workflow({id: 'workflow-id'})
```

### Get Execution Details
```javascript
n8n_executions({action: 'get', executionId: 'exec-id'})
```

---

## Testing Checklist

- [ ] Happy path tests pass
- [ ] Boundary conditions tested
- [ ] Error handling verified
- [ ] Security inputs sanitized
- [ ] Performance acceptable
- [ ] All branches covered
- [ ] Webhook responses correct
- [ ] Credentials working
- [ ] Error messages helpful
- [ ] Logging appropriate
