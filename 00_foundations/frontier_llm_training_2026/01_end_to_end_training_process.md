# 01 — End-to-End Training Process


## The Three Phases

Frontier model training has three distinct phases, executed in sequence:

1. **Pre-training** — learn language from raw text (self-supervised)
2. **Supervised fine-tuning (SFT)** — learn to follow instructions
3. **Alignment** — learn human preferences (RLHF, DPO, etc.)

Each phase has different data, objectives, compute requirements, and duration.


## Phase 1: Pre-Training

**Objective**: Next-token prediction on massive text corpora.

- **Self-supervised** — no human labels needed
- Model learns grammar, facts, reasoning patterns, code, math
- Trained on **trillions of tokens** (5T–20T+ as of early 2026)
- Data: web crawl, books, code, scientific papers, multilingual text
- Loss function: cross-entropy on next-token prediction

**This is the most expensive phase by far.**

| Aspect | Typical Range |
|---|---|
| Duration | 2–6 months of continuous training |
| Compute | 10K–100K+ GPUs running 24/7 |
| Cost | $50M–$500M+ (depends on scale) |
| Data | 5T–20T+ tokens |
| Output | Base model (strong but not instruction-following) |


## Phase 2: Supervised Fine-Tuning (SFT)

**Objective**: Teach the base model to follow instructions and produce structured outputs.

- Uses (instruction, response) pairs curated by humans or generated synthetically
- Much smaller dataset than pre-training (100K–10M examples)
- Much cheaper and faster than pre-training

| Aspect | Typical Range |
|---|---|
| Duration | Days to 1–2 weeks |
| Compute | Hundreds to low thousands of GPUs |
| Cost | $100K–$5M |
| Data | 100K–10M instruction-response pairs |
| Output | Instruction-following model |


## Phase 3: Alignment (Post-Training)

**Objective**: Steer the model toward outputs humans actually prefer — helpful, harmless, honest.

Multiple techniques, often combined:

### RLHF (Reinforcement Learning from Human Feedback)
- Train a **reward model** on human preference data
- Use PPO to optimize the LLM against the reward model
- Complex (4 models in memory), but powerful
- Used by OpenAI, Anthropic, and others since 2022

### DPO (Direct Preference Optimization)
- Skip the reward model entirely
- Train directly on (chosen, rejected) preference pairs
- Simpler, cheaper, more stable than RLHF
- Widely adopted by early 2026

### ORPO (Odds Ratio Preference Optimization)
- Combines SFT and preference alignment in one training step
- Eliminates the need for a separate SFT phase before alignment
- Newer approach, gaining traction

### KTO (Kahneman-Tversky Optimization)
- Works with binary feedback (good/bad) instead of pairwise preferences
- Easier to collect data — don't need side-by-side comparisons
- Based on prospect theory loss functions

### Synthetic Data Loops
- Use a strong model to generate training data for a weaker model
- **Reasoning distillation**: strong model produces chain-of-thought traces,
  weaker model learns to replicate the reasoning pattern
- Used extensively for reasoning-focused models (o-series, Claude reasoning)
- Increasingly important in early 2026

| Technique | Reward Model? | Data Format | Complexity | Adoption (2026) |
|---|---|---|---|---|
| RLHF (PPO) | Yes | Preference pairs | High | Established |
| DPO | No | Preference pairs | Low | Widespread |
| ORPO | No | Preference pairs | Low | Growing |
| KTO | No | Binary labels | Low | Growing |
| Reasoning distillation | No | Synthetic traces | Medium | Widespread |


## End-to-End Pipeline (Numbered Steps)

```
1. Data collection
   - Web crawl, books, code, licensed data, synthetic data
   - Dedup, filter, quality score, tokenize

2. Pre-training
   - Next-token prediction on trillions of tokens
   - Months of continuous GPU training
   - Periodic checkpoints (every few minutes)

3. Supervised fine-tuning (SFT)
   - Instruction-response pairs (human + synthetic)
   - Days to weeks

4. Alignment
   - RLHF or DPO on human preference data
   - Synthetic data loops for reasoning
   - Days to weeks

5. Safety evaluation
   - Red-teaming, benchmark suites, bias testing
   - Automated + human evaluation

6. Deployment preparation
   - Quantization (for inference efficiency)
   - Distillation (smaller serving models)
   - A/B testing, canary rollout
```


## Pre-Training vs Fine-Tuning vs Alignment

