# Phase 7 — Wrap-Up

## Bottlenecks

### 1. LLM Provider Latency
- Each step blocks on an LLM API call (1–10 seconds depending on model/tokens)
- A 6-step run spends ~80% of wall-clock time waiting on LLM responses
- **Mitigation**: Temporal heartbeats detect stuck calls; timeout + retry policy; consider faster models for triage steps (e.g., GPT-4o-mini for routing, GPT-4o for specialist)

### 2. Sequential Step Execution
- Plan → Act → Observe is inherently sequential within one agent
- Parallelism is only possible across independent tool calls within a single step
- **Mitigation**: Minimize step count via better prompts; use handoffs to specialists that solve in fewer steps

### 3. Context Window Growth
- Each step appends to the messages array; later steps have larger input → higher latency + cost
- A 20-step run with tool results can hit 30K+ tokens of context
- **Mitigation**: Context summarization between steps (trade accuracy for speed); truncate old tool results; set token budgets

### 4. Temporal Worker Pool Saturation
- Workers are I/O-bound (waiting on LLM APIs), but each worker holds a task slot
- 50 concurrent runs × 1 active activity each = 50 task slots needed
- **Mitigation**: HPA on task queue depth; workers use async I/O (not blocking threads)

---

## Scaling Strategy

### More Workers (Horizontal)
- Temporal workers are stateless → add more pods via HPA
- Scale trigger: task queue depth > 5 pending tasks
- **WHY**: Primary scaling axis for handling more concurrent runs

### Event Buffering
- Redis pub/sub is fire-and-forget; no backpressure
- If Stream Manager falls behind: buffer events in Redis Streams (ordered, persistent) instead of plain pub/sub
- **WHY**: Prevents event loss during traffic spikes without slowing down workers

### Rate Limits
- Per-team rate limits on `POST /runs` (e.g., 10 concurrent runs per team)
- Token budget limits per team per day (e.g., 5M tokens/day/team)
- **WHY**: Prevents one team from monopolizing workers or LLM budget

### Read Replicas (If Needed)
- PostgreSQL read replica for dashboard queries and analytics
- Writes go to primary; reads (run status, step history) can hit replica
- **WHY**: Separates operational read load from write path; not needed at initial scale (~2 writes/sec) but ready for 10x growth

---

## Trade-Offs

### SSE vs WebSockets

| Factor | SSE | WebSocket |
|---|---|---|
| Direction | Server → Client only | Bidirectional |
| Reconnect | Built-in (`Last-Event-ID`) | Manual implementation |
| HTTP compatibility | Works through proxies/CDNs | Requires upgrade handshake |
| Complexity | Simpler (plain HTTP) | More complex (connection management) |

- **Decision: SSE**
- **WHY**: Agent events are unidirectional (server pushes step updates). No client-to-server messaging needed during a run. SSE's auto-reconnect and HTTP compatibility make it operationally simpler.
- **When to reconsider**: If interactive/collaborative editing features are added (user provides mid-run input), WebSocket becomes necessary.

### PostgreSQL vs Redis for Primary State

| Factor | PostgreSQL | Redis |
|---|---|---|
| Durability | Full ACID | Optional (AOF/RDB) |
| Query flexibility | SQL, JSONB queries, joins | Key-value, limited querying |
| Audit trail | Natural (append-only tables) | Not designed for audit |
| Operational cost | Higher (backups, vacuuming) | Lower (simpler ops) |

- **Decision: PostgreSQL for source of truth; Redis for hot state**
- **WHY**: Audit/compliance requires durable, queryable records (PostgreSQL). Real-time operational data (current run status, pub/sub) needs low-latency ephemeral storage (Redis). Using both plays to each store's strength.
- **When to reconsider**: If runs exceed 100K/day, consider moving step ledger to a columnar store (ClickHouse) for analytics while keeping PostgreSQL for operational queries.

### Strict Schemas vs Flexibility

