# WAT Systems Factory -- Workflow Pattern Catalog

> Proven, reusable workflow patterns for building GitHub-native autonomous systems with Claude Code and MCP tools.

Each pattern below is a composable building block. Patterns can be combined: a **Monitor > Detect > Alert** system might trigger an **Issue > Execute > PR** workflow, which internally uses **Fan-Out > Process > Merge** for the heavy lifting.

---

## 1. Scrape > Process > Output

**Summary:** A web scraping pipeline that fetches raw content from one or more URLs via a web-access MCP, processes and structures the data with Python (or Claude itself), and writes clean output to a target destination.

### When to Use

- You need structured data extracted from websites that lack APIs.
- You want to convert messy HTML into clean JSON, CSV, or Markdown on a recurring schedule.
- You are building a dataset from publicly available web content.

### Steps

1. **Define targets** -- Specify URLs, selectors, or search queries in a config file or workflow input.
2. **Fetch raw content** -- Use a web MCP (Fetch, Puppeteer, or Playwright) to retrieve page content. Handle pagination if needed.
3. **Parse and extract** -- Strip irrelevant markup. Pull target fields using CSS selectors, XPath, or Claude-driven semantic extraction.
4. **Transform** -- Normalize data types, deduplicate, validate schema. Python scripts or inline Claude processing.
5. **Output** -- Write results to a file in the repo (`data/`, `output/`), post to an API, or commit as a structured artifact.

### Key Tools / MCPs

- **Fetch MCP** -- lightweight HTTP retrieval, returns Markdown-converted content.
- **Puppeteer / Playwright MCP** -- for JavaScript-rendered pages requiring a headless browser.
- **Python** -- pandas, BeautifulSoup, or custom scripts for heavy transformation.
- **filesystem MCP** -- write results to disk.

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '0 6 * * *'   # daily at 06:00 UTC
  workflow_dispatch:        # manual trigger
```

### Example Use Cases

- Scrape competitor pricing pages nightly; output a CSV diff showing changes.
- Collect job postings from three sites; normalize into a single JSON feed committed to the repo.
- Pull public government data tables and convert to machine-readable Parquet files.

### Failure Handling

- **Retry with backoff** on transient HTTP errors (429, 503).
- **Schema validation** after extraction -- if required fields are missing, flag the record rather than silently dropping it.
- **Stale-data guard** -- if fetch returns identical content to last run, skip processing and log "no change."
- **Alert on structural change** -- if selectors return zero matches (site redesign), open a GitHub Issue for human review.

---

## 2. Research > Analyze > Report

**Summary:** A multi-source research workflow that gathers information from diverse sources (web, APIs, local files), synthesizes findings with Claude, and produces a formatted report committed to the repository.

### When to Use

- You need to compile information from multiple sources into a single coherent document.
- Periodic market research, competitive analysis, or literature reviews.
- Any task where a human would spend hours reading and summarizing.

### Steps

1. **Define research brief** -- Specify the topic, questions to answer, source priorities, and output format.
2. **Gather sources** -- Query web search, fetch specific URLs, read local reference files, call APIs.
3. **Extract key findings** -- For each source, pull relevant facts, quotes, data points. Tag each with provenance.
4. **Analyze and synthesize** -- Claude cross-references findings, identifies patterns, contradictions, and gaps.
5. **Generate report** -- Produce a structured Markdown document with sections, citations, and an executive summary.
6. **Commit and notify** -- Commit the report to the repo. Optionally open a PR or send a notification.

### Key Tools / MCPs

- **Web Search MCP / Fetch MCP** -- gather online sources.
- **filesystem MCP** -- read local reference documents.
- **GitHub MCP** -- commit output, open issues or PRs.
- **Claude (extended thinking)** -- deep analysis and synthesis.

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'   # weekly on Monday at 09:00 UTC
  workflow_dispatch:
    inputs:
      topic:
        description: 'Research topic'
        required: true
```

### Example Use Cases

