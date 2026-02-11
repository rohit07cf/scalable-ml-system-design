# Evaluation Basics


## 1. Why Evaluation Matters

- LLMs are non-deterministic -- same prompt can produce different outputs
- Hallucination is silent -- models confidently generate false information
- Prompt sensitivity -- small wording changes can shift quality dramatically
- Model drift -- behavior changes over time as providers update models
- Cost explosion -- unmonitored token usage leads to surprise bills

Without structured evaluation, you are flying blind in production.


## 2. Evaluation Types

- **Offline evaluation** -- run against held-out datasets before deployment; fast, cheap, controlled
- **Online evaluation** -- measure on live traffic via A/B tests or shadow mode; high signal, higher risk
- **Human evaluation** -- domain experts rate outputs; most reliable, least scalable
- **LLM-as-a-judge** -- use a separate LLM to score outputs; scalable proxy for human judgment
- **Automated metrics** -- BLEU, ROUGE, exact match; fast but often weakly correlated with quality


## 3. Core Metrics for LLMs

- **Accuracy** -- useful for classification tasks; less meaningful for open-ended generation
- **BLEU / ROUGE** -- measure n-gram overlap with references; cheap but shallow for LLM output
- **Perplexity** -- how surprised the model is by text; useful for model comparison, not answer quality
- **Latency** -- time to first token and total response time; directly affects user experience
- **Token usage** -- input + output tokens per request; primary driver of cost and latency
- **Cost per request** -- computed from token counts and model pricing; must track per feature
- **Safety violations** -- toxic, biased, or off-policy outputs; track rate over time
- **Response consistency** -- variance across repeated identical prompts; high variance signals instability


## 4. RAG-Specific Evaluation

- **Retrieval accuracy** -- did the retriever return the right documents?
- **Context relevance** -- are the retrieved chunks actually useful for answering the question?
- **Faithfulness** -- does the generated answer stay grounded in the retrieved context?
- **Answer groundedness** -- can every claim in the answer be traced back to a source chunk?
- **Chunk quality** -- are chunks the right size and boundary to carry coherent meaning?
- **Embedding drift** -- have the embeddings shifted enough that retrieval quality degrades?
- **Recall vs precision tradeoff** -- retrieving more chunks increases recall but adds noise and cost


## 5. Ragas Framework

### What It Is

Ragas is an open-source framework for evaluating RAG pipelines.
It provides reference-free metrics -- you do not need ground-truth answers for most evaluations.

### Why It Matters

- Standard metrics (BLEU, ROUGE) do not capture retrieval + generation quality together
- Ragas evaluates the full RAG pipeline: retrieval quality and generation faithfulness
- Gives structured scores without expensive human annotation

### Key Metrics

**Context Precision**
- Of the retrieved chunks, how many were actually relevant?
- High precision = low noise in context window

**Context Recall**
- Of all relevant chunks in the corpus, how many were retrieved?
- High recall = fewer missed answers

**Faithfulness**
- Does the generated answer contain only claims supported by the retrieved context?
- Low faithfulness = hallucination

**Answer Relevancy**
- Is the generated answer actually relevant to the original question?
- Catches correct-but-off-topic responses

### How It Works

1. Takes a question, retrieved contexts, and generated answer as input
2. Uses an LLM to decompose the answer into individual claims
3. Checks each claim against the context for support
4. Aggregates into per-metric scores (0 to 1)

### When to Use

- Evaluating RAG pipeline changes (chunking strategy, retriever swap, prompt edits)
- Regression testing before deploying new prompt versions
- Comparing retriever configurations (top-k, hybrid vs dense)

### Limitations

- Relies on an LLM for scoring -- subject to that LLM's own biases
- Scores can vary across runs due to LLM non-determinism
- Does not replace domain-expert evaluation for high-stakes use cases
- Context window limits constrain how many chunks can be evaluated at once

### How to Explain Ragas in Interviews

