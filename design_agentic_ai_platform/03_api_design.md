# Phase 3 — API Design

## Endpoints Overview

| Method | Path | Purpose |
|---|---|---|
| POST | `/runs` | Start a new agent run |
| GET | `/runs/{id}` | Get run status + result |
| GET | `/runs/{id}/stream` | SSE stream of step events |
| POST | `/runs/{id}/cancel` | Cancel a running run |
| GET | `/configs/{type}/{version}` | Fetch a versioned agent config |

---

## POST /runs — Start a Run

### Request

```json
{
  "config_id": "triage-agent-v3",
  "config_version": 7,
  "input": {
    "query": "Why was invoice #4821 rejected?",
    "context": {"customer_id": "cust_abc123"}
  },
  "options": {
    "max_steps": 20,
    "max_tokens": 50000,
    "timeout_seconds": 120,
    "stream": true
  },
  "idempotency_key": "run_req_8f3a1b"
}
```

### Pydantic Request Model

```python
class RunOptions(BaseModel):
    max_steps: int = Field(default=25, ge=1, le=100)
    max_tokens: int = Field(default=50000, ge=1000, le=500000)
    timeout_seconds: int = Field(default=120, ge=10, le=600)
    stream: bool = Field(default=True)

class CreateRunRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    config_id: str
    config_version: int
    input: dict[str, Any]
    options: RunOptions = RunOptions()
    idempotency_key: str = Field(min_length=8, max_length=64)
```

**WHY `idempotency_key`**: Client retries on network failure must not create duplicate runs. The platform deduplicates by this key within a 24h window.

### Response (202 Accepted)

```json
{
  "run_id": "run_x7k9m2",
  "status": "queued",
  "stream_url": "/runs/run_x7k9m2/stream",
  "created_at": "2025-01-15T10:30:00Z"
}
```

```python
class CreateRunResponse(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    stream_url: str
    created_at: datetime
```

---

## GET /runs/{id} — Run Status

### Response (200 OK)

```json
{
  "run_id": "run_x7k9m2",
  "status": "completed",
  "config_id": "triage-agent-v3",
  "config_version": 7,
  "steps_completed": 6,
  "tokens_used": 14200,
  "output": {
    "answer": "Invoice #4821 was rejected due to missing PO number.",
    "confidence": 0.92,
    "sources": ["tool:erp_lookup", "tool:policy_search"]
  },
  "error": null,
  "started_at": "2025-01-15T10:30:01Z",
  "completed_at": "2025-01-15T10:30:28Z"
}
```

```python
class RunStatusResponse(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    config_id: str
    config_version: int
    steps_completed: int
    tokens_used: int
    output: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
```

**WHY separate from stream**: Polling clients and dashboards need a simple status check without maintaining a stream connection.

---

## GET /runs/{id}/stream — SSE Event Stream

### Connection
- Protocol: **Server-Sent Events (SSE)** over HTTP/2
- Content-Type: `text/event-stream`
- Reconnection: client sends `Last-Event-ID` header on reconnect

**WHY SSE over WebSocket**: Unidirectional (server → client) is sufficient; SSE is simpler, works through HTTP proxies, and supports auto-reconnect natively.

### Event Types

```
event: run_start
data: {"run_id": "run_x7k9m2", "agent": "supervisor"}

event: step_start
data: {"step_id": "step_001", "agent": "triage-agent", "step_num": 1}

event: tool_call_start
data: {"step_id": "step_002", "tool": "erp_lookup", "input": {"invoice_id": "4821"}}

event: tool_call_result
data: {"step_id": "step_002", "tool": "erp_lookup", "output": {"status": "rejected", "reason": "missing_po"}, "latency_ms": 450}

event: handoff
data: {"from_agent": "triage-agent", "to_agent": "invoice-specialist", "reason": "invoice dispute detected"}

event: step_end
data: {"step_id": "step_002", "tokens_used": 2100}

event: run_end
data: {"run_id": "run_x7k9m2", "status": "completed", "output": {"answer": "..."}}

event: error
data: {"run_id": "run_x7k9m2", "error": "step_limit_exceeded", "message": "Run hit 25 step limit"}
```

