# Phase 6 — Deep Dives

## 1. Supervisor Routing Logic (Child Selection) + Fallback

### How the Supervisor Decides

```
Input arrives → Supervisor LLM call → structured routing decision

Supervisor system prompt includes:
- List of available child agents with capability descriptions
- Routing instructions: "Given the user query, select the best agent"
- Output schema: RoutingDecision(target_agent, confidence, reason)
```

### Routing Decision Model

```python
class RoutingDecision(BaseModel):
    target_agent: str          # config_id of child agent
    confidence: float          # 0.0–1.0
    reason: str                # one-line explanation (for audit)
    fallback_agent: str | None # if primary can't handle it
```

### Routing Flow

```
1. Supervisor receives input
2. LLM produces RoutingDecision (structured output)
3. Validate target_agent exists in Child Agent Registry
4. If confidence < 0.7 → use fallback_agent (or default generalist)
5. Execute handoff to selected child agent
6. If child agent fails (step limit, tool error) → Supervisor can re-route to fallback
```

### Fallback Strategy
- **Primary fallback**: Supervisor config specifies a `default_agent` for low-confidence routing
- **Error fallback**: If a child agent fails after 3 steps, control returns to Supervisor, which can try an alternative child
- **Dead letter**: If all routing attempts fail, run marked as `failed` with full ledger for debugging
- **WHY**: LLM routing is probabilistic; fallbacks prevent single-agent failures from killing the entire run

---

## 2. Multi-Step Loop Control

### Step Limits
- **Per-run hard cap**: configurable (default 25), set in `RunOptions.max_steps`
- **Per-agent soft cap**: each agent config has its own `max_steps` (e.g., verifier limited to 3 steps)
- **WHY**: Without limits, a confused agent loops forever; per-agent caps prevent one specialist from consuming the entire budget

### Recursion Limits
- **Max handoff depth**: 5 (supervisor → child → sub-child → ...)
- Tracked as `handoff_depth` counter in workflow state
- **WHY**: Prevents infinite handoff chains (Agent A → Agent B → Agent A → ...)

### Token Budgets
- Per-run budget: `RunOptions.max_tokens` (default 50K)
- After each LLM call: `tokens_used += step_tokens`
- If `tokens_used > max_tokens * 0.9` → emit warning event
- If `tokens_used >= max_tokens` → terminate run with `budget_exceeded` error
- **WHY**: Token costs scale linearly; budgets are the primary cost control mechanism

### Loop Termination Summary

| Condition | Action | Status |
|---|---|---|
| Final output produced + validated | Complete run | `completed` |
| Step limit reached | Stop, return partial | `failed` (step_limit_exceeded) |
| Token budget exceeded | Stop, return partial | `failed` (budget_exceeded) |
| Run timeout (Temporal workflow timeout) | Stop | `failed` (timeout) |
| All handoff targets exhausted | Stop | `failed` (routing_exhausted) |
| User cancellation | Stop current activity | `cancelled` |

---

## 3. Structured Outputs

### Pydantic Schemas for Tool Results

Each tool declares its output schema in the config:

```python
class ERPLookupResult(BaseModel):
    model_config = ConfigDict(strict=True)

    invoice_id: str
    status: Literal["approved", "rejected", "pending"]
    reason: str | None = None
    amount_cents: int
    currency: str = "USD"
```

- Tool Executor validates result against schema before returning to agent
- On validation failure → tool call marked as `failed`, error returned to agent context
- **WHY**: Without typed tool results, the LLM might hallucinate tool output structure, causing downstream failures

### Pydantic Schemas for Final Output

Each agent config references an output schema:

```python
class InvoiceTriageOutput(BaseModel):
    model_config = ConfigDict(strict=True)

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str]
    action_required: bool
    escalation_reason: str | None = None
```

- Output Validator runs after agent produces final answer
- Enforced via `response_format` parameter in LLM call (if provider supports it)
- **WHY**: Downstream systems (APIs, UIs, workflows) consume typed data; free-form text breaks integrations

### Validation Failure → Repair Prompt Strategy

