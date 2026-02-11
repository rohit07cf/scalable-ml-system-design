# LLM Fundamentals


## 1. What is an LLM

- A probabilistic next-token predictor trained on massive text corpora
- Transformer-based architecture with billions of parameters
- Generates output by predicting the most statistically likely next token, one at a time
- It is not a reasoning engine -- it produces plausible text, not verified truth
- Quality depends heavily on training data, prompt design, and decoding settings


## 2. Tokens and Tokenization

- Text is split into tokens before the model processes it -- tokens are the atomic unit
- Words are not tokens -- a single word may be 1-3 tokens depending on the tokenizer
- Subword tokenization (BPE, SentencePiece) handles rare words by breaking them into pieces
- Common words ("the", "is") are usually one token; rare words get split into subword pieces

**Why tokens matter for cost:**

- You pay per input token and per output token
- Input tokens = system prompt + user message + chat history + retrieved context
- Output tokens = the generated response
- Output tokens are typically 2-4x more expensive than input tokens

**Why tokens matter for latency:**

- Input tokens are processed in parallel (prefill phase)
- Output tokens are generated one at a time (autoregressive -- sequential)
- More output tokens = proportionally more latency

**Intuition:**

"How are you doing today?" is roughly 6 tokens.
A 500-word response is roughly 650-750 tokens.


## 3. Context Windows

- The context window is the maximum number of tokens the model can see at once
- Input tokens and output tokens share the same window
- If input uses 90% of the window, only 10% is left for the response

**Practical implications:**

- Larger context = more expensive (every token in the window is processed)
- Long chat history consumes context on every turn -- grows linearly
- Truncation drops old content to stay within limits -- loses information
- Summarization compresses history -- saves tokens but loses detail
- Retrieval-based memory fetches only relevant past context -- best cost/quality balance

**Rule of thumb:** supporting 128k tokens does not mean you should send 128k tokens.


## 4. Embeddings

- Dense vector representations of text (typically 768-3072 dimensions)
- Texts with similar meaning have vectors that are close together
- The foundation of semantic search and RAG retrieval

**Used for:**

- Retrieval in RAG pipelines (embed query, search against embedded documents)
- Semantic similarity and clustering
- Classification and anomaly detection

**Production concerns:**

- Embedding models can drift -- re-embedding may be needed when switching models
- Different embedding models produce incompatible vector spaces
- Embedding dimension affects storage cost and search latency


## 5. Attention (High-Level Only)

- The attention mechanism lets the model weigh the importance of every previous token when generating the next one
- Every token attends to every other token -- this is what makes transformers powerful
- Cost scales quadratically with sequence length -- doubling context roughly quadruples compute
- This is why long contexts are expensive and slow

**KV cache:**

- During generation, the model caches key-value pairs from previous tokens
- Avoids recomputing attention over the full history on each new token
- KV cache grows with context length and consumes GPU memory
- This is the main reason longer conversations use more memory


## 6. Prompting Fundamentals

- **System prompt** -- sets behavior, tone, constraints; sent on every request
- **User prompt** -- the actual question or instruction from the user
- **Role prompting** -- "You are a senior engineer..." biases the model toward a persona
- **Few-shot prompting** -- include examples in the prompt to guide output format
- **Chain-of-thought** -- ask the model to reason step-by-step; improves accuracy on complex tasks
- **Prompt injection** -- adversarial input that overrides system instructions; a real security risk

**System design note:** system prompts add input tokens to every request. A 500-token system prompt at 10k requests/day is 5M input tokens/day just from the system prompt.


## 7. Fine-Tuning vs RAG

| Dimension | Fine-Tuning | RAG |
|---|---|---|
| What changes | Model weights | External knowledge provided at inference |
| Cost | High (training compute, data prep) | Low (retrieval infra, no training) |
| Knowledge freshness | Frozen at training time | Up-to-date (depends on index refresh) |
| Best for | Behavior shift, tone, format, domain style | Factual grounding, enterprise knowledge |
| Data needed | Curated labeled pairs | Documents in a searchable index |
| Latency impact | None at inference | Adds retrieval latency (100-500ms) |
| Hallucination | Still hallucinates | Reduces hallucination via grounding |

**When to use fine-tuning:**

- You need the model to behave differently (tone, format, domain vocabulary)
- You have high-quality training data
- RAG alone does not fix the quality gap

**When to use RAG:**

- You need up-to-date or enterprise-specific knowledge
- You want to ground answers in source documents
- You want citations and traceability

**Often used together:** fine-tune for behavior, RAG for knowledge.


## 8. Hallucination and Failure Modes

- **Fabricated facts** -- model generates plausible but false information with high confidence
- **Overconfidence** -- model rarely says "I don't know"; it fills gaps with invented details
- **Prompt sensitivity** -- small wording changes produce significantly different outputs
- **Context confusion** -- model conflates information from different parts of a long context
- **Long-output drift** -- quality degrades in longer responses as the model drifts from the prompt
- **Safety risks** -- model may generate harmful, biased, or off-policy content without guardrails

**Why hallucination matters for system design:**

- You cannot trust raw LLM output for factual tasks without verification
- RAG reduces but does not eliminate hallucination
- Production systems need faithfulness checks, citations, and human review paths


## 9. Temperature, Top-k, Top-p

**Temperature:**

- Controls randomness in token selection
- Low temperature (0.0-0.3) -- deterministic, repetitive, safe
- High temperature (0.7-1.0) -- creative, varied, riskier
- Temperature 0 -- always picks the highest probability token (greedy)

