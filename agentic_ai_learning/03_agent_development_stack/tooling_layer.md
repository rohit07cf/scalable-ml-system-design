# Tooling Layer

## What It Is

- The **integration layer** that connects agents to external systems, APIs, and compute
- Includes: REST/gRPC APIs, MCP servers, code interpreters, database connectors
- This is how agents **do things** beyond generating text
- The tooling layer must be secure, reliable, and observable

## Why It Matters (Interview Framing)

> "An agent without tools is just a chatbot. The tooling layer is the interface between AI reasoning and real-world action. Interviewers want to see that you can design tool integrations that are secure, reliable, and maintainable."

---

## Tooling Layer Architecture

```
┌─────────────────────────────────────────────┐
│              AGENT / LLM LAYER              │
├─────────────────────────────────────────────┤
│           TOOLING LAYER                     │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   REST   │  │   gRPC   │  │   MCP    │  │
│  │   APIs   │  │ Services │  │ Servers  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  │
│  │  Code    │  │    DB    │  │ Browser  │  │
│  │Interpret.│  │Connectors│  │ Actions  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  Auth │ Rate Limit │ Sandbox │ Logs  │   │
│  └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│         KNOWLEDGE / EXECUTION LAYER         │
└─────────────────────────────────────────────┘
```

---

## Tool Types in Detail

### REST APIs

| Aspect | Details |
|---|---|
| **Protocol** | HTTP/HTTPS, JSON payloads |
| **Use cases** | Third-party services, internal microservices, SaaS integrations |
| **Auth** | API keys, OAuth2, JWT |
| **Agent integration** | Tool schema maps to endpoint: name, description, params → HTTP method + path + body |

```python
# Tool definition for a REST API
{
    "name": "get_weather",
    "description": "Get current weather for a city",
    "endpoint": "GET /api/weather?city={city}",
    "parameters": {
        "city": {"type": "string", "required": True}
    }
}
```

### gRPC Services

| Aspect | Details |
|---|---|
| **Protocol** | HTTP/2, Protocol Buffers |
| **Use cases** | Internal microservices, high-throughput, low-latency |
| **Advantage over REST** | 2-10x faster, typed contracts, streaming support |
| **Agent integration** | Proto definitions map to tool schemas |

**When to use gRPC over REST:**
- Internal service-to-service communication
- High-frequency tool calls (>100/sec)
- Streaming results (e.g., real-time data feeds)

### Model Context Protocol (MCP)

```
┌──────────┐     JSON-RPC      ┌──────────────┐
│  Agent   │◀══════════════════▶│  MCP Server  │
│ (Client) │                    │              │
└──────────┘                    │  ┌────────┐  │
                                │  │Tool A  │  │
  Capabilities:                 │  │Tool B  │  │
  - List tools                  │  │Tool C  │  │
  - Call tool                   │  └────────┘  │
  - Get resources               │              │
  - Subscribe to updates        └──────────────┘
```

- **Universal tool protocol** — any MCP client works with any MCP server
- Supports: tool discovery, execution, resource access, prompts
- Transport: stdio, HTTP+SSE
- Growing ecosystem of pre-built MCP servers

💡 **MCP is becoming the standard for tool integration.** Know it for interviews.

### Code Interpreter

| Aspect | Details |
|---|---|
| **What** | Sandboxed runtime for executing agent-generated code |
| **Languages** | Python (most common), JavaScript, SQL |
| **Use cases** | Data analysis, calculations, file processing |
| **Security** | MUST be sandboxed (Docker, gVisor, Firecracker) |

⚠️ **Never execute LLM-generated code in an unsandboxed environment.** This is a critical security rule.

### Database Connectors

| DB Type | Tool Pattern | Security |
|---|---|---|
| **SQL** (PostgreSQL, MySQL) | Text-to-SQL → execute → return results | Parameterized queries, read-only connections |
| **NoSQL** (MongoDB, DynamoDB) | Structured query generation | Scoped permissions per collection |
| **Vector DB** (Pinecone, Weaviate) | Semantic search tool | Read-only for most agents |
| **Graph DB** (Neo4j) | Cypher query generation | Read-only, query timeout limits |

---

## Tool Registration Pattern

```python
class ToolRegistry:
    """Central registry for agent tools"""

    def __init__(self):
        self.tools = {}

    def register(self, name, fn, description, params, permissions):
        self.tools[name] = {
            "function": fn,
            "schema": {
                "name": name,
                "description": description,
                "parameters": params
            },
            "permissions": permissions,     # Who can call this
            "rate_limit": "10/min",         # Max call frequency
            "timeout": 30,                  # Seconds
            "sandbox": True                 # Run in sandbox?
        }

    def execute(self, tool_name, args, caller):
        tool = self.tools[tool_name]
        self._check_permissions(tool, caller)
        self._check_rate_limit(tool, caller)
        return self._execute_with_timeout(tool, args)
```

---

## Practical Example: Enterprise Tool Stack

```
Agent: "Analyze Q4 sales and email the report to the VP"

Tools used:
  1. sql_query      → SELECT revenue, region FROM sales WHERE quarter='Q4'
  2. run_python     → pandas analysis, matplotlib chart generation
  3. save_file      → Save chart as PNG to workspace
  4. generate_pdf   → Compile analysis + chart into PDF report
  5. send_email     → Email PDF to vp@company.com

Tool chain: sql_query → run_python → save_file → generate_pdf → send_email
```

---

## Interview Questions They Will Ask

1. **"How do you design tool integration for an agent?"**
   → Define clear schemas (name, description, typed params). Register in a tool registry. Add auth, rate limits, timeouts, sandboxing. Use MCP for standardization.

2. **"REST vs gRPC for agent tools?"**
   → REST for external/third-party APIs (universal, simple). gRPC for internal high-throughput services (faster, typed, streaming).

3. **"What is MCP and why should I care?"**
   → Model Context Protocol — universal standard for agent-tool communication. Like USB for AI tools. Reduces bespoke integration work. Growing ecosystem.

4. **"How do you secure tool execution?"**
   → Sandbox code execution, parameterize SQL, scope permissions (least privilege), rate limit tool calls, validate inputs, audit log every call.

5. **"How do you handle tool failures?"**
   → Return structured errors to the agent. Agent reasons about the error and can: retry, try alternative tool, or escalate. Set max retries. Use circuit breakers for flaky external services.

---

## Common Mistakes

⚠️ **No sandboxing for code execution** — LLM-generated code can do anything. Sandbox it. Always.

⚠️ **Trusting LLM-generated SQL** — Use parameterized queries. Never pass raw LLM output to a SQL engine.

⚠️ **No rate limits on tool calls** — A looping agent can call an expensive API thousands of times. Always cap.

⚠️ **Building custom integrations when MCP exists** — Check if an MCP server already exists for your tool before writing custom code.

⚠️ **No timeout on tool execution** — External APIs can hang. Set timeouts on every tool call.

---

## TL;DR

- Tooling layer = **REST, gRPC, MCP, code interpreter, DB connectors**
- **MCP** is the emerging universal standard — learn it
- Every tool needs: **auth, rate limits, timeouts, sandboxing, logging**
- Use **gRPC internally, REST externally**, MCP where supported
- Biggest risk: **unsandboxed code execution and SQL injection**