- Weekly competitive landscape report that tracks new features announced by three competitors.
- Monthly technology radar summarizing emerging tools relevant to the team's stack.
- Ad-hoc deep-dive report triggered manually via `workflow_dispatch` with a topic input.

### Failure Handling

- **Source fallback** -- if a primary source is unreachable, log it and proceed with remaining sources. Note gaps in the report.
- **Confidence scoring** -- Claude flags low-confidence claims; the report includes a "Caveats" section.
- **Minimum-source threshold** -- if fewer than N sources are successfully retrieved, abort and open an issue rather than publishing a thin report.

---

## 3. Monitor > Detect > Alert

**Summary:** A continuous monitoring system that periodically checks a target (website, API, dataset, repo) for changes, applies detection logic, and fires alerts or triggers downstream workflows when significant changes are found.

### When to Use

- You want to be notified when something changes: a webpage, an API response, a competitor's pricing, a regulatory filing.
- You need a lightweight, Git-native alternative to commercial monitoring SaaS.
- Ideal for cron-triggered GitHub Actions that run on a schedule.

### Steps

1. **Fetch current state** -- Retrieve the current snapshot of the monitored target.
2. **Load previous state** -- Read the last-known state from a file committed in the repo (e.g., `state/last_snapshot.json`).
3. **Diff** -- Compare current vs. previous. Use structural diff for JSON, text diff for prose, hash comparison for binary.
4. **Evaluate significance** -- Apply rules or Claude-based judgment to determine if the change is meaningful (filter noise).
5. **Alert** -- If significant: open a GitHub Issue, send a Slack message, trigger a downstream workflow via `repository_dispatch`, or all three.
6. **Persist new state** -- Commit the current snapshot as the new baseline.

### Key Tools / MCPs

- **Fetch MCP / Puppeteer MCP** -- retrieve current state from web targets.
- **filesystem MCP** -- read/write state files.
- **GitHub MCP** -- open issues, trigger dispatches.
- **Slack MCP** -- send alert messages.

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # every 30 minutes
```

### Example Use Cases

- Monitor a government regulatory page for new filings; alert the legal team via Slack when a new document appears.
- Watch a competitor's changelog page; open a GitHub Issue summarizing each detected update.
- Track an API's response schema for breaking changes; alert the engineering team.

### Failure Handling

- **Transient failure tolerance** -- if the fetch fails, do NOT overwrite previous state. Log the failure. After N consecutive failures, escalate to an alert.
- **False-positive suppression** -- use Claude to evaluate whether a detected "change" is meaningful (e.g., ignore timestamp-only diffs).
- **State corruption recovery** -- if state file is missing or unparseable, re-initialize from scratch and log a warning instead of crashing.

---

## 4. Intake > Enrich > Deliver

**Summary:** A data enrichment pipeline that receives raw input (from a form, webhook, file drop, or API), augments it with additional data from external sources, and delivers the enriched result to its destination.

### When to Use

- Incoming data is incomplete and needs augmentation before it is useful.
- You are building a lead enrichment, content tagging, or metadata enhancement system.
- Raw data arrives in one format and must be transformed and enriched before storage or delivery.

### Steps

1. **Intake** -- Receive raw data. Sources: webhook payload, new file in repo, manual trigger with JSON input, or a watched directory.
2. **Validate** -- Check that required fields exist and data types are correct. Reject malformed input early.
3. **Enrich** -- For each record, call enrichment sources: web search for context, APIs for supplementary data, Claude for classification or summarization.
4. **Merge** -- Combine original data with enrichment results into a unified schema.
5. **Deliver** -- Write enriched data to its destination: commit to repo, POST to API, append to a dataset file, or open a PR.

### Key Tools / MCPs

- **Web Search MCP** -- find supplementary information.
- **Fetch MCP** -- call enrichment APIs.
- **Claude** -- classify, tag, summarize, or score records.
- **filesystem MCP** -- read input, write output.
- **GitHub MCP** -- commit results or open PRs.

### GitHub Actions Trigger

```yaml
on:
  push:
    paths:
      - 'inbox/**'          # new file dropped in inbox
  workflow_dispatch:
    inputs:
      payload:
        description: 'JSON data to enrich'
        required: true
