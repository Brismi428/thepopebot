---
name: n8n-ai-workflows
description: "Expert knowledge for building AI and LangChain workflows in n8n. Activates when: building AI agents, using LLMs, configuring AI tools, chat interfaces, or RAG systems."
version: 1.0.0
---

# n8n AI Workflows Skill

## Overview

Build production-ready AI workflows using n8n's LangChain integration. This skill covers AI Agents, language models, tools, memory, and output parsers.

---

## AI Agent Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Trigger   │────▶│  AI Agent   │────▶│   Output    │
│ (Chat/HTTP) │     │             │     │   Parser    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │   LLM   │     │  Tools  │     │ Memory  │
    └─────────┘     └─────────┘     └─────────┘
```

---

## Core AI Nodes

### AI Agent (`@n8n/n8n-nodes-langchain.agent`)

The orchestrator that connects LLM, tools, and memory.

```json
{
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "agent": "conversationalAgent",
    "promptType": "define",
    "text": "You are a helpful assistant.",
    "options": {
      "returnIntermediateSteps": false,
      "maxIterations": 10
    }
  }
}
```

**Agent Types**:
| Type | Use Case |
|------|----------|
| `conversationalAgent` | Chat with memory |
| `openAiFunctionsAgent` | OpenAI function calling |
| `reactAgent` | Reasoning + Acting |
| `planAndExecuteAgent` | Complex multi-step tasks |

### Language Models

**OpenAI Chat** (`@n8n/n8n-nodes-langchain.lmChatOpenAi`):
```json
{
  "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
  "parameters": {
    "model": "gpt-4",
    "options": {
      "temperature": 0.7,
      "maxTokens": 1000
    }
  }
}
```

**Anthropic** (`@n8n/n8n-nodes-langchain.lmChatAnthropic`):
```json
{
  "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
  "parameters": {
    "model": "claude-3-opus-20240229",
    "options": {
      "temperature": 0.7,
      "maxTokensToSample": 1000
    }
  }
}
```

---

## Connection Types (CRITICAL)

AI nodes use **8 special connection types**:

| Connection Type | Purpose | Connects To |
|-----------------|---------|-------------|
| `ai_languageModel` | LLM connection | AI Agent |
| `ai_tool` | Tool connection | AI Agent |
| `ai_memory` | Memory connection | AI Agent |
| `ai_outputParser` | Parser connection | AI Agent |
| `ai_document` | Document input | Vector stores |
| `ai_embedding` | Embedding model | Vector stores |
| `ai_retriever` | Retriever connection | AI Agent as tool |
| `ai_vectorStore` | Vector store | Retriever |

### Connection Example

```json
{
  "connections": {
    "OpenAI Chat Model": {
      "ai_languageModel": [
        [{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]
      ]
    },
    "Calculator Tool": {
      "ai_tool": [
        [{"node": "AI Agent", "type": "ai_tool", "index": 0}]
      ]
    },
    "Window Buffer Memory": {
      "ai_memory": [
        [{"node": "AI Agent", "type": "ai_memory", "index": 0}]
      ]
    }
  }
}
```

---

## AI Tools

### Built-in Tools

| Tool | Type | Use Case |
|------|------|----------|
| Calculator | `@n8n/n8n-nodes-langchain.toolCalculator` | Math operations |
| Code | `@n8n/n8n-nodes-langchain.toolCode` | Execute code |
| HTTP Request | `@n8n/n8n-nodes-langchain.toolHttpRequest` | API calls |
| Wikipedia | `@n8n/n8n-nodes-langchain.toolWikipedia` | Wikipedia lookup |
| Wolfram Alpha | `@n8n/n8n-nodes-langchain.toolWolframAlpha` | Computational queries |
| SerpAPI | `@n8n/n8n-nodes-langchain.toolSerpApi` | Web search |

### Custom Tool (Workflow as Tool)

Make ANY n8n workflow available as an AI tool:

```json
{
  "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
  "parameters": {
    "name": "get_customer_data",
    "description": "Gets customer information from CRM. Input: customer email address.",
    "workflowId": "your-workflow-id"
  }
}
```

---

## Memory Types

### Window Buffer Memory
Remembers last N messages:
```json
{
  "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
  "parameters": {
    "sessionKey": "={{ $json.sessionId }}",
    "contextWindowLength": 10
  }
}
```

### Postgres Chat Memory
Persistent memory across sessions:
```json
{
  "type": "@n8n/n8n-nodes-langchain.memoryPostgresChat",
  "parameters": {
    "sessionId": "={{ $json.sessionId }}",
    "tableName": "chat_history"
  }
}
```

### Redis Chat Memory
Fast, scalable memory:
```json
{
  "type": "@n8n/n8n-nodes-langchain.memoryRedisChat",
  "parameters": {
    "sessionKey": "={{ $json.sessionId }}",
    "sessionTTL": 3600
  }
}
```

---

## RAG (Retrieval Augmented Generation)

### Architecture

```
Documents → Loader → Splitter → Embeddings → Vector Store
                                                   │
                                                   ▼
Query → Retriever → Context + Query → LLM → Response
```

### Vector Store Setup

```json
{
  "type": "@n8n/n8n-nodes-langchain.vectorStorePinecone",
  "parameters": {
    "pineconeIndex": "my-index",
    "options": {
      "namespace": "documents"
    }
  }
}
```

### Document Loading

```json
{
  "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader",
  "parameters": {
    "options": {
      "metadata": {
        "source": "={{ $json.filename }}"
      }
    }
  }
}
```

### Text Splitter

```json
{
  "type": "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter",
  "parameters": {
    "chunkSize": 1000,
    "chunkOverlap": 200
  }
}
```

---

## Common Patterns

### Pattern 1: Basic Chat Agent

```
Chat Trigger → AI Agent (with LLM + Memory) → Response
```

### Pattern 2: Agent with Tools

```
Trigger → AI Agent → Tools (Calculator, HTTP, Code) → Response
         ↑
         └── LLM + Memory
```

### Pattern 3: RAG Pipeline

```
Documents → Split → Embed → Store (Index Phase)

Query → Retrieve → Context → AI Agent → Response (Query Phase)
```

### Pattern 4: Multi-Agent

```
Orchestrator Agent
    ├── Research Agent (with search tools)
    ├── Analysis Agent (with code tools)
    └── Writer Agent (with output tools)
```

---

## Critical Gotchas

### 1. Streaming Mode Constraints
When `streaming: true`:
- ❌ Cannot use output parsers
- ❌ Cannot use intermediate steps
- ✅ Better user experience for chat

### 2. Session ID Required
For memory to work:
```javascript
// Always pass sessionId
const sessionId = $json.body.sessionId || $json.body.chatId || Date.now().toString();
```

### 3. Tool Descriptions Matter
LLM uses description to decide when to use tool:
```javascript
// ❌ Vague
"Gets data"

// ✅ Specific
"Searches the product catalog by name or SKU. Returns product details including price, stock, and description. Input: search query string."
```

### 4. Token Limits
Watch for context window limits:
```javascript
// Set maxTokens appropriately
"maxTokens": 1000  // Leave room for context

// Use summarization for long conversations
```

---

## Error Handling

### Common AI Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limit | Too many requests | Add retry with backoff |
| Context length | Input too long | Summarize or truncate |
| Invalid tool | Tool not found | Check tool connections |
| Memory error | Session not found | Ensure sessionId passed |

### Retry Pattern

```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 1000
}
```

---

## Best Practices

1. **Start Simple**: Basic agent → add tools → add memory
2. **Test Prompts**: Iterate on system prompts
3. **Monitor Costs**: Track token usage
4. **Use Caching**: Cache repeated queries
5. **Handle Failures**: AI can fail; always have fallback

---

## Quick Reference

### MCP Tool Calls

```javascript
// Search AI nodes
search_nodes({query: 'langchain agent', includeExamples: true})

// Get AI agent details
get_node({
  nodeType: '@n8n/n8n-nodes-langchain.agent',
  detail: 'full'
})

// Search AI templates
search_templates({
  searchMode: 'by_nodes',
  nodeTypes: ['@n8n/n8n-nodes-langchain.agent']
})
```
