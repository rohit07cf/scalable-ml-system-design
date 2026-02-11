# Design: LLM Evaluation Framework

## Problem Statement

Design a scalable evaluation framework that scores LLM outputs across correctness, relevance, fluency, and safety using automated judges, human review, and regression benchmarks.


## Key Requirements

- Support multiple eval methods (model-based judges, heuristic checks, human annotation) behind a unified API
- Run evaluations on every prompt-template or model change and block deployments that regress below thresholds
- Return per-example scores with explanations so developers can debug failures, not just see aggregate numbers


## Core Components

- Eval registry: catalog of eval definitions (metric name, judge type, passing threshold, dataset reference)
- Dataset store: versioned golden sets, adversarial sets, and sampled production traffic for evaluation
- Judge orchestrator: dispatches each example to the configured judge (LLM-as-judge, regex, embedding similarity, human)
- Scoring pipeline: aggregates per-example results into suite-level pass/fail with confidence intervals
- Results dashboard and CI gate: visualizes trends over time and blocks merges or rollouts on regressions


## Key Trade-offs

- LLM-as-judge vs. human annotation: automated judges scale but introduce their own biases; human review is accurate but slow and expensive
- Comprehensive suites vs. evaluation speed: more test cases catch more regressions but slow the development loop
- Generic metrics vs. task-specific metrics: reusable scorers (fluency, coherence) are convenient but miss domain-specific failure modes


## Must Explain in Interview

- How you version eval datasets alongside prompt templates so results are reproducible
- Why LLM-as-judge needs calibration and how you detect judge drift over time
- How you set passing thresholds: baseline from current production, not arbitrary numbers
- How the framework plugs into CI/CD to gate deployments on eval regressions
- How you handle disagreement between automated judges and human reviewers (tie-breaking, escalation)
