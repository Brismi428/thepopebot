# WAT Systems Factory — Build Workflow

This is the factory's own WAT workflow. Follow these steps to build a new WAT system from a problem description or n8n workflow JSON.

## Inputs

- **problem_description**: A natural language description of the system to build, OR an n8n workflow JSON file
- **system_name**: A lowercase-with-dashes name for the new system
- **enable_agent_teams**: Boolean — whether to use Agent Teams for parallelizable tasks (optional, default false)

## Outputs

- A complete WAT system in `systems/{system_name}/` containing:
  - `CLAUDE.md` — operating instructions
  - `workflow.md` — the system's process workflow
  - `tools/` — Python tool files
  - `.github/workflows/` — GitHub Actions workflow files
  - `requirements.txt` — Python dependencies
  - `README.md` — setup and usage instructions

---

## Step 1: Intake

Receive and classify the input.

1. Read the `problem_description` input
2. **Is this an n8n workflow JSON?**
   - Check if the input is valid JSON containing n8n workflow structure (nodes, connections)
   - **If yes**: Route to Step 1b (n8n Conversion)
   - **If no**: Continue to Step 2 with the problem description as-is

### Step 1b: n8n Conversion

Convert an existing n8n workflow into WAT format.

1. Parse the n8n JSON using `factory/tools/convert_n8n.py`
2. Reference `converters/n8n_node_map.md` to translate every node type
3. Map each n8n element:
   - **Trigger nodes** (Webhook, Schedule, Manual) → GitHub Actions triggers
   - **Action nodes** (HTTP Request, Function, etc.) → Python tools
   - **Logic nodes** (IF, Switch, Merge) → Decision points in workflow.md
   - **Connections** → Step ordering and data flow in workflow.md
4. Extract the underlying workflow logic as a structured design
5. Preserve the original n8n JSON as `reference/original_n8n.json` in the output system
6. Continue to Step 3 with the translated design

**Failure mode**: If the n8n JSON is malformed or contains unsupported node types, log the specific issues and generate a partial conversion with TODO markers for unsupported elements.

---

## Step 2: Research

Identify available tools and resources for the system.

1. Read `config/mcp_registry.md` — what MCPs are available?
2. Read `library/tool_catalog.md` — what reusable tool patterns exist?
3. Read `library/patterns.md` — does this problem match a known pattern?
4. For each capability the system needs:
   - Check if an MCP provides it (preferred — less code to maintain)
   - Check if a tool pattern exists in the catalog (reusable — faster to implement)
   - Plan a custom tool if nothing exists (document as a new pattern candidate)
5. Document the research findings: which MCPs, patterns, and tools will be used

**Failure mode**: If the MCP registry is empty or missing, fall back to direct HTTP/API tools. The system must work without any specific MCP.

---

## Step 3: Design

Architect the workflow for the new system.

1. Break the problem into discrete steps — each step should do one thing clearly
2. Define the order: which steps depend on which?
3. Identify decision points: where does the workflow branch based on conditions?
4. Define failure modes for each step: what can go wrong and what's the fallback?
5. Define inputs and outputs for each step
6. **Design Subagents** — identify specialist subagents for the system:
   - **Every system gets subagents**. Subagents are the DEFAULT delegation mechanism. For each major phase or capability in the workflow, define a specialist subagent.
   - For each subagent, define:
     - **name**: lowercase-with-hyphens identifier (e.g., `search-specialist`, `data-processor`)
     - **description**: When Claude should delegate to this subagent (used for automatic delegation)
     - **tools**: Which Claude Code tools this subagent needs (Read, Write, Edit, Bash, Grep, Glob, etc.) — grant only what's needed
     - **model**: `sonnet` for most tasks, `haiku` for simple/fast tasks, `opus` for complex reasoning
     - **permissionMode**: `default` unless the subagent needs autonomous writes (`acceptEdits`)
     - **system_prompt**: Detailed instructions — the subagent's domain expertise, how to use its tools, expected inputs/outputs, error handling
   - **Delegation hierarchy** (critical):
     - **Subagents are the default** for all task delegation within a system. When the workflow reaches a phase, delegate to its specialist subagent.
     - **Agent Teams is ONLY used** when the design identifies 3+ truly independent tasks that can run in parallel. Agent Teams is a parallelization optimization, not a delegation mechanism.
     - A system can use BOTH: subagents for delegation AND Agent Teams for parallel execution of independent subagent tasks.
   - Document all subagents in the design output — they will be generated in Step 5b
