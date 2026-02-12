# Self-Reflection Pattern

## What It Is

- Agent **evaluates its own output** before returning it to the user
- A "critic" step that checks for correctness, completeness, safety, and quality
- Can be implemented as: same-agent reflection, separate critic agent, or structured rubric
- Key mechanism for reducing hallucinations and improving output quality

## Why It Matters (Interview Framing)

> "Self-reflection is how you answer 'How do you prevent hallucinations in an agent system?' It shows you understand that LLMs make mistakes, and you've designed for it — not just hoped for the best."

---

## Simple Mental Model

> Self-reflection is like **proofreading your own email before hitting send:**
> - Write the email (generate)
> - Read it again (reflect)
> - Fix any issues (revise)
> - Maybe read it one more time (iterate)

---

## The Self-Reflection Loop

```
┌────────────┐
│  GENERATE  │  Agent produces initial output
└─────┬──────┘
      │
┌─────▼──────┐
│  REFLECT   │  Agent critiques own output
│            │  "Is this correct? Complete? Safe?"
└─────┬──────┘
      │
      ├── PASS → Return output ✅
      │
      └── FAIL → Feed critique back
                     │
              ┌──────▼───────┐
              │   REVISE     │  Agent regenerates with critique
              └──────┬───────┘
                     │
              ┌──────▼───────┐
              │   REFLECT    │  Check again
              └──────┬───────┘
                     │
                     ├── PASS → Return ✅
                     └── FAIL → (max 3 iterations)
```

---

## Implementation Approaches

### Approach 1: Same-Agent Reflection

```python
def reflect_and_revise(agent, goal, max_iterations=3):
    output = agent.generate(goal)

    for i in range(max_iterations):
        critique = agent.reflect(
            f"Goal: {goal}\n"
            f"Output: {output}\n"
            f"Evaluate: Is this correct, complete, and safe?\n"
            f"If there are issues, describe them specifically."
        )

        if critique.is_satisfactory:
            return output

        output = agent.revise(
            f"Original output: {output}\n"
            f"Critique: {critique.feedback}\n"
            f"Generate an improved version addressing the critique."
        )

    return output  # Return best attempt after max iterations
```

### Approach 2: Separate Critic Agent

```
┌────────────┐         ┌──────────────┐
│  GENERATOR │──output─▶│   CRITIC     │
│  AGENT     │◀─feedback│   AGENT      │
│            │         │              │
│ (creative, │         │ (analytical, │
│  generative)│        │  evaluative) │
└────────────┘         └──────────────┘
```

- Generator focuses on creating output
- Critic focuses on finding flaws
- Different system prompts optimize each role
- Can use different models (cheaper critic)

### Approach 3: Structured Rubric

```python
REFLECTION_RUBRIC = {
    "factual_accuracy": {
        "check": "Are all facts verifiable? Any hallucinated data?",
        "weight": 0.3
    },
    "completeness": {
        "check": "Does the output address all parts of the goal?",
        "weight": 0.25
    },
    "safety": {
        "check": "Does the output contain PII, harmful content, or bias?",
        "weight": 0.25
    },
    "quality": {
        "check": "Is the output well-structured and clear?",
        "weight": 0.2
    }
}

# Agent scores each dimension, revision triggered if total < threshold
```

---

## Reflection Prompts

```
REFLECTION PROMPT (general):
"Review your previous output against these criteria:
1. CORRECTNESS: Are all facts accurate? Could any statement be wrong?
2. COMPLETENESS: Did you address every part of the request?
3. SAFETY: Does the output contain PII, bias, or harmful content?
4. RELEVANCE: Is everything in the output relevant to the goal?

If you find issues, describe each one specifically.
If the output is satisfactory, respond with 'PASS'."

REFLECTION PROMPT (code-specific):
"Review this code for:
1. CORRECTNESS: Will it produce the right output? Edge cases?
2. SECURITY: SQL injection, XSS, command injection, hardcoded secrets?
3. PERFORMANCE: Any N+1 queries, unbounded loops, memory leaks?
4. COMPLETENESS: Does it handle errors? Missing edge cases?"
```

