# Phase 4 — High-Level Design

## Architecture Diagram

```
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                              KUBERNETES CLUSTER                                │
 │                                                                                │
 │  ┌──────────────┐     ┌──────────────────────────────────────────────────────┐  │
 │  │              │     │              CONTROL PLANE (FastAPI)                 │  │
 │  │   API        │     │  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │  │
 │  │   Gateway    │────>│  │ Run        │  │ Config     │  │ Stream       │   │  │
 │  │   + Auth     │     │  │ Controller │  │ Service    │  │ Manager      │   │  │
 │  │              │     │  └─────┬──────┘  └────────────┘  └──────┬───────┘   │  │
 │  └──────────────┘     │        │                                │           │  │
 │                       └────────┼────────────────────────────────┼───────────┘  │
 │                                │                                │              │
 │                                ▼                                ▼              │
 │  ┌─────────────────────────────────────────┐         ┌──────────────────┐     │
 │  │         TEMPORAL CLUSTER                │         │   REDIS          │     │
 │  │  ┌───────────┐   ┌──────────────────┐   │         │   - SSE pub/sub  │     │
 │  │  │ Workflow   │   │ Task Queues      │   │         │   - Hot state    │     │
 │  │  │ Engine     │   │ (agent-runtime)  │   │         │   - Idempotency  │     │
 │  │  └───────────┘   └───────┬──────────┘   │         └──────────────────┘     │
 │  └───────────────────────────┼─────────────┘                                  │
 │                              │                                                │
 │                              ▼                                                │
 │  ┌─────────────────────────────────────────────────────────────────────┐       │
 │  │                    WORKER POOL (Temporal Workers)                   │       │
 │  │                                                                     │       │
 │  │  ┌──────────────────┐   ┌──────────────┐   ┌──────────────────┐    │       │
 │  │  │  Agent Runtime   │   │  Tool        │   │  Output          │    │       │
 │  │  │  (Supervisor +   │   │  Executor    │   │  Validator       │    │       │
 │  │  │   Child Agents)  │   │  (sandboxed) │   │  (Pydantic)      │    │       │
 │  │  └──────────────────┘   └──────────────┘   └──────────────────┘    │       │
 │  │                                                                     │       │
 │  │  ┌──────────────────┐   ┌──────────────────────────────────────┐   │       │
 │  │  │  Child Agent     │   │  Hooks Engine                        │   │       │
 │  │  │  Registry        │   │  (AgentHooks + ToolHooks → events)   │   │       │
 │  │  └──────────────────┘   └──────────────────────────────────────┘   │       │
 │  └─────────────────────────────────────────────────────────────────────┘       │
 │                              │                                                │
 │                              ▼                                                │
 │  ┌─────────────────────────────────────────────────────────────────────┐       │
 │  │                      DATA LAYER                                     │       │
 │  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐    │       │
 │  │  │  PostgreSQL      │   │  Config Store     │   │ Observability│    │       │
 │  │  │  - Runs          │   │  (versioned       │   │ - Metrics    │    │       │
 │  │  │  - Steps (ledger)│   │   agent configs)  │   │ - Traces     │    │       │
 │  │  │  - Tool calls    │   │                   │   │ - Logs       │    │       │
 │  │  └──────────────────┘   └──────────────────┘   └──────────────┘    │       │
 │  └─────────────────────────────────────────────────────────────────────┘       │
 └────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components + WHY

### 1. API Gateway + Auth
- Ingress controller (NGINX/Envoy) with JWT validation
- Rate limiting per team
- **WHY**: Single entry point for all API traffic; auth at the edge keeps internal services trust-boundary-free

### 2. Control Plane (FastAPI)
Three internal services behind the gateway:

**Run Controller**
- Accepts `POST /runs`, validates input, writes run record, starts Temporal workflow
- **WHY**: Thin orchestration layer — real execution happens in Temporal workers

**Config Service**
- CRUD for versioned agent configs; serves `GET /configs/{type}/{version}`
- **WHY**: Decouples config management from execution; configs are read at run start and pinned

**Stream Manager**
- Manages SSE connections; subscribes to Redis pub/sub for run events
- Delivers events to connected clients; buffers for reconnection
- **WHY**: Separates streaming concern from execution; stream manager scales independently

### 3. Temporal Cluster + Task Queues
- **Workflow engine**: manages run lifecycle as a durable workflow
- **Task queue** (`agent-runtime`): workers poll for activities
- **WHY**: Gives us retries, timeouts, heartbeats, and crash recovery without custom state machines

### 4. Worker Pool (Temporal Workers)
Stateless worker pods that execute activities:

**Agent Runtime (Supervisor + Child Agents)**
- Runs the Plan → Act → Observe loop
- Supervisor decides: tool call or handoff
- On handoff: loads child agent config, transfers context
- **WHY**: Core execution engine; stateless workers scale horizontally

**Tool Executor (Sandboxed)**
- Executes tool calls in isolation (subprocess/container)
- Enforces per-tool timeouts
- **WHY**: Tools call external APIs, run code — sandboxing prevents blast radius

**Output Validator (Pydantic)**
- Validates tool results and final outputs against Pydantic schemas
- On failure: generates repair prompt, retries LLM call (up to 2 attempts)
- **WHY**: Typed outputs are a hard requirement; validation at this layer catches errors before they propagate

**Child Agent Registry**
- In-memory lookup of agent configs (refreshed from Config Store)
- Maps agent IDs to their capabilities, tools, and output schemas
- **WHY**: Supervisor needs fast lookup to route handoffs; avoids DB call per step

**Hooks Engine (AgentHooks + ToolHooks)**
- Fires lifecycle events: `on_agent_start`, `on_tool_call`, `on_tool_result`, `on_handoff`, etc.
- Publishes events to Redis pub/sub
- **WHY**: Decouples event emission from consumption; hooks pattern matches OpenAI Agents SDK design

### 5. Redis
- **SSE pub/sub**: Stream Manager subscribes to per-run channels
- **Hot state**: Current step number, token count, active agent (fast reads for status API)
- **Idempotency store**: Deduplicates run creation requests (TTL: 24h)
- **WHY**: Low-latency, ephemeral data store; PostgreSQL is overkill for pub/sub and counters

### 6. PostgreSQL
- Durable store for runs, steps (ledger), tool calls, configs
- Source of truth for audit and replay
- **WHY**: Relational model fits naturally (runs → steps → tool calls); strong consistency for audit

### 7. Observability
- **Metrics**: Run latency, step count, tool call latency, token usage (Prometheus)
- **Traces**: Distributed traces per run linking all steps (OpenTelemetry)
- **Logs**: Structured JSON logs from all services (shipped to ELK/Loki)
- **WHY**: Multi-step agent runs are opaque without observability; traces are essential for debugging

---

## Data Flow (Step-by-Step)

```
1. Client → POST /runs
   │
