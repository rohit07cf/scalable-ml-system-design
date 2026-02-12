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

---

## Reference Implementation: `agent_tree/`

A minimal, runnable hierarchical agent tree with structured handoffs.

### Architecture

```
              ┌─────────────┐
              │  Supervisor  │  (root of AgentTree)
              │  Orchestrator│
              └──────┬───────┘
                     │  HandoffResult (Pydantic-validated)
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │ Triage  │ │ Specialist│ │ Verifier │
   │ Agent   │ │ Agent     │ │ Agent    │
   └─────────┘ └──────────┘ └──────────┘
        │            │            │
        └────────────┴────────────┘
           All return HandoffResult
           back to Supervisor
```

### Files

| File | Purpose |
|---|---|
| `agent_tree/__init__.py` | Public API exports |
| `agent_tree/agent_node.py` | `AgentNode` — single node with children, tools, parent ref |
| `agent_tree/agent_tree.py` | `AgentTree` — root wrapper with `visualize()` and `find()` |
| `agent_tree/handoff_models.py` | `HandoffResult` + `SupervisorResult` Pydantic models |
| `agent_tree/orchestrator.py` | `SupervisorOrchestrator` — async loop with hooks |
| `agent_tree/demo.py` | End-to-end runnable demo |

### Quick Start

```bash
pip install pydantic
cd design_agentic_ai_platform/
python agent_tree/demo.py
```

### How to Build a Tree

```python
from agent_tree import AgentNode, AgentTree

# 1. Create nodes
supervisor = AgentNode("supervisor")
triage     = AgentNode("triage", tools=["classify"])
specialist = AgentNode("invoice-specialist", tools=["erp_lookup"])
verifier   = AgentNode("verifier", tools=["policy_check"])

# 2. Wire the hierarchy
supervisor.add_child(triage)
supervisor.add_child(specialist)
supervisor.add_child(verifier)

# 3. Wrap in a tree and inspect
tree = AgentTree(supervisor)
print(tree.visualize())
# supervisor (root)
# ├── triage [tools: classify]
# ├── invoice-specialist [tools: erp_lookup]
# └── verifier [tools: policy_check]
```

### How Handoffs Work

Every child agent returns a **`HandoffResult`** — a Pydantic model that the
Supervisor validates and uses to decide what to do next.

```python
from agent_tree import HandoffResult

result = HandoffResult(
    from_agent="invoice-specialist",
    to_agent="supervisor",
    status="ok",                # "ok" | "needs_more_info" | "failed"
    summary="Invoice #4821 rejected due to missing PO.",
    payload={"invoice_id": "4821", "reason": "missing_po"},
    artifacts=["erp://invoices/4821"],
)
```

**Supervisor loop**: route to child → receive `HandoffResult` → if `ok`, done; if `needs_more_info` or `failed`, try next child.

### Running the Orchestrator

```python
from agent_tree import AgentTree, SupervisorOrchestrator, OrchestratorHooks

orchestrator = SupervisorOrchestrator(
    tree=tree,
    hooks=OrchestratorHooks(
        on_node_start=my_start_hook,   # async (node, input) -> None
        on_node_end=my_end_hook,       # async (node, result) -> None
        on_handoff=my_handoff_hook,    # async (result) -> None
    ),
    max_steps=10,
)
result = await orchestrator.run("Why was invoice #4821 rejected?")
print(result.answer)   # "Invoice #4821 rejected due to missing PO number."
print(result.status)   # "completed"
```
