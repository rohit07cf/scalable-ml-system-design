# Reliability Patterns


## 1. Why Reliability Matters for LLM Systems

- LLM calls are expensive -- a single failed batch job can waste hundreds of dollars in tokens
- LLM providers are external dependencies -- you do not control their uptime, latency, or rate limits
- LLM output is non-deterministic -- the same input can produce different outputs, making failures harder to detect
- GPU resources are scarce and shared -- one bad workload can starve others
- Token costs scale with usage -- a runaway loop or prompt regression can spike costs in minutes
- Enterprise customers expect SLAs -- 99.9% uptime means less than 8.7 hours of downtime per year

Reliability in LLM systems is not optional. It is the difference between a demo and a product.


## 2. Common Failure Modes in LLM Systems

- **Model API timeout** -- provider takes too long; request hangs or times out
- **Rate limit errors (429)** -- provider throttles you; requests rejected until quota resets
- **GPU OOM** -- model or batch too large for available GPU memory; job crashes
- **Token explosion** -- prompt or agent loop generates excessive tokens; cost and latency spike
- **Retrieval failure** -- vector database or search service is down; RAG pipeline returns no context
- **Tool failure in agents** -- an external tool call fails mid-chain; agent enters undefined state
- **Partial streaming failure** -- connection drops during streamed response; user sees incomplete output
- **Network failure** -- DNS, TLS, or connectivity issues between services
- **Prompt regression** -- a prompt change causes worse output quality, higher cost, or new failure modes

Each of these needs a specific mitigation strategy. Generic error handling is not enough.


## 3. Retry Patterns

**Exponential backoff:**

- Wait 1s, 2s, 4s, 8s between retries
- Prevents hammering a struggling service
- Gives the downstream system time to recover

**Jitter:**

- Add random delay to each retry interval
- Prevents thundering herd -- many clients retrying at the exact same time
- Without jitter, synchronized retries can amplify the original failure

**Retry limits:**

- Always set a max retry count (typically 3-5)
- Retrying forever wastes resources and delays failure detection
- After max retries, fail explicitly and alert

**When to retry:**

- 429 (rate limit) -- yes, with backoff
- 500/502/503 (server error) -- yes, with backoff
- Timeout -- yes, with backoff
- Network error -- yes, with backoff

**When NOT to retry:**

- 400 (bad request) -- your input is wrong; retrying won't help
- 401/403 (auth error) -- credentials are wrong; retrying won't help
- 413 (payload too large) -- input exceeds limits; retrying won't help
- Any deterministic error -- same input will produce the same failure


## 4. Idempotency

**Why duplicate requests happen:**

- Client retries after a timeout, but the first request actually succeeded
- Network failure after server processes but before client receives response
- Queue delivers the same message twice (at-least-once delivery)

**Idempotency keys:**

- Attach a unique key (UUID) to each request
- Server checks if it has already processed that key
- If yes, return the cached result instead of reprocessing
- Prevents duplicate side effects (double charges, duplicate jobs)

**LLM-specific examples:**

- Prevent duplicate fine-tuning job submissions -- same idempotency key rejects the duplicate
- Prevent duplicate embedding ingestion -- same document ID skips re-processing
- Prevent duplicate tool calls in agent loops -- track call IDs to detect repeated actions

**Rule of thumb:** any operation that costs money, changes state, or triggers external calls should be idempotent.


## 5. Circuit Breakers

- Monitors error rate of calls to a downstream service
- When error rate exceeds threshold, the circuit "opens" -- all subsequent calls fail fast without reaching the downstream
- After a cooldown period, the circuit enters "half-open" -- allows a small number of test requests
- If test requests succeed, the circuit "closes" -- normal traffic resumes
- If test requests fail, the circuit stays open

**Why this matters for LLM systems:**

- Prevents cascading failures when the LLM provider is down
- Stops wasting money on requests that will fail
- Frees up resources for fallback behavior (cached responses, degraded mode)
- Protects your rate limit quota from being consumed by failing requests

