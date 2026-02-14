# PRP Generation Log - instagram-publisher

**Generated**: 2026-02-14 00:21:57 UTC  
**System**: instagram-publisher  
**Confidence Score**: 9/10

## Research Phase

### Patterns Analyzed
- Reviewed `library/patterns.md` for best-fit workflow pattern
- Selected: **Intake > Enrich > Deliver**
- Rationale: Content validation (Intake) → optional enrichment (Enrich) → Graph API publishing (Deliver)
- Pattern modifications: Added intelligent retry logic, per-post error isolation, audit logging

### Tools Analyzed
- Reviewed `library/tool_catalog.md` for reusable patterns
- Adapted: `rest_client` (for Graph API calls with retry), `llm_prompt` (for content enrichment), `json_read_write` (for result storage), `git_commit_push` (for result commits)
- New tools: Instagram-specific validation, two-step Graph API publish flow

### MCPs Analyzed
- Reviewed `config/mcp_registry.md` for available integrations
- Selected MCPs:
  - **fetch**: Optional for HTTP calls (fallback to Python requests)
  - **anthropic**: Optional for content enrichment
  - **firecrawl**: Optional for image scraping from web pages
- All MCPs have fallback strategies (direct HTTP/API calls)

## Design Phase

### Subagent Architecture
- **content-validator-specialist**: Validates caption, hashtags, image URL, format requirements
- **publisher-specialist**: Handles Graph API operations (create container, publish, retry logic)
- **fallback-handler-specialist**: Manages failed posts and retry queue
- **report-generator-specialist**: Generates daily/weekly summaries

### Agent Teams Analysis
- Applied **3+ Independent Tasks Rule**
- Recommendation: Agent Teams for batch processing (3+ posts), sequential for single posts
- Rationale: Each post is independent, parallel processing provides 2x speedup for batches
- Sequential fallback: Simpler, sufficient for single-post triggers

### Workflow Steps
1. Load Content Queue (from input/queue/*.json or workflow_dispatch)
2. Validate Content (caption length, hashtags, image URL)
3. Enrich Metadata (optional: hashtag analysis, alt text generation)
4. Create Media Container (Graph API: POST to /media)
5. Publish Container (Graph API: POST to /media_publish)
6. Log Results (output/published/ or output/failed/)
7. Generate Report (aggregate results, markdown summary)
8. Commit Results (git commit with specific file staging)

## Implementation Blueprint

### Tools Specified
1. **validate_content.py** - Instagram content validation
2. **instagram_create_container.py** - Graph API container creation with retry
3. **instagram_publish_container.py** - Graph API container publishing with retry
4. **enrich_content.py** - Optional LLM-based content enhancement
5. **write_result.py** - Timestamped result logging
6. **generate_report.py** - Markdown report generation
7. **git_commit.py** - Git staging and commit

### Critical Constraints Documented
- Instagram rate limit: 200 calls/hour per user
- Two-step publish flow: create container → publish container
- Image requirements: JPEG/PNG, max 8MB, min 320px width, aspect ratio 4:5 to 1.91:1
- Caption max: 2,200 characters including hashtags
- Max 30 hashtags per post
- Access token requires `instagram_content_publish` permission
- Retry on rate limit (429), fail fast on auth errors (190)
- Container processing delay: 1-2 seconds between create and publish

### Validation Strategy
- **Level 1**: Syntax & structure (AST parse, import checks, main() verification)
- **Level 2**: Unit tests with sample data (validation, write operations)
- **Level 3**: Integration test with real Instagram API credentials

## Confidence Assessment

### High Confidence Areas (9/9)
- Instagram Graph API integration (well-documented API, clear error codes)
- Content validation logic (explicit requirements, straightforward validation)
- Error handling and fallback (documented error codes, retry strategies)
- Workflow pattern selection (proven Intake > Enrich > Deliver pattern)
- Subagent architecture (clear separation of concerns, no circular dependencies)
- Agent Teams decision (3+ Independent Tasks Rule applies cleanly)
- Tool implementations (reusable patterns from catalog, clear inputs/outputs)
- Validation strategy (three-level gates with real API test)
- Secrets management (GitHub Secrets or .env, no hardcoding)

### Medium Confidence Areas (1/9)
- Edge case handling (image accessibility validation, container processing delay need real-world testing)

### Ambiguity Flags
- NONE - All requirements are clear and well-specified

## PRP Quality Metrics

- **Completeness**: 100% (all sections filled, no TODOs)
- **Specificity**: High (concrete examples, pseudocode, validation commands)
- **Context density**: High (API docs referenced, constraints documented, gotchas listed)
- **Validation clarity**: High (three levels with executable commands)
- **Tool specifications**: Complete (7 tools, all with inputs/outputs/dependencies)
- **Subagent definitions**: Complete (4 specialists, responsibilities clear)
- **Agent Teams analysis**: Complete (task count, recommendation, rationale)
- **Anti-patterns**: Documented (14 anti-patterns to avoid)

## Ready to Build: YES

The PRP is complete, confidence score is 9/10 (above the 7/10 threshold), and there are no ambiguity flags requiring clarification. The factory can proceed with execution.

## Next Step

Execute the factory build:
```
/execute-prp PRPs/instagram-publisher.md
```
