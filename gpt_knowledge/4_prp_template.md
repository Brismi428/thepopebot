name: "{System Name}"
description: |

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint that gives the factory enough context to build a complete, working system in one pass.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
[What system needs to be built. Be specific about the end state: what it does, who uses it, and what success looks like when deployed.]

## Why
- [Business value and user impact]
- [What manual process this automates or what gap it fills]
- [Who benefits and how often they benefit]

## What
[User-visible behavior and technical requirements. Describe what the system does from the perspective of someone triggering it.]

### Success Criteria
- [ ] [Specific measurable outcome 1]
- [ ] [Specific measurable outcome 2]
- [ ] [Specific measurable outcome 3]
- [ ] System runs autonomously via GitHub Actions on schedule
- [ ] Results are committed back to repo or delivered via webhook/notification
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "{input_name}"
  type: "{string | JSON | file | URL | list}"
  source: "{manual input | API | file path | webhook payload}"
  required: true
  description: "{What this input is and what format it should be in}"
  example: "{A concrete example value}"
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "{output_name}"
  type: "{JSON | CSV | Markdown | file | webhook}"
  destination: "{repo commit | email | Slack | webhook URL | file path}"
  description: "{What this output contains}"
  example: "{A concrete example or link to sample}"
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "{Official API docs URL}"
  why: "{Specific sections/methods the tools will need}"

- url: "{Library documentation URL}"
  why: "{Specific patterns or gotchas to follow}"

- file: "{path/to/existing/pattern.py}"
  why: "{Pattern to follow, conventions to match}"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide the capabilities this system needs"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for this system"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns to adapt"
```

### Workflow Pattern Selection
```yaml
# Reference library/patterns.md — select the best-fit pattern
pattern: "{Pattern name from library/patterns.md, e.g., Scrape > Process > Output}"
rationale: "{Why this pattern fits the problem}"
modifications: "{Any adjustments needed to the standard pattern}"
```

### MCP & Tool Requirements
```yaml
# Reference config/mcp_registry.md — list capabilities needed
capabilities:
  - name: "{capability, e.g., web scraping}"
    primary_mcp: "{MCP name from registry, e.g., firecrawl}"
    alternative_mcp: "{Alternative MCP}"
    fallback: "{Direct API/HTTP approach if no MCP available}"
    secret_name: "{UPPERCASE_SECRET_NAME}"

  - name: "{capability 2}"
    primary_mcp: "{MCP name}"
    alternative_mcp: "{Alternative}"
    fallback: "{Fallback approach}"
    secret_name: "{SECRET_NAME}"
```

### Known Gotchas & Constraints
```
# CRITICAL: {API/service name} has rate limit of {N} requests per {period}
# CRITICAL: {Library} requires {specific setup or version}
# CRITICAL: {Data source} returns {unexpected format} — must handle {edge case}
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "{function}-specialist"
    description: "When Claude should delegate to this subagent — be specific"
    tools: "Read, Bash, Grep"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "{What this subagent does — step 1}"
      - "{What this subagent does — step 2}"
    inputs: "{What data it receives}"
    outputs: "{What data it produces}"

  - name: "{function}-specialist"
    description: "When Claude should delegate to this subagent"
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "{Responsibility 1}"
      - "{Responsibility 2}"
    inputs: "{Input data}"
    outputs: "{Output data}"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "{Task A — no dependency on other tasks}"
  - "{Task B — no dependency on other tasks}"
  - "{Task C — no dependency on other tasks}"

independent_task_count: "{N}"
recommendation: "{Use Agent Teams | Sequential execution}"
rationale: "{Why — e.g., '3 independent API calls each taking 10s = 30s sequential vs 10s parallel'}"

# If Agent Teams recommended:
team_lead_responsibilities:
  - "Create shared task list"
  - "Spawn teammates for independent tasks"
  - "Merge results and run quality control"

teammates:
  - name: "{Teammate 1}"
    task: "{Scoped task description}"
    inputs: "{What it receives}"
    outputs: "{What it produces}"