2. Run Controller validates input (Pydantic strict mode)
   │  Writes run record to PostgreSQL (status: "queued")
   │  Checks idempotency key in Redis
   │  Starts Temporal workflow (RunWorkflow)
   │
3. Temporal dispatches to Worker Pool
   │
4. Worker loads agent config from Child Agent Registry
   │  Hooks Engine fires: run_start event → Redis pub/sub
   │
5. ┌─── PLAN-ACT-OBSERVE LOOP ──────────────────────────────┐
   │                                                          │
   │  5a. PLAN: LLM call with current context                │
   │      → Hooks: step_start                                │
   │      → Heartbeat to Temporal (proves worker is alive)   │
   │                                                          │
   │  5b. ACT: LLM response parsed                           │
   │      ├─ TOOL CALL path:                                 │
   │      │   → Hooks: tool_call_start                       │
   │      │   → Tool Executor runs tool (sandboxed)          │
   │      │   → Output Validator checks tool result schema   │
   │      │   → Hooks: tool_call_result                      │
   │      │   → Result appended to context                   │
   │      │                                                   │
   │      └─ HANDOFF path:                                   │
   │          → Hooks: handoff event                         │
   │          → Load target agent config                     │
   │          → Transfer context + new system prompt         │
   │          → New agent takes over loop                    │
   │                                                          │
   │  5c. OBSERVE: Check termination conditions              │
   │      → Final answer produced? → validate output schema  │
   │      → Step limit reached? → fail with error            │
   │      → Token budget exceeded? → fail with error         │
   │      → Continue loop                                    │
   │      → Hooks: step_end                                  │
   │      → Write step to PostgreSQL (ledger)                │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
   │
6. Run complete
   │  Output Validator checks final output against Pydantic schema
   │  Write final run record to PostgreSQL (status: "completed")
   │  Hooks: run_end event → Redis pub/sub
   │
7. Stream Manager delivers run_end to SSE client
   │  Client closes connection
```

---

## Step Ledger ("Tape") Concept

Every step in a run is recorded as an immutable ledger entry:

```
┌──────────────────────────────────────────────────────────┐
│  STEP LEDGER (run_id: run_x7k9m2)                       │
├────┬──────────┬────────────┬────────────┬───────────────┤
│ #  │ Agent    │ Type       │ Action     │ Tokens        │
├────┼──────────┼────────────┼────────────┼───────────────┤
│ 1  │ superv.  │ plan       │ LLM call   │ 1200 in/300 o │
│ 2  │ superv.  │ handoff    │ → triage   │ -             │
│ 3  │ triage   │ tool_call  │ erp_lookup │ 800 in/200 o  │
│ 4  │ triage   │ plan       │ LLM call   │ 1500 in/400 o │
│ 5  │ triage   │ handoff    │ → verifier │ -             │
│ 6  │ verifier │ plan       │ LLM call   │ 1800 in/500 o │
│ 7  │ verifier │ final      │ output     │ 900 in/200 o  │
└────┴──────────┴────────────┴────────────┴───────────────┘
```

- **Append-only**: Steps are never modified after creation
- **Replayable**: Given the ledger + configs, you can reconstruct exactly what happened
- **WHY**: Debugging agent failures requires seeing the full chain of decisions; auditors need tamper-evident records

---

## Tool Calls vs Handoffs (Clear Distinction)

```
                    ┌──────────────────────┐
                    │   Agent A (running)  │
                    └──────────┬───────────┘
                               │
               ┌───────────────┼───────────────┐
               │                               │
        TOOL CALL                         HANDOFF
               │                               │
               ▼                               ▼
    ┌──────────────────┐           ┌──────────────────┐
    │ External Function│           │   Agent B         │
    │ (e.g., API call) │           │ (new prompt,      │
    │                  │           │  new tools,       │
    │  Returns result  │           │  takes over)      │
    └────────┬─────────┘           └──────────────────┘
             │                               │
             ▼                               ▼
    ┌──────────────────┐           Agent B now owns
    │  Agent A resumes │           the run. Agent A
    │  with result in  │           does NOT resume.
    │  its context     │
    └──────────────────┘
