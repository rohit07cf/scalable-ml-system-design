# Tool Usage

## What It Is

- **Tools** are external capabilities an agent can invoke to interact with the real world
- Without tools, an LLM can only generate text — tools let it **do things**
- Tool use = function calling: the LLM outputs a structured call, the system executes it
- The tool ecosystem is the agent's "hands and eyes"

## Why It Matters (Interview Framing)

> "Tool use is what converts an LLM from a text generator into an agent. Interview questions will probe whether you understand tool design, safety, error handling, and the MCP protocol."

---

## Simple Mental Model

> **LLM = Brain. Tools = Hands.**
> The brain decides what to do. The hands execute it. The brain reads the result. Repeat.

---

## Categories of Tools

| Category | Examples | Use Case |
|---|---|---|
| **API Calls** | REST, GraphQL, gRPC | Fetch/push data to external services |
| **Code Execution** | Python sandbox, Node.js | Calculations, data transforms, file ops |
| **Database** | SQL queries, NoSQL ops | CRUD operations, analytics queries |
| **Browser Actions** | Navigate, click, scrape | Web research, form filling, testing |
| **Vector DB Retrieval** | Pinecone, Weaviate, Chroma | RAG — fetch relevant context |
| **File Operations** | Read, write, parse | Document processing, config management |
| **Communication** | Email, Slack, webhooks | Notifications, human escalation |

---

## How Tool Calling Works

```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│  Agent   │────▶│  LLM decides │────▶│ Tool Exec│
│ (prompt  │     │  which tool  │     │  Runtime  │
│  + tools │     │  + arguments │     │          │
│  schema) │     └──────────────┘     └────┬─────┘
│          │                               │
│          │◀──────── Result ──────────────┘
└─────────┘
```

**Step by step:**

1. Agent sends prompt + **tool schemas** (JSON) to the LLM
2. LLM outputs a **tool call** (function name + arguments)
3. Runtime executes the tool, captures the result
4. Result is appended to context, LLM reasons on next step

---

## Tool Schema Example

```json
{
  "name": "search_orders",
  "description": "Search customer orders by order ID or customer email",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "The order ID (e.g., ORD-12345)"
      },
      "customer_email": {
        "type": "string",
        "description": "Customer email address"
      }
    },
    "required": []
  }
}
```

💡 **Good tool descriptions = better tool selection by the LLM.** This is prompt engineering for tools.

---

## Model Context Protocol (MCP)

```
┌──────────┐    MCP     ┌──────────────┐
│  Agent   │◀─────────▶│  MCP Server   │
│ (Client) │  (JSON-RPC)│  (Tool Host)  │
└──────────┘            └──────┬───────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
               ┌────▼──┐ ┌────▼──┐ ┌────▼──┐
               │Tool A │ │Tool B │ │Tool C │
               └───────┘ └───────┘ └───────┘
```

- **MCP** = standardized protocol for agent-tool communication
- Like USB for AI tools — any MCP client works with any MCP server
- Replaces bespoke tool integrations with a universal interface
- Supports: tool discovery, execution, streaming, authentication

---

## Tool Design Best Practices

| Practice | Why |
|---|---|
| **Descriptive names** | `search_customer_orders` > `query_db` |
| **Clear descriptions** | LLM uses description to decide when to call |
| **Typed parameters** | Prevents malformed calls |
| **Error messages** | Return actionable errors, not stack traces |
| **Idempotent when possible** | Safe to retry on failure |
| **Scoped permissions** | Tool should only access what it needs |
| **Timeout limits** | Prevent hanging on slow external services |
| **Rate limiting** | Prevent cost explosions from rapid tool calls |

---

## Practical Example: Research Agent Tools

```python
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information",
        "params": {"query": "string"}
    },
    {
        "name": "read_url",
        "description": "Fetch and read content from a URL",
        "params": {"url": "string"}
    },
    {
        "name": "run_python",
        "description": "Execute Python code for analysis",
        "params": {"code": "string"}
    },
    {
        "name": "save_report",
        "description": "Save final report to storage",
        "params": {"title": "string", "content": "string"}
    }
]

# Agent flow:
# 1. web_search("competitor analysis Acme Corp")
# 2. read_url("https://...")  for each result
# 3. run_python("import pandas as pd; ...")  to analyze
# 4. save_report("Competitor Analysis", report_md)
```

---

## Interview Questions They Will Ask

1. **"How does an LLM know which tool to call?"**
   → It receives tool schemas (name, description, params) in the prompt. It outputs a structured tool call based on the task. Good descriptions are critical.

2. **"What is MCP and why does it matter?"**
   → Model Context Protocol — a universal standard for agent-tool communication. Like USB for tools. Avoids vendor lock-in and bespoke integrations.

3. **"How do you handle tool errors?"**
   → Return structured error messages. Let the agent reason about the error and retry or try an alternative tool. Set max retries.

4. **"What are the security risks of tool use?"**
   → Prompt injection causing unintended tool calls, SQL injection via text-to-SQL, unauthorized data access, cost explosion from unbounded tool calls.

5. **"How do you decide which tools to give an agent?"**
   → Principle of least privilege. Only the tools needed for the task. More tools = more confusion for the LLM + larger attack surface.

---

## Common Mistakes

⚠️ **Too many tools** — 50+ tools confuse the LLM. Group into categories or use hierarchical tool selection.

⚠️ **Vague tool descriptions** — "query_data" tells the LLM nothing. Be specific about WHAT data and WHEN to use it.

⚠️ **No error handling** — Tools will fail. The agent must gracefully handle timeouts, rate limits, auth failures.

⚠️ **Unbounded tool calls** — An agent in a loop can call an expensive API 1000 times. Always cap tool call count and cost.

⚠️ **Trusting LLM-generated SQL/code** — Always sandbox code execution. Validate and parameterize SQL queries.

---

## TL;DR

- Tools = external capabilities (APIs, code exec, DB, browser, vector DB)
- LLM selects tools via **schemas** (name + description + params)
- **MCP** is the emerging universal standard for tool integration
- Design tools with **clear names, scoped permissions, error handling, rate limits**
- Biggest risks: **injection attacks, cost explosion, too many tools confusing the LLM**