```

### Example Use Cases

- A sales team drops a CSV of company names into `inbox/`; the pipeline enriches each with industry, size, website, and LinkedIn URL, then writes to `data/enriched_leads.csv`.
- Incoming support tickets are enriched with customer history and sentiment score before routing.
- Raw RSS feed items are enriched with summaries, topic tags, and relevance scores.

### Failure Handling

- **Per-record error isolation** -- if enrichment fails for one record, mark it as `enrichment_failed` and continue processing the rest. Do not let one bad record kill the batch.
- **Rate-limit awareness** -- track API call counts; pause and retry when rate-limited rather than failing fast.
- **Partial delivery** -- deliver successfully enriched records on schedule; queue failed records for retry in the next run.

---

## 5. Generate > Review > Publish

**Summary:** A content generation pipeline with built-in quality gates. Claude generates draft content, a review step validates quality and compliance, and approved content is published to its destination.

### When to Use

- Automated content creation (blog posts, documentation, social media, release notes) where quality must be verified before publishing.
- Any workflow where you want a "human-in-the-loop" approval step or an automated quality check before output goes live.

### Steps

1. **Brief** -- Define the content requirements: topic, audience, tone, length, format, and any reference material.
2. **Generate** -- Claude produces a first draft using the brief and any provided reference material.
3. **Automated review** -- Run quality checks: spelling/grammar, factual consistency against source material, tone analysis, compliance rules (e.g., no prohibited claims).
4. **Gate decision** -- If automated review passes, proceed. If it fails, loop back to step 2 with feedback (max N retries). Optionally, require human approval via a PR review.
5. **Publish** -- Commit final content to the repo, deploy to a CMS via API, or post to a platform.

### Key Tools / MCPs

- **Claude** -- generation and review (use separate system prompts for generator vs. reviewer to create genuine separation).
- **filesystem MCP** -- read briefs, write drafts and final output.
- **GitHub MCP** -- open a draft PR for human review; merge on approval.
- **Fetch MCP** -- publish to external CMS or platform APIs.

### GitHub Actions Trigger

```yaml
on:
  issues:
    types: [labeled]        # label "content-request" triggers generation
  pull_request_review:
    types: [submitted]      # human approval triggers publish
  workflow_dispatch:
```

### Example Use Cases

- Weekly changelog: gather merged PRs, generate a formatted changelog, open a PR for team review, publish on approval.
- Blog post pipeline: issue labeled "draft-request" triggers generation; editor reviews the PR; merge triggers deployment.
- Social media batch: generate a week's worth of posts, run brand-voice review, output approved posts to a scheduling queue.

### Failure Handling

- **Retry budget** -- if automated review rejects the draft, regenerate with targeted feedback up to 3 times. After that, escalate to a human by opening an issue.
- **Rollback on publish failure** -- if the publish step fails (API error), keep the approved content in the repo and log the failure for manual retry.
- **Diff guard** -- before publishing, diff against previously published content to prevent accidental overwrite of manual edits.

---

## 6. Listen > Decide > Act

**Summary:** An event-driven agent that listens for incoming events (webhooks, GitHub events, messages), applies decision logic to determine the appropriate response, and takes autonomous action.

### When to Use

- You need a system that reacts to external events in near-real-time.
- Webhook-triggered GitHub Actions are the execution engine.
- The appropriate response depends on the content of the event (routing, triage, conditional logic).

### Steps

1. **Receive event** -- GitHub Actions triggers on the event (webhook, issue creation, PR comment, `repository_dispatch`).
2. **Parse and classify** -- Extract relevant data from the event payload. Use Claude to classify intent or severity if the input is unstructured (e.g., natural language).
3. **Decide** -- Apply decision logic: rule-based routing, Claude-driven triage, or a lookup table. Determine which action(s) to take.
4. **Act** -- Execute the chosen action: respond to the issue, trigger another workflow, call an API, update a file, or escalate to a human.
5. **Log** -- Record the event, decision, and action taken for auditability.

### Key Tools / MCPs

- **GitHub MCP** -- read event payloads, respond to issues/PRs, trigger dispatches.
- **Claude** -- classify, triage, and decide.
- **Slack MCP** -- notify humans when escalation is needed.
- **Fetch MCP** -- call external APIs as part of the action.

### GitHub Actions Trigger

```yaml
on:
  issues:
    types: [opened, labeled]
  issue_comment:
    types: [created]
  repository_dispatch:
    types: [incoming_webhook]
