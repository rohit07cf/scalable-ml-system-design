# 08 — Preference Data Pipeline


## What Is Preference Data?

Every RLHF method (PPO or DPO) needs **preference data**.

Each example is a triplet:

```json
{
  "prompt":   "Customer: My package never arrived.",
  "chosen":   "I'm really sorry about that! Let me track your package and arrange a reshipment right away.",
  "rejected": "Check your tracking number on the website."
}
```

- **prompt** — the input context
- **chosen** — the response a human (or AI) preferred
- **rejected** — the response that was NOT preferred

The model learns: "given this prompt, produce outputs more like chosen, less like rejected."


## Data Format Variants

### Simple pairs (most common)

```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

### Ranked lists (convert to pairs)

```json
{
  "prompt": "...",
  "responses": ["best", "good", "bad", "worst"],
  "ranking": [1, 2, 3, 4]
}
```

Convert to pairs: (1 vs 2), (1 vs 3), (1 vs 4), (2 vs 3), (2 vs 4), (3 vs 4)
→ 6 preference pairs from 4 responses.

### With metadata (recommended for production)

```json
{
  "prompt": "...",
  "chosen": "...",
  "rejected": "...",
  "annotator_id": "ann-42",
  "confidence": "high",
  "timestamp": "2024-01-15T10:30:00Z",
  "category": "refund_request"
}
```

WHY metadata: Filter by confidence, track annotator quality, debug bad batches.


## How to Collect Preferences

### Method 1: Human annotation (gold standard)

```
1. Generate 2+ responses per prompt (from the model or manually)
2. Show annotator: "Which response is better?"
3. Annotator picks one → (chosen, rejected) pair

Tools: Label Studio, Argilla, Scale AI, custom UI
```

- Best quality, most expensive
- Use for final alignment training

### Method 2: Model-based / AI feedback (RLAIF)

```
1. Generate 2+ responses per prompt
2. Ask a strong LLM (e.g., GPT-4, Claude): "Which is better and why?"
3. Parse the preference → (chosen, rejected) pair
```

- Cheaper, faster, scalable
- Good for bootstrapping — refine with human labels later

### Method 3: Implicit signals (production data)

```
- Thumbs up/down on chatbot responses
- User edits of model output (edited version = chosen, original = rejected)
- Conversation completion vs abandonment
```

- Free data from production traffic
- Noisier — needs careful filtering

### Which to use?

| Stage | Method | Volume |
|---|---|---|
| Prototype | AI feedback (RLAIF) | 1K–5K pairs |
| V1 training | Human annotation | 5K–50K pairs |
| Ongoing improvement | Implicit signals + human QA | Continuous |


## Quality Controls

### Deduplication

- Remove exact duplicate prompts (same prompt, same responses)
- Remove near-duplicates (fuzzy match on prompt text)
- WHY: Duplicates skew the model toward overrepresented topics

### Annotator agreement

- Have 2–3 annotators label each pair independently
- Keep only pairs where annotators agree (e.g., 2/3 majority)
- WHY: Disagreed pairs are ambiguous — training on them adds noise

### Toxicity / safety filtering

- Run chosen AND rejected through a toxicity classifier
- Remove pairs where the chosen response is toxic
- WHY: You don't want the model to learn that toxic responses are "preferred"

### Length bias check

- If chosen responses are always longer, the model learns "longer = better"
- Mix in pairs where the shorter response is preferred
- WHY: Prevents the model from gaming alignment by being verbose

### Difficulty balance

- Include easy pairs (clearly good vs clearly bad)
- Include hard pairs (both good, one slightly better)
- WHY: Easy pairs teach the basics; hard pairs teach nuance


## Train / Eval Split

```
Total: 10,000 preference pairs

Train: 8,000  (80%)  — used for DPO/PPO training
Eval:  1,000  (10%)  — used to measure alignment quality during training
Test:  1,000  (10%)  — held out, never seen during training

Split by prompt (not by pair):
  All pairs for a given prompt go to the SAME split.
  WHY: Prevents data leakage (model sees similar prompts in train and eval).
```


## How This Plugs Into PPO / DPO

### For DPO

```
Preference pairs → directly into DPO training
  - Each batch = N (prompt, chosen, rejected) triplets
  - DPO loss computed on each triplet
  - No preprocessing beyond tokenization
```

### For PPO (reward model training)

```
Preference pairs → train Reward Model
  - RM learns: score(chosen) > score(rejected)
  - Then prompts (without preferences) → PPO loop
  - PPO generates new responses, RM scores them
```

### Pipeline diagram

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Collect     │ ──> │  Validate    │ ──> │  Split        │
│  preferences │     │  + clean     │     │  train/eval   │
└─────────────┘     └──────────────┘     └──────┬────────┘
                                                │
                          ┌─────────────────────┤
                          │                     │
                          ▼                     ▼
                    ┌───────────┐         ┌───────────┐
                    │  DPO      │         │  Train RM  │
                    │  training │         │  → PPO     │
                    └───────────┘         └───────────┘
```


## Common Mistakes

- Not versioning preference data
  — model is only as good as its data; you need to reproduce results

- Mixing train/eval at the pair level instead of prompt level
  — data leakage makes eval metrics look better than reality

- Not tracking annotator quality
  — one bad annotator can poison thousands of pairs

- Using only easy pairs (clearly good vs clearly bad)
  — model learns obvious stuff but can't handle nuanced cases

- Ignoring length bias
  — model learns "be verbose" instead of "be helpful"


## Interview Answer: "How do you build a preference data pipeline?"

> "We collect preference pairs — prompt, chosen response, rejected
> response — through human annotation, AI feedback, or implicit signals.
> Quality controls include dedup, annotator agreement filtering, toxicity
> checks, and length bias mitigation. We split by prompt (not pair) to
> prevent leakage. The data feeds directly into DPO training, or first
> trains a reward model for PPO. We version every dataset for
> reproducibility and track annotator quality over time."


## TL;DR (Interview Summary)

- Preference data = (prompt, chosen, rejected) triplets
- Collection methods: human annotation (best), AI feedback (cheapest), implicit signals (free but noisy)
- Quality controls: dedup, annotator agreement, toxicity filter, length bias check
- Split by PROMPT, not pair — prevents data leakage
- For DPO: pairs go directly into training
- For PPO: pairs first train a reward model, then PPO uses prompts only
- Version everything — model reproducibility depends on exact data version
- Start with AI feedback to bootstrap, refine with human labels
