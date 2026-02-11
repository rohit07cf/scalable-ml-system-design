# Design: Safety and Policy Enforcement

## Problem Statement

Design a guardrail system that enforces content safety policies on both user inputs and LLM outputs, blocking or modifying responses that violate policy before they reach the end user.


## Key Requirements

- Evaluate every request and response against configurable policy rules (toxicity, PII, off-topic, jailbreak) with p99 under 200ms added latency
- Support layered enforcement: fast heuristic filters first, then model-based classifiers, with policy-specific actions (block, redact, warn, log-only)
- Allow per-product policy profiles so different applications can enforce different rule sets through configuration, not code changes


## Core Components

- Input scanner: runs pre-generation checks for prompt injection, jailbreak patterns, and disallowed content before the request reaches the LLM
- Output classifier: evaluates generated text against policy categories (toxicity, PII leakage, off-topic, harmful instructions) using specialized classifiers
- Policy engine: maps classifier verdicts to actions based on the product's policy profile (block, redact, fallback response, log-only)
- Redaction service: masks or removes PII and sensitive content from responses while preserving readability
- Audit trail and analytics: logs every enforcement decision with full context for compliance review, policy tuning, and false-positive analysis


## Key Trade-offs

- Pre-generation vs. post-generation enforcement: input scanning prevents waste on blocked requests but cannot catch hallucinated policy violations in the output
- Sensitivity vs. user experience: aggressive filtering reduces risk but increases false positives and frustrates legitimate users
- Centralized guardrail service vs. in-model alignment: external guardrails are auditable and model-agnostic but add latency; relying on model alignment alone is not auditable


## Must Explain in Interview

- Why you need both input and output guardrails and what each layer catches that the other cannot
- How you keep the fast-path latency low (heuristic pre-filters, async detailed classification for borderline cases)
- How policy profiles are structured so a children's product and an enterprise tool share infrastructure but enforce different rules
- How you detect and handle adversarial jailbreak prompts that evolve over time (updatable pattern lists, classifier retraining)
- How you measure guardrail effectiveness: false positive rate, false negative rate, and how you tune thresholds with human review