**Key settings:**

- Error rate threshold (e.g., 50% errors in last 60 seconds)
- Cooldown duration (e.g., 30 seconds before half-open)
- Test request count (e.g., 3 requests in half-open state)


## 6. Rate Limiting and Throttling

**Why rate limiting matters:**

- Protects your GPU pool from being overloaded by a single tenant or feature
- Prevents exceeding external LLM API quotas
- Controls cost by limiting total token throughput
- Ensures fair access across tenants

**Types of rate limits:**

- **Request-based** -- max N requests per minute per tenant
- **Token-based** -- max N tokens per minute per tenant (more relevant for LLM systems)
- **Concurrency-based** -- max N simultaneous in-flight requests
- **Cost-based** -- max $N spend per hour per tenant

**Token-based rate limiting:**

- More accurate than request-based for LLM systems -- one request with 10k tokens costs 100x more than one with 100 tokens
- Estimate input tokens before sending (tokenizer count)
- Track output tokens from response metadata
- Enforce limits on the sum of input + output tokens

**Implementation:**

- Token bucket or sliding window algorithms
- Per-tenant tracking in Redis or similar fast store
- Return 429 with Retry-After header when limit exceeded


## 7. Backpressure and Queueing

**The problem:**

- LLM inference is slow (seconds, not milliseconds)
- Burst traffic can overwhelm GPU pools or exhaust API rate limits
- Without backpressure, requests pile up, memory grows, and the system crashes

**Backpressure strategies:**

- **Queue-based** -- put requests in a durable queue (Kafka, Redis, SQS); workers pull at their own pace
- **Concurrency control** -- limit in-flight requests with semaphores or worker pools
- **Load shedding** -- drop low-priority requests when overloaded rather than degrading everything
- **Admission control** -- reject requests at the gateway when queue depth exceeds threshold

**Where queues appear in LLM systems:**

- GPU training job queues -- batch fine-tuning jobs processed sequentially
- RAG ingestion queues -- documents queued for chunking and embedding
- Agent task queues -- multi-step agent actions queued to limit concurrency
- Evaluation queues -- model eval jobs queued behind production inference

**Key metric:** queue depth. Rising queue depth = system cannot keep up. Alert on it.


## 8. Timeout Management

**Why timeouts matter:**

- LLM inference can take 5-60+ seconds depending on output length
- Without timeouts, a stuck request holds resources indefinitely
- Zombie tasks consume GPU slots, memory, and connection pool entries

**Timeout layers:**

- **Client timeout** -- how long the caller waits for a response (e.g., 30s)
- **LLM inference timeout** -- max time for the model to generate a response (e.g., 45s)
- **Tool call timeout** -- max time for an external tool in an agent chain (e.g., 10s)
- **Workflow activity timeout** -- max time for a single step in an orchestrated pipeline (e.g., 60s)
- **End-to-end timeout** -- total budget for the entire request across all steps (e.g., 120s)

**Best practices:**

- Set timeouts at every boundary, not just the outermost
- Inner timeouts must be shorter than outer timeouts
- Log timeout events with context (which step, how long, what input)
- Timed-out LLM requests may still complete on the provider side and cost tokens


## 9. Caching for Reliability

**What to cache:**

- **LLM responses** -- cache exact prompt-response pairs for repeated queries (semantic or exact match)
- **Embeddings** -- cache computed embeddings to avoid recomputation on repeated documents
- **Retrieval results** -- cache search results for common queries to reduce vector DB load
- **Tool call results** -- cache deterministic tool outputs (e.g., API lookups)

**Cache as fallback:**

- When the LLM provider is down, serve cached responses for common queries
- Stale cache is often better than no response
- Mark cached responses so downstream consumers know the data is not fresh

**Cache invalidation:**

- Time-based TTL for LLM responses (e.g., 1 hour for factual queries)
- Version-based invalidation when prompts or models change
- Embedding caches must be fully rebuilt when switching embedding models

