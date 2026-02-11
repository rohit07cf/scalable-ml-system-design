# Latency and Cost Tradeoffs


## 1. Why Latency and Cost Matter

- Every 100ms of latency in a user-facing LLM app increases abandonment
- Token-based pricing means cost scales linearly with usage -- no free margin
- GPU compute is expensive and finite -- poor utilization wastes money fast
- Enterprise budgets require predictable cost per user, per feature, per workflow
- Latency and cost often move in opposite directions -- optimizing one degrades the other


## 2. What Drives LLM Latency

- **Model size** -- larger models have more parameters to compute through per token
- **Output token count** -- generation is autoregressive; each token is a sequential step
- **KV cache growth** -- longer context means more memory reads per generated token
- **Context window size** -- more input tokens = longer prefill phase before generation starts
- **Retrieval overhead** -- RAG adds embedding lookup, vector search, and re-ranking before generation
- **Network overhead** -- API calls to external model providers add round-trip time
- **Cold starts** -- serverless or autoscaled GPU instances take seconds to load a model
- **GPU contention** -- shared GPU clusters queue requests; high load = high tail latency


## 3. What Drives LLM Cost

- **Input tokens** -- system prompt + user prompt + chat history + retrieved context; often the largest cost lever
- **Output tokens** -- generated response; priced higher than input tokens on most providers
- **Model tier** -- frontier models (GPT-4, Claude Opus) cost 10-50x more than smaller models
- **Context window usage** -- sending 100k tokens when 4k would suffice wastes money
- **Embedding calls** -- every document chunk and every query needs an embedding; volume adds up
- **Agent tool recursion** -- agents that loop, retry, or fan out multiply token spend per request
- **Long chat history** -- multi-turn conversations grow input tokens linearly with each turn
- **Re-ranking calls** -- cross-encoder re-rankers add a separate model call per retrieval

**Cost formula:**

```
cost = (input_tokens x input_rate) + (output_tokens x output_rate)
```

Input rate and output rate differ by model. Output tokens are typically 2-4x more expensive than input tokens.


## 4. Token-Level Tradeoffs

- Longer system prompts increase input tokens on every single request
- More detailed answers increase output tokens -- good for quality, bad for cost and latency
- Higher temperature can increase verbosity and output length unpredictably
- Streaming does NOT reduce total token cost -- it only changes delivery timing
- Prompt compression (removing examples, shortening instructions) directly reduces input cost
- Context truncation saves cost but risks losing relevant information


## 5. Model Size Tradeoffs

- Larger models produce higher quality output for complex reasoning tasks
- Larger models have higher per-token cost and higher latency per token
- Larger models require more GPU memory, limiting concurrent request capacity

**When to downshift to a smaller model:**

- Task is simple (classification, extraction, formatting)
- Latency budget is tight (sub-200ms)
- Volume is high and cost must stay low
- Quality difference between large and small model is negligible for the task

**When to use a mixture of models:**

- Route simple queries to a small model, complex queries to a large model
- Use a small model for first-pass filtering, large model for final generation
- Use a small model for summarization, large model for reasoning


## 6. Context Window Tradeoffs

- Long chat history sends the entire conversation as input tokens on every turn
- A 20-turn conversation can easily reach 10k+ input tokens per request
- 128k context windows are technically available but sending 128k tokens per request is expensive
- Context trimming (drop old turns) saves cost but loses conversational continuity
- Retrieval-based memory (fetch relevant past turns) balances cost and quality
- Summarization of history compresses context but loses detail

**Rule of thumb:** just because a model supports 128k tokens does not mean you should use 128k tokens.


## 7. RAG Latency vs Quality Tradeoffs

- **More chunks retrieved** -- better recall, but more tokens in context and higher latency
- **Larger chunk size** -- fewer retrieval calls, but each chunk may contain irrelevant content
- **Hybrid search (vector + BM25)** -- better accuracy than either alone, but two retrieval paths add latency
- **Re-ranking** -- significantly improves precision, but adds a separate model call (50-200ms)
- **Top-k tradeoff** -- higher k = better recall, lower k = faster and cheaper

**Typical RAG latency budget:**

| Stage | Typical Range |
|---|---|
| Query embedding | 10-30ms |
| Vector search | 20-50ms |
| BM25 search | 10-30ms |
| Re-ranking | 50-200ms |
| LLM generation | 500-3000ms |

Re-ranking and generation dominate the latency budget.


## 8. Batching vs Real-Time Tradeoffs

- **Dynamic batching** groups multiple requests into one GPU pass -- increases throughput
- **Batching increases latency** because each request waits for a batch to fill
- **Best for non-interactive workloads** -- batch summarization, offline eval, bulk embedding
- **GPU utilization improves** with batching -- more tokens processed per second per GPU
- **Not suitable for chat** -- users expect immediate response, not queued processing

| Mode | Throughput | Latency | Use Case |
|---|---|---|---|
| Real-time | Lower | Low | Chat, interactive |
| Batched | Higher | Higher | Offline, bulk |
| Continuous batching | High | Moderate | Serving frameworks (vLLM) |


## 9. Streaming Tradeoffs

- **Improves perceived latency** -- user sees tokens appearing immediately
- **Does not reduce total latency** -- the full response still takes the same wall-clock time
- **Does not reduce token cost** -- same number of tokens generated regardless of delivery mode
- **Useful for chat UX** -- gives the user something to read while generation continues
- **Complicates error handling** -- errors mid-stream are harder to recover from than batch errors
- **Complicates evaluation** -- harder to score a partial stream than a complete response


## 10. GPU vs CPU vs Edge Tradeoffs