```
1. Agent produces final output
2. Pydantic validation fails (e.g., "confidence must be >= 0.0, got -0.5")
3. Construct repair prompt:
   "Your output failed validation: {error_details}
    Original output: {raw_output}
    Please fix the output to match the schema: {schema_json}"
4. Re-call LLM with repair prompt (counts as an extra step)
5. Validate again
6. If still fails after 2 repair attempts → mark run as failed with validation_error
```

- **WHY**: LLMs occasionally produce malformed structured output even with `response_format`; a repair loop is cheaper than failing the entire run
- **Budget impact**: Repair steps count against step and token limits (no free retries)

---

## 4. Streaming

### Event Types

| Event | When Emitted | Key Data |
|---|---|---|
| `run_start` | Workflow begins | run_id, agent_id, config_version |
| `step_start` | Agent begins a new reasoning step | step_id, step_number, agent_id |
| `tool_call_start` | Agent invokes a tool | tool_name, tool_input |
| `tool_call_result` | Tool returns result | tool_output, latency_ms, validation_ok |
| `handoff` | Agent transfers to another agent | from_agent, to_agent, reason |
| `step_end` | Step completes | tokens_used, latency_ms |
| `run_end` | Run terminates (success or failure) | status, output or error |
| `error` | Non-fatal error during execution | error_type, message, step_id |

### Streaming Architecture

```
Worker (Hooks Engine)
    │
    │ publish per-run channel
    ▼
Redis Pub/Sub ──────────────► Stream Manager
    channel: run:{run_id}         │
                                  │ SSE push
                                  ▼
                              Client (browser/API consumer)
```

### Hooks Implementation (OpenAI Agents SDK Pattern)

```python
class PlatformAgentHooks:
    """Fires on agent lifecycle events."""

    async def on_start(self, context: RunContext, agent: Agent):
        await emit_event("run_start", run_id=context.run_id, agent=agent.name)

    async def on_handoff(self, context: RunContext, source: Agent, target: Agent):
        await emit_event("handoff", from_agent=source.name, to_agent=target.name)

    async def on_end(self, context: RunContext, agent: Agent, output: Any):
        await emit_event("run_end", run_id=context.run_id, output=output)


class PlatformToolHooks:
    """Fires on tool lifecycle events."""

    async def on_tool_start(self, context: RunContext, agent: Agent, tool: Tool):
        await emit_event("tool_call_start", tool=tool.name, input=tool.input)

    async def on_tool_end(self, context: RunContext, agent: Agent, tool: Tool, result: Any):
        await emit_event("tool_call_result", tool=tool.name, output=result)
```

### Client Disconnect Handling

- **Server keeps running**: Run execution is decoupled from the SSE connection
  - Temporal workflow continues regardless of client state
  - Events are published to Redis whether or not anyone is subscribed
- **Reconnection**: Client sends `Last-Event-ID` header; Stream Manager replays missed events from Redis (short buffer, ~5 min TTL) or from `stream_events` table (if persisted)
- **No client connected at all**: Run still completes; result available via `GET /runs/{id}`
- **WHY**: The run is a background job, not a synchronous request. Streaming is a convenience layer, not a dependency.

---

## 5. Memory / State

### Short-Term Memory (Within a Run)

- **What**: The accumulated messages array (system prompt + user input + LLM responses + tool results)
- **Where**: Held in workflow state during execution; snapshot persisted per step in `steps.input_context`
- **Scope**: Lives for the duration of one run; discarded after run completes
- **On handoff**: Relevant context is transferred to the new agent (not the full history — a summary or selected messages)
- **WHY**: Agents need conversation context to reason about multi-step tasks; without it, each step would be stateless

### Step Ledger (The "Tape")

- **What**: Append-only record of every step (see DB design)
- **Purpose**: Debugging, replay, audit, analytics
- **Not used for runtime decisions**: The agent uses short-term memory (messages array), not the ledger
- **WHY separate from memory**: The ledger includes metadata (tokens, latency, validation status) that the agent doesn't need in its context

### Replay for Debugging

