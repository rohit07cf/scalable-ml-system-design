# Hallucination Detection

## What It Is

- **Hallucination** = agent generating information that is factually incorrect, unsupported by context, or completely fabricated
- The #1 reliability problem in LLM-based agent systems
- Types: factual errors, fabricated citations, made-up numbers, invented entities
- Detection requires a combination of automated and manual approaches

## Why It Matters (Interview Framing)

> "Hallucination detection is always asked in AI engineer interviews. It's the biggest trust barrier for enterprise adoption. Show you understand the types of hallucination, detection methods, and mitigation strategies."

---

## Types of Hallucination

| Type | Description | Example | Severity |
|---|---|---|---|
| **Factual** | States incorrect facts | "Python was created in 2005" (actually 1991) | High |
| **Fabricated citation** | Invents sources that don't exist | "According to Smith et al., 2023..." (paper doesn't exist) | High |
| **Numerical** | Makes up numbers | "Revenue was $15.2M" (actual: $12.3M) | Critical |
| **Entity** | Invents people, companies, products | "Competitor XyzCorp offers..." (doesn't exist) | High |
| **Unfaithful** | Output contradicts provided context | Context says "30-day policy", output says "60-day policy" | Critical |
| **Extrapolation** | Makes claims beyond available data | "This trend will continue for 5 years" (no evidence) | Medium |

💡 **In agent systems, hallucinations are worse than in chatbots because agents can ACT on hallucinated information** — calling APIs with wrong parameters, making decisions on fake data.

---

## Detection Methods

### Method 1: Faithfulness Check (Context Grounding)

```
Context: "Our refund policy allows returns within 30 days"
Output: "You can return items within 60 days for a full refund"

Faithfulness Check:
  - Claim: "60 days" → NOT in context (context says 30 days)
  - Result: HALLUCINATION DETECTED
  - Score: 0.0 (unfaithful)
```

**Implementation:**

```python
def check_faithfulness(context, output, judge_llm):
    """Check if output is grounded in the provided context"""

    # Step 1: Extract claims from output
    claims = judge_llm.call(
        f"Extract all factual claims from this text:\n{output}"
    )

    # Step 2: Verify each claim against context
    results = []
    for claim in claims:
        verdict = judge_llm.call(
            f"Context: {context}\n"
            f"Claim: {claim}\n"
            f"Can this claim be supported by the context? (yes/no/partially)"
        )
        results.append(verdict)

    # Step 3: Calculate score
    supported = sum(1 for r in results if r == "yes")
    return supported / len(results)  # 0.0 to 1.0
```

---

### Method 2: Self-Consistency Check

```
Ask the same question 3 times:
  Response 1: "Revenue was $12.3M"
  Response 2: "Revenue was $12.3M"
  Response 3: "Revenue was $15.1M"  ← Inconsistent!

If answers disagree → likely hallucination
If answers agree → more likely correct (not guaranteed)
```

- Generate N responses for the same query
- Check consistency across responses
- Inconsistency = low confidence = possible hallucination
- More expensive but effective (N × cost)

---

### Method 3: External Verification

```
Agent claims: "Acme Corp was founded in 2019"
    │
    ▼
Verification tool: web_search("Acme Corp founded year")
    │
    ▼
Result: "Acme Corp was founded in 2017"
    │
    ▼
Verdict: HALLUCINATION (2019 ≠ 2017)
```

- Use external tools (search, databases, APIs) to verify claims
- Most reliable but most expensive and slow
- Not feasible for every claim — use selectively for critical outputs

---

### Method 4: LLM-as-Judge

```python
JUDGE_PROMPT = """
You are a hallucination detector. Evaluate the following output.

Source context: {context}
Agent output: {output}

For each factual claim in the output, classify as:
- SUPPORTED: Claim is directly supported by the context
- NOT_SUPPORTED: Claim is not in the context but not contradicted
- CONTRADICTED: Claim directly contradicts the context
- FABRICATED: Claim appears to be invented (fake citations, entities)

Output your analysis as JSON.
"""
```

---

### Method 5: Entropy / Confidence Based

- High token-level uncertainty (entropy) correlates with hallucination risk
- If the LLM is "unsure" about a token, it's more likely hallucinating
- Requires access to log probabilities (available from some APIs)
- Use as a signal, not as a definitive detector

---

## Detection Pipeline

```
┌──────────────────────────────────────────────────────┐
│           HALLUCINATION DETECTION PIPELINE            │
│                                                      │
│  Agent Output                                        │
│       │                                              │
│  ┌────▼────────────────┐                             │
│  │ 1. Claim Extraction │ Extract factual claims      │
│  └────┬────────────────┘                             │
│       │                                              │
│  ┌────▼────────────────┐                             │
│  │ 2. Faithfulness     │ Check claims vs context     │
│  │    Check            │ (fast, cheap)               │
│  └────┬────────────────┘                             │
│       │                                              │
│       ├── All supported → PASS ✅                     │
│       │                                              │
│       ├── Some unsupported:                          │
│       │                                              │
│  ┌────▼────────────────┐                             │
│  │ 3. External Verify  │ Verify with search/DB      │
│  │    (for critical    │ (slower, more reliable)     │
│  │     claims only)    │                             │
│  └────┬────────────────┘                             │
│       │                                              │
│       ├── Verified → PASS ✅                          │
│       └── Not verified → FLAG ⚠️ → Human review       │
│                          or auto-remove claim        │
└──────────────────────────────────────────────────────┘
```

---

## Mitigation Strategies

| Strategy | How It Helps |
|---|---|
| **RAG (retrieval)** | Ground responses in real documents — reduces factual hallucination |
| **Self-reflection** | Agent critiques its own output before returning |
| **Source attribution** | Force agent to cite sources — easier to verify |
| **Confidence scoring** | Agent rates its own confidence — low confidence = flag for review |
| **Constrained generation** | Limit agent to structured output (JSON, tables) — harder to hallucinate |
| **Temperature = 0** | Reduce randomness — more deterministic, fewer hallucinations |
| **Prompt engineering** | "Only state facts from the provided context. Say 'I don't know' if unsure" |

---

## Practical Example: Financial Report Hallucination Check

```python
def validate_financial_report(report, source_data):
    """Check financial report for hallucinated numbers"""

    # Extract all numbers from report
    numbers = extract_numbers(report)
    # e.g., [("revenue", "$12.3M"), ("growth", "15%"), ("margin", "22%")]

    violations = []
    for label, value in numbers:
        # Check against source data
        source_value = source_data.get(label)

        if source_value is None:
            violations.append(f"FABRICATED: {label}={value} not in source data")
        elif not values_match(value, source_value, tolerance=0.01):
            violations.append(
                f"INCORRECT: {label}={value}, source says {source_value}"
            )

    if violations:
        return {"status": "HALLUCINATION_DETECTED", "violations": violations}
    return {"status": "PASS"}
```

---

## Interview Questions They Will Ask

1. **"How do you detect hallucinations in agent output?"**
   → Multi-layered: faithfulness check (output vs context), self-consistency (multiple generations), LLM-as-judge, external verification for critical claims. Use a pipeline — cheap checks first, expensive checks for flagged items.

2. **"What's the difference between unfaithful and factual hallucination?"**
   → Unfaithful: output contradicts the provided context. Factual: output states false facts (even without context). RAG helps with unfaithfulness. External verification helps with factual.

3. **"How do you prevent hallucinations?"**
   → RAG (ground in documents), low temperature, explicit prompting ("only use provided context"), source attribution, self-reflection loop, constrained output format.

4. **"Can you fully eliminate hallucinations?"**
   → No. LLMs are probabilistic — hallucination is inherent. You can reduce it significantly (RAG + reflection + verification), but never to zero. Design systems that are resilient to occasional hallucination (verification layers, human review for critical outputs).

5. **"How do you measure hallucination rate?"**
   → Faithfulness score from Ragas or similar tool on a representative sample. Continuous evaluation on production traffic. Human annotation for calibration.

---

## Common Mistakes

⚠️ **Assuming RAG eliminates hallucination** — RAG reduces it, but the LLM can still hallucinate beyond the retrieved context.

⚠️ **No detection at all** — "The model is usually right" is not a strategy. Measure and monitor.

⚠️ **Checking every claim with expensive methods** — Use tiered detection: cheap faithfulness check first, expensive external verification only for critical or flagged claims.

⚠️ **Using the same model for generation and detection** — The model may not catch its own errors. Use a different model or approach for verification.

⚠️ **Not tracking hallucination rate over time** — Model updates, prompt changes, and data changes can all increase hallucination. Monitor continuously.

---

## TL;DR

- **Hallucination** = fabricated, incorrect, or unsupported output — the #1 agent reliability risk
- **Detection methods:** Faithfulness check, self-consistency, external verification, LLM-as-judge
- **Use a tiered pipeline:** cheap checks first, expensive verification for critical claims
- **Mitigation:** RAG, self-reflection, source attribution, low temperature, constrained output
- **Cannot be fully eliminated** — design systems that are resilient to occasional hallucination