- "Ragas provides reference-free metrics for RAG -- it scores retrieval and generation without needing gold labels"
- "The four key metrics are context precision, context recall, faithfulness, and answer relevancy"
- "It uses an LLM to decompose answers into claims and verify each against retrieved context"
- "I use it for regression testing when I change chunking, retrieval, or prompt templates"
- "It is a scalable proxy -- not a replacement for human eval in high-stakes domains"


## 6. Offline vs Online Evaluation

| Dimension | Offline | Online |
|---|---|---|
| Environment | Controlled test sets | Real user traffic |
| Cost | Low | Higher (infra + risk) |
| Iteration speed | Fast | Slow (need traffic volume) |
| Realism | Limited | High |
| Risk | None | Can degrade user experience |
| Signal quality | Moderate | Strong |
| Use case | Pre-deploy gating | Post-deploy validation |

**Use both.** Offline catches regressions early. Online catches what offline misses.


## 7. Evaluation in Production


### 7.1 Continuous Evaluation

- Run scheduled eval jobs against golden datasets (daily or per-deploy)
- Track prompt regression scores across model and prompt versions
- Monitor RAG quality metrics (faithfulness, retrieval recall) as a time series
- Compare performance trends week-over-week to catch gradual degradation

LLM behavior drifts because:
- Upstream model providers silently update weights
- User input distributions shift over time
- Chat history grows, changing prompt structure


### 7.2 Canary Releases

- Route 1-5% of traffic to the new model/prompt version
- Compare against baseline on: quality scores, token usage, hallucination rate, latency
- Set automated rollback triggers (e.g., faithfulness drops >5%)
- Only promote to full traffic after canary passes for a defined window
- Track cost per request in canary vs baseline to catch token inflation


### 7.3 Prompt Regression Testing

- Maintain a golden dataset of question-answer pairs with expected behavior
- On every prompt change, run the golden set and compare:
  - Quality score (faithfulness, relevancy)
  - Token consumption (input + output)
  - Latency
- Detect silent cost increases -- a prompt change that adds 200 tokens per request costs real money at scale
- Gate deployments on regression test pass/fail


### 7.4 Drift Detection

**What to monitor for drift:**

- **Input distribution drift** -- user queries shift in topic, length, or language
- **Output token length drift** -- model starts producing longer or shorter responses
- **Embedding drift** -- vector representations shift, degrading retrieval quality
- **Retrieval drift** -- retriever returns different documents for the same queries over time
- **Prompt template drift** -- accumulated edits change prompt behavior in unexpected ways

**Why token length changes matter:**

- Increasing output tokens often correlates with hallucination -- the model is "making up more"
- Sudden token length changes signal the model is behaving differently even if quality scores look stable
- Track p50 and p95 output token length as a first-class drift metric


### 7.5 Token-Level Monitoring

**Track per request:**

- Input tokens
- Output tokens
- Total tokens
- Model used
- Latency (time to first token, total)
- Prompt version
- User / tenant ID

**Track aggregates:**

- Avg input tokens per request
- Avg output tokens per request
- p95 input and output tokens
- Cost per request
- Cost per user
- Cost per workflow / feature

**Cost formula:**

```
cost = (input_tokens x input_rate) + (output_tokens x output_rate)
```

**Why this matters:**

- Input tokens drive cost -- long system prompts and chat history are the biggest cost lever
- Output tokens drive latency -- more output tokens = longer time to complete
- Long chat history inflates input tokens on every turn (grows linearly with conversation length)
- Streaming does not reduce token cost -- it only changes delivery timing, total tokens are identical
- A prompt change that adds 100 input tokens costs nothing in dev but thousands per month at scale


### 7.6 Cost Monitoring

- Set cost alerts per feature, per tenant, per model
- Track per-feature cost to identify expensive workflows
- Detect token spikes -- sudden jumps in avg tokens per request
- Watch for recursive agent cost explosion -- agents that loop or retry accumulate unbounded token spend
- Enforce budget caps -- hard limits that kill requests when a tenant or workflow exceeds its budget


