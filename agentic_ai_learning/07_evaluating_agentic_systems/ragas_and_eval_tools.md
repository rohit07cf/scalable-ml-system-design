# Evaluation Tools: Ragas, TruLens, DeepEval & More

## What It Is

- **Evaluation frameworks** that automate quality assessment of agent and RAG outputs
- They measure: faithfulness, relevance, hallucination, context quality, and more
- Essential for continuous evaluation in production — you can't manually review every output
- The tooling is maturing fast — know the key players and when to use each

## Why It Matters (Interview Framing)

> "When an interviewer asks 'How do you evaluate your RAG/agent system?', naming specific tools and metrics shows you've built production systems. Ragas for RAG quality, TruLens for general LLM apps, DeepEval for unit testing — know when to use each."

---

## Tool Comparison

| Tool | Focus | Best For | Metrics | Self-hosted? |
|---|---|---|---|---|
| **Ragas** | RAG evaluation | RAG pipeline quality | Faithfulness, relevance, context precision/recall | Yes (OSS) |
| **TruLens** | LLM app evaluation | General LLM app feedback | Groundedness, relevance, sentiment | Yes (OSS) |
| **DeepEval** | LLM unit testing | CI/CD integration | 14+ metrics, custom metrics | Yes (OSS) |
| **Arize Phoenix** | Tracing + eval | Full observability | Traces + evals + embeddings | Yes (OSS) |
| **LangSmith** | LangChain ecosystem | LangChain/LangGraph apps | Custom evals, traces, datasets | Managed |
| **Braintrust** | Eval + prompt mgmt | Prompt optimization | Custom scoring, experiments | Managed |

---

## Ragas (RAG Assessment)

**What it measures:**

```
┌─────────────────────────────────────────────────┐
│                 RAGAS METRICS                     │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │  FAITHFULNESS     │  │  ANSWER RELEVANCE│    │
│  │  Is the answer    │  │  Does the answer │    │
│  │  supported by     │  │  address the     │    │
│  │  the context?     │  │  question?       │    │
│  │  Score: 0-1       │  │  Score: 0-1      │    │
│  └──────────────────┘  └──────────────────┘    │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │ CONTEXT PRECISION│  │ CONTEXT RECALL   │    │
│  │ Is the retrieved │  │ Was all needed   │    │
│  │ context relevant?│  │ context retrieved?│   │
│  │ Score: 0-1       │  │  Score: 0-1      │    │
│  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────┘
```

**Usage:**

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

# Prepare evaluation dataset
eval_dataset = {
    "question": ["What is our refund policy?"],
    "answer": ["You can get a full refund within 30 days..."],
    "contexts": [["Policy doc: Refunds are available within 30 days..."]],
    "ground_truth": ["Full refund within 30 days of purchase"]
}

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)

# Results:
# faithfulness: 0.95
# answer_relevancy: 0.92
# context_precision: 0.88
# context_recall: 0.90
```

**When to use Ragas:**
- Evaluating RAG pipeline quality
- Comparing chunking strategies
- Comparing embedding models
- Continuous monitoring of RAG degradation

---

## TruLens

**What it measures:**

| Metric | Description |
|---|---|
| **Groundedness** | Is the output grounded in the source material? |
| **Answer relevance** | Does the output address the question? |
| **Context relevance** | Is the retrieved context relevant to the question? |
| **Sentiment** | What's the tone of the output? |
| **Custom feedback** | Define your own evaluation functions |

**Usage:**

```python
from trulens_eval import TruChain, Feedback, Tru

# Define feedback functions
f_groundedness = Feedback(
    provider.groundedness_measure_with_cot_reasons
).on(context).on_output()

f_relevance = Feedback(
    provider.relevance
).on_input().on_output()

# Wrap your chain
tru_chain = TruChain(
    chain,
    feedbacks=[f_groundedness, f_relevance],
    app_id="my_agent_v1"
)

# Run and evaluate
result = tru_chain.invoke("What is our refund policy?")

# View results in TruLens dashboard
Tru().run_dashboard()
```

**When to use TruLens:**
- General LLM application evaluation (not just RAG)
- Need feedback dashboard
- Want to track quality across app versions

---

## DeepEval

**What it is:** Unit testing framework for LLM outputs. Integrates with pytest.

```python
import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric
)
from deepeval.test_case import LLMTestCase

def test_agent_output():
    test_case = LLMTestCase(
        input="What is our refund policy?",
        actual_output="Full refund within 30 days of purchase.",
        retrieval_context=["Policy: Refunds available within 30 days..."]
    )

    relevancy = AnswerRelevancyMetric(threshold=0.7)
    faithfulness = FaithfulnessMetric(threshold=0.8)
    hallucination = HallucinationMetric(threshold=0.5)

    assert_test(test_case, [relevancy, faithfulness, hallucination])

