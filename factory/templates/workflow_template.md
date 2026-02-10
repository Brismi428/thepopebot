# {System Name} — Workflow

{Brief description of what this system does and why it exists.}

## Inputs

- **{input_name}**: {Type} — {Description of the input and expected format}

## Outputs

- **{output_name}**: {Type} — {Description of the output and where it goes}

---

## Step 1: {Step Name}

{Description of what this step does.}

1. {Sub-step 1}
2. {Sub-step 2}
3. {Sub-step 3}

**Decision point**: **If {condition}**:
- **Yes**: {What to do}
- **No**: {What to do instead}

**Failure mode**: {What can go wrong and what's the fallback}

---

## Step 2: {Step Name}

{Continue with additional steps following the same structure.}

1. {Sub-step 1}
2. {Sub-step 2}

**Tool**: `tools/{tool_name}.py` — {Brief description of what the tool does}

**Failure mode**: {What can go wrong and what's the fallback}

---

## Step N: Deliver Results

{Final step — how results are delivered.}

1. {Format output as specified}
2. {Commit results to repo / send notification / write file}
3. {Log completion}

**Failure mode**: If delivery fails, save results locally and retry on next run.

---

## Notes

- {Any additional context, caveats, or configuration notes}
- {MCP dependencies and alternatives}
- {Token cost considerations if Agent Teams is used}
