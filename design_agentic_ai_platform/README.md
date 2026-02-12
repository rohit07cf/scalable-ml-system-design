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
                     │
            ┌────────┴────────┐
            ▼                 ▼
     Plan (optional)    Route + Execute
     (PlannerCallable)  (child agents)
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
            ┌─────────┐ ┌──────────┐ ┌──────────┐
            │ Triage  │ │ Specialist│ │ Verifier │
            │ Agent   │ │ Agent     │ │ Agent    │
            └────┬────┘ └────┬─────┘ └────┬─────┘
                 │           │            │
            Tool Calls  Tool Calls   Tool Calls
           (registered  (erp_lookup, (verify_answer)
            callables)   policy_search)
                 │           │            │
                 └───────────┴────────────┘
                    All return HandoffResult
                    (Pydantic-validated) back
                    to Supervisor
```

### Files

| File | Purpose |
|---|---|
| `agent_tree/__init__.py` | Public API exports |
| `agent_tree/agent_node.py` | `AgentNode` — children, tool registry, `as_tool()`, `run_tool()` |
| `agent_tree/agent_tree.py` | `AgentTree` — root wrapper with `visualize()` and `find()` |
| `agent_tree/handoff_models.py` | `HandoffResult` + `ToolResult` + `SupervisorResult` Pydantic models |
| `agent_tree/orchestrator.py` | `SupervisorOrchestrator` — plan-then-execute loop with 3-tier hooks |
| `agent_tree/demo.py` | End-to-end runnable demo (tools, planner, hooks) |

### Quick Start

```bash
pip install pydantic
cd design_agentic_ai_platform/
python agent_tree/demo.py
```

### How to Build a Tree

```python
from agent_tree import AgentNode, AgentTree

# 1. Create nodes + register tool callables (not just strings)
supervisor = AgentNode("supervisor")
triage     = AgentNode("triage")
specialist = AgentNode("invoice-specialist")

async def erp_lookup(invoice_id: str) -> dict:
    return {"status": "rejected", "reason": "missing_po"}

specialist.add_tool(erp_lookup)          # registers callable + name
specialist.add_tool("policy_search")     # name-only also works

# 2. Wire the hierarchy
supervisor.add_child(triage)
supervisor.add_child(specialist)

# 3. Agents-as-tools: expose a child as a callable tool on the parent
#    (mirrors OpenAI Agents SDK: agent.as_tool())
supervisor.add_tool(specialist.as_tool("run_specialist"))

# 4. Wrap in a tree and inspect
tree = AgentTree(supervisor)
print(tree.visualize())
# supervisor (root) [tools: run_specialist]
# ├── triage
# └── invoice-specialist [tools: erp_lookup, policy_search]
```

### Tool Calls vs Handoffs

| Concept | What happens | Example |
|---|---|---|
| **Tool Call** | Agent invokes a function, gets result, *continues reasoning* | `node.run_tool("erp_lookup", invoice_id="4821")` → `ToolResult` |
| **Handoff** | Agent returns `HandoffResult` to Supervisor, *gives up control* | `HandoffResult(status="ok", summary="...")` |

- **Tool calls** happen *within* a child agent's `run()` — they are sub-steps
- **Handoffs** happen *between* agents — the child returns control to the Supervisor
- The Supervisor can also invoke children as tools via `child.as_tool()`

### How Handoffs Work

Every child agent returns a **`HandoffResult`** — a Pydantic model that the
Supervisor validates and uses to decide what to do next.

```python
from agent_tree import HandoffResult, ToolResult, HandoffTraces

result = HandoffResult(
    from_agent="invoice-specialist",
    to_agent="supervisor",
    status="ok",                # "ok" | "needs_more_info" | "failed"
    summary="Invoice #4821 rejected due to missing PO.",
    payload={"invoice_id": "4821", "reason": "missing_po"},
    artifacts=["erp://invoices/4821"],
    traces=HandoffTraces(
        tool_calls=["erp_lookup"],
        tool_results=[ToolResult(tool_name="erp_lookup", output={...}, status="ok")],
        reasoning_steps=["Need to look up invoice in ERP"],
        token_usage=2500,
    ),
)
```

**Supervisor loop**: plan (optional) → route to child → receive `HandoffResult` → if `ok`, done; if `needs_more_info`, enrich context + try next child; if `failed`, try next child.

### Running the Orchestrator

```python
from agent_tree import AgentTree, SupervisorOrchestrator, OrchestratorHooks

# Optional planner (mirrors reference's call_reasoner)
async def my_planner(user_input: str) -> dict:
    return {"strategy": "triage → specialist → verifier"}

orchestrator = SupervisorOrchestrator(
    tree=tree,
    hooks=OrchestratorHooks(
        # Agent lifecycle hooks
        on_node_start=my_start_hook,       # async (node, input) -> None
        on_node_end=my_end_hook,           # async (node, result) -> None
        on_handoff=my_handoff_hook,        # async (result) -> None
        # Tool lifecycle hooks
        on_tool_start=my_tool_start_hook,  # async (tool_name, args) -> None
        on_tool_end=my_tool_end_hook,      # async (tool_name, result) -> None
        # Reasoning hooks
        on_reasoning_step=my_reason_hook,  # async (agent_name, thought) -> None
    ),
    max_steps=10,
    planner=my_planner,  # plan-then-execute (optional)
)
result = await orchestrator.run("Why was invoice #4821 rejected?")
print(result.answer)   # "Invoice #4821 rejected due to missing PO number."
print(result.status)   # "completed"
print(result.plan)     # {"strategy": "triage → specialist → verifier"}
```