**Top-k:**

- Limits selection to the top k most probable tokens
- Lower k = more focused; higher k = more diverse

**Top-p (nucleus sampling):**

- Limits selection to the smallest set of tokens whose cumulative probability exceeds p
- Top-p 0.9 = consider tokens until 90% cumulative probability is covered
- More adaptive than top-k -- adjusts the candidate pool dynamically

**System design note:** higher temperature can increase output length unpredictably, which increases cost and latency. Production systems typically use low temperature for factual tasks.


## 10. RLHF (High-Level)

- Reinforcement Learning from Human Feedback -- a post-training alignment step
- Humans rate model outputs; a reward model is trained on these preferences
- The LLM is then fine-tuned to maximize the reward model's score
- Makes the model more helpful, less harmful, and better at following instructions

**Key points:**

- RLHF is what makes ChatGPT-style models conversational and instruction-following
- It does not eliminate hallucination -- it reduces obviously bad outputs
- DPO (Direct Preference Optimization) is a simpler alternative gaining traction
- RLHF is expensive -- requires human annotators and iterative training


## 11. LLM Limitations in Production

- **Non-determinism** -- same input can produce different outputs across calls
- **High token cost** -- scales linearly with usage; no economies of scale on per-request cost
- **Latency spikes** -- variable output length, cold starts, and GPU contention cause unpredictable latency
- **Drift** -- model providers silently update weights; behavior changes without your code changing
- **Context limits** -- cannot process arbitrarily long inputs; requires chunking or retrieval strategies
- **Safety constraints** -- models can generate harmful content; requires guardrails and policy enforcement
- **No built-in memory** -- each request is stateless; conversation history must be explicitly managed


## 12. System Design Implications

- **Token cost drives budgeting** -- every design decision that adds tokens (longer prompts, more context, more turns) increases cost proportionally
- **Context window affects memory strategy** -- you must choose between full history, truncation, summarization, or retrieval-based memory
- **Embeddings enable RAG** -- semantic search depends on embedding quality; model changes require re-indexing
- **Attention scaling affects latency** -- longer inputs mean quadratically more compute; keep context lean
- **Prompt design impacts output length** -- verbose prompts encourage verbose responses; concise prompts save tokens
- **Monitoring token usage is critical** -- log input/output tokens per request, per user, per feature; alert on spikes
- **Non-determinism requires evaluation infrastructure** -- you cannot rely on spot-checks; you need automated eval pipelines


## 13. Common Interview Questions

**What is an LLM?**
A probabilistic next-token predictor trained on large text corpora. It generates statistically likely text, not verified truth. Transformer-based, with billions of parameters.

**Why are tokens important in system design?**
Tokens are the unit of cost and latency. Input tokens drive cost (sent every request). Output tokens drive latency (generated sequentially). Every design choice that adds tokens increases both.

**Why is a large context window expensive?**
Attention scales quadratically with context length. More tokens in the window means more compute per request. A 128k context request costs significantly more than a 4k request.

**When should you use fine-tuning vs RAG?**
Fine-tuning for behavior change (tone, format, domain style). RAG for knowledge grounding (up-to-date facts, enterprise documents). Often combined: fine-tune for behavior, RAG for knowledge.

**What causes hallucinations?**
The model predicts statistically likely tokens, not verified facts. It fills knowledge gaps with plausible but fabricated content. RAG reduces this by grounding answers in retrieved documents, but does not eliminate it.

**Why is temperature important for production systems?**
Temperature controls output randomness. High temperature increases creativity but also increases unpredictability, output length, and hallucination risk. Production factual systems use low temperature.

**Why does longer context increase latency?**
More input tokens mean a longer prefill phase (quadratic attention cost). More output tokens mean more sequential generation steps. Both compound for long conversations.

**What is the KV cache and why does it matter?**
It stores key-value pairs from previously processed tokens so they don't need to be recomputed. It speeds up generation but consumes GPU memory. Longer contexts = larger cache = more memory pressure.

**How do you handle conversation memory without blowing up context?**
Truncate old turns, summarize history into a compact block, or use retrieval-based memory to fetch only relevant past context. Each approach trades off cost, continuity, and detail.

**What is RLHF and why does it matter?**
Reinforcement Learning from Human Feedback aligns models to be helpful and safe. It is why instruction-following models work well in conversation. It does not eliminate hallucination.

**Why is non-determinism a problem in production?**
Same input can produce different outputs. Makes testing hard, debugging hard, and user experience inconsistent. Requires automated evaluation infrastructure, not manual spot-checks.

**How do embeddings relate to RAG?**
Embeddings convert text to dense vectors. Similar texts have similar vectors. RAG embeds the query, searches a vector index of documents, and retrieves relevant chunks to ground the LLM response.


## 14. Fast Revision Summary

- An LLM is a next-token predictor, not a reasoning engine -- it generates plausible text
- Tokens are the unit of cost and latency; input tokens drive cost, output tokens drive latency
- Context window is shared between input and output; keep it lean
- Attention scales quadratically with context -- long contexts are expensive and slow
- Embeddings power RAG; different models produce incompatible vector spaces
- Fine-tune for behavior, RAG for knowledge -- often used together
- Hallucination is inherent; RAG reduces it but does not eliminate it
- Temperature controls randomness; low for factual, higher for creative
- Every request is stateless; conversation memory must be explicitly designed
- Monitor tokens per request, cost per feature, and alert on drift