```

### Example Use Cases

- Triage bot: new issues are classified by Claude (bug, feature, question) and auto-labeled, assigned, and replied to with relevant templates.
- Deployment gatekeeper: a PR comment like "/deploy staging" triggers a deployment workflow after validating the commenter's permissions.
- Customer feedback router: webhook delivers feedback; Claude scores sentiment and routes critical items to Slack.

### Failure Handling

- **Idempotency** -- design actions to be safe to retry. Use event IDs to detect and skip duplicate deliveries.
- **Decision logging** -- log the full decision chain (event > classification > decision > action) so failures can be diagnosed.
- **Safe defaults** -- if classification confidence is low, default to escalation (notify a human) rather than taking an autonomous action that might be wrong.

---

## 7. Collect > Transform > Store

**Summary:** A classic ETL (Extract, Transform, Load) pipeline where Git serves as the data store. Data is collected from external sources, transformed into a canonical format, and committed to the repository as versioned, queryable files.

### When to Use

- You want a version-controlled data lake without standing up a database.
- Small-to-medium datasets (tens of MB) that benefit from Git's diff, history, and branching.
- Data pipelines where auditability and reproducibility matter more than query speed.

### Steps

1. **Collect** -- Pull data from source(s): APIs, web scrapes, file uploads, other repos.
2. **Validate** -- Check data integrity: schema validation, null checks, type enforcement.
3. **Transform** -- Normalize, clean, reshape. Convert to the canonical schema. Deduplicate against existing data in the store.
4. **Diff** -- Compare transformed data against the current version in the repo. Compute what is new, changed, or deleted.
5. **Store** -- Commit the updated dataset files to the repo. Use meaningful commit messages describing what changed (e.g., "Add 14 new records from source X").

### Key Tools / MCPs

- **Fetch MCP** -- pull data from APIs and web sources.
- **Python** -- pandas or custom scripts for transformation.
- **filesystem MCP** -- read/write data files.
- **GitHub MCP / Git CLI** -- commit, push, branch as needed.

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # every 6 hours
  workflow_dispatch:
```

### Example Use Cases

- Collect cryptocurrency prices from three APIs every 6 hours; store as daily CSV files in `data/prices/`.
- Pull open government datasets weekly; transform into a normalized schema; maintain a living dataset in the repo.
- Aggregate internal metrics from multiple microservice health endpoints; store as JSON for a dashboard.

### Failure Handling

- **Atomic commits** -- only commit if the entire pipeline succeeds. Never commit partial or corrupted data.
- **Schema drift detection** -- if source data no longer matches the expected schema, abort and alert rather than storing malformed data.
- **Rollback via Git** -- if bad data is committed, revert the commit. The previous state is always recoverable.
- **Dedup safety** -- idempotent writes ensure that re-running the pipeline does not create duplicate records.

---

## 8. Fan-Out > Process > Merge

**Summary:** The Agent Teams pattern. A coordinator agent splits a large task into independent sub-tasks, dispatches them to parallel sub-agents (or sequential iterations), collects all results, and merges them into a unified output.

### When to Use

- A task is naturally decomposable into independent units of work (e.g., process each file, research each topic, analyze each competitor).
- You want to reduce wall-clock time by parallelizing work.
- The final deliverable requires combining results from multiple sub-tasks.

### Steps

