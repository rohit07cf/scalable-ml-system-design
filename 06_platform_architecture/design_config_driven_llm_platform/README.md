# Design a Config-Driven LLM Platform

Design a platform where product teams configure LLM behavior through declarative configs rather than writing custom inference code.


## Key Requirements

- Teams onboard new LLM use cases without deploying custom services
- Config changes (model, prompt template, guardrails) roll out without code deploys
- Platform enforces cost limits, rate limits, and safety policies centrally


## Core Components

- Config store: versioned YAML/JSON defining model, prompt, guardrails per use case
- Request router: reads config at runtime, selects model and prompt template
- Prompt assembler: injects context, few-shot examples, and system instructions from config
- Guardrail executor: runs pre/post-processing checks defined in the config
- Observability layer: logs token usage, latency, and policy violations per config version


## Key Trade-offs

- Flexibility of configs vs complexity of the config schema and validation
- Centralized platform control vs team autonomy over model behavior
- Hot-reloading configs vs cache consistency across distributed nodes


## Must Explain in Interview

- How config versioning enables safe rollback without redeployment
- Why you need a schema validation step before configs reach production
- How the platform enforces per-team cost budgets and rate limits
- What happens when a config references a model the platform does not support
- How you test prompt template changes before they go live (shadow mode, A/B)