7. **Agent Teams Analysis** — evaluate whether this system ALSO benefits from Agent Teams:
   - **Count independent tasks**: List all tasks that have no data dependencies on each other
   - **Apply the 3+ Independent Tasks Rule**:
     - **3 or more independent tasks** → Recommend Agent Teams. Flag these tasks for parallel execution with the native team lead/teammate pattern. Set `enable_agent_teams` to true.
     - **Fewer than 3 independent tasks** → Sequential execution is sufficient. Note in the design that Agent Teams is not recommended.
   - **Assess parallelization benefit**: Will concurrent execution meaningfully reduce total time? (e.g., 3 API calls at 10s each → 10s parallel vs 30s sequential = meaningful)
   - **Check merge complexity**: Can the parallel results be combined without complex reconciliation? If merging is harder than the parallel speedup, prefer sequential.
   - **Document the decision**: Record in the design whether Agent Teams is recommended, which tasks would run in parallel, and the rationale
   - **If Agent Teams is recommended**: Define team roles:
     - **Team Lead responsibilities**: What the coordinator does (create task list, spawn teammates, merge results, quality control)
     - **Teammate definitions**: For each parallel task, define the scoped instructions, expected inputs, and expected outputs
     - **Shared task list structure**: What tasks appear on the list, their dependencies (blockedBy/blocks), and completion criteria
   - **If Agent Teams is NOT recommended**: Design for sequential execution only. Note why (e.g., "all tasks depend on previous output" or "only 2 independent tasks — overhead not justified")
   - **Regardless of recommendation**: The design MUST include a sequential execution path. Agent Teams is always an optimization, never a requirement.
8. Select the workflow pattern from `library/patterns.md` that best fits (or define a new one)

**Failure mode**: If the problem is too vague to design a clear workflow, generate a minimal viable workflow with TODO markers and document what clarification is needed.

---

## Step 3b: Factory Parallel Build (Agent Teams)

**This step applies to the factory's own build process, not the generated system.**

When the factory is building a complex system (4+ tools or multiple independent workflow phases), it can use Agent Teams to generate artifacts in parallel. This accelerates the build without affecting the output.

1. **Check if Agent Teams is enabled**: Read `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` from the environment
2. **Assess build complexity**:
   - Count the number of tools to generate
   - Count the number of independent generation steps (workflow, tools, Actions, CLAUDE.md)
   - **If 4+ generation artifacts AND Agent Teams enabled**: Use parallel build
   - **Otherwise**: Continue to Steps 4–7 sequentially (skip this step)
3. **If parallel build**: The factory team lead creates a shared task list and spawns teammates:
   - **Task: Generate Workflow** — Teammate generates `workflow.md` from the design (Step 4)
   - **Task: Generate Tools** — Teammate generates all Python tools from the design (Step 5)
   - **Task: Generate GitHub Actions** — Teammate generates `.github/workflows/` files (Step 6)
   - **Task: Generate CLAUDE.md** — Teammate generates the system's CLAUDE.md (Step 7)
   - Each teammate receives the full design from Step 3 as context
   - Each teammate writes its output to the system's output directory
4. **Team lead collects and validates**: After all teammates complete, the team lead:
   - Verifies all expected files were generated
   - Checks cross-references (e.g., workflow.md mentions tools that exist in `tools/`)
   - Resolves any conflicts or inconsistencies
   - Proceeds to Step 8 (Test)

**Sequential fallback**: If Agent Teams is not enabled, Steps 4–7 execute sequentially as defined below. Results are identical.

**Failure mode**: If a teammate fails, the team lead falls back to generating that artifact sequentially. A partial parallel build is still faster than fully sequential.

---

## Step 4: Generate Workflow

Write the system's `workflow.md`.

1. Run `factory/tools/generate_workflow.py` with the design from Step 3
2. Follow the structure in `factory/templates/workflow_template.md`
3. Include:
   - Clear header with system name and purpose
   - Inputs section with expected parameters
   - Outputs section with deliverables
   - Numbered steps with sub-steps
   - Decision points with bold conditional text
   - Failure modes and fallback steps for every step