1. **Plan** -- The coordinator analyzes the task and determines how to decompose it. Produces a work manifest: a list of sub-tasks with their inputs.
2. **Fan-Out** -- Dispatch each sub-task. Options: parallel GitHub Actions jobs via a matrix strategy, sequential Claude tool calls, or `repository_dispatch` events to separate workflows.
3. **Process** -- Each sub-agent executes its sub-task independently. Results are written to a known location (e.g., `temp/results/task_01.json`).
4. **Collect** -- The coordinator waits for all sub-tasks to complete and gathers their outputs.
5. **Merge** -- Combine results: concatenate, deduplicate, reconcile conflicts, and produce the final unified output.
6. **Deliver** -- Commit the merged output or pass it to the next stage in a larger pipeline.

### Key Tools / MCPs

- **Claude** -- coordinator logic, sub-task execution, merge logic.
- **GitHub Actions matrix** -- parallel job execution.
- **filesystem MCP** -- read/write intermediate and final results.
- **GitHub MCP** -- coordinate via issues, artifacts, or dispatch events.

### GitHub Actions Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      task_manifest:
        description: 'JSON array of sub-tasks'
        required: true
  repository_dispatch:
    types: [fan_out_request]
```

### Example Use Cases

- Analyze 20 competitor websites: fan out one sub-agent per competitor, each produces a profile, merge into a single competitive analysis report.
- Process a batch of 50 documents: each sub-agent summarizes one document, merge into a master summary with cross-references.
- Multi-language translation: fan out one sub-agent per target language, merge all translations into a localized content bundle.

### Failure Handling

- **Partial success tolerance** -- if some sub-tasks fail, merge the successful results and report failures. Do not discard all work because of one failure.
- **Retry failed sub-tasks** -- the coordinator can re-dispatch failed sub-tasks up to N times before giving up.
- **Timeout enforcement** -- set a maximum wall-clock time for the fan-out phase. Collect whatever is done when the timer expires.
- **Conflict resolution** -- if sub-task results conflict, the merge step uses Claude to reconcile or flags the conflict for human review.

---

## 9. Issue > Execute > PR

**Summary:** The GitHub Agent HQ pattern. An agent receives a task specification via a GitHub Issue, autonomously executes the required workflow, and delivers the results as a draft Pull Request for human review.

### When to Use

- You want a human-in-the-loop task queue where work is requested via Issues and delivered via PRs.
- The agent should be fully autonomous in execution but the output requires human approval before merging.
- Building an internal tool where non-technical stakeholders can request work by opening an Issue.

### Steps

1. **Receive** -- A new Issue is opened (or an existing Issue is labeled with a trigger label like `agent-task`). GitHub Actions fires.
2. **Parse task** -- Claude reads the Issue body and extracts the task specification: what to do, inputs, constraints, expected output.
3. **Create branch** -- Create a feature branch named after the Issue (e.g., `agent/issue-42`).
4. **Execute** -- Run the appropriate workflow or pattern to complete the task. This might invoke any other pattern in this catalog.
5. **Commit results** -- Commit all output files to the feature branch with clear commit messages.
6. **Open draft PR** -- Open a draft PR linked to the original Issue. The PR body includes a summary of what was done, key decisions made, and anything that needs human attention.
7. **Comment on Issue** -- Post a comment on the Issue linking to the PR and summarizing the outcome.

### Key Tools / MCPs

- **GitHub MCP** -- read issues, create branches, commit, open PRs, post comments.
- **Claude** -- parse task, execute logic, generate summaries.
- **Any other MCP** -- depending on the task being executed.

### GitHub Actions Trigger

```yaml
on:
  issues:
    types: [opened, labeled]
  issue_comment:
    types: [created]       # support "/execute" command in comments
