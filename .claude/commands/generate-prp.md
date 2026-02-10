# Generate PRP — Product Requirements Prompt

Generate a comprehensive PRP from a problem description or INITIAL.md file. The PRP gives the factory enough structured context to build a complete WAT system in one pass.

## Input: $ARGUMENTS

## Process

### 1. Read and Understand the Input

- Read the input file (INITIAL.md or raw problem description)
- Extract: the problem being solved, what goes in, what comes out, how often it runs, where results go
- If the input is sparse or ambiguous, ask the user 2-3 targeted clarifying questions before proceeding. Do not guess — ask.

### 2. Research the Factory's Knowledge Base

Before writing the PRP, gather all relevant context from the factory:

**Pattern matching:**
- Read `library/patterns.md` — which workflow pattern best fits this problem?
- If multiple patterns could work, note the top 2-3 candidates with rationale

**Tool discovery:**
- Read `library/tool_catalog.md` — which reusable tool patterns apply?
- For each capability the system needs, check if a catalog pattern exists

**MCP assessment:**
- Read `config/mcp_registry.md` — which MCPs provide the needed capabilities?
- For each MCP, note the alternative and fallback approaches
- Identify required secrets (API keys, tokens)

**Existing systems:**
- Scan `systems/` — has a similar system been built before?
- If yes, reference it as a pattern to follow or improve upon

**Codebase conventions:**
- Read `factory/templates/` to understand the expected output format
- Read `factory/templates/subagent_template.md` for subagent file structure
- Read `factory/templates/prompts/` for persona templates

### 3. External Research (if needed)

- If the system needs external APIs, search for their documentation
- If the system needs specific libraries, search for usage patterns and gotchas
- Include specific URLs in the PRP's Documentation & References section
- Note rate limits, authentication requirements, and known quirks

### 4. Design the System Architecture

Based on research findings, design:

**Workflow steps:**
- Break the problem into discrete, ordered steps
- Each step does one thing clearly
- Define inputs, outputs, failure modes, and fallbacks for each step

**Subagent architecture:**
- Identify specialist subagents — one per major capability or workflow phase
- Follow naming convention: `{function}-specialist`, `{function}-agent`, `{function}-reviewer`
- Define tools, model, and permissions for each subagent
- Write clear descriptions (Claude uses these for automatic delegation routing)

**Agent Teams analysis:**
- Count independent tasks (no data dependencies between them)
- Apply the 3+ Independent Tasks Rule:
  - 3+ independent tasks → Recommend Agent Teams, define team lead and teammates
  - Fewer than 3 → Recommend sequential, document why
- Assess whether parallelization meaningfully reduces total execution time

**Tool specifications:**
- For each tool, define: purpose, inputs, outputs, dependencies, MCP usage, error handling
- Reference catalog patterns where they exist
- Write pseudocode for the core logic

### 5. Score Confidence

Rate the PRP on a 1-10 scale for one-pass build success:

**Scoring criteria:**
- **10**: Every requirement is specific, all APIs are documented, all patterns exist in the catalog, no ambiguity
- **8-9**: Requirements are clear, most patterns exist, minor unknowns that can be resolved during build
- **6-7**: Some requirements are vague, may need iteration, but core architecture is sound
- **4-5**: Significant ambiguity — multiple interpretation are possible, key APIs undocumented
- **1-3**: Requirements too vague to build — clarification required before proceeding

**Flag ambiguities:**
- For each area scoring below 7, create an explicit ambiguity flag explaining what needs clarification
- If ANY ambiguity flag exists, note that the user should resolve it before running `/execute-prp`

### 6. Generate the PRP

Using `PRPs/templates/prp_base.md` as the template, fill in every section:

- **Goal, Why, What**: From the user's problem description, expanded with research context
- **Inputs/Outputs**: Specific formats, sources, destinations with examples
- **Documentation & References**: All URLs, file paths, and docs discovered during research
- **Workflow Pattern Selection**: Best-fit pattern with rationale
- **MCP & Tool Requirements**: Full capability mapping with primary, alternative, and fallback
- **Known Gotchas**: Rate limits, auth quirks, format issues, library constraints
- **Subagent Architecture**: Complete subagent definitions with system prompt summaries
- **Agent Teams Analysis**: Decision and rationale with team structure if recommended
- **Implementation Blueprint**: Ordered workflow steps, tool specs, pseudocode, integration points
- **Validation Loop**: Concrete, executable commands for all three levels
- **Anti-Patterns**: System-specific anti-patterns in addition to the standard list
- **Confidence Score**: Numeric score with per-area rationale and ambiguity flags

**Think carefully about the PRP before writing it. The goal is one-pass build success.**

### 7. Save and Report

Save the PRP to: `PRPs/{system-name}.md`

The system name is derived from the problem description — lowercase, hyphens, descriptive (e.g., `competitor-monitor`, `lead-gen-machine`, `content-pipeline`).

Report to the user:
- PRP saved to `PRPs/{system-name}.md`
- Confidence score and any ambiguity flags
- Recommended next steps:
  - If score >= 7 and no ambiguity flags: "Review the PRP, then run `/execute-prp PRPs/{system-name}.md` to build."
  - If score < 7 or ambiguity flags exist: "Resolve the flagged ambiguities in the PRP, then run `/execute-prp PRPs/{system-name}.md` to build."

---

## Quality Checklist

Before saving, verify:
- [ ] Every PRP section is filled in (no empty placeholders)
- [ ] Validation gates are executable (real commands, not pseudocode)
- [ ] Subagent definitions follow CLAUDE.md naming and format rules
- [ ] MCP requirements reference the actual MCP registry
- [ ] Tool specifications include error handling and fallback approaches
- [ ] Anti-patterns section includes system-specific risks
- [ ] Confidence score has per-area rationale, not just a number
- [ ] Ambiguity flags are actionable (state what needs to be clarified and why)

The goal is one-pass build success through comprehensive context.