4. **If Agent Teams applies**: Include parallel execution sections using `factory/templates/agent_teams_template.md`
   - Define which steps run as sub-agents
   - Define the merge/coordination logic
   - Include a sequential fallback section

**Failure mode**: If workflow generation fails, write a minimal skeleton workflow.md with the key steps and TODO markers.

---

## Step 5: Generate Tools

Write Python tools for each action step.

1. Run `factory/tools/generate_tools.py` with the workflow steps from Step 4
2. For each action step in the workflow:
   - Check `library/tool_catalog.md` for a reusable pattern
   - If found: adapt the pattern for this system's specific needs
   - If not found: generate a new tool following `factory/templates/tool_template.py`
3. Every tool MUST have:
   - Module docstring (purpose, inputs, outputs)
   - `main()` entry point
   - `try/except` error handling
   - `logging` integration
   - Type hints
4. **If Agent Teams is used**: Generate sub-agent task definitions using `factory/tools/generate_agent_teams.py`
5. Generate `requirements.txt` listing all Python dependencies

**Failure mode**: If a tool cannot be generated (e.g., requires an unknown API), create a stub tool with clear TODO markers and document what's missing.

---

## Step 5b: Generate Subagents

Create `.claude/agents/` markdown files for the system's specialist subagents.

1. Run `factory/tools/generate_subagents.py` with the subagent definitions from Step 3
2. For each subagent defined in the design:
   - Generate a markdown file following `factory/templates/subagent_template.md`
   - YAML frontmatter with: `name`, `description`, `tools`, `model`, `permissionMode`
   - Detailed system prompt in the markdown body covering:
     - What the subagent specializes in
     - Which tools to use and how
     - Expected inputs and outputs
     - Step-by-step execution instructions
     - Failure handling procedures
3. Place all subagent files in `{system_dir}/.claude/agents/`
4. Validate each subagent file:
   - Frontmatter parses as valid YAML
   - `name` is lowercase-with-hyphens only
   - `tools` lists only valid Claude Code tools
   - `model` is one of: sonnet, opus, haiku, inherit
   - System prompt is non-empty and specific to the domain

**Failure mode**: If a subagent file fails validation, fix the issue and regenerate. If generation fails entirely, create stub subagent files with TODO markers — the system should still work without subagents (Claude will use tools directly).

---

## Step 6: Generate GitHub Actions

Create `.github/workflows/` files for the new system.

1. Run `factory/tools/generate_github_actions.py` with the system design
2. Using `factory/templates/github_action_template.yml`, create the main workflow:
   - Configure triggers based on the system's needs (dispatch, cron, webhook)
   - Set up Python environment and dependencies
   - Inject required secrets (reference GitHub Secrets, NEVER hardcode)
   - Run Claude Code with the system's workflow.md
   - Commit results back to the repo
   - Configure failure notifications
   - Set `timeout-minutes` on every job
3. Using `factory/templates/agent_hq_template.yml`, create `agent_hq.yml`:
   - Respond to issue assignment and @claude mentions
   - Parse issue body as task input
   - Submit results as draft PR
   - Support iterative feedback

**Failure mode**: If trigger configuration is ambiguous, default to `workflow_dispatch` with a manual input parameter.

---

## Step 7: Generate CLAUDE.md

Write the system's operating instructions.

1. Using `factory/templates/claude_md_template.md`, generate CLAUDE.md with:
   - System identity and purpose
   - Required MCPs and their alternatives
   - Expected inputs and outputs
   - How to execute the workflow
   - **Subagents section**: List all subagents, when to delegate to each, and how to chain them
   - **Delegation hierarchy**: Subagents are the default, Agent Teams only for parallel execution
   - Agent Teams configuration (if any) with token cost notes
   - Agent HQ usage instructions
   - Secret requirements (names only, never values)
   - Troubleshooting common issues
2. This file MUST serve double duty:
   - Instructions for Claude Code when running via CLI or GitHub Actions
   - Context for GitHub Agent HQ when running via issue assignment

**Failure mode**: If unsure about MCP requirements, list all possible MCPs with notes on which are required vs. optional.

---

## Step 8: Test (3-Level Validation Gates)