```python
class StreamEvent(BaseModel):
    event_type: Literal[
        "run_start", "step_start", "tool_call_start",
        "tool_call_result", "handoff", "step_end",
        "run_end", "error"
    ]
    run_id: str
    data: dict[str, Any]
    timestamp: datetime
    sequence_num: int  # monotonic, for ordering on reconnect
```

---

## POST /runs/{id}/cancel — Cancel a Run

### Response (200 OK)

```json
{
  "run_id": "run_x7k9m2",
  "status": "cancelled",
  "steps_completed": 3,
  "reason": "user_requested"
}
```

**WHY**: Long-running or stuck runs need a kill switch. Cancellation signals the Temporal workflow to terminate gracefully (finish current activity, skip remaining).

---

## GET /configs/{type}/{version} — Fetch Agent Config

### Response (200 OK)

```json
{
  "config_id": "triage-agent",
  "version": 3,
  "agent_type": "supervisor",
  "model": "gpt-4o",
  "system_prompt": "You are a triage agent. Route to the appropriate specialist...",
  "tools": ["erp_lookup", "policy_search"],
  "handoff_targets": ["invoice-specialist", "refund-specialist"],
  "output_schema": "InvoiceTriageOutput_v2",
  "max_steps": 10,
  "created_at": "2025-01-10T08:00:00Z",
  "created_by": "team-finance"
}
```

```python
class AgentConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    config_id: str
    version: int
    agent_type: Literal["supervisor", "specialist", "verifier"]
    model: str
    system_prompt: str
    tools: list[str] = []
    handoff_targets: list[str] = []
    output_schema: str | None = None
    max_steps: int = Field(default=25, ge=1, le=100)
    created_at: datetime
    created_by: str
```

**WHY versioned + immutable**: A running run must use the exact config it started with. Immutable versions prevent mid-run config changes from causing inconsistent behavior.

---

## Error Cases

### Schema Validation Failure (422)
```json
{
  "error": "validation_error",
  "message": "input.context.customer_id: string required, got int",
  "details": [
    {"field": "input.context.customer_id", "type": "string_type", "msg": "Input should be a valid string"}
  ]
}
```
**WHY**: Pydantic strict mode catches type mismatches at the API boundary, not deep inside execution.

### Step Limit Exceeded (200 with error status)
```json
{
  "run_id": "run_x7k9m2",
  "status": "failed",
  "error": "step_limit_exceeded",
  "message": "Run reached max 25 steps without producing final output",
  "steps_completed": 25,
  "partial_output": {"last_agent": "invoice-specialist", "last_step": "..."}
}
```
**WHY**: Step limit is a safety net, not a client error — so it completes the run with a failure status rather than returning an HTTP error.

### Tool Timeout (streamed as error event)
```
event: error
data: {"step_id": "step_005", "error": "tool_timeout", "tool": "erp_lookup", "timeout_ms": 30000}
```
**WHY**: Tool timeouts are handled per-activity by Temporal. The platform retries per config, then emits an error event and lets the agent decide (skip, retry, fail).

---

## TL;DR (Interview Summary)
- **5 endpoints** total — minimal surface area for a run lifecycle
- **Pydantic strict mode** on all request/response models — catches type errors at the boundary
- **SSE** for streaming (not WebSocket) — simpler, HTTP-native, supports reconnect via `Last-Event-ID`
- **Idempotency key** on run creation — prevents duplicate runs on client retry
- **Immutable versioned configs** — a run always uses the exact config it started with
- **Step limit exceeded** returns as a completed run with failure status, not an HTTP error
- **Tool timeouts** handled by Temporal activities, surfaced as stream error events
