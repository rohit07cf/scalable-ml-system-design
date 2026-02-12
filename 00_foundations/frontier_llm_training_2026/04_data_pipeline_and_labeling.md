# 04 — Data Pipeline and Labeling


## Pre-Training Data

### Where the data comes from

- **Common Crawl derivatives** — web text, filtered and deduplicated
  - RefinedWeb, FineWeb, DCLM, RedPajama — curated CC subsets
  - Raw CC is ~250B+ pages; after filtering, usable fraction is much smaller

- **Code repositories** — GitHub, GitLab (permissive licenses)
  - The Stack v2, StarCoder training data
  - Code trains reasoning, structure, logic — not just for code models

- **Books and academic papers** — curated collections
  - Books3, academic corpora, arXiv, PubMed
  - Licensing is a legal gray area; increasingly negotiated

- **Licensed / proprietary datasets** — purchased or partnership-based
  - News archives, enterprise data, specialized domains
  - Labs increasingly pay for high-quality, legally clean data

- **Multilingual text** — web, Wikipedia, government documents
  - Coverage varies; English still dominates most training mixes

- **Synthetic data** — model-generated text, augmented examples
  - Used to fill gaps: underrepresented languages, math, reasoning
  - Growing fraction of training data in 2026


### How the data is filtered

Filtering is where most data engineering effort goes:

- **Deduplication** — exact and near-duplicate removal (MinHash, SimHash)
  - Removes ~30–60% of raw web crawl data
  - Prevents memorization of repeated content

- **Quality filtering** — heuristic and model-based scoring
  - Heuristics: document length, language detection, character ratios
  - Model-based: classifier trained on "good" vs "bad" text (e.g., perplexity scoring)

- **Toxicity / safety filtering** — remove harmful content
  - Classifiers for hate speech, explicit content, PII
  - Not perfect — some content slips through

- **Domain mixing** — control the ratio of web, code, books, math, etc.
  - The mix ratio significantly affects model capabilities
  - Optimized empirically (ablation studies on smaller models)

### Scale

| Data Type | Typical Scale |
|---|---|
| Raw web crawl | 100T+ tokens (before filtering) |
| After filtering / dedup | 5T–20T tokens |
| Code | 500B–2T tokens |
| Books / papers | 100B–500B tokens |
| Synthetic | 100B–1T+ tokens (growing) |
| **Total training tokens** | **5T–20T+** |


## Post-Training Data

### Human preference data

Used for RLHF, DPO, and other alignment techniques:

- **Format**: (prompt, chosen_response, rejected_response)
- **Collection**: human annotators compare model outputs side-by-side
- **Scale**: 500K–5M+ preference pairs for a frontier model
- **Cost**: $5–$50 per annotated pair (depending on complexity)

### Instruction-following data (SFT)

- **(instruction, response)** pairs
- Mix of human-written and synthetic
- 100K–10M examples
- Covers: Q&A, summarization, coding, math, multi-turn conversation

### Synthetic reasoning traces

- Strong model generates chain-of-thought traces
- Traces are filtered for correctness (verify the final answer)
- Weaker model is trained to replicate the reasoning pattern
- Critical for reasoning-focused models (o-series, Claude reasoning)

### AI feedback loops

- Use a strong model (e.g., GPT-4, Claude) as a judge
- Generate preference labels at scale without human annotators
- **RLAIF** (RL from AI Feedback) — cheaper than human labeling
- Quality depends on the judge model
- Used to bootstrap, then refined with targeted human labeling


## How Labeling Works

### In-house annotators

- Employed directly by the lab
- Highest quality, most expensive
- Used for the most critical alignment data
- Anthropic, OpenAI, Google all maintain internal teams

### Contracted labeling (Scale AI, Surge AI, etc.)

- **Scale AI** is the largest provider for frontier labs
  - Provides human preference labeling, RLHF data, red-teaming
  - Manages annotator pools, quality control, calibration
  - Used by OpenAI, Meta, and others

- **Surge AI**, **Labelbox**, **Appen** — alternatives for specific tasks

- Process:
  1. Lab defines the task (e.g., "which response is better and why")
  2. Labeling company recruits and trains annotators
  3. Annotators label thousands of examples
  4. Quality control: inter-annotator agreement, spot checks, calibration
  5. Data delivered in structured format (JSON/CSV)

### AI-assisted labeling

- Model generates initial labels
- Human annotators review and correct
- 2–5x faster than fully manual labeling
- Standard practice by 2026


## Data Pipeline Summary

```
PRE-TRAINING DATA
─────────────────
Web crawl → dedup → quality filter → toxicity filter → domain mix → tokenize
Code repos → license filter → dedup → quality filter → tokenize
Books/papers → dedup → tokenize
Synthetic → generate → filter → tokenize
                                                    ↓
                                           5T–20T tokens
                                                    ↓
                                            Pre-training


POST-TRAINING DATA
──────────────────
Human preference pairs → quality control → format → DPO/RLHF
Instruction-response pairs → filter → format → SFT
Synthetic reasoning traces → verify answers → filter → distillation
AI feedback labels → calibrate → supplement human labels
                                                    ↓
                                     100K–5M+ examples
                                                    ↓
                                        Post-training
```


## Scale Summary Table

| Data Category | Source | Scale | Use |
|---|---|---|---|
| Web text | Common Crawl (filtered) | 5T–15T tokens | Pre-training |
| Code | GitHub (permissive) | 500B–2T tokens | Pre-training |
| Books / academic | Curated collections | 100B–500B tokens | Pre-training |
| Synthetic text | Model-generated | 100B–1T+ tokens | Pre-training + post-training |
| SFT instruction pairs | Human + synthetic | 100K–10M examples | SFT |
| Preference pairs | Human annotators | 500K–5M pairs | RLHF / DPO |
| Reasoning traces | Strong model distillation | 100K–1M traces | Reasoning training |


## TL;DR (Interview Summary)

- Pre-training data: 5T–20T tokens from web, code, books, synthetic — heavily filtered and deduped
- Filtering removes 30–60% of raw data; quality scoring and toxicity removal are critical
- Domain mix ratio (web vs code vs math) significantly impacts model capabilities
- Post-training: 500K–5M preference pairs + 100K–10M SFT examples
- Scale AI is the largest third-party provider for human preference labeling
- AI feedback loops (RLAIF) bootstrap labeling cheaply; humans refine the critical subset
- Synthetic reasoning traces are now essential for reasoning-focused models
- Data quality is the single biggest lever on model quality — more important than scale alone
