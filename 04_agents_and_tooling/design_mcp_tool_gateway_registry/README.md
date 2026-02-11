# Design: MCP Tool Gateway and Registry

Design a centralized gateway and registry that lets LLM agents discover, authenticate against, and invoke external tools using a standardized protocol (e.g., Model Context Protocol).


## Key Requirements

- Agents discover available tools dynamically via a searchable registry with schema introspection
- All tool calls go through the gateway for auth, rate limiting, logging, and schema validation
- Support heterogeneous tool backends (REST APIs, databases, code interpreters, file systems)


## Core Components

- **Tool Registry** -- catalog of tools with name, description, input/output JSON schemas, and capability tags
- **Gateway Router** -- receives tool call requests, resolves the target backend, applies middleware, and forwards
- **Auth and Policy Layer** -- per-agent and per-tool permissions, scoped credentials, and secret injection
- **Schema Validator** -- validates agent-generated tool call arguments against registered schemas before execution
- **Execution Sandbox** -- isolated runtime for tools that execute code or access sensitive resources


## Key Trade-offs

- Centralized gateway (uniform policy, single point of failure) vs. sidecar/embedded tools (lower latency, scattered policy)
- Strict schema validation (fewer runtime errors) vs. lenient pass-through (faster iteration, more failures downstream)
- Static tool registration (predictable) vs. dynamic discovery (flexible, harder to audit and secure)


## Must Explain in Interview

- How agents select the right tool when multiple tools have overlapping capabilities
- How you prevent prompt injection from leaking through tool descriptions or tool outputs back to the LLM
- How rate limiting and cost budgets are enforced per-agent and per-tool at the gateway
- How you version tool schemas without breaking agents that depend on older versions
- How the sandbox isolates code-execution tools and caps resource usage (CPU, memory, network)
