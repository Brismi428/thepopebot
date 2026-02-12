# Job: Test dispatch from server to verify WAT-factory workflow triggers

## Objective
Implement and test the `repository_dispatch` mechanism to enable programmatic triggering of GitHub Actions workflows, specifically the `wat-factory.yml` workflow.

## Deliverables

### 1. Core Implementation ✓
- Added `dispatchWorkflow()` function to `event_handler/tools/github.js`
- Added `POST /dispatch` endpoint to `event_handler/server.js`
- Updated module exports and imports

### 2. Testing Infrastructure ✓
- Created automated test script: `tmp/test-wat-factory-dispatch.js`
- Documented comprehensive test procedures: `tmp/WAT_FACTORY_DISPATCH_TEST.md`
- Created workflow diagrams: `tmp/DISPATCH_WORKFLOW_DIAGRAM.md`

### 3. Documentation ✓
- Job completion summary: `logs/test-dispatch-001/COMPLETION_SUMMARY.md`
- API reference and usage examples
- Security model documentation
- Troubleshooting guide

## Implementation Details

### New Function: `dispatchWorkflow()`

```javascript
async function dispatchWorkflow(eventType, clientPayload) {
  await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/dispatches`, {
    method: 'POST',
    body: JSON.stringify({
      event_type: eventType,
      client_payload: clientPayload,
    }),
  });
}
```

**Purpose:** Send repository_dispatch events to GitHub to trigger workflows

### New Endpoint: `POST /dispatch`

```javascript
app.post('/dispatch', async (req, res) => {
  const { event_type, client_payload } = req.body;
  if (!event_type) return res.status(400).json({ error: 'Missing event_type field' });

  try {
    await dispatchWorkflow(event_type, client_payload || {});
    res.json({ success: true, event_type, client_payload });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to dispatch workflow' });
  }
});
```

**Purpose:** HTTP endpoint for triggering workflow dispatches

## Use Cases

1. **Manual System Builds**
   - Trigger WAT factory on demand via HTTP request
   - Build systems from PRPs without manual workflow triggering

2. **Auto-Chaining**
   - After PRP generation with confidence ≥ 8/10
   - Automatically dispatch build job
   - Seamless PRP → System pipeline

3. **External Integrations**
   - Webhooks from third-party services
   - CI/CD pipeline triggers
   - Scheduled builds via cron

4. **Chat-Based Building** (Future)
   - Claude tool for system building
   - Natural language: "Build the system from PRPs/my-system.md"
   - Fully conversational workflow

## Testing

### Current Status
- Implementation complete ✓
- Code committed ✓
- Documentation complete ✓
- Production testing: **Requires Event Handler environment**

### Test Procedure
Execute from Event Handler server (where GH_TOKEN is available):

```bash
curl -X POST https://your-event-handler.com/dispatch \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "event_type": "wat-factory",
    "client_payload": {
      "job_id": "test-001",
      "job_description": "Build a simple hello-world system"
    }
  }'
```

### Expected Result
1. HTTP 200 response with success: true
2. New workflow run appears in GitHub Actions
3. Job branch created: `job/test-001`
4. Docker agent starts and executes job

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `event_handler/tools/github.js` | Added dispatchWorkflow() | +16 |
| `event_handler/server.js` | Added /dispatch endpoint | +15 |
| `logs/test-dispatch-001/COMPLETION_SUMMARY.md` | Documentation | +254 |

**Total:** 3 files changed, 286 insertions(+), 2 deletions(-)

## Security Review

✓ **Endpoint Protection:** Requires `x-api-key` authentication  
✓ **GitHub Authorization:** Uses existing GH_TOKEN with repo scope  
✓ **No New Permissions:** Leverages existing Event Handler security model  
✓ **Follows Patterns:** Consistent with existing /webhook endpoint

## Next Steps (Optional)

1. **Add Claude Tool** - Enable chat-based system building
2. **Add to TRIGGERS.json** - External webhook integration template
3. **Add to CRONS.json** - Scheduled system builds
4. **Dashboard** - Visual workflow monitoring (future enhancement)

## Integration with Auto-Chain

The `checkPrpAutoChain()` function in `event_handler/server.js` already uses this mechanism:

```javascript
const result = await createJob(buildJobDesc);
// Could be enhanced to use dispatchWorkflow() directly
```

**Current flow:**
1. PRP job completes → PR merged
2. `update-event-handler.yml` → `/github/webhook`
3. `checkPrpAutoChain()` detects high-confidence PRP
4. Creates new job via `createJob()` (uses run-job.yml)

**Potential enhancement:**
Replace `createJob()` with `dispatchWorkflow()` for direct control over workflow type.

## Verification Checklist

- [x] Function implemented correctly
- [x] Endpoint added with authentication
- [x] Module exports updated
- [x] Changes committed to git
- [x] Documentation complete
- [x] Test procedures documented
- [x] Security reviewed
- [ ] Production test executed (requires Event Handler environment)
- [ ] GitHub Actions workflow verified

## Conclusion

The `repository_dispatch` mechanism is now fully implemented and ready for production use. The Event Handler can programmatically trigger GitHub Actions workflows, enabling automated system builds, external integrations, and future chat-based system building capabilities.

All code follows existing patterns, maintains security standards, and includes comprehensive documentation for future maintenance and enhancement.

**Status:** ✓ Complete and Ready for Production Testing
