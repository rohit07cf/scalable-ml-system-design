# Design an LLM Gateway with Routing

Design a gateway service that routes LLM requests to the best backend model based on cost, latency, capability, and availability.


## Key Requirements

- Route requests across multiple LLM providers (OpenAI, Anthropic, self-hosted)
- Support fallback chains when a provider is degraded or rate-limited
- Enforce org-wide policies: token budgets, content filtering, audit logging


## Core Components

- Ingress API: unified request format that abstracts provider differences
- Router: selects backend based on routing rules (cost tier, task type, latency SLA)
- Provider adapters: translate unified format to provider-specific APIs
- Circuit breaker and retry manager: handles provider failures and rate limits
- Usage tracker: records tokens, cost, and latency per team, per provider


## Key Trade-offs

- Lowest cost routing vs latency-sensitive routing for real-time use cases
- Single gateway (simplicity) vs regional gateways (lower latency, data residency)
- Transparent fallback vs explicit error to caller when primary provider fails


## Must Explain in Interview

- How the router decides between providers (rule-based vs score-based vs hybrid)
- Why circuit breakers need per-provider, per-model granularity
- How you handle streaming responses through the gateway without buffering
- What metadata the gateway attaches for downstream observability
- How you prevent a single team from exhausting shared rate limits