```

| Aspect | Tool Call | Handoff |
|---|---|---|
| Control flow | Agent calls, gets result, continues | Agent transfers control permanently |
| Context | Same agent, same context window | New agent, new system prompt, context transferred |
| Use case | Data retrieval, computation, API calls | Triage → specialist, escalation |
| Temporal model | Single activity within same workflow step | New activity set under same workflow |
| Example | `search_db(query="...")` → result | `handoff(target="invoice-specialist")` |

---

## Temporal Workflow Boundaries

```
┌─────────────────────────────────────────────────────┐
│  RunWorkflow (1 per run)                            │
│  - Durable state: current agent, step count, budget │
│  - Manages loop: decides next activity to schedule  │
│                                                      │
│  Activities:                                         │
│  ┌─────────────────────────────────────────────┐    │
│  │ llm_call_activity                            │    │
│  │ - Calls LLM provider API                     │    │
│  │ - Retry: 3x with exponential backoff         │    │
│  │ - Timeout: 60s                               │    │
│  │ - Heartbeat: every 5s (for streaming LLMs)   │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ tool_call_activity                           │    │
│  │ - Executes tool in sandbox                   │    │
│  │ - Retry: per-tool config (default 2x)        │    │
│  │ - Timeout: per-tool config (default 30s)     │    │
│  │ - Heartbeat: every 10s                       │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ validate_output_activity                     │    │
│  │ - Pydantic validation + optional repair      │    │
│  │ - Retry: 2x (with repair prompt)             │    │
│  │ - Timeout: 30s                               │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ persist_step_activity                        │    │
│  │ - Writes step to PostgreSQL ledger           │    │
│  │ - Retry: 3x                                  │    │
│  │ - Timeout: 5s                                │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ emit_event_activity                          │    │
│  │ - Publishes to Redis pub/sub                 │    │
│  │ - Retry: 2x                                  │    │
│  │ - Timeout: 2s                                │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**WHY this boundary**:
- **Workflow** = the run's decision loop; holds durable state (survives crashes)
- **Activities** = individual side-effects; each independently retryable and timeout-able
- Temporal replays the workflow on crash; activities are NOT re-executed if already completed

---

## Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────┐
│  Namespace: agent-platform                              │
│                                                          │
│  Deployments:                                            │
│  ┌─────────────────────┐  ┌───────────────────────┐     │
│  │ control-plane       │  │ temporal-workers       │     │
│  │ replicas: 2         │  │ replicas: 3–10 (HPA)  │     │
│  │ (FastAPI + uvicorn) │  │ (Python worker pods)   │     │
│  └─────────────────────┘  └───────────────────────┘     │
│                                                          │
│  StatefulSets:                                           │
│  ┌─────────────────────┐  ┌───────────────────────┐     │
│  │ postgresql           │  │ redis                 │     │
│  │ replicas: 1 (+ r/o) │  │ replicas: 1           │     │
│  └─────────────────────┘  └───────────────────────┘     │
│                                                          │
│  HPA (temporal-workers):                                 │
│  │ metric: temporal_task_queue_depth                     │
│  │ target: < 5 pending tasks                            │
│  │ min: 3, max: 10                                      │
│                                                          │
│  Temporal Cluster: managed (Temporal Cloud) or           │
│  self-hosted (3-node StatefulSet)                        │
└─────────────────────────────────────────────────────────┘
```

**WHY HPA on task queue depth**: CPU-based scaling is wrong for LLM workloads (workers are I/O-bound waiting on LLM APIs). Queue depth directly measures backlog.

---

## TL;DR (Interview Summary)
- **3-tier architecture**: API Gateway → Control Plane (FastAPI) → Worker Pool (Temporal workers)
- **Temporal** = 1 workflow per run; each LLM call, tool call, and persist step = separate activity with its own retry/timeout
- **Step ledger ("tape")**: append-only record of every decision for replay and audit
- **Tool call** = function invocation, agent continues; **Handoff** = permanent control transfer to another agent
- **Hooks Engine** (AgentHooks + ToolHooks) emits events → Redis pub/sub → Stream Manager → SSE to client
- **Redis** for hot state + pub/sub + idempotency; **PostgreSQL** for durable runs/steps/configs
- **K8s HPA** scales workers on Temporal task queue depth, not CPU (workers are I/O-bound)
- **Stateless workers** = horizontal scaling; all state lives in Temporal + PostgreSQL + Redis
