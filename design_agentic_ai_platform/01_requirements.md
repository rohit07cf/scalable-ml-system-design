# Phase 1 — Requirements

## Functional Requirements

### FR-1: Hierarchical Supervisor -> Child Agent Routing
- A **Supervisor agent** receives every incoming request and decides which **specialized child agent** handles it
- Routing chain: `Triage -> Specialist -> Verifier`
- Child agents are registered in a **Child Agent Registry** with capabilities metadata
- **WHY**: Enterprise workflows are too diverse for a single prompt; decomposition into specialist agents improves accuracy and lets teams own their agents independently

### FR-2: Multi-step Execution (Plan -> Act -> Observe Loop)
- Each agent runs an iterative loop:
  1. **Plan** — LLM decides next action given current context
  2. **Act** — execute a tool call or handoff
  3. **Observe** — append result to context, check termination conditions
- Loop terminates on: final answer, step limit, budget exhaustion, or explicit stop
- **WHY**: Agents rarely solve tasks in one shot; the loop lets them reason incrementally and self-correct

### FR-3: Tool Calls vs Handoffs
- **Tool Call**: Agent invokes a function (e.g., `search_db`, `call_api`), gets structured result back, *continues reasoning in the same agent context*
- **Handoff**: Agent transfers full control to a *different* agent with a new system prompt and context window; the original agent does NOT resume
- Both are modeled as step types in the execution ledger
- **WHY**: Tool calls extend an agent's capabilities; handoffs enable separation of concerns across agents with different instructions, models, or guardrails

### FR-4: Step Streaming via Hooks
- Real-time event emission using `AsyncCallbackHandler` + `AgentHooks` + `ToolHooks`
- Events: `run_start`, `step_start`, `tool_call_start`, `tool_call_result`, `handoff`, `step_end`, `run_end`, `error`
- Delivered to clients via SSE (Server-Sent Events)
- **WHY**: Users and downstream systems need live progress visibility; batch "wait and return" UX is unacceptable for multi-step runs that take 30s+

### FR-5: Structured Outputs via Pydantic Models
- **Final output** of each agent is validated against a Pydantic model (strict mode)
- **Tool results** are also typed via Pydantic schemas
- On validation failure: retry with a repair prompt that includes the error
- **WHY**: Downstream consumers (APIs, UIs, pipelines) need typed, predictable data — not free-form text

### FR-6: Config-Driven Agent Definitions (Versioned)
- Agent configs stored as versioned JSON/YAML: system prompt, model, tools, output schema, routing rules
- Configs are immutable per version — new version = new record
- Teams self-serve config creation via internal UI/API
- **WHY**: Decouples agent behavior from platform code; enables safe rollbacks and A/B testing

### FR-7: Durable Run/Step State + Memory + Traceability
- Every run and step persisted to a **state store** (PostgreSQL)
- Full **step ledger** ("tape") captures: input, LLM response, tool calls, outputs, latencies, token counts
- Short-term memory: conversation context within a run
- **WHY**: Debugging, auditing, compliance, and replay all require a complete execution record

### FR-8: Temporal Orchestration for Long-Running Runs
- Each run = a Temporal **workflow**
- Each agent step (LLM call, tool call) = a Temporal **activity**
- Built-in retries, timeouts, and heartbeats for activities
- **WHY**: LLM calls and tool calls are unreliable and slow; Temporal gives durable execution without hand-rolled retry/state-machine logic

---

## Non-Functional Requirements

### NFR-1: Streaming Latency
- First token/event within **2 seconds** of run start
- Step events streamed with < 500ms delay from generation
- **WHY**: Perceived responsiveness is critical; users abandon if nothing appears for 5s+

### NFR-2: Reliability
- No lost runs — Temporal ensures workflow completion even through crashes
- Idempotent step execution — safe to retry any activity
- **WHY**: Enterprise workflows may trigger real actions (DB writes, API calls); lost or duplicated runs have business cost

### NFR-3: Availability
- Target **99.9% uptime** for the control plane (API)
- Temporal cluster and workers can tolerate individual node failures
- **WHY**: Internal platform serves many teams; downtime blocks multiple product lines

### NFR-4: Cost Awareness (Token Budget)
- Per-run token budget tracked and enforced
- Step limits prevent runaway loops (default: 25 steps/run)
- **WHY**: LLM API costs scale with token usage; unbounded loops can burn through budget in minutes

### NFR-5: Auditability
- Every LLM call, tool call, and handoff logged with timestamps, token counts, and agent IDs
- Step ledger is append-only and immutable
- **WHY**: Enterprise compliance (SOC2, internal audit) requires a complete, tamper-evident execution trail

### NFR-6: Security
- All tool calls execute in sandboxed environments
- Agent configs and prompts are access-controlled per team
- Secrets (API keys for tools) stored in a vault, never in configs
- **WHY**: Single-org but multi-team — one team's agent must not access another team's tools or data without authorization

---

## TL;DR (Interview Summary)
- **Supervisor -> child** routing via handoffs; each child has its own prompt, model, and tools
- **Plan-Act-Observe** loop with step limits and token budgets to prevent runaway
- **Tool calls** = function invocations within same agent; **Handoffs** = full control transfer to another agent
- **SSE streaming** via AgentHooks/ToolHooks for real-time step visibility
- **Pydantic strict mode** on both final outputs and tool results; repair prompt on validation failure
- **Temporal workflows** for durable execution; each step is an activity with retries/timeouts
- **Append-only step ledger** for debugging, replay, and compliance audit
- **Versioned configs** decouple agent behavior from platform code
