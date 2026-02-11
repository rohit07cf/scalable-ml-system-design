# Diagram: RLHF PPO Loop


## The Full PPO Pipeline (Two Phases)

```
╔══════════════════════════════════════════════════════════════════╗
║                  PHASE 1: Train Reward Model (one-time)         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   Preference Data                                                ║
║   ┌─────────────────────────────────────┐                        ║
║   │ prompt: "My order is late."         │                        ║
║   │ chosen:  "I'm sorry! Let me help."  │──┐                    ║
║   │ rejected: "Check the website."      │  │                    ║
║   └─────────────────────────────────────┘  │                    ║
║                                             │                    ║
║                                             ▼                    ║
║                                    ┌─────────────────┐           ║
║                                    │  Reward Model   │           ║
║                                    │  Training        │           ║
║                                    │                  │           ║
║                                    │  Learn:          │           ║
║                                    │  score(chosen)   │           ║
║                                    │  > score(reject) │           ║
║                                    └────────┬────────┘           ║
║                                             │                    ║
║                                             ▼                    ║
║                                    ┌─────────────────┐           ║
║                                    │  Trained RM      │           ║
║                                    │  (frozen, used   │           ║
║                                    │   in Phase 2)    │           ║
║                                    └─────────────────┘           ║
╚══════════════════════════════════════════════════════════════════╝


╔══════════════════════════════════════════════════════════════════╗
║              PHASE 2: PPO Training Loop (repeated)              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   ┌──────────────┐                                               ║
║   │  Prompt Batch │                                               ║
║   │  "My order    │                                               ║
║   │   is late."   │                                               ║
║   └──────┬───────┘                                               ║
║          │                                                        ║
║          ▼                                                        ║
║   ┌──────────────┐     generate      ┌──────────────────────┐    ║
║   │   POLICY     │ ──────────────> │  "I'm so sorry!       │    ║
║   │   (LLM)      │     response     │   Let me track your   │    ║
║   │   trainable   │                  │   order right away."  │    ║
║   └──────────────┘                  └──────────┬────────────┘    ║
║          ▲                                     │                  ║
║          │                          ┌──────────┴──────────┐       ║
║          │                          │                     │       ║
║          │                          ▼                     ▼       ║
║          │                  ┌──────────────┐     ┌──────────────┐ ║
║          │                  │  REWARD      │     │  REFERENCE   │ ║
║          │                  │  MODEL       │     │  MODEL       │ ║
║          │                  │  (frozen)    │     │  (frozen)    │ ║
║          │                  │              │     │              │ ║
║          │                  │  score=0.82  │     │  KL anchor   │ ║
║          │                  └──────┬───────┘     └──────┬───────┘ ║
║          │                         │                    │         ║
║          │                         ▼                    ▼         ║
║          │              ┌───────────────────────────────────┐     ║
║          │              │  Adjusted Reward                   │     ║
║          │              │  = reward - β × KL(policy ‖ ref)  │     ║
║          │              │  = 0.82  - 0.1 × 0.3              │     ║
║          │              │  = 0.79                            │     ║
║          │              └──────────────┬────────────────────┘     ║
║          │                             │                          ║
║          │                             ▼                          ║
║          │              ┌──────────────────────┐                  ║
║          │              │  VALUE MODEL          │                  ║
║          │              │  (trainable)          │                  ║
║          │              │  expected = 0.65      │                  ║
║          │              │                       │                  ║
║          │              │  advantage = 0.79     │                  ║
║          │              │             - 0.65    │                  ║
║          │              │             = +0.14   │                  ║
║          │              │  (better than         │                  ║
║          │              │   expected!)          │                  ║
║          │              └──────────┬────────────┘                  ║
║          │                         │                               ║
║          │                         ▼                               ║
║          │              ┌──────────────────────┐                  ║
║          │              │  PPO UPDATE           │                  ║
║     ◄────┘              │                       │                  ║
║   update                │  • Positive advantage │                  ║
║   weights               │    → increase prob    │                  ║
║                         │  • Clip changes to    │                  ║
║                         │    ±epsilon (0.2)     │                  ║
║                         │  • Small, safe update │                  ║
║                         └──────────────────────┘                  ║
║                                                                    ║
║                         ── repeat with next batch ──              ║
╚══════════════════════════════════════════════════════════════════╝
```


## The Four Models (Memory Map)

```
┌─────────────────────────────────────────────────────┐
│                GPU Memory Layout (7B)                │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Policy       │  │ Reference    │                 │
│  │ (trainable)  │  │ (frozen)     │                 │
│  │ 14 GB        │  │ 14 GB        │                 │
│  └──────────────┘  └──────────────┘                 │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Reward Model │  │ Value Model  │                 │
│  │ (frozen)     │  │ (trainable)  │                 │
│  │ 14 GB        │  │ 14 GB        │                 │
│  └──────────────┘  └──────────────┘                 │
│                                                      │
│  Total: ~56 GB + optimizer states + activations     │
│  Practical: needs 2–4× A100 (80 GB) for 7B         │
└─────────────────────────────────────────────────────┘
```


## What Each Component Does (One Line)

| Component | Role | Trainable? |
|---|---|---|
| **Policy** | The LLM we're improving — generates responses | Yes |
| **Reference** | Frozen copy of the pre-PPO policy — KL anchor | No |
| **Reward Model** | Scores (prompt, response) — learned from preferences | No |
| **Value Model** | Estimates expected reward — helps compute advantage | Yes |


## What to Say in Interviews

- "PPO has two phases: first train a reward model on preference data,
  then run the RL loop where the policy generates responses, the RM
  scores them, and PPO updates the policy toward higher scores."

- "The KL penalty keeps the policy anchored to the reference model —
  without it, the policy would reward-hack by finding adversarial
  outputs that fool the RM."

- "The main cost is four models in GPU memory. For a 7B model that's
  about 56 GB minimum, which is why DPO — needing only two models — is
  the simpler starting point for most teams."


## TL;DR (Interview Summary)

- Phase 1: Train reward model on preference pairs (one-time)
- Phase 2: Loop — generate, score with RM, compute advantage, PPO update
- KL penalty = leash that keeps policy near reference (prevents reward hacking)
- Advantage = adjusted_reward - value_estimate ("better or worse than expected?")
- PPO clips updates to ±epsilon — small, safe steps
- 4 models in memory: policy + reference + RM + value (~4x model size)
- Expensive but flexible — can use any scalar reward signal
