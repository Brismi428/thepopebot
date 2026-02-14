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

### RSS Digest Monitor (rss-digest-monitor)
- **Pattern**: Monitor > Collect > Transform > Deliver (with state persistence)
- **Flow**: Load state > Fetch RSS feeds > Filter new posts > Generate HTML digest > Send email > Update state > Commit
- **Key insight**: State persistence in Git prevents post duplication across runs. Composite GUID keys (feed_url::guid) prevent false deduplication. State is ONLY updated after successful email delivery, ensuring retry on failure.
- **Subagent architecture**: Three specialist subagents (rss-fetcher-specialist, digest-generator-specialist, state-manager-specialist). Subagents are the DEFAULT delegation mechanism. Sequential execution is correct due to clear data dependencies.
- **Per-feed error isolation**: One failed feed does NOT kill the entire run. Each feed is fetched independently with try/except. Failed feeds are logged and skipped. Graceful degradation ensures partial success.
- **Composite GUID pattern**: Use `feed_url::entry_guid` as deduplication key instead of guid alone. Prevents false positives when different feeds use the same GUID format.
- **State file size management**: Enforce maximum 10,000 GUIDs by keeping most recent entries. Prevents unbounded state growth. Log warning if limit is hit.
- **Email with fallback**: MIME multipart with HTML primary and plain-text fallback. Ensures compatibility with all email clients. HTML is styled with inline CSS for maximum rendering support.
- **Conditional email send**: Skip email generation if no new posts found. Silent run with state update only. Saves API calls and prevents empty emails.
- **SMTP retry logic**: Retry once with 30s delay on transient failures (auth, network, timeout). Do NOT update state if email send fails -- posts retry on next run.
- **First-run initialization**: Missing or corrupted state file initializes empty state. All posts are processed on first run. Log warning but continue (better to duplicate once than crash).
- **Date parsing with fallback**: Use python-dateutil for robust parsing of varied date formats. If unparseable, use current timestamp. Include post anyway (better to duplicate than miss).
- **Three execution paths**: (1) Scheduled cron at 8 AM UTC (primary), (2) Manual dispatch with force_send (testing), (3) Local CLI (development). All produce identical output.
- **Run summary logging**: Each run produces `logs/YYYY-MM-DD_run.json` with feeds_checked, feeds_failed, new_posts, email_sent, failed_feeds array. Machine-readable audit trail.
- **Git commit discipline**: Stage ONLY state/rss_state.json and logs/*.json. NEVER `git add -A`. Commit message includes date and post count for easy history review.
- **No MCP dependencies**: Uses standard Python libraries (feedparser, smtplib, json, pathlib). Works out-of-the-box with only Python and requirements.txt. No external MCPs required.
- **Cost awareness**: ~3-5 minutes per day = ~90-150 GitHub Actions minutes/month. Well within free tier (2,000/month private, unlimited public). Minimal token cost for state management only.

## 11. Content Transformation with Tone Matching

**Summary:** An AI-powered content repurposing pipeline that extracts content from a source URL, analyzes its tone and style, and generates platform-optimized variants (social media, email, etc.) that match the source tone automatically.

### When to Use

- You need to publish the same content across multiple platforms with different format requirements
- Content must maintain consistent voice/tone across all platforms
- Manual reformatting for each platform is time-consuming and error-prone
- You want AI to handle platform-specific best practices (character limits, hashtags, formatting)

### Steps

1. **Fetch source content** -- Scrape the source URL (blog post, article) and extract clean text/markdown. Use Firecrawl with HTTP fallback for reliability.
2. **Analyze tone** -- Use LLM (Claude) with structured output to analyze writing style across multiple dimensions: formality, technical level, humor, primary emotion. Return confidence score.
3. **Generate platform variants (parallel)** -- For each target platform (Twitter, LinkedIn, email, Instagram):
   - Send source content + tone analysis to LLM
   - Request platform-optimized output matching source tone
   - Enforce platform-specific constraints (char limits, hashtag counts, formatting rules)
   - Validate character counts before accepting output
4. **Merge and output** -- Combine all variants into single JSON file with metadata, tone analysis, and all platform content

### Key Tools / MCPs

- **Firecrawl MCP** -- reliable web scraping with JS rendering support
- **Anthropic MCP** -- Claude for tone analysis and content generation
- **HTTP + BeautifulSoup** -- fallback scraping if Firecrawl unavailable
- **Python stdlib** -- JSON manipulation, filename slugification, output assembly

### GitHub Actions Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      blog_url:
        description: 'Blog post URL to repurpose'
        required: true
  # Can also be triggered on new blog post detection via RSS or webhook
```

### Example Use Cases

- Marketing team publishes a blog post, wants Twitter thread, LinkedIn post, email newsletter section, and Instagram caption
- Content creator wants to maximize reach by publishing same content on all major platforms
- Agency needs to repurpose client blog posts for multi-channel campaigns
- Developer advocates want to turn technical blog posts into social-friendly content

### Subagent Architecture

- **content-scraper-specialist** -- Handles web scraping with fallback strategies
- **tone-analyzer-specialist** -- Analyzes source content tone/style
- **content-generator-specialist** -- Coordinates multi-platform generation (can use Agent Teams for parallelization)
- **output-assembler-specialist** -- Merges all content into final JSON

### Agent Teams Parallelization

Platform generation is ideal for Agent Teams:
- 4 independent platform generation tasks (Twitter, LinkedIn, email, Instagram)
- Each takes 10-15 seconds sequentially = 40-55s total
- Parallel execution with 4 teammates = 12-18s
- **2x speedup** with identical results and same token cost

### Platform-Specific Constraints

| Platform | Char Limit | Hashtags | Format Notes |
|----------|------------|----------|--------------|
| Twitter | 280 per tweet | 2-3 per thread | Numbered thread (1/N format), hook in first tweet, CTA in last |
| LinkedIn | 3000 max, 1300 target | 3-5 | Professional tone, hook before "see more" fold, line breaks |
| Email | 500-800 words | N/A | Subject line (40-60 chars), scannable format, HTML + plain text |
| Instagram | 2200 max | 10-15 | Casual tone, emojis (3-5), line breaks, hook before "more" button |

### Tone Matching Pattern

1. LLM analyzes source content with structured JSON schema
2. Returns tone profile: {formality, technical_level, humor_level, primary_emotion, confidence}
3. Platform generators receive tone profile in their prompts
4. Each generator adjusts output style to match source tone (formal → formal, casual → casual)
5. Result: All platforms sound like they were written by the same person

### Failure Handling

- **Scraping failure** -- Halt workflow immediately (no content = can't proceed). Log clear error about paywall/404/timeout.
- **Tone analysis failure** -- Return default neutral profile, continue with warning. Quality slightly reduced but system remains functional.
- **Single platform failure** -- Continue with other platforms. Include error structure for failed platform in output. Partial success is acceptable.
- **Character limit exceeded** -- Tools automatically truncate with "..." and log warning. Better than crashing.

### Performance & Cost

**Execution time**:
- Sequential: ~52-74 seconds
- With Agent Teams: ~25-37 seconds (2x faster)

**API cost per run** (Claude Sonnet 4):
- Scraping: $0.01-0.02 (Firecrawl)
- LLM calls: ~$0.09 (tone + 4 platforms)
- **Total: ~$0.10-0.11 per blog post**

### Success Criteria

✅ Source content extracted (≥ 100 chars)
✅ Tone analysis returns confidence ≥ 0.5
✅ At least 2/4 platforms generate successfully
✅ All character counts within platform limits
✅ Output JSON file written to repo

### Key Learnings

- **Tone matching is powerful** -- AI can accurately replicate writing style when given structured tone analysis
- **Parallel generation scales well** -- 4 independent LLM calls are perfect for Agent Teams
- **Character validation is critical** -- Must validate before returning, not after
- **Partial success is acceptable** -- 3/4 platforms working is better than all-or-nothing
- **Firecrawl + fallback pattern works** -- Primary API with HTTP backup maximizes reliability
- **Subagent specialization reduces complexity** -- Each subagent has clear, scoped responsibility

### Related Patterns

Combines elements of:
- **Scrape > Process > Output** (content extraction)
- **Fan-Out > Process > Merge** (parallel platform generation via Agent Teams)
- **Generate > Review > Publish** (content creation with validation)

## 12. Sequential State Management Pipeline

**Summary:** A data transformation pipeline that maintains persistent state across runs using atomic file operations. Each execution reads current state, transforms data, generates output, updates state, and commits results -- all while preventing race conditions.

### When to Use

- You need sequential numbering or versioning that persists across workflow runs
- Output depends on previous runs (counters, IDs, sequence numbers)
- Concurrent execution must not create duplicates
- State must survive container/server restarts
- Git-native state storage is preferred over external databases

### Steps

1. **Read State** -- Load previous state from committed file
2. **Lock State** -- Acquire file lock to prevent concurrent modifications
3. **Transform Data** -- Process input using current state
4. **Update State** -- Increment counter, add ID, update version
5. **Generate Output** -- Produce artifacts using updated state
6. **Commit State** -- Write state file and outputs to repo
7. **Release Lock** -- Allow next execution to proceed

### Key Tools / MCPs

- **filelock** (Python) -- Atomic file locking with timeout
- **Git** -- State file versioning and recovery
- **filesystem MCP** -- Read/write state files
- **JSON** (stdlib) -- State serialization

### GitHub Actions Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      data:
        description: 'Input data to process'
        required: true
  push:
    paths:
      - 'input/**'
```

### Example Use Cases

- Invoice generator with sequential invoice numbers (INV-1001, INV-1002...)
- Document versioning system (v1.0, v1.1, v2.0...)
- Sequential ID assignment for records
- Incrementing batch job numbers
- Auto-incrementing PR numbers in custom systems

### State File Format

```json
{
  "last_value": 1042,
  "prefix": "INV-",
  "padding": 4,
  "metadata": {
    "last_updated": "2026-02-11T14:30:00Z",
    "total_count": 1042
  }
}
```

### Atomic Operations Pattern

```python
from filelock import FileLock, Timeout

lock_path = f"{state_file}.lock"
try:
    with FileLock(lock_path, timeout=5):
        # Read current state
        state = json.loads(Path(state_file).read_text())
        
        # Modify state
        state["last_value"] += 1
        
        # Write updated state
        Path(state_file).write_text(json.dumps(state, indent=2))
        
        # Return new value
        return state["last_value"]
except Timeout:
    # Fallback: use timestamp or other unique value
    return generate_fallback_value()
```

### Failure Handling

**Lock timeout (5 seconds)**
- **Cause**: Concurrent execution or filesystem issue
- **Action**: Use fallback mechanism (timestamp, UUID, or queue for retry)
- **Log**: Warning with details for investigation
- **Continue**: Workflow proceeds with fallback value

**State file missing**
- **Cause**: First run or file deleted
- **Action**: Initialize to default starting value
- **Log**: Info message about initialization
- **Continue**: Normal operation from initial state

**State file corrupted**
- **Cause**: Incomplete write, manual edit, merge conflict
- **Action**: Restore from Git history or reinitialize
- **Log**: Error with corrupted content
- **Halt**: Require manual intervention (prevents data loss)

**Concurrent modifications**
- **Prevented by**: File locking ensures only one process modifies at a time
- **If lock fails**: Fallback prevents workflow failure
- **Trade-off**: Fallback may break sequential ordering but ensures system continues

### Git-Native State Management

State files are committed to the repository:

**Benefits:**
- Version history (full audit trail)
- Rollback capability (`git checkout HEAD~5 state.json`)
- Merge conflict detection
- No external database needed
- Free hosting on GitHub

**Considerations:**
- Not suitable for high-frequency updates (>100/min)
- Commit overhead (~1-2 seconds per update)
- Repo size impact (minimal for small JSON files)

### Fallback Strategies

When atomic state update fails, use one of these fallbacks:

| Strategy | When to Use | Trade-off |
|----------|-------------|-----------|
| **Timestamp** | Unique value needed, order not critical | Breaks sequential numbering |
| **UUID** | Unique value needed, no pattern required | No human-readable sequence |
| **Queue for retry** | Sequential order is critical | Delays processing |
| **Range allocation** | High concurrency expected | More complex state management |

### Integration Points

**GitHub Actions:**
```yaml
steps:
  - name: Get next value
    id: state
    run: |
      python tools/manage_state.py state.json get_next > output.json
      VALUE=$(jq -r '.value' output.json)
      echo "VALUE=$VALUE" >> $GITHUB_OUTPUT
  
  - name: Use value
    run: |
      process_data.py --id ${{ steps.state.outputs.VALUE }}
  
  - name: Commit state
    run: |
      git add state.json output/*
      git commit -m "Process ID ${{ steps.state.outputs.VALUE }}"
      git push
```

### Success Criteria

- State file exists and is valid JSON
- Lock acquired within timeout (5 seconds)
- State incremented correctly
- Output files reference correct state value
- State file committed (or queued for commit)
- Audit trail complete (log entry written)

### Performance Characteristics

- **Lock acquisition**: < 100ms (no contention) to 5s (with contention)
- **State read/write**: < 50ms (small JSON files)
- **Git commit**: 1-2 seconds
- **Total overhead**: 2-7 seconds per execution

**Bottleneck:** Git commit (unavoidable for state persistence)

### Key Learnings (from invoice-generator build)

- **Lock timeout must have fallback** -- Never let locking failure halt the workflow
- **Initialize on missing file** -- Don't fail on first run
- **Timestamp fallback works** -- Breaks sequence but ensures uniqueness
- **Audit log is separate** -- State update and audit logging are independent
- **State-before-output** -- Update state BEFORE generating output (prevents duplicate detection)
- **Decimal for currency** -- Use Decimal type when state affects financial calculations

### Anti-Patterns to Avoid

- **No locking** -- Race conditions create duplicates
- **Hardcoded initial value** -- Make it configurable
- **Fail without fallback** -- Lock timeout should not crash the system
- **Update state after output** -- Output first, then state (wrong order leads to duplicates on failure)
- **Manual state edits** -- Always use the tool (manual edits bypass validation)
- **Ignore lock timeouts** -- Log and investigate when locks time out frequently

### Related Patterns

Combines elements of:
- **Collect > Transform > Store** (base pipeline)
- **Monitor > Detect > Alert** (state changes can trigger alerts)
- **Generate > Review > Publish** (state affects generated content)

Often used with:
- **Intake > Enrich > Deliver** (state provides IDs or version numbers)
- **Fan-Out > Process > Merge** (each parallel task gets unique ID from state)

## 13. Multi-Source Weekly Monitor with Snapshot Comparison

**Summary:** A scheduled monitoring system that crawls multiple websites weekly, stores Git-native snapshots, detects changes by comparing against previous week's state, and generates a unified digest report. Combines web scraping, state persistence, and change detection in a single workflow.

### When to Use

- Need to monitor 3+ websites/competitors on a recurring schedule (weekly/daily)
- Want version-controlled audit trail of historical snapshots
- Need to detect specific change types (new content, price changes, feature additions)
- Generating comparative reports across multiple sources
- Git-native storage is preferred over external databases

### Steps

1. **Load targets** -- Read configuration listing all URLs to monitor
2. **Crawl sources** -- Scrape each target website (parallel if 3+ targets)
3. **Compare snapshots** -- Load previous snapshot, diff against current
4. **Detect changes** -- Identify new content, updated values, removed items
5. **Generate report** -- Create unified digest across all sources
6. **Save snapshots** -- Store current state with atomic writes + pruning
7. **Commit to Git** -- Push report + snapshots to repository

### Key Tools / MCPs

- **Firecrawl MCP** -- primary web scraping (handles JS rendering)
- **HTTP + BeautifulSoup** -- fallback scraping if Firecrawl unavailable
- **Git** -- state persistence, version history, audit trail
- **Python difflib** -- snapshot comparison logic
- **Agent Teams** -- parallel crawling for 3+ sources (optional)

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'   # Every Monday at 8 AM UTC (weekly)
  workflow_dispatch:
    inputs:
      force_run:
        type: boolean
        default: false
```

### Example Use Cases

- Weekly competitor monitoring (blog posts, pricing, features)
- Daily government filing tracker (new documents, regulatory changes)
- E-commerce price monitoring across multiple retailers
- Multi-blog content aggregation with change detection
- Product changelog aggregation across vendor sites

### Subagent Architecture

**Pattern uses specialist subagents** (default delegation mechanism):

- **crawl-specialist** -- Web scraping with fallback strategies
- **change-detector-specialist** -- Snapshot comparison and diff logic
- **report-generator-specialist** -- Digest markdown generation
- **snapshot-manager-specialist** -- State persistence and pruning

Delegation is the default. Agent Teams is ONLY used for parallel crawling (3+ sources).

### Agent Teams Parallelization

**When:** 3+ sources configured  
**Why:** Independent crawls with no data dependencies  
**Benefit:** 3-4x speedup (5 sources: 75s sequential → 20s parallel)  
**Trade-off:** None (same token cost, just parallel execution)

**Team structure:**
- Team lead: Coordinates crawlers, collects snapshots
- Teammates: One per source, each delegates to `crawl-specialist`
- Merge: Simple collection (no conflict resolution)

**Sequential fallback:** Always available if Agent Teams disabled/fails

### Git-Native Snapshot Storage

**Pattern:** Commit JSON snapshots to `state/snapshots/{source}/YYYY-MM-DD.json`

**Benefits:**
- Version history (full audit trail)
- Free hosting (no external database costs)
- Rollback capability (`git checkout HEAD~10`)
- Merge conflict detection
- Queryable with `jq`, `grep`, `git log`

**Storage management:**
- Atomic writes (temp file + rename)
- Automatic pruning (keep last 52 snapshots = 1 year)
- Size limits (compress if > 10MB, drop excerpts)
- Latest symlink/copy for easy access

### Change Detection Logic

**New content detection:**
- Blog posts: Compare URLs or titles (case-insensitive)
- Features: Compare feature titles (case-insensitive)

**Value change detection:**
- Pricing: Numeric comparison with delta calculation
- Text: String comparison with change percentage

**First-run handling:**
- Missing previous snapshot → Treat all content as "new"
- This is expected behavior, not an error

### Report Generation

**Output:** Markdown digest with:
- Summary statistics across all sources
- Per-source sections with detected changes
- Links to new content
- Price deltas with percentage change
- Zero-changes report (still generated as "heartbeat")

**Email delivery (optional):**
- Plain-text version of markdown report
- SMTP with retry logic
- Failure is non-fatal (report already in Git)

### Failure Handling

| Scenario | Action | Rationale |
|----------|--------|-----------|
| 1 source fails crawl | SKIP source, continue | Partial data better than none |
| All sources fail | HALT workflow | No data to process |
| Previous snapshot missing | CONTINUE as first run | Normal initialization |
| Snapshot too large (>10MB) | COMPRESS (drop excerpts) | Keep repo lean |
| Email send fails | LOG error, continue | Report already in Git |
| Git push fails | RETRY once, then HALT | Results not persisted = failure |

**Per-source error isolation:** One failed crawl does not kill entire workflow.

### Performance Characteristics

**Sequential (1-2 sources):**
- Time: ~15-30s per source
- Suitable for: Small deployments

**Parallel (3+ sources with Agent Teams):**
- Time: ~20-40s total (regardless of source count)
- Speedup: 3-4x for 5+ sources
- Token cost: Same as sequential

### Cost Analysis (3 sources, weekly)

**GitHub Actions:**
- Per run: ~5 minutes
- Monthly: ~20 minutes (4 runs)
- Within free tier: 2,000 min/month (private repos)

**API costs:**
- Firecrawl: ~$0.03-0.06/run (3 pages × 3 sources)
- Claude: ~$0.05-0.15/run
- Total: ~$0.08-0.21/run
- Monthly: ~$0.32-0.84 (4 runs)

### Key Learnings (from competitor-monitor build)

**Selector-based extraction with fallback:**
- Primary: CSS selectors configured per source
- Fallback 1: Generic extraction (all links, headings)
- Fallback 2: Full-page markdown
- Rationale: Partial data beats no data

**Firecrawl → HTTP fallback chain:**
- Firecrawl handles JS-heavy sites (primary)
- HTTP + BeautifulSoup if API unavailable (fallback)
- No external dependency required (system works with stdlib only)

**Git-native state is sufficient:**
- No external database needed for weekly monitoring
- Git history = audit trail
- 52-week retention is adequate
- Pruning prevents repo bloat

**Zero-changes reports are valuable:**
- Generate report even if no changes detected
- Serves as "heartbeat" confirmation system ran
- Prevents silent failures

**Email is optional, not critical:**
- Report committed to Git is the source of truth
- Email failure should not fail workflow
- Retry once, then log and continue

**Atomic Git commits:**
- Either all files commit or none
- Retry logic with rebase prevents partial state
- Failure to push = workflow fails (correct behavior)

**Subagent specialization reduces complexity:**
- Each subagent has clear, scoped responsibility
- Tools are simple (single purpose)
- Main agent coordinates, subagents execute
- Agent Teams only for parallel execution, not delegation

### Success Criteria

- ✅ Report committed to Git (`reports/YYYY-MM-DD.md`)
- ✅ Snapshots saved for all sources (`state/snapshots/{slug}/`)
- ✅ At least 1 source successfully crawled
- ✅ Workflow exits 0 (success)

### Anti-Patterns to Avoid

- **All-or-nothing crawling** -- Skip failed sources, continue with successful ones
- **Hardcoded URLs** -- Always use config files
- **Ignoring first-run** -- Missing previous snapshot is normal, not an error
- **Skipping zero-changes report** -- Always generate (serves as heartbeat)
- **External database for state** -- Git-native is simpler and free
- **Manual snapshot management** -- Always use atomic writes + pruning tool
- **Email as critical path** -- Report in Git is the source of truth

### Related Patterns

Combines elements of:
- **Monitor > Detect > Alert** (scheduled change detection)
- **Scrape > Process > Output** (web scraping with extraction)
- **Collect > Transform > Store** (Git-native state persistence)
- **Fan-Out > Process > Merge** (Agent Teams parallel crawling)

Often paired with:
- **Generate > Review > Publish** (report generation)
- **Sequential State Management Pipeline** (if snapshot ordering matters)

### Proven Compositions

**Competitor intelligence pipeline:**
- Monitor 3-5 competitor websites weekly
- Detect blog posts, pricing changes, feature launches
- Generate digest report with side-by-side comparison
- Email to product/marketing teams

**Regulatory filing tracker:**
- Monitor government/regulatory sites daily
- Detect new filings, rule changes, notices
- Generate daily digest with links
- Alert legal/compliance teams

**Multi-vendor changelog aggregator:**
- Monitor 10+ vendor documentation sites
- Detect API changes, deprecation notices
- Generate weekly engineering digest
- Reduce surprise breaking changes

## 14. Multi-Stage Content Generation with Quality Gates

**Summary:** An AI-powered content generation pipeline that creates platform-optimized content (social media, marketing, etc.), runs multi-dimensional automated quality review, and either auto-publishes or generates manual content packs based on quality gates.

### When to Use

- Need to generate high-volume content while maintaining brand voice consistency
- Content must pass compliance checks before publishing
- Want automated quality assurance without sacrificing human oversight option
- Publishing decision should depend on automated quality score
- Platform-specific formatting and optimization required

### Steps

1. **Input Validation** -- Parse inputs (brand guidelines, theme, content plan), validate structure
2. **Reference Research** -- Fetch source material from URLs for factual grounding
3. **Strategy Generation** -- Create per-item content strategy with LLM analysis
4. **Content Generation (Parallel or Sequential)** -- Generate all content items
   - **If 3+ items**: Use Agent Teams for parallel generation (5x speedup)
   - **If <3 items**: Generate sequentially
5. **Multi-Dimensional Quality Review** -- Score across N dimensions (brand voice, compliance, format, claims)
6. **Gate Decision** -- Deterministic logic: if quality >= threshold AND mode == auto: publish, else: manual pack
7a. **Auto-Publish** -- Format for platform API, execute publish calls, handle rate limits/errors
7b. **Manual Content Pack** -- Generate human-readable + machine-readable output, upload checklist
8. **Archive & Index** -- Update rolling index, prune old archives, commit to repo
9. **Notification** -- Post summary to issue/Slack with links to outputs

### Key Tools / MCPs

- **Anthropic MCP** -- Content generation, quality review, strategy
- **Firecrawl MCP** -- Reference content extraction (with HTTP fallback)
- **Platform API** -- Publishing integration (Instagram Graph API, LinkedIn, Twitter, etc.)
- **Python** -- Tool orchestration, data transformation

### GitHub Actions Trigger

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'   # Weekly content generation
  workflow_dispatch:
    inputs:
      theme: ...
      content_plan: ...
      publishing_mode: choice[auto_publish, content_pack_only]
  issues:
    types: [opened, labeled]  # Agent HQ pattern
```

### Example Use Cases

- **Weekly Instagram Content:** Generate 7 posts (reels, carousels, singles) with captions, hashtags, creative briefs
- **LinkedIn Thought Leadership:** Generate weekly posts with brand voice compliance
- **Email Newsletter Sequences:** Generate multi-email outreach or nurture campaigns
- **Blog Post Drafts:** Generate SEO-optimized blog posts with automated fact-checking
- **Product Descriptions:** Generate e-commerce product descriptions at scale

### Subagent Architecture (6 specialists)

This pattern benefits from specialist subagents:

- **strategist** -- Research + strategy generation
- **copywriter** -- Text content generation
- **hashtag-specialist** -- Platform-specific optimization (hashtags, keywords)
- **creative-director** -- Visual content briefs, image prompts
- **reviewer** -- Multi-dimensional quality scoring
- **publisher** -- Platform API integration or manual pack generation

**Key insight:** Subagents are the DEFAULT delegation mechanism. Each specialist has focused domain expertise and minimal tool access (principle of least privilege).

### Agent Teams Parallelization

**Apply the 3+ Independent Tasks Rule:**
- If content_plan specifies 3+ items (e.g., 7 Instagram posts): Use Agent Teams
- Each teammate generates ONE item independently
- Team lead merges results, runs consistency check (no duplicate content)

**Performance:**
- Sequential: ~10-15 seconds per item × 7 items = 70-105 seconds
- Parallel: ~12-18 seconds total (5x wall-time speedup, same token cost)

**Fallback:** Always provide sequential execution path (identical output, slower wall time).

### Multi-Dimensional Quality Review Pattern

**Core concept:** Score content across N independent dimensions with configurable thresholds.

**Typical dimensions:**
1. **Brand Voice Alignment** (0-100) -- Tone, audience fit, style match
2. **Compliance Checks** (0-100, must be 100) -- Banned topics, prohibited claims, approved CTAs
3. **Platform Optimization** (0-100) -- Hashtag hygiene, character limits, format rules
4. **Format Validation** (0-100) -- Character counts, required fields present
5. **Claims Verification** (0-100, must be 100) -- Factual claims sourced from references

**Scoring:**
- Each dimension scored independently by LLM with structured JSON output
- Overall score = average of all dimensions
- Pass/fail logic: `overall >= 80 AND critical_dimensions == 100`

**Benefits:**
- Transparent quality assessment (human-readable breakdown)
- Tunable per dimension (adjust thresholds for different content types)
- Fails gracefully (manual pack if gates not met)

### Gate Decision Pattern

**Deterministic logic layer** between quality review and publishing:

```
IF quality.pass_fail == "PASS" AND mode == "auto_publish":
  action = "publish"
ELSE IF quality.pass_fail == "FAIL":
  action = "manual_pack"
  rationale = "Quality score below threshold or compliance issues"
ELSE:  # mode == "content_pack_only"
  action = "manual_pack"
  rationale = "Manual review mode enabled"
```

**Key insight:** Separating gate logic from quality review keeps review neutral (just reports scores) and makes decision logic easy to modify.

### Failure Handling

**Progressive degradation:**
- **Reference fetch failures** -- Continue with available references, flag if all fail
- **LLM API failures** -- Retry once with exponential backoff, escalate if fails
- **Quality gates not met** -- Generate manual content pack (fail-safe)
- **Publishing failures** -- Fall back to manual pack for failed items, log details
- **Rate limits** -- Pause, log next retry time, generate manual pack for remaining

**Philosophy:** Partial success is acceptable. Manual intervention is always an option.

### Output Structure

**Dual-format outputs:**
- **Markdown** -- Human-readable, ideal for review/approval
- **JSON** -- Machine-readable, ideal for automation/integration
- **Upload Checklist** -- Copy-paste ready instructions for manual publishing

**Rolling archive:**
- `latest.md` -- Always points to most recent output
- Dated directories (YYYY-MM-DD) with full content packs
- Configurable retention (default: 12 weeks)

### Cost Optimization

**Per run (7 items):**
- LLM calls: Strategy (1) + Items (7) + Review (1) = 9 calls
- Claude Sonnet 4: ~$0.08-0.12 per run
- Platform API: Usually free (rate limits apply)
- GitHub Actions: ~5-10 minutes (~$0.008, fits free tier)

**Total: ~$0.10-0.15 per content pack**
**Monthly (4 runs): ~$0.40-0.60**

### Success Criteria

✅ Generates complete content items with all required fields
✅ Runs N-dimensional quality review
✅ Auto-publishes when quality gates pass and mode enabled
✅ Falls back to manual packs when needed
✅ Outputs structured JSON + human-readable Markdown
✅ Maintains rolling archive with latest index
✅ System runs autonomously via GitHub Actions
✅ All three execution paths work (CLI, Actions, Agent HQ)

### Key Learnings (from weekly-instagram-content-publisher build)

- **Subagent specialization reduces complexity** -- 6 focused subagents > 1 monolithic agent
- **Quality gates prevent bad content** -- 3-check system (overall, compliance, claims) is effective
- **Dual-format output is valuable** -- Markdown for humans, JSON for machines
- **Firecrawl + HTTP fallback pattern works** -- Primary API with degraded fallback maximizes reliability
- **Agent Teams scales content generation** -- 5x speedup for 7 posts with identical token cost
- **Platform API error handling is critical** -- Rate limits, auth failures, media URL issues all need graceful degradation
- **Rolling archive with retention** -- 12-week retention prevents repo bloat while maintaining history
- **Three execution paths required** -- CLI (dev), Actions (prod), Agent HQ (user-driven) cover all use cases

### Related Patterns

Combines elements of:
- **Generate > Review > Publish** (core flow)
- **Fan-Out > Process > Merge** (Agent Teams parallelization)
- **Sequential State Management** (rolling archive)
- **Multi-Source Research** (reference extraction)

Often paired with:
- **Intake > Enrich > Deliver** (enrich with brand voice)
- **Monitor > Detect > Alert** (quality score monitoring over time)