**Trade-off:** caching reduces cost and improves reliability, but cached responses may be stale or miss personalization.


## 10. Observability and Monitoring

**Request-level metrics:**

- Request latency (p50, p95, p99) -- broken down by model, endpoint, tenant
- Token usage per request (input tokens, output tokens)
- Error rate by type (timeout, rate limit, server error, client error)
- Retry count per request

**System-level metrics:**

- Queue depth per queue
- GPU utilization and memory usage
- Connection pool usage
- Active in-flight requests

**Cost metrics:**

- Token spend per hour, per tenant, per feature
- Cost per request (input tokens x input price + output tokens x output price)
- Cost anomaly detection -- alert when spend exceeds baseline by a threshold

**Alerting rules:**

- Error rate exceeds X% for Y minutes
- p99 latency exceeds threshold
- Queue depth exceeds threshold
- Token spend exceeds hourly budget
- GPU memory utilization exceeds 90%

**Structured logging:**

- Log every LLM call with: model, input tokens, output tokens, latency, status, tenant ID
- Correlation IDs across services for end-to-end tracing
- Log prompt templates (not user data) for debugging prompt regressions


## 11. Temporal Reliability Patterns

**Why Temporal (or similar orchestration):**

- LLM pipelines are multi-step -- embedding, retrieval, generation, post-processing
- Any step can fail, and the pipeline must recover without restarting from scratch
- Temporal provides durable execution -- workflow state survives crashes

**Key patterns:**

- **Activity retries** -- each step (activity) has its own retry policy; a failed LLM call retries independently
- **Workflow retries** -- the entire workflow can be retried from the beginning if needed
- **Checkpointing** -- Temporal records the result of each completed activity; on restart, completed steps are skipped
- **Heartbeats** -- long-running activities (e.g., fine-tuning) send periodic heartbeats; if heartbeat stops, Temporal detects the failure
- **Dead-letter queues** -- permanently failed workflows are routed to a DLQ for manual review instead of being silently dropped

**Resume from failure:**

- If step 3 of 5 fails, Temporal re-executes only step 3 (and beyond) using cached results from steps 1-2
- No duplicate side effects if activities are idempotent
- This is the foundation of reliable multi-step LLM pipelines

**Long-running workflow safety:**

- Set workflow execution timeouts to prevent infinite workflows
- Set activity start-to-close timeouts to prevent zombie activities
- Use heartbeat timeouts to detect stuck long-running tasks


## 12. Multi-Tenant Isolation

**The noisy neighbor problem:**

- One tenant sends a massive batch of long-context requests
- This consumes GPU capacity, rate limit quota, and queue slots
- Other tenants experience degraded latency or failures

**Isolation strategies:**

- **Separate token budgets** -- each tenant has an independent token-per-minute limit
- **Separate rate limits** -- per-tenant request rate limits enforced at the gateway
- **Job isolation** -- tenant jobs run in separate queues or worker pools
- **Priority tiers** -- high-priority tenants get dedicated capacity; best-effort tenants share the rest
- **Fair scheduling** -- round-robin or weighted fair queuing across tenants

**What to track per tenant:**

- Token usage (input + output)
- Request count and error rate
- Queue depth and wait time
- Cost accumulation

**Rule of thumb:** if tenants share infrastructure, every shared resource needs per-tenant limits.


## 13. Common Production Failures

**Token runaway loop in agent:**
Agent calls a tool, gets a large response, includes it in the next prompt, which triggers an even larger response. Tokens grow exponentially. Mitigation: cap max tokens per turn, cap total turns, monitor token count per request.

**RAG retrieval latency spike:**
Vector database query takes 5 seconds instead of 200ms. Entire pipeline times out. Mitigation: timeout on retrieval, fallback to cached results or no-context generation.

**Model API outage:**
LLM provider returns 503 for 10 minutes. All requests fail. Mitigation: circuit breaker, fallback to cached responses, secondary model provider.