| | Pre-Training | Fine-Tuning (SFT) | Alignment |
|---|---|---|---|
| **Goal** | Learn language | Follow instructions | Match human preferences |
| **Supervision** | Self-supervised | Supervised | Preference-based |
| **Data size** | Trillions of tokens | Millions of examples | Millions of pairs |
| **Duration** | Months | Days–weeks | Days–weeks |
| **Cost** | $50M–$500M+ | $100K–$5M | $100K–$10M |
| **Output** | Base model | Instruction model | Aligned model |
| **Compute** | 10K–100K+ GPUs | 100–1K GPUs | 100–1K GPUs |


## Interview Phrasing

> "Frontier training is a three-phase pipeline. Pre-training is self-supervised
> next-token prediction on trillions of tokens — that's the expensive part,
> running for months on tens of thousands of GPUs. Then SFT teaches the model
> to follow instructions using curated examples. Finally, alignment uses
> techniques like RLHF or DPO to steer outputs toward human preferences.
> In 2026, DPO has largely replaced PPO for alignment because it's simpler
> and cheaper, and synthetic data loops — especially reasoning distillation —
> have become a critical part of post-training."

> "The key insight is that pre-training is 90%+ of the compute cost.
> Post-training (SFT + alignment) is comparatively cheap but has outsized
> impact on model quality and safety."


## Mini Python Example: Pre-train -> SFT -> Align (Toy Walkthrough)

A complete runnable toy is in [`examples/three_phase_training_toy.py`](examples/three_phase_training_toy.py).

Below is the conceptual walkthrough of what that code does and WHY.


### The Three Phases — Detailed Breakdown

#### Phase 1: Pre-Training (Self-Supervised)

**Goal**
- Teach the model to predict the next token in raw text
- No human labels — the text itself is the supervision

**Input data format**
```
"the cat sat on the mat and looked around"
"machine learning models learn from data"
```
Just raw strings. No instructions. No labels. No preference pairs.

**What the model learns**
- Statistical patterns: which words follow which
- Grammar, facts, reasoning patterns (at scale)
- Think of it like: a student reading millions of books without a teacher

**What the loss means (in words)**
- "How surprised was the model by the actual next token?"
- Low loss = model predicted correctly = it learned the pattern
- Technically: cross-entropy between predicted distribution and actual next token

**What comes out**
- A **base model checkpoint** — knows language but can't follow instructions
- At frontier scale: this checkpoint is hundreds of GB

**What changes next phase**
- The data changes (from raw text to instruction pairs)
- The model architecture stays the same
- The loss function stays the same (still next-token prediction)
- But the model learns a new skill: responding to instructions


#### Phase 2: SFT (Supervised Fine-Tuning)

**Goal**
- Teach the model to follow instructions
- Learn the format: "when asked X, respond with Y"

**Input data format**
```
Instruction: "greet the customer"
Response:    "Hello! How can I help you today?"
```
Formatted as a single sequence: `"greet the customer -> Hello! How can I help you today?"`

**What the model learns**
- The pattern of helpful, structured responses
- How to transition from prompt to answer
- Think of it like: the student now gets a tutor with flashcards

**What the loss means**
- Same as pre-training: next-token prediction cross-entropy
- But now the model predicts the RESPONSE tokens given the INSTRUCTION
- The loss is computed on the response portion (not the instruction)

**What comes out**
- An **SFT checkpoint** — follows instructions, but may not match human preferences
- This model is useful but can give technically correct yet unhelpful responses

**What changes next phase**
- The data changes (from instruction pairs to preference triplets)
- The objective changes (from "predict next token" to "prefer chosen over rejected")
- The loss function changes (DPO loss instead of cross-entropy)


#### Phase 3: Alignment (DPO-Style Preference Optimization)

**Goal**
- Steer the model toward responses humans actually prefer
- Learn: "Response A is better than Response B — internalize why"

**Input data format**
```
Prompt:   "My order is late"
Chosen:   "I'm sorry! Let me check your order right now."
Rejected: "Check the tracking page yourself."
```

**What the model learns**
- The subtle qualities that make one response better: empathy, specificity, action
- Not just correctness, but preference and tone
- Think of it like: the tutor shows pairs of exam answers and says "this one is better"

**What the loss means (DPO, in words)**
- "Make the model prefer the chosen response more than the reference model does,
  relative to the rejected response"
- No reward model needed — the preference signal is in the loss function itself
- The frozen reference model prevents the model from changing too much (stability anchor)

**What comes out**
- An **aligned checkpoint** — the final production model
- Follows instructions AND matches human preferences
- This is what gets deployed