| Dimension | GPU | CPU | Edge |
|---|---|---|---|
| Throughput | High | Low | Very low |
| Cost | High | Low | Hardware-dependent |
| Latency | Low (for large models) | High (for large models) | Low (for small models) |
| Model size | Any | Small to medium | Small only |
| Scaling | Vertical (bigger GPU) or horizontal | Horizontal (many cores) | Per-device |
| Best for | LLM inference, training | ONNX/small models, embedding | On-device, offline, privacy |

**Decision shortcuts:**

- Large LLM (7B+) -- GPU required
- Embedding models / small classifiers -- CPU is often sufficient
- Privacy-sensitive or offline -- edge with quantized small model
- High QPS with small model -- CPU fleet may be cheaper than GPU


## 11. Throughput vs Latency

- High throughput systems use batching, queuing, and GPU saturation
- Low latency systems avoid batching, use dedicated resources, and minimize queue depth
- You cannot fully optimize both -- more batching = more throughput but higher p99 latency
- Continuous batching (vLLM, TensorRT-LLM) is the best compromise for LLM serving
- SLA-driven systems define latency targets first, then optimize throughput within that constraint


## 12. Scaling Strategies

- **Cache responses** -- identical queries get cached results; eliminates redundant LLM calls
- **Cache embeddings** -- avoid re-embedding the same document or query
- **Prompt compression** -- shorter prompts reduce input tokens across all requests
- **Smaller model fallback** -- route simple tasks to cheaper models automatically
- **Two-stage inference** -- small model classifies/filters, large model handles complex cases only
- **Request prioritization** -- serve paying users on faster path, deprioritize background jobs
- **Token budget enforcement** -- hard cap on tokens per request, per user, per workflow
- **Horizontal scaling** -- add more replicas behind a load balancer for throughput
- **Autoscaling** -- scale GPU instances based on queue depth, not just CPU utilization


## 13. Common Failure Patterns

- **Token explosion from recursive agents** -- an agent retries or fans out, each call multiplies cost
- **Context window blow-up** -- chat history or retrieved chunks exceed the window, causing truncation or errors
- **Silent cost spike from prompt change** -- a small prompt edit adds 200 tokens, costs compound at scale
- **Long outputs from high temperature** -- verbose, repetitive generation inflates output tokens
- **Retrieval drift increasing latency** -- embedding or index degradation causes more retrieval retries
- **Cold start cascades** -- sudden traffic spike hits scaled-down cluster; all requests queue behind model loading
- **Unmonitored embedding calls** -- high-volume embedding requests silently accumulate cost


## 14. Interview Q&A

**Why is output token count the main driver of LLM latency?**
Generation is autoregressive -- each token depends on all previous tokens. More output tokens = more sequential steps. Input tokens are processed in parallel during prefill, but output is inherently sequential.

**How would you reduce LLM cost in production?**
Shorten system prompts, cache frequent queries, route simple tasks to smaller models, truncate chat history or use retrieval-based memory, set token budgets per request, and compress retrieved context before sending to the LLM.

**Why does RAG increase latency compared to a direct LLM call?**
RAG adds embedding, vector search, optional BM25, optional re-ranking, and context assembly before the LLM call. Each step adds 10-200ms. The total pipeline is typically 100-500ms longer than a standalone LLM call.

**When would you use a smaller model instead of a frontier model?**
When the task is simple (classification, extraction, formatting), latency is critical, volume is high, or the quality gap between small and large models is negligible for the specific use case.

**How would you monitor cost spikes?**
Log input/output tokens per request with model ID, prompt version, and user/tenant. Aggregate cost per feature and per user. Set threshold alerts on daily cost and per-request token counts. Watch for recursive agent loops.

**What is the difference between latency and throughput?**
Latency is time per request. Throughput is requests per second. Batching improves throughput but increases latency. Dedicated resources reduce latency but may lower throughput efficiency.

**Why does streaming not reduce cost?**
Streaming changes when tokens are delivered to the client, not how many tokens are generated. The model still produces the same output tokens. Cost is based on total token count, not delivery timing.

**How do you handle the cost of long chat history?**
Truncate older turns, summarize history into a compact block, use retrieval-based memory to fetch only relevant past turns, or set a hard cap on input tokens per request.

**What is continuous batching and why does it matter?**
Continuous batching (used by vLLM, TensorRT-LLM) adds new requests to an in-flight batch as slots free up, instead of waiting for the entire batch to finish. It improves both throughput and latency compared to static batching.

**How do you decide between GPU and CPU for inference?**
Large LLMs (7B+) need GPUs. Small models (embeddings, classifiers, quantized models under 1B) can run on CPU cost-effectively. Decision depends on model size, latency requirements, and cost constraints.

**What happens when an agent recurses without a token budget?**
Each iteration calls the LLM again, accumulating input and output tokens. Without a cap, a looping agent can spend hundreds of thousands of tokens in minutes. Always set max iterations and per-request token budgets.

**How would you design a two-stage inference pipeline?**
First stage: small fast model classifies the request (simple vs complex). Simple requests go to a small model. Complex requests go to a large model. This reduces average cost while maintaining quality where it matters.


## 15. Fast Revision Summary

- Output tokens drive latency (sequential generation); input tokens drive cost (sent on every request)
- cost = (input_tokens x input_rate) + (output_tokens x output_rate)
- Streaming improves perceived latency but does not reduce cost or total latency
- Batching increases throughput but increases per-request latency
- RAG adds 100-500ms (embedding + search + rerank) before the LLM call
- Route simple tasks to small models; reserve large models for complex reasoning
- Long chat history grows input tokens linearly -- truncate, summarize, or retrieve
- Recursive agents without token budgets are the fastest path to cost explosion
- Cache responses, cache embeddings, compress prompts -- cheapest token is the one not sent
- Monitor tokens per request, cost per feature, and alert on spikes