**Prompt update causing cost spike:**
New system prompt is 3x longer. Token cost triples overnight. Mitigation: monitor token usage per prompt version, set cost alerts, review prompt changes like code changes.

**GPU node crash mid-training:**
Fine-tuning job loses 6 hours of progress. Mitigation: checkpoint every N steps, resume from last checkpoint, use orchestration with heartbeats.

**Queue backlog explosion:**
Ingestion queue grows to 500k messages during a bulk upload. Workers cannot keep up. Mitigation: backpressure at the producer, scale workers, drop or delay low-priority items.


## 14. Interview Q&A

**How would you prevent duplicate fine-tuning jobs?**
Use idempotency keys. Each job submission includes a unique key. The system checks if a job with that key already exists before creating a new one. Duplicates return the existing job ID.

**What happens if the LLM API goes down?**
Circuit breaker trips after error threshold is reached. Requests fail fast without hitting the provider. System serves cached responses or degrades gracefully. Alert fires for on-call response.

**How do you protect the GPU pool from overload?**
Per-tenant rate limits on tokens and requests. Concurrency limits on in-flight inference jobs. Queue-based admission control to absorb bursts. Load shedding for low-priority traffic when utilization is high.

**Why use exponential backoff with jitter?**
Exponential backoff gives the failing service time to recover. Jitter prevents thundering herd -- without it, all clients retry at the same instant, re-creating the overload.

**How does Temporal improve reliability for LLM pipelines?**
Temporal provides durable execution with checkpointing. If step 3 of a 5-step pipeline fails, it retries only step 3 using cached results from steps 1-2. No duplicate work, no lost progress.

**How would you prevent token explosion in an agent?**
Cap max tokens per turn. Cap total conversation turns. Monitor cumulative token count. If token budget is exceeded, force-terminate the loop and return partial results or an error.

**How do you handle the noisy neighbor problem?**
Per-tenant token budgets, rate limits, and queue isolation. Fair scheduling ensures one tenant cannot starve others. Monitor per-tenant usage and alert on anomalies.

**What is the difference between a timeout and a circuit breaker?**
A timeout protects a single request from waiting too long. A circuit breaker protects the system from repeatedly calling a failing service. Timeouts are per-request; circuit breakers are per-service over a window of time.

**How would you cache LLM responses safely?**
Cache by exact prompt hash with a TTL. Invalidate when the prompt template or model version changes. Mark cached responses so consumers know the output is not fresh. Use cache as fallback during provider outages.

**Why is token-based rate limiting better than request-based for LLM systems?**
Requests vary wildly in cost. A 100-token request and a 10k-token request are not equivalent. Token-based limits align rate limiting with actual resource consumption and cost.

**What do you monitor in a production LLM system?**
Latency (p50, p95, p99), token usage per request, error rate by type, retry count, queue depth, GPU utilization, and cost per tenant per feature. Alert on deviations from baseline.

**How do you resume a failed multi-step LLM pipeline?**
Use an orchestration framework like Temporal. Each step's result is checkpointed. On failure, the pipeline restarts from the failed step, not from the beginning. Activities must be idempotent.


## 15. Fast Revision Summary

- LLM calls are expensive and non-deterministic -- every failure costs money and is hard to reproduce
- Retry with exponential backoff and jitter; never retry deterministic errors (400, 401, 413)
- Use idempotency keys for any operation that costs money or changes state
- Circuit breakers prevent cascading failures when the LLM provider is down
- Token-based rate limiting is more accurate than request-based for LLM systems
- Queues absorb bursts; monitor queue depth and alert when it grows
- Set timeouts at every boundary; inner timeouts must be shorter than outer timeouts
- Cache LLM responses and embeddings; use cache as fallback during outages
- Monitor latency, token usage, error rates, queue depth, GPU utilization, and cost per tenant
- Temporal provides checkpointing and durable execution for multi-step LLM pipelines