---

## When to Use Self-Reflection

| Scenario | Use Reflection? | Why |
|---|---|---|
| High-stakes output (financial, medical, legal) | **Yes** | Errors are costly |
| Code generation | **Yes** | Bugs are common |
| Simple factual Q&A | **Maybe** | If accuracy is critical |
| Creative writing | **No** | Subjective quality |
| Real-time chat | **No** | Latency constraint |
| Data analysis with numbers | **Yes** | LLMs make calculation errors |

---

## Trade-offs

| Advantage | Disadvantage |
|---|---|
| Reduces hallucinations | 2-4x more LLM calls |
| Catches errors before user sees them | Adds latency |
| Self-improving output quality | Can over-correct (make things worse) |
| Configurable quality threshold | May never "pass" its own check |

---

## Practical Example: Financial Report Agent

```
GENERATE:
  "Q4 revenue was $12.3M, up 15% YoY. Operating margin improved
   to 22%. The company's P/E ratio is 45x."

REFLECT:
  Critique:
  - Revenue figure: UNVERIFIED — agent should cite data source
  - YoY growth: CALCULATION NOT SHOWN — could be hallucinated
  - P/E ratio: POSSIBLY STALE — needs current stock price

  Verdict: FAIL — financial figures need verification

REVISE:
  "Based on the Q4 earnings report (source: SEC filing 10-Q):
   - Q4 revenue: $12.3M (verified from filing)
   - YoY growth: 15% (Q4 2023: $10.7M → Q4 2024: $12.3M)
   - Operating margin: 22% (operating income $2.7M / revenue $12.3M)
   - P/E ratio: Requires current market data — flagged for human review"

REFLECT:
  Critique: PASS — figures sourced, calculations shown, uncertainty flagged
```

---

## Interview Questions They Will Ask

1. **"How do you reduce hallucinations in agent output?"**
   → Self-reflection: agent critiques its own output, checks for accuracy, completeness, and safety. Revises if issues found. Multiple iterations with a quality threshold.

2. **"Isn't self-reflection just the LLM checking itself? How is that reliable?"**
   → Good point — it's not perfect. Mitigations: use a separate critic agent (different model), structured rubrics with specific checks, external verification tools (fact-checking APIs, code execution for validation).

3. **"How many reflection iterations should you do?"**
   → 1-3 is the sweet spot. Beyond 3, you get diminishing returns and risk over-correction. Always set a max iteration limit.

4. **"When would you NOT use self-reflection?"**
   → Real-time conversations (latency), creative/subjective tasks (no "correct" answer), cost-sensitive scenarios (2-4x more expensive).

5. **"How do you measure if self-reflection is actually helping?"**
   → A/B test: compare output quality with and without reflection. Measure: accuracy, user satisfaction, error rate, hallucination rate.

---

## Common Mistakes

⚠️ **No max iteration limit** — Agent can loop forever critiquing and revising. Set max_iterations = 3.

⚠️ **Same model critiquing itself** — An LLM may not catch its own errors. Use a different model or external tools for verification.

⚠️ **Over-correction** — Each revision can introduce new errors. Sometimes the first draft is better. Track quality across iterations.

⚠️ **Vague reflection prompts** — "Is this good?" doesn't work. Use specific criteria: factual accuracy, completeness, safety, format compliance.

⚠️ **Reflecting on everything** — Only reflect on high-value outputs. Reflecting on a simple "hello" response is wasteful.

---

## TL;DR

- Self-reflection = **generate → critique → revise → repeat**
- Best for **high-stakes outputs** (financial, medical, code)
- Use **structured rubrics** for consistent evaluation
- Limit to **1-3 iterations** — diminishing returns beyond that
- Consider a **separate critic agent** for better error detection