| Factor | Strict (Pydantic strict=True) | Flexible (dict/Any) |
|---|---|---|
| Type safety | Full — catches errors at boundary | None — errors surface downstream |
| Developer experience | Must define schemas upfront | Faster iteration, no schema work |
| LLM compatibility | Requires `response_format` support | Works with any LLM output |
| Maintenance cost | Schema versioning required | No schema debt, but debugging debt |

- **Decision: Strict schemas on API boundary and final outputs; flexible (JSONB) for intermediate state**
- **WHY**: External consumers need typed contracts. Internal agent reasoning is exploratory — over-constraining intermediate steps reduces LLM effectiveness. The boundary between "typed" and "flexible" is the Output Validator.
- **When to reconsider**: If intermediate step validation becomes critical (regulated industries), add optional per-step schemas.

---

## Failure Modes Checklist

| Failure Mode | Detection | Impact | Mitigation |
|---|---|---|---|
| **Tool timeout** | Temporal activity timeout (30s default) | Step fails, agent retries or skips | Per-tool timeout config; max 2 retries; fallback tool or agent-level error handling |
| **Schema validation failure** | Pydantic validation raises `ValidationError` | Output rejected | Repair prompt strategy (max 2 attempts); if still fails, run marked `failed` with raw output preserved |
| **LLM provider outage** | HTTP 5xx / connection timeout from provider | All active LLM calls fail | Temporal retries (3x with backoff); circuit breaker after 5 consecutive failures; alert to on-call |
| **LLM rate limit** | HTTP 429 from provider | Calls throttled | Exponential backoff in retry policy; per-team token rate limits to prevent one team from triggering org-wide throttling |
| **Worker crash** | Heartbeat timeout detected by Temporal | Activity appears stuck | Temporal reschedules activity on another worker; idempotent execution prevents duplicate side-effects |
| **Temporal cluster failure** | Health check fails; workflows stop progressing | All runs stall | Multi-node Temporal cluster (3+ nodes); automated failover; pending workflows resume after recovery |
| **Redis failure** | Health check fails; pub/sub stops | Streaming breaks; hot state stale | Graceful degradation: Stream Manager falls back to polling PostgreSQL; run execution unaffected (Redis is not on critical path) |
| **PostgreSQL failure** | Connection errors on write | Steps can't be persisted | Temporal retries persist_step_activity; if DB is down for extended period, steps buffered in workflow state; alert to on-call |
| **Runaway agent loop** | Step count exceeds `max_steps` | Tokens wasted, run takes too long | Hard step limit; token budget; Temporal workflow timeout (10 min hard cap) |
| **Infinite handoff cycle** | Handoff depth exceeds 5 | Agents ping-pong forever | `handoff_depth` counter in workflow state; terminate with `routing_exhausted` error |
| **Client disconnect during stream** | SSE connection closed | No impact on execution | Server continues run; client reconnects with `Last-Event-ID`; result available via GET /runs/{id} |
| **Config version missing** | Config lookup returns 404 | Run can't start | Validate config existence before starting Temporal workflow; return 400 to client immediately |
| **Idempotency key collision** | Duplicate key in Redis/PostgreSQL | Duplicate run prevented | Return existing run_id; no new workflow started |

---

## TL;DR (Interview Summary)
- **Primary bottleneck**: LLM latency (1–10s per step); mitigate with faster models for routing, timeouts, and step minimization
- **Scale horizontally** via stateless Temporal workers with HPA on queue depth; Redis Streams for event buffering at higher load
- **SSE over WebSocket**: Simpler, HTTP-native, sufficient for unidirectional agent events; reconsider if interactive features are needed
- **PostgreSQL + Redis**: Durable audit trail in PostgreSQL; low-latency hot state in Redis; each store plays to its strength
- **Strict schemas at boundaries** (API + final output); flexible JSONB for intermediate agent reasoning
- **13 failure modes** covered: tool timeout, schema failure, provider outage, worker crash, runaway loops, Redis/PostgreSQL failures — each with detection + mitigation
- **Five independent kill switches**: step limit, token budget, handoff depth, workflow timeout, user cancellation
- **Graceful degradation**: Redis failure doesn't stop runs (only streaming degrades); client disconnect doesn't stop execution