# If NOT recommended:
sequential_rationale: "{Why sequential is sufficient — e.g., 'all tasks depend on previous output'}"
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "{workflow_dispatch | schedule | repository_dispatch}"
    config: "{cron expression, input parameters, or event type}"
    description: "{When and why this trigger fires}"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "{Step 1 name}"
    description: "{What happens in this step}"
    subagent: "{Which subagent handles this, if any}"
    tools: ["{tool_1.py}", "{tool_2.py}"]
    inputs: "{What this step receives}"
    outputs: "{What this step produces}"
    failure_mode: "{What can go wrong}"
    fallback: "{What to do if it fails}"

  - name: "{Step 2 name}"
    description: "{Description}"
    subagent: "{subagent name}"
    tools: ["{tool_name.py}"]
    inputs: "{From previous step}"
    outputs: "{For next step}"
    failure_mode: "{Failure scenario}"
    fallback: "{Recovery action}"
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "{tool_name}.py"
    purpose: "{One-line description}"
    catalog_pattern: "{Pattern name from tool_catalog.md, or 'new' if custom}"
    inputs:
      - "{arg1}: {type} — {description}"
      - "{arg2}: {type} — {description}"
    outputs: "{JSON structure or file format}"
    dependencies: ["{pip package 1}", "{pip package 2}"]
    mcp_used: "{MCP name, or 'none'}"
    error_handling: "{How errors are handled}"

  - name: "{tool_name_2}.py"
    purpose: "{Description}"
    catalog_pattern: "{Pattern or 'new'}"
    inputs:
      - "{arg}: {type} — {description}"
    outputs: "{Output format}"
    dependencies: ["{package}"]
    mcp_used: "{MCP or 'none'}"
    error_handling: "{Error approach}"
```

### Per-Tool Pseudocode
```python
# {tool_name}.py
def main():
    # PATTERN: {Which catalog pattern this follows}
    # Step 1: Parse inputs
    args = parse_args()  # argparse or env vars

    # Step 2: {Core logic description}
    # GOTCHA: {Important caveat about this API/library}
    result = do_work(args.input)

    # Step 3: Output results
    # PATTERN: Structured JSON to stdout
    print(json.dumps(result))

# {tool_name_2}.py
def main():
    # PATTERN: {Catalog pattern}
    # CRITICAL: {Key constraint — rate limit, auth, format}
    pass
```

### Integration Points
```yaml
SECRETS:
  - name: "{SECRET_NAME}"
    purpose: "{What API/service this authenticates}"
    required: true

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "{VAR_NAME}={placeholder_value}  # {description}"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "{package}=={version}  # {why}"

GITHUB_ACTIONS:
  - trigger: "{workflow_dispatch | schedule | repository_dispatch}"
    config: "{Details}"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/{tool_name}.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.{tool_name}')"

# Structure check — verify main() exists
python -c "from tools.{tool_name} import main; assert callable(main)"

# Repeat for every tool file
# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test each tool independently with mock/sample data

python tools/{tool_name}.py --input "{sample_input}"
# Expected output: {expected JSON or result}

python tools/{tool_name_2}.py --input "{sample_input}"
# Expected output: {expected result}

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Step 1: Run first tool
python tools/{tool_1}.py --input "{sample}" > /tmp/step1_output.json

# Step 2: Feed output to next tool
python tools/{tool_2}.py --input /tmp/step1_output.json > /tmp/step2_output.json

# Step 3: Verify final output
python -c "
import json
result = json.load(open('/tmp/step2_output.json'))
assert '{expected_key}' in result, 'Missing expected key in output'
print('Integration test passed')
"

# Verify workflow.md references match actual tool files
# Verify CLAUDE.md documents all tools and subagents
# Verify .github/workflows/ YAML is valid
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables
- [ ] .gitignore excludes .env, __pycache__/, credentials
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only specific files
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — the overhead is not justified
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function

---

## Confidence Score: {N}/10

**Score rationale:**
- [{Area}]: {Why confident or uncertain} — Confidence: {high | medium | low}
- [{Area}]: {Rationale} — Confidence: {high | medium | low}
- [{Area}]: {Rationale} — Confidence: {high | medium | low}

**Ambiguity flags** (areas requiring clarification before building):
- [ ] {Ambiguous requirement 1 — what needs clarification and why}
- [ ] {Ambiguous requirement 2 — what needs clarification and why}

**If any ambiguity flag is checked, DO NOT proceed to build. Ask the user to clarify first.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/{system-name}.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
