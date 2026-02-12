# Design: Single-Org Enterprise Agent Runtime Platform

> Supervisor -> Child Agents | Multi-step | Streaming | Structured Outputs

## What This Is

Interview-ready system design for an internal (single-tenant) platform that lets
enterprise teams run **config-driven agent chains** with hierarchical supervision,
durable execution, and typed outputs.

## Tech Stack

| Layer | Choice |
|---|---|
| Control Plane | Python / FastAPI |
| Validation | Pydantic (strict mode) |
| Orchestration | Temporal (workflows + activities) |
| Runtime | Kubernetes (service + worker pools) |
| State Store | PostgreSQL (runs/steps/audit) + Redis (hot state/streaming) |

## 7-Phase Design Pack

| # | File | Focus |
|---|---|---|
| 1 | [01_requirements.md](01_requirements.md) | Functional + non-functional requirements |
| 2 | [02_estimation.md](02_estimation.md) | Back-of-envelope math |
| 3 | [03_api_design.md](03_api_design.md) | REST API + Pydantic models |
| 4 | [04_hld.md](04_hld.md) | Architecture + data flow + ASCII diagrams |
| 5 | [05_db_design.md](05_db_design.md) | Schema + indexing + retention |
| 6 | [06_deep_dives.md](06_deep_dives.md) | Routing, streaming, reliability, structured outputs |
| 7 | [07_wrap_up.md](07_wrap_up.md) | Bottlenecks, scaling, trade-offs, failure modes |

## Key Concepts (OpenAI Agents SDK Framing)

- **Tool Call**: Agent invokes an external function, gets result back, continues reasoning
- **Handoff**: Agent transfers full control to another agent (new context, new instructions)
- **Supervisor**: Top-level agent that triages and routes via handoffs
- **Hooks**: `AgentHooks` + `ToolHooks` fire lifecycle events for streaming/observability
- **Structured Output**: Pydantic model enforced on final agent output + tool results