### 7.7 Human Feedback Loop

- **Thumbs up/down** -- simplest explicit signal; track per prompt version
- **Implicit feedback** -- user retries, rephrases, or abandons the conversation
- **Human review queues** -- route low-confidence or flagged outputs for expert review
- **Feedback to prompt updates** -- use patterns in negative feedback to refine prompts
- **Feedback to fine-tuning** -- collect high-quality human-rated pairs for supervised tuning

Automated metrics are not enough because:
- They measure surface quality, not user satisfaction
- They miss domain-specific correctness that only experts can judge
- Users tolerate different failure modes than metrics predict


## 8. Common Interview Questions

**How do you evaluate a chatbot in production?**
Track automated metrics (faithfulness, relevancy), collect explicit feedback (thumbs up/down), monitor implicit signals (retry rate, session abandonment), and run periodic human review on sampled conversations.

**How do you measure hallucination?**
Use faithfulness scoring -- decompose the answer into claims and check each against the provided context. Claims not supported by context are hallucinated. Track hallucination rate as a time series.

**How do you monitor LLM cost in production?**
Log input/output tokens per request with model ID and prompt version. Compute cost using the pricing formula. Aggregate by user, feature, and workflow. Set alerts on cost spikes and budget caps.

**How do you evaluate a RAG pipeline?**
Use Ragas or similar framework. Measure context precision, context recall, faithfulness, and answer relevancy. Test on a golden dataset. Monitor retrieval quality separately from generation quality.

**How do you detect prompt regression?**
Maintain a golden evaluation set. Run it on every prompt change. Compare quality scores, token counts, and latency against the previous version. Block deploys that regress on any key metric.

**How do you evaluate without ground-truth labels?**
Use LLM-as-a-judge for quality scoring. Use reference-free metrics like Ragas faithfulness. Collect human feedback over time. Compare outputs pairwise across model versions.

**What is the difference between faithfulness and relevancy?**
Faithfulness = is the answer grounded in the context? Relevancy = does the answer address the question? An answer can be faithful but irrelevant (correct facts, wrong question) or relevant but unfaithful (right topic, hallucinated details).

**How do you detect embedding drift?**
Track the distribution of embedding vectors over time. Monitor retrieval recall on a fixed query set. If recall drops without query changes, embeddings or the index have drifted.

**Why might output tokens increase over time?**
Model updates, prompt changes, or input distribution shifts. Longer outputs often correlate with hallucination or verbose system prompt instructions. Track p50/p95 output tokens as a drift signal.

**How do you handle evaluation for multi-turn conversations?**
Evaluate per-turn and per-session. Per-turn: faithfulness and relevancy of each response. Per-session: task completion rate, total tokens consumed, user satisfaction signal.

**When do you use human eval vs automated eval?**
Use automated for scale and speed (regression tests, continuous monitoring). Use human eval for high-stakes decisions (launch/no-launch), calibrating automated metrics, and catching failure modes that metrics miss.

**How do you prevent agent cost explosion?**
Set max iteration limits, per-request token budgets, and per-workflow cost caps. Monitor recursive call depth. Alert on token spend that exceeds expected bounds. Kill runaway agents automatically.


## 9. Fast Revision Summary

- LLMs are non-deterministic -- evaluation is not optional, it is infrastructure
- Track faithfulness, relevancy, context precision, and context recall for RAG
- Ragas gives reference-free RAG evaluation using LLM-based claim decomposition
- Log input tokens, output tokens, model, prompt version, and latency on every request
- Cost = (input_tokens x input_rate) + (output_tokens x output_rate)
- Input tokens drive cost; output tokens drive latency
- Output token length increase is a hallucination signal
- Use golden datasets for prompt regression testing
- Combine automated metrics + human feedback; neither alone is sufficient
- Set cost alerts, budget caps, and canary rollbacks in production