```
1. Load run from PostgreSQL (all steps)
2. For each step: reconstruct input_context + agent config
3. Re-execute LLM call with same input → compare outputs
4. Identify divergence point (where the agent "went wrong")
```

- **Determinism caveat**: LLM outputs are stochastic; replay shows *what the agent saw*, not guaranteed same output
- **WHY**: When a run produces a wrong answer, the team needs to see the chain of reasoning, not just the final output

---

## 6. Reliability

### Idempotent Step Execution

- Each activity has a unique `activity_id` (derived from `run_id + step_number + attempt`)
- Tool calls check: "Has this exact call already succeeded?" (via `tool_calls` table)
- If already succeeded → return cached result, skip re-execution
- **WHY**: Temporal retries activities on worker crash; without idempotency, a tool call might execute twice (e.g., double API write)

### Temporal Retries

```python
# Activity retry policy
retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
    non_retryable_error_types=["ValidationError", "BudgetExceededError"]
)
```

- **Retryable**: LLM API 5xx, tool timeout, transient network errors
- **Non-retryable**: Schema validation failure, budget exceeded, step limit hit
- **WHY**: Not all errors are transient; retrying a validation failure wastes tokens

### Temporal Timeouts

| Timeout | Value | Purpose |
|---|---|---|
| Workflow execution timeout | 10 min | Hard cap on entire run |
| Activity start-to-close | 60s (LLM), 30s (tool) | Individual step timeout |
| Activity schedule-to-start | 30s | Detect worker pool starvation |
| Heartbeat | 5s (LLM), 10s (tool) | Detect stuck activities |

### Heartbeats

- Workers send heartbeats during long-running activities (LLM streaming, slow tools)
- If heartbeat missed → Temporal marks activity as failed → retries on another worker
- **WHY**: Without heartbeats, a stuck worker holds the activity until timeout (could be 60s of wasted time)

---

## 7. Tool Calls vs Handoffs — When Each Is Appropriate

### Use a Tool Call When:
- Agent needs **data** to continue reasoning (DB query, API lookup, calculation)
- The task stays within the **same agent's domain**
- Agent retains full control and context after the call
- Example: Invoice specialist calls `erp_lookup` to get invoice details

### Use a Handoff When:
- The task requires a **different specialization** (different prompt, model, or tools)
- The current agent has completed its role (triage done, now specialist needed)
- You want **separation of concerns** (triage agent shouldn't have access to write tools)
- Example: Supervisor hands off to `invoice-specialist` after determining the query type

### Decision Matrix

| Signal | Tool Call | Handoff |
|---|---|---|
| Agent needs external data | x | |
| Task domain changes | | x |
| Agent needs different tools | | x |
| Agent needs different model | | x |
| Quick lookup, same context | x | |
| Complex sub-task, different prompt | | x |
| Result goes back to same agent | x | |
| Control transfers permanently | | x |

### Anti-Patterns
- **Handoff for a simple lookup**: Overkill — use a tool call instead (avoids context transfer overhead)
- **Tool call that changes agent behavior**: If a "tool" is really re-routing logic, it should be a handoff
- **Ping-pong handoffs**: Agent A → Agent B → Agent A — use a tool call from A instead, or redesign the agent chain

---

## TL;DR (Interview Summary)
- **Supervisor routing**: LLM produces `RoutingDecision` (typed); confidence threshold triggers fallback agent
- **Loop control**: Step limits (per-run + per-agent), token budgets, handoff depth cap, Temporal workflow timeout — five independent kill switches
- **Structured outputs**: Pydantic strict mode on tool results + final output; repair prompt on failure (max 2 retries)
- **Streaming**: Hooks (AgentHooks + ToolHooks) → Redis pub/sub → Stream Manager → SSE; server keeps running on client disconnect
- **Memory**: Short-term (messages array in workflow state) vs step ledger (append-only in PostgreSQL); replay reconstructs context per step
- **Idempotency**: Activity ID = run_id + step_number + attempt; tool results cached to prevent double execution
- **Tool calls** = data retrieval within same agent; **Handoffs** = permanent control transfer when domain changes