Validate the generated system through three progressive levels. **Each level must pass before proceeding to the next.** Do not skip levels. Do not proceed past a failing gate.

### Level 1: Syntax & Structure

Verify every generated file is syntactically valid and structurally correct.

1. Run `factory/tools/test_tools.py` in syntax-only mode against each generated tool
2. For each Python tool file:
   - **AST parse**: Verify the file is valid Python (`python -c "import ast; ast.parse(open('{tool}').read())"`)
   - **Import check**: Verify the file imports without errors (`python -c "import importlib; importlib.import_module('{tool_module}')"`)
   - **Structure check**: Verify `main()` exists and is callable
   - **Docstring check**: Verify module-level docstring exists
   - **Error handling check**: Verify at least one `try/except` block exists (AST inspection)
3. For each workflow/markdown file:
   - Verify it is non-empty
   - Verify it has required sections (Inputs, Outputs for workflow.md)
4. For each YAML file (.github/workflows/):
   - Verify valid YAML syntax
   - Verify `timeout-minutes` is set on every job
5. For each subagent file (.claude/agents/):
   - Verify YAML frontmatter parses correctly
   - Verify required fields (`name`, `description`) are present
   - Verify `name` is lowercase-with-hyphens only
   - Verify system prompt body is non-empty
6. Log all Level 1 results

**Gate**: ALL files must pass Level 1. If any file fails:
- Attempt automatic fix (syntax errors, missing docstrings, missing main())
- Re-run Level 1 on the fixed files
- If auto-fix fails after 2 attempts, log the failure and halt the build

**Failure mode**: If the testing infrastructure itself fails, generate a manual Level 1 checklist in README.md and proceed to Level 2 with a warning.

### Level 2: Unit Tests

Verify each tool produces correct output for sample inputs.

1. For each Python tool:
   - Run with sample/mock inputs: `python tools/{tool_name}.py --help` (verify argparse works)
   - Run with minimal valid input and verify:
     - Exit code is 0 on success
     - Output is valid JSON (if tool outputs JSON)
     - Output contains expected keys/structure
   - Run with invalid input and verify:
     - Exit code is non-zero
     - Error message is meaningful (not a raw traceback)
     - The tool does not hang or crash silently
2. For tools that call external APIs:
   - Verify the tool handles missing API keys gracefully (clear error message, non-zero exit)
   - If the PRP provides mock data, use it for testing
   - If no mock data, verify the tool's error path (missing credentials) works correctly
3. Verify `requirements.txt` contains all dependencies used by the tools
4. Log all Level 2 results

**Gate**: ALL tools must pass Level 2. If any tool fails:
- Read the error output, identify the root cause
- Fix the tool code (not the test)
- Re-run Level 2 on the fixed tool
- If fix fails after 2 attempts, log the failure and halt the build

**Failure mode**: If external APIs are unreachable and no mock data exists, verify error handling paths only and document untested happy paths in README.md.

### Level 3: Integration Tests

Verify tools work together as a pipeline and the system is complete.

1. **Pipeline test**: Simulate the workflow end-to-end with sample data
   - Run tools in workflow order, passing each tool's output as the next tool's input
   - Verify the final output matches expected format and contains expected data
   - Verify no tool drops data or produces incompatible output for the next step
2. **Cross-reference validation**:
   - Verify workflow.md references only tools that exist in `tools/`
   - Verify CLAUDE.md documents every tool, subagent, and secret
   - Verify .github/workflows/ YAML references correct tool paths and secret names
   - Verify .env.example lists every secret referenced in CLAUDE.md and GitHub Actions
   - Verify README.md covers all three execution paths
3. **Subagent integration**:
   - Verify each subagent file in `.claude/agents/` is referenced in CLAUDE.md
   - Verify subagent tool lists contain only valid Claude Code tools
   - Verify subagent descriptions match the workflow phases they serve
4. **Package completeness**:
   - Verify all required system files exist (CLAUDE.md, workflow.md, tools/, .github/workflows/, requirements.txt, README.md, .env.example, .gitignore)
   - Verify no hardcoded secrets in any file (scan for common patterns: `sk-`, `api_key=`, bearer tokens)
5. Log all Level 3 results

