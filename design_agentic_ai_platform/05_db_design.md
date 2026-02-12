# Phase 5 — Database Design

## Overview

- **PostgreSQL** = source of truth for all durable data (runs, steps, tool calls, configs)
- **Redis** = ephemeral hot state (current run status, pub/sub, idempotency keys)
- **WHY split**: PostgreSQL for durability + audit; Redis for low-latency operational data that can be rebuilt from PostgreSQL

---

## Tables

### 1. Runs

```sql
CREATE TABLE runs (
    run_id          TEXT PRIMARY KEY,          -- e.g., "run_x7k9m2"
    config_id       TEXT NOT NULL,             -- e.g., "triage-agent"
    config_version  INT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
                    -- enum: queued | running | completed | failed | cancelled
    input           JSONB NOT NULL,            -- user input payload
    output          JSONB,                     -- final structured output (nullable until complete)
    error           TEXT,                      -- error message if failed
    steps_completed INT NOT NULL DEFAULT 0,
    tokens_used     INT NOT NULL DEFAULT 0,
    max_steps       INT NOT NULL DEFAULT 25,
    max_tokens      INT NOT NULL DEFAULT 50000,
    idempotency_key TEXT UNIQUE,               -- dedup key (24h window)
    team_id         TEXT NOT NULL,             -- owning team
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**WHY JSONB for input/output**: Agent inputs and outputs vary by config; JSONB avoids schema coupling while still allowing indexed queries.

### 2. Steps (The Ledger / "Tape")

```sql
CREATE TABLE steps (
    step_id         TEXT PRIMARY KEY,          -- e.g., "step_001"
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    step_number     INT NOT NULL,              -- 1-indexed, monotonic per run
    agent_id        TEXT NOT NULL,             -- which agent executed this step
    step_type       TEXT NOT NULL,
                    -- enum: plan | tool_call | handoff | final_output | error
    input_context   JSONB,                     -- LLM input (messages array snapshot)
    llm_response    JSONB,                     -- raw LLM response
    output          JSONB,                     -- parsed result (tool result or final output)
    tokens_input    INT NOT NULL DEFAULT 0,
    tokens_output   INT NOT NULL DEFAULT 0,
    latency_ms      INT,                       -- wall-clock time for this step
    status          TEXT NOT NULL DEFAULT 'running',
                    -- enum: running | completed | failed | skipped
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,

    UNIQUE (run_id, step_number)               -- enforce ordering within a run
);
```

**WHY input_context snapshot**: Enables replay — given the context at each step, you can re-run the LLM call and compare outputs for debugging.

### 3. ToolCalls

```sql
CREATE TABLE tool_calls (
    tool_call_id    TEXT PRIMARY KEY,          -- e.g., "tc_a3f8"
    step_id         TEXT NOT NULL REFERENCES steps(step_id),
    run_id          TEXT NOT NULL,             -- denormalized for fast queries
    tool_name       TEXT NOT NULL,             -- e.g., "erp_lookup"
    tool_input      JSONB NOT NULL,            -- arguments passed to tool
    tool_output     JSONB,                     -- result from tool (nullable until complete)
    status          TEXT NOT NULL DEFAULT 'running',
                    -- enum: running | completed | failed | timeout
    validation_ok   BOOLEAN,                   -- Pydantic validation passed?
    retry_count     INT NOT NULL DEFAULT 0,
    latency_ms      INT,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
```

**WHY separate from steps**: A single step can trigger multiple tool calls (parallel tool use); separate table keeps the model clean and allows per-tool-call metrics.

### 4. StreamEvents (Optional — for replay)

```sql
CREATE TABLE stream_events (
    event_id        BIGSERIAL PRIMARY KEY,     -- monotonic sequence
    run_id          TEXT NOT NULL,
    event_type      TEXT NOT NULL,
                    -- enum: run_start | step_start | tool_call_start |
                    --        tool_call_result | handoff | step_end |
                    --        run_end | error
    payload         JSONB NOT NULL,
    sequence_num    INT NOT NULL,              -- per-run sequence for ordering
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (run_id, sequence_num)
);
```

**WHY optional**: Primary streaming path is Redis pub/sub (ephemeral). This table is only needed if you want to replay streams for debugging or re-deliver events after a client disconnect. Can be enabled per-team.

### 5. ConfigVersions

```sql
CREATE TABLE config_versions (
    config_id       TEXT NOT NULL,             -- e.g., "triage-agent"
    version         INT NOT NULL,
    agent_type      TEXT NOT NULL,             -- supervisor | specialist | verifier
    model           TEXT NOT NULL,             -- e.g., "gpt-4o"
    system_prompt   TEXT NOT NULL,
    tools           JSONB NOT NULL DEFAULT '[]',
    handoff_targets JSONB NOT NULL DEFAULT '[]',
    output_schema   TEXT,                      -- Pydantic model name for validation
    max_steps       INT NOT NULL DEFAULT 25,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      TEXT NOT NULL,             -- team or user that created this version
    is_active       BOOLEAN NOT NULL DEFAULT true,

    PRIMARY KEY (config_id, version)
);
```

**WHY immutable versions**: A running run pins `config_version` at start. Even if a team publishes v8, runs started on v7 continue using v7. No mid-run behavior changes.

---

## Indexing Strategy

```sql
-- Runs: query by status (dashboard), team (access control), time (retention)
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_team_created ON runs(team_id, created_at DESC);
CREATE INDEX idx_runs_created_at ON runs(created_at);  -- retention cleanup
CREATE INDEX idx_runs_idempotency ON runs(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Steps: always queried by run_id; ordered by step_number
CREATE INDEX idx_steps_run_id ON steps(run_id, step_number);
CREATE INDEX idx_steps_status ON steps(status) WHERE status = 'failed';  -- partial: find failures

-- ToolCalls: query by run_id (debugging), tool_name (analytics)
CREATE INDEX idx_tool_calls_run_id ON tool_calls(run_id);
CREATE INDEX idx_tool_calls_step_id ON tool_calls(step_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name, created_at DESC);

-- StreamEvents: query by run_id + sequence for replay
CREATE INDEX idx_stream_events_run ON stream_events(run_id, sequence_num);

-- Configs: query by config_id (latest version), active status
CREATE INDEX idx_configs_active ON config_versions(config_id, version DESC) WHERE is_active = true;
```

**WHY partial indexes**: `WHERE status = 'failed'` index is tiny (most steps succeed) but critical for failure dashboards.

---

## Read/Write Paths

### Write Path (during run execution)

```
1. Run starts     → INSERT INTO runs (status: queued)
2. Each step      → INSERT INTO steps
3. Each tool call → INSERT INTO tool_calls
4. Each event     → PUBLISH to Redis pub/sub (+ optional INSERT INTO stream_events)
5. Run ends       → UPDATE runs SET status, output, completed_at
```

- **Write frequency**: ~6 steps/run × 0.35 runs/sec = ~2 writes/sec (trivial for PostgreSQL)
- Steps and tool calls are **append-only** (never updated after completion)
- Run row updated only: `queued → running`, `running → completed/failed/cancelled`

### Read Path

| Query | Table | Index | Frequency |
|---|---|---|---|
| Get run status | runs | PK (run_id) | Every poll (~1/sec per active run) |
| Get run steps | steps | idx_steps_run_id | On-demand (debug UI) |
| List team runs | runs | idx_runs_team_created | Dashboard (~1/min) |
| Get failed steps | steps | idx_steps_status (partial) | Alert/dashboard |
| Replay stream | stream_events | idx_stream_events_run | On-demand (rare) |
| Get latest config | config_versions | idx_configs_active | At run start |

**Hot-path optimization**: Run status is also cached in Redis (updated on each step). The `GET /runs/{id}` endpoint reads Redis first, falls back to PostgreSQL.

---

## Retention Policy

| Data | Retention | Strategy |
|---|---|---|
| Runs | 90 days | Auto-delete via `pg_cron` job on `created_at` |
| Steps | 90 days | Cascade delete with runs |
| ToolCalls | 90 days | Cascade delete with steps |
| StreamEvents | 30 days | Shorter retention (replay rarely needed after 30d) |
| ConfigVersions | Indefinite | Never delete (audit trail for what config a run used) |

- **WHY 90 days**: Balances audit needs with storage cost (~32 GB at 90 days is manageable)
- **WHY configs indefinite**: A compliance query like "what prompt did run X use?" requires the config to exist even after the run is deleted — so we keep a FK reference but the config row persists

---

## Entity Relationship Diagram

```
┌──────────────────┐
│  config_versions │
│  (config_id, ver)│──────────────────────────┐
└──────────────────┘                          │
                                              │ pinned at run start
┌──────────────────┐                          │
│  runs            │◄─────────────────────────┘
│  (run_id) PK     │
└────────┬─────────┘
         │ 1:N
         ▼
┌──────────────────┐
│  steps           │
│  (step_id) PK    │
│  run_id FK       │
└────────┬─────────┘
         │ 1:N
         ▼
┌──────────────────┐       ┌──────────────────┐
│  tool_calls      │       │  stream_events   │
│  (tool_call_id)  │       │  (event_id)      │
│  step_id FK      │       │  run_id          │
│  run_id          │       └──────────────────┘
└──────────────────┘
```

---

## TL;DR (Interview Summary)
- **5 tables**: runs, steps (ledger), tool_calls, stream_events (optional), config_versions
- **Steps are append-only** — the ledger is immutable for audit and replay
- **JSONB** for input/output/context — avoids schema coupling across diverse agent configs
- **Partial indexes** on failure status for fast debugging queries
- **Redis caches hot state** (run status, token counts); PostgreSQL is source of truth
- **90-day retention** for runs/steps; configs kept indefinitely for compliance
- **~2 writes/sec** at peak — single PostgreSQL instance handles this without sharding