```

### Example Use Cases

- A product manager opens an Issue: "Research top 5 CRM tools and compare features." The agent researches, builds a comparison table, and opens a PR with the report.
- An engineer opens an Issue: "Add unit tests for the auth module." The agent generates tests and delivers them as a PR.
- A stakeholder opens an Issue: "Update the pricing page data for Q1." The agent pulls new data, updates the files, and opens a PR for review.

### Failure Handling

- **Status updates** -- the agent comments on the Issue at each major step ("Starting research...", "Generating report...", "Opening PR...") so progress is visible.
- **Graceful failure** -- if the agent cannot complete the task, it comments on the Issue with a clear explanation of what went wrong and what it tried, then labels the Issue `agent-failed` for human triage.
- **Scope guard** -- if Claude determines the task is ambiguous or out of scope, it asks a clarifying question in the Issue comments rather than guessing.
- **Draft-only PRs** -- all PRs are opened as drafts. The agent never merges its own work.

---

## 10. n8n Import > Translate > Deploy

**Summary:** A conversion pattern that ingests an n8n workflow JSON export, translates it into a WAT-native system (Claude Code + MCP + GitHub Actions), and deploys it as a fully functional GitHub-native workflow.

### When to Use

- You are migrating from n8n (or a similar visual workflow tool) to a GitHub-native architecture.
- You want to leverage existing workflow logic without manually rewriting it.
- You are evaluating whether an n8n workflow can run as a WAT system to reduce infrastructure dependencies.

### Steps

1. **Import** -- Read the n8n workflow JSON file. This contains nodes, connections, credentials references, and configuration.
2. **Parse and map** -- Walk the node graph. For each n8n node type, identify the equivalent WAT component:
   - HTTP Request node -> Fetch MCP call
   - Code (JavaScript/Python) node -> inline script or Python file
   - IF/Switch node -> Claude decision logic or conditional in workflow
   - Webhook trigger -> `repository_dispatch` or `workflow_dispatch`
   - Cron trigger -> `schedule` trigger in GitHub Actions
   - Set/Merge nodes -> data transformation in Claude or Python
3. **Translate** -- Generate the WAT system files:
   - `.github/workflows/*.yml` -- GitHub Actions workflow definition.
   - `prompts/` -- Claude system prompts for nodes that require AI logic.
   - `scripts/` -- Python or shell scripts for code nodes.
   - `config/` -- Configuration extracted from the n8n workflow.
4. **Validate** -- Dry-run the generated workflow. Check that all node types were mapped, no credentials are hardcoded, and the control flow is correct.
5. **Deploy** -- Commit the generated files to the repo. Open a PR with a detailed summary of the translation, noting any nodes that required manual review or could not be auto-translated.

### Key Tools / MCPs

- **filesystem MCP** -- read n8n JSON, write generated files.
- **Claude** -- interpret node logic, generate prompts, translate code, produce workflow YAML.
- **GitHub MCP** -- commit files, open PR.
- **Python** -- parse n8n JSON, generate boilerplate.

### GitHub Actions Trigger

```yaml
on:
  push:
    paths:
      - 'imports/n8n/*.json'   # drop an n8n export to trigger conversion
  workflow_dispatch:
    inputs:
      n8n_file:
        description: 'Path to n8n JSON file in the repo'
        required: true
```

### Example Use Cases

- Migrate a 15-node n8n lead-scoring workflow to a Git-versioned, GitHub Actions-powered system.
- Convert an n8n social media posting pipeline into a WAT **Generate > Review > Publish** system.
- Translate an n8n monitoring workflow into a WAT **Monitor > Detect > Alert** pattern, eliminating the need for a running n8n instance.

### Failure Handling

- **Unsupported node catalog** -- maintain a list of n8n node types that cannot be auto-translated. When encountered, flag them in the PR description with a `TODO` and a suggested manual implementation.
- **Credential safety** -- never translate credentials. Replace all credential references with GitHub Secrets placeholders (`${{ secrets.SERVICE_API_KEY }}`) and document which secrets need to be configured.
- **Fidelity check** -- generate a side-by-side comparison of the n8n flow and the translated WAT flow so a human reviewer can verify correctness.
- **Incremental migration** -- support translating a subset of the n8n workflow, allowing teams to migrate node-by-node rather than all-at-once.

---

## Pattern Composition Quick Reference

Patterns are building blocks. Here are common compositions:

| Composition | How It Works |
|---|---|
| **Monitor > Detect > Alert** + **Issue > Execute > PR** | Monitor detects a change, opens an Issue, which triggers the agent to act and deliver a PR. |
| **Issue > Execute > PR** using **Fan-Out > Process > Merge** | A complex Issue task is decomposed and parallelized internally before the PR is opened. |
| **Scrape > Process > Output** feeding **Collect > Transform > Store** | Scraping output is piped into the ETL pattern for versioned storage. |
| **Listen > Decide > Act** routing to any pattern | An event-driven dispatcher that selects and triggers the appropriate pattern based on the event. |
| **n8n Import > Translate > Deploy** producing any pattern | The translator identifies which WAT pattern best fits the n8n workflow and generates accordingly. |

---

## Choosing a Pattern

| Question | Recommended Pattern |
|---|---|
| Do I need to pull data from websites? | **Scrape > Process > Output** |
| Do I need to synthesize information from many sources? | **Research > Analyze > Report** |
| Do I need to watch for changes over time? | **Monitor > Detect > Alert** |
| Do I need to augment incoming data? | **Intake > Enrich > Deliver** |
| Do I need AI-generated content with quality control? | **Generate > Review > Publish** |
| Do I need to react to external events? | **Listen > Decide > Act** |
| Do I need versioned data storage without a database? | **Collect > Transform > Store** |
| Do I need to parallelize a large task? | **Fan-Out > Process > Merge** |
| Do I need a task queue with human approval? | **Issue > Execute > PR** |
| Do I need to migrate an n8n workflow? | **n8n Import > Translate > Deploy** |
| Do I need B2B lead generation from web data? | **Intake > Enrich > Deliver** (lead-gen variant) |

---

## Proven Compositions (from builds)

### Lead Generation Pipeline (lead-gen-machine)
- **Pattern**: Intake > Enrich > Deliver + Scrape > Process > Output
- **Flow**: Parse profile > Search web > Scrape sites > Extract contacts (Claude) > Score leads > Output CSV
- **Key insight**: The Intake > Enrich > Deliver pattern works well when the "enrichment" involves multi-step web scraping + AI extraction. Each company is an independent unit of work, making this a strong candidate for Fan-Out > Process > Merge parallelization.
- **Scoring pattern**: Decompose match criteria into independent dimensions (industry, size, location, keywords) with weighted point values. This makes the scoring transparent and tunable.
- **Fallback chains**: Firecrawl > HTTP+BeautifulSoup for scraping, Claude > regex for extraction. Always have a degraded-but-functional fallback.

### Marketing Pipeline (marketing-pipeline)
- **Pattern**: Intake > Enrich > Deliver + Generate > Review > Publish
- **Flow**: Ingest CSV > Enrich via Apollo/Hunter/Brave/Claude > Deep-score (5 dimensions) > Segment (Hot/Warm/Cold) > Generate outreach (Hot) > Generate nurture (Warm) > Output CSVs + emails
- **Key insight**: Multi-API enrichment with graceful degradation. Apollo (primary) > Hunter (email verification) > Brave (research) > Claude (pain analysis). Each API layer adds value but the system works with only Anthropic API.
- **Scoring pattern**: 5-dimension scoring (size fit, tech stack compatibility, budget signals, accessibility, pain signals) with transparent point breakdown. More dimensions = more nuanced than lead-gen-machine's 4-dimension approach.
- **Content generation pattern**: Outreach and nurture are independent post-segmentation, making them natural Agent Teams candidates. Outreach is per-lead personalized; nurture is aggregate-informed.
- **API fallback chain**: Apollo > Hunter > Brave > Claude > HTTP scraping. Four-level fallback with clear degradation at each level.
- **CSV-in/CSV-out**: Accepts CSV input (compatible with lead-gen-machine output), produces segmented CSVs + markdown email sequences. Easy to chain systems.

### Website Uptime Monitor (website-uptime-monitor)
- **Pattern**: Monitor > Log (simplified from Monitor > Detect > Alert)
- **Flow**: Check URL via HTTP GET > Measure response time > Determine up/down status > Append to CSV > Commit to Git
- **Key insight**: Simplest possible monitoring system - no detection logic, no alerting, just raw data collection. Every check produces a log entry regardless of status. Git history IS the audit trail.
- **No MCPs needed**: Direct Python `requests` library is simpler and more reliable than Fetch MCP for a single GET request. CSV append uses stdlib. Zero external dependencies beyond GitHub Actions.
- **Exit code signaling**: Tool exits 0 if up, 1 if down - GitHub Actions UI shows workflow as "failed" when site is down, providing at-a-glance status without additional alerting logic.
- **Concurrency handling**: GitHub Actions `concurrency` setting prevents simultaneous runs. Git push includes retry with rebase to handle rare concurrent commits.
- **CSV as database**: Append-only CSV committed to Git provides versioned, auditable, queryable dataset. No external database needed. Git handles MB-scale data easily.
- **Cron variance accepted**: GitHub Actions cron has ±5 minute variance - documented as expected behavior rather than a bug to fix.
- **Three execution paths**: (1) Scheduled cron (primary), (2) Manual dispatch (testing), (3) Local CLI (development). Agent HQ (4) optional for issue-driven tasks.
- **Cost awareness**: ~1,440 GitHub Actions minutes/month for 5-minute checks. Fits within free tier (2,000/month private, unlimited public).
- **Extensibility points**: Add alerting by extending monitor.yml (Slack webhook, GitHub Issue). Add multiple URLs via matrix strategy or separate workflows. Add authentication via tool arguments + GitHub Secrets.

### CSV-to-JSON Converter (csv-to-json-converter)
- **Pattern**: Collect > Transform > Store
- **Flow**: Collect CSV files > Analyze structure > Parse CSV > Infer types > Validate data > Convert to JSON/JSONL > Generate reports > Commit
- **Key insight**: Multi-phase transformation with specialist subagents. Each phase (analyze, infer, validate, write) has a dedicated subagent with focused responsibilities. Main agent orchestrates the pipeline.
- **Subagent architecture**: Four specialist subagents (csv-analyzer, type-inference-specialist, data-validator, json-writer) with minimal tool access. Subagents are the DEFAULT delegation mechanism, not Agent Teams.
- **Type inference pattern**: Statistical analysis with confidence scoring (80% threshold). Detects int, float, boolean, datetime, string. Falls back to string for ambiguous columns. Handles 10+ null value representations.
- **Encoding detection**: chardet for automatic encoding detection with UTF-8 fallback. Strips BOM (byte order mark) automatically. Supports UTF-8, Latin-1, Windows-1252, etc.
- **Ragged row handling**: Pad short rows with null, truncate long rows with warning. Log all issues in validation report but continue processing (graceful degradation).
- **Validation without failure**: Validator NEVER raises exceptions. Always returns a report. Strict mode controls whether issues halt the pipeline, but validation itself is fail-safe.
- **JSONL streaming**: For large files (1M+ rows), JSONL format writes one record at a time. No array wrapper. Memory-efficient for multi-GB datasets.
- **Batch processing modes**: Sequential (1-2 files) or parallel (3+ files with Agent Teams). Parallel is 5x faster wall time but same token cost. Always has sequential fallback.
- **Three execution paths**: (1) CLI for local development, (2) GitHub Actions for production, (3) Agent HQ for issue-driven tasks. All three produce identical output.
- **Metadata reporting**: run_summary.json (machine-readable) + validation_report.md (human-readable). Includes per-file stats, type inference results, validation issues, recommendations.
- **No secrets required**: Uses only stdlib (csv, json, pathlib) + chardet + python-dateutil. No external APIs. Pure data transformation pipeline.
- **Git commit discipline**: Stage ONLY output files (never `git add -A`). Commit message includes file count, row count, timestamp. Output directory is parameterized.
