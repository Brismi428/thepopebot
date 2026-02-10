# n8n Workflow OS - Skills

This directory contains **7 extended skills** that complement the base skills from [n8n-skills](https://github.com/czlonkowski/n8n-skills).

## Skill Overview

### Base Skills (from n8n-skills)
Install these first: `/plugin install czlonkowski/n8n-skills`

| Skill | Focus |
|-------|-------|
| n8n-expression-syntax | `{{}}` patterns, variables |
| n8n-mcp-tools | MCP tool usage |
| n8n-workflow-patterns | 5 proven architectures |
| n8n-validation | Error interpretation |
| n8n-node-config | Property dependencies |
| n8n-code-javascript | JS in Code nodes |
| n8n-code-python | Python limitations |

### Extended Skills (this directory)

| Skill | Focus | Activates When |
|-------|-------|----------------|
| **n8n-ai-workflows** | AI/LangChain patterns | Building AI agents, using LLMs |
| **n8n-error-recovery** | Runtime error handling | Workflow failures, retries |
| **n8n-data-transformation** | Data manipulation | Transforming, mapping data |
| **n8n-webhook-patterns** | Webhook security | Webhooks, external integrations |
| **n8n-integration-patterns** | Service connections | Connecting APIs, services |
| **n8n-performance** | Optimization | Slow workflows, scaling |
| **n8n-testing** | Test strategies | QA, validation |

## Installation

### For Claude Code
```bash
# Install base skills
/plugin install czlonkowski/n8n-skills

# Copy extended skills
cp -r skills/* ~/.claude/skills/
```

### For Claude.ai
1. Zip each skill folder
2. Upload via Settings → Capabilities → Skills

## Skill Structure

Each skill follows this structure:
```
skill-name/
├── SKILL.md          # Main skill content (< 500 lines)
├── examples/         # Example configurations
│   └── *.json
└── tests/           # Evaluation scenarios
    └── *.md
```

## Auto-Activation

Skills activate automatically based on context. No manual invocation needed.

Example triggers:
- "Build an AI agent workflow" → n8n-ai-workflows
- "Handle errors gracefully" → n8n-error-recovery
- "Transform this JSON" → n8n-data-transformation
- "Secure this webhook" → n8n-webhook-patterns
- "Connect to Salesforce" → n8n-integration-patterns
- "Make this faster" → n8n-performance
- "Test this workflow" → n8n-testing

## Skill Composition

Multiple skills can activate simultaneously:

```
"Build an AI agent that handles errors gracefully"
→ Activates: n8n-ai-workflows + n8n-error-recovery

"Create a fast webhook that transforms data"
→ Activates: n8n-webhook-patterns + n8n-data-transformation + n8n-performance
```