**Gate**: ALL integration checks must pass. If any fail:
- Identify the inconsistency (e.g., workflow.md references a tool that does not exist)
- Fix the source file
- Re-run Level 3
- If fix fails after 2 attempts, log the failure and halt the build

**Failure mode**: If the full pipeline cannot be tested (e.g., requires live API access), test each tool independently with sample data and document the untested integration path in README.md.

---

## Step 8c: Smoke Tests (Level 4 Validation)

Run post-build smoke tests on the generated tools. This is a 4th validation level that attempts to actually execute each tool with sample input.

1. Run `factory/tools/smoke_test.py --system-dir systems/{system_name}`
2. For each tool in `tools/`:
   - **Check for `# SMOKE_TEST: {"key": "value"}` comment** — if present, use it as sample input
   - **Skip tools requiring external API keys** — detected by scanning for `os.environ[...]` patterns referencing API_KEY, SECRET, TOKEN, etc., or imports of known API client libraries (openai, anthropic, boto3, etc.)
   - **Attempt import** — verify the module loads without errors
   - **Run `main()` with sample input** — inject smoke test data as CLI args, enforce 30-second timeout
   - **Record result**: passed, failed, or skipped (with reason)
3. Log the full smoke test report: total tools, passed, failed, skipped
4. **If any tool fails**: Log the failure details but do NOT halt the build — smoke test failures are warnings, not blockers (tools may need live APIs or data that isn't available during build)

**Gate**: Smoke test results are informational. They are included in the job summary but do not block packaging.

**Sample input convention**: Add this comment to any tool file to enable smoke testing:
```python
# SMOKE_TEST: {"input": "sample_value", "format": "json"}
```

**Failure mode**: If the smoke test infrastructure itself fails (e.g., import error in smoke_test.py), skip smoke tests entirely and proceed to packaging. Log the error for debugging.

---

## Step 8b: Version Existing System

Before overwriting an existing system, archive the current version.

1. Check if `systems/{system_name}/` already exists
2. **If it exists**: Run `factory/tools/version_system.py --system-name {system_name} --job-id {job_id} --confidence {confidence}`
   - This copies all current files (excluding `versions/`) into `systems/{system_name}/versions/vN/`
   - Writes `metadata.json` with version number, date, job ID, and confidence score
   - The version number is auto-incremented from existing versions
3. **If it does not exist**: Skip — this is a first build, no versioning needed
4. Log the versioning result (version number or "skipped")

**Failure mode**: If versioning fails, log the error but do NOT halt the build. The new system should still be generated — losing the old version is preferable to blocking the build entirely.

---

## Step 9: Package

Bundle everything into a deployable system.

1. Run `factory/tools/package_system.py`
2. Create the output directory: `systems/{system_name}/`
3. Place all files:
   - `CLAUDE.md` (from Step 7)
   - `workflow.md` (from Step 4)
   - `tools/` (from Step 5)
   - `.claude/agents/` (from Step 5b)
   - `.github/workflows/` (from Step 6)
   - `requirements.txt` (from Step 5)
4. Generate `README.md` with:
   - System overview
   - Setup instructions for ALL THREE execution paths:
     - **(a) Claude Code CLI**: Clone repo, set env vars, run `claude` with workflow.md
     - **(b) GitHub Actions dispatch**: Push to GitHub, configure secrets, trigger via Actions UI or API
     - **(c) GitHub Agent HQ**: Assign issue to @claude with task description in issue body
   - Required secrets list
   - Example usage for each path
5. Verify the package is complete: all required files present, no hardcoded secrets

**Failure mode**: If any files are missing, log what's missing and package what exists with a TODO list in README.md.

---

## Step 10: Learn

Extract learnings and update the factory's knowledge base.

1. Review the system that was just built — what patterns were used?
2. **Update `library/patterns.md`**:
   - If a new pattern was discovered, add it with a description and example
   - If an existing pattern was refined, update its entry
3. **Update `library/tool_catalog.md`**:
   - If new tool patterns were created, catalog them for reuse
   - If existing tool patterns were improved, update their entries
4. **If this was an n8n conversion**:
   - Save the n8n-to-WAT mapping in `converters/n8n_examples/` for future reference
5. Log what worked well and what was difficult — this informs future improvements
6. Commit all library updates

**Failure mode**: If learning extraction fails, the system build is still valid — learning is a bonus, not a requirement.