**What changes vs previous phases**
- Loss function is DPO (not cross-entropy)
- Data is preference triplets (not instruction pairs)
- A frozen reference model is introduced (the SFT checkpoint, unchanged)
- Two models in memory: the policy (training) and the reference (frozen)


### What the Toy Code Demonstrates

The script in `examples/three_phase_training_toy.py` runs all three phases on a
tiny dummy model (embedding + linear — not a transformer) with toy data.

| Aspect | Toy Example | Real Training |
|---|---|---|
| Model | 3-layer linear (~10 KB) | Transformer (7B–1T+ params) |
| Pre-train data | 8 short strings | 5T–20T tokens |
| SFT data | 5 instruction pairs | 100K–10M pairs |
| Preference data | 4 triplets | 500K–5M pairs |
| Training steps | 50 + 40 + 30 | Millions of steps |
| Checkpoints | ~40 KB each | 140 GB–8 TB each |
| Hardware | Your laptop CPU | 10K–100K+ GPUs |
| Duration | ~2 seconds | Months |

**What IS realistic in the toy:**
- The three-phase pipeline structure (pre-train -> SFT -> align)
- Each phase starts from the previous checkpoint (not from scratch)
- The training loop: forward pass -> compute loss -> backward pass -> optimizer step
- DPO uses a frozen reference model + the policy model (2 models)
- Checkpoints saved after each phase

**What IS simplified:**
- Model is not a transformer (just embedding + linear)
- Tokenizer maps characters, not subwords
- No batching, no distributed training, no mixed precision
- DPO loss is correct in structure but data is trivially small


### Behind the Scenes: The Training Loop

Every phase follows the same core loop, regardless of scale:

```
1. LOAD DATA     — prepare a batch of token sequences
2. FORWARD PASS  — feed tokens through the model, get logits
3. COMPUTE LOSS  — compare predictions to targets
                   (cross-entropy for pre-train/SFT, DPO loss for alignment)
4. BACKWARD PASS — compute gradients (how each weight should change)
5. OPTIMIZER STEP — update weights using gradients (Adam, typically)
6. REPEAT        — next batch, next step
```

This loop runs billions of times during pre-training.
The only things that change between phases: the DATA and the LOSS.

> If you remember one thing: the training loop is always
> forward -> loss -> backward -> step.
> What changes across phases is what data goes in and what loss is computed.


### What to Say in Interviews (Code-Informed)

- "The three phases share the same core training loop — forward, loss, backward, step.
  What changes is the data and the loss function."

- "Pre-training and SFT both use cross-entropy on next-token prediction. The difference
  is the data: raw text for pre-training, curated instruction pairs for SFT."

- "DPO alignment introduces a second model — the frozen reference. The loss pushes the
  policy to prefer chosen responses more than the reference does. No reward model needed."

- "Each phase starts from the previous phase's checkpoint. You never train alignment
  from a random initialization — it builds on SFT, which builds on pre-training."

- "The DPO reference model is just a frozen copy of the SFT checkpoint. It's the
  anchor that prevents the policy from drifting too far during alignment."


### Common Traps

- Confusing **SFT with pre-training** — SFT uses instruction data and comes after
  pre-training. The loss function is the same but the data is entirely different.

- Thinking **DPO needs a reward model** — it does NOT. DPO skips the reward model.
  Only PPO-based RLHF needs a reward model.

- Thinking **alignment replaces SFT** — it does not. Alignment builds ON TOP of
  SFT. Skipping SFT and going straight to alignment produces poor results.

- Believing **pre-training is "just more of the same data"** — the data sources,
  filtering, and mixing ratios for pre-training are carefully engineered. It is not
  just "dump the internet into the model."

- Confusing **the reference model in DPO with the reward model in RLHF** — the
  reference model is a frozen copy of the policy (used for KL constraint).
  The reward model is a separate model that scores outputs (PPO only).


## TL;DR (Interview Summary)

- Three phases: pre-training (months, $50M–$500M+) -> SFT (days) -> alignment (days)
- Pre-training = self-supervised next-token prediction on trillions of tokens
- SFT = same loss, different data — instruction pairs teach the response format
- Alignment (DPO) = new loss function — preference pairs, no reward model needed
- Each phase starts from the previous checkpoint — alignment builds on SFT builds on pre-training
- The core loop never changes: forward -> loss -> backward -> step
- DPO has largely displaced PPO by 2026 (simpler, cheaper, similar quality)
- Synthetic data loops and reasoning distillation are now critical post-training steps
- See `examples/three_phase_training_toy.py` for a runnable toy demonstrating all three phases