# Run with: pytest test_agent.py
```

**When to use DeepEval:**
- CI/CD pipeline integration (runs in pytest)
- Regression testing (new prompt/model doesn't break quality)
- Specific test cases you want to guard against

💡 **DeepEval in CI/CD is the gold standard for preventing quality regressions.**

---

## Arize Phoenix

**What it is:** Open-source observability + evaluation tool.

- **Tracing:** Visualize every step of agent execution
- **Evaluation:** Score outputs on quality metrics
- **Embedding analysis:** Visualize embedding drift
- **Integration:** Works with OpenAI, LangChain, LlamaIndex, etc.

**When to use Phoenix:**
- Need both tracing AND evaluation in one tool
- Want to visualize embeddings and detect drift
- Self-hosted requirement

---

## LangSmith

**What it is:** LangChain's managed evaluation and monitoring platform.

- **Tracing:** First-class LangChain/LangGraph integration
- **Datasets:** Manage evaluation datasets
- **Evaluators:** Run custom and built-in evaluators
- **Experiments:** Compare different prompts/models
- **Human feedback:** Annotate outputs

**When to use LangSmith:**
- Building with LangChain/LangGraph
- Need managed platform (don't want to self-host)
- Want prompt experimentation workflow

---

## Evaluation Pipeline Architecture

```
┌──────────────────────────────────────────────────────┐
│              EVALUATION PIPELINE                      │
│                                                      │
│  DEVELOPMENT:                                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Test Cases  │─▶│  DeepEval  │─▶│ CI/CD Gate   │  │
│  │ (pytest)    │  │  (scoring) │  │ (pass/fail)  │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
│                                                      │
│  STAGING:                                            │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Eval Dataset│─▶│   Ragas    │─▶│ Benchmark    │  │
│  │ (100+ cases)│  │  (scoring) │  │ vs baseline  │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
│                                                      │
│  PRODUCTION:                                         │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Live traffic│─▶│  TruLens   │─▶│ Drift Alert  │  │
│  │ (sampled)   │  │  (ongoing) │  │ Dashboard    │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## Practical Example: Eval-Driven Development

```python
# 1. Define test cases from real failures
test_cases = [
    {"input": "What's our refund policy?",
     "expected": "30-day full refund",
     "context": "Refund policy document"},

    {"input": "Can I return after 60 days?",
     "expected": "No, refund window is 30 days",
     "context": "Refund policy document"},

    # Edge case: ambiguous question
    {"input": "What about returns?",
     "expected": "Should ask: product returns or financial refunds?",
     "context": "Both return and refund policies"}
]

# 2. Run eval suite before each deploy
# 3. Block deploy if scores drop below threshold
# 4. Add new test cases from production failures
```

---

## Interview Questions They Will Ask

1. **"How do you evaluate RAG quality?"**
   → Ragas: faithfulness (answer grounded in context), answer relevancy (addresses question), context precision (relevant docs retrieved), context recall (all needed docs found). Continuous scoring.

2. **"How do you integrate evaluation into CI/CD?"**
   → DeepEval with pytest. Define test cases, set thresholds. Pipeline fails if quality scores drop below threshold. Prevents deploying quality regressions.

3. **"What's the difference between Ragas and TruLens?"**
   → Ragas is RAG-specific (faithfulness, context quality). TruLens is general-purpose (any LLM app). Use Ragas for RAG pipelines, TruLens for general agents.

4. **"How do you build an evaluation dataset?"**
   → Start with 50-100 representative queries. Include: happy path, edge cases, adversarial inputs. Add ground truth answers. Grow dataset from production failures.

5. **"How do you evaluate without ground truth?"**
   → LLM-as-judge: use a strong model to score outputs. Ragas metrics don't always need ground truth (faithfulness checks answer vs context). Human eval for calibration.

---

## Common Mistakes

⚠️ **No evaluation at all** — "It seems to work" is not evaluation. Measure quality systematically.

⚠️ **Evaluation only in development** — Quality degrades in production. Continuous evaluation is essential.

⚠️ **Too few test cases** — 10 test cases can't cover real-world diversity. Aim for 100+ across categories.

⚠️ **Not adding production failures to test set** — Every production failure should become a test case.

⚠️ **Only automated eval, no human review** — Automated metrics have blind spots. Periodically validate with human review.

---

## TL;DR

- **Ragas** = RAG-specific evaluation (faithfulness, relevance, context quality)
- **TruLens** = general LLM app evaluation with dashboard
- **DeepEval** = pytest-integrated LLM unit testing (best for CI/CD)
- **Phoenix** = open-source tracing + eval (best for self-hosted)
- Build an **evaluation pipeline:** DeepEval in CI/CD, Ragas in staging, TruLens in production
