# Evaluation Basics

## What This Covers

How to measure whether an ML system is actually working.


## Key Concepts

- Offline evaluation: held-out sets, backtesting, human annotation
- Online evaluation: A/B tests, shadow mode, interleaving experiments
- Metric selection: choosing what to measure and what to optimize


## Core Components

- Classification metrics: precision, recall, F1, AUC-ROC
- Ranking metrics: NDCG, MRR, MAP
- Generation metrics: BLEU, ROUGE, human preference, LLM-as-judge
- Statistical significance and sample size reasoning
- Guardrail metrics vs primary metrics in experiments


## Key Trade-offs

- Automated metrics (cheap, fast) vs human evaluation (expensive, reliable)
- Optimizing one metric often degrades another (precision vs recall)
- Offline gains do not always translate to online improvements


## Must Explain in Interview

- Why you need both offline and online evaluation, not just one
- How to choose between precision-oriented and recall-oriented metrics
- What LLM-as-judge is and when it is appropriate vs human eval
- How to size an A/B test and when results are trustworthy
- Common pitfalls: data leakage, label bias, metric gaming
