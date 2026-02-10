# Execute PRP — Build a WAT System

Build a complete WAT system from a PRP (Product Requirements Prompt) file.

## PRP File: $ARGUMENTS

## Execution Process

### 1. Load and Validate PRP

- Read the specified PRP file in full
- Check the **Confidence Score** — if below 7/10, STOP and report which areas need clarification
- Check **Ambiguity Flags** — if any are checked, STOP and ask the user to resolve them before building
- Understand all context: inputs, outputs, subagent design, MCP requirements, workflow pattern, tool specs
- Read all referenced documentation and files listed in the PRP's "Documentation & References" section
- If any referenced file does not exist, note it and proceed with available context

### 2. Plan the Build

Think carefully before executing. This is a full system build — plan it thoroughly.

- Read `factory/workflow.md` to understand the factory's build process
- Map PRP sections to factory workflow steps:
  - PRP Goal/What/Inputs/Outputs → Step 1 (Intake)
  - PRP Documentation & References → Step 2 (Research)
  - PRP System Design → Step 3 (Design)
  - PRP Implementation Blueprint → Steps 4-7 (Generate)
  - PRP Validation Loop → Step 8 (Test)
- Read `config/mcp_registry.md` to verify MCP availability for listed capabilities
- Read `library/patterns.md` to confirm the selected workflow pattern exists
- Read `library/tool_catalog.md` to identify reusable tool patterns
- Create a task list tracking each major generation step

### 3. Execute factory/workflow.md

Follow the factory workflow using the PRP as structured input:

**Step 1 (Intake)**: Use the PRP's Goal, Inputs, and Outputs sections as the problem description. The system name comes from the PRP filename.

**Step 2 (Research)**: Cross-reference the PRP's MCP & Tool Requirements against the actual MCP registry and tool catalog. Note any mismatches.

**Step 3 (Design)**: Use the PRP's System Design section (subagents, Agent Teams analysis, triggers) as the design. Validate that subagent definitions follow CLAUDE.md rules.

**Step 3b (Parallel Build)**: If the PRP recommends Agent Teams AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is set, use parallel generation. Otherwise, proceed sequentially through Steps 4-7.

**Steps 4-7 (Generate)**: Generate workflow.md, tools, subagents, GitHub Actions, and CLAUDE.md using the PRP's Implementation Blueprint as the specification.

**Step 8 (Test)**: Run the PRP's Validation Loop — all three levels, in order. Each level must pass before proceeding to the next:
  - Level 1: Syntax & Structure
  - Level 2: Unit Tests
  - Level 3: Integration Tests

**Step 9 (Package)**: Bundle into `systems/{system-name}/`. Verify all required files are present.

**Step 10 (Learn)**: Extract patterns and update the library.

### 4. Validate Against PRP

After the build completes:

- Re-read the PRP file
- Walk through every **Success Criteria** checkbox — verify each one is met
- Walk through the **Final Validation Checklist** — verify each item
- Walk through the **Anti-Patterns to Avoid** — verify none were violated
- If any criteria are not met, fix the issue and re-validate

### 5. Report Completion

Summarize:
- System location: `systems/{system-name}/`
- Files generated (list each)
- Validation results (pass/fail for each level)
- Any items that need manual attention
- Instructions for the user's next steps (configure secrets, test locally, push to GitHub)

### 6. Reference the PRP

The PRP remains the source of truth throughout the build. If any step is unclear, re-read the relevant PRP section. Do not deviate from the PRP's specifications without documenting why.

---

**Note**: If validation fails at any level, use the error output to fix the issue and re-run that level. Do not proceed to the next level until the current one passes. Do not skip validation. Do not mock to make tests pass — fix the actual code.
