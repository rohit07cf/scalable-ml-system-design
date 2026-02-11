# Design: Enterprise Chatbot

## Problem Statement

Design a multi-turn conversational AI system for enterprise customer support with access to internal knowledge bases.


## Key Requirements

- Sub-2-second response latency for user-facing interactions
- Multi-turn conversation with memory across sessions
- Role-based access control over knowledge sources and actions


## Core Components

- Conversation orchestrator managing turn-taking, context window, and routing
- RAG pipeline retrieving from internal docs, FAQs, and ticket history
- Guardrails layer for content safety, PII redaction, and hallucination detection
- Session store persisting conversation history and user context
- Feedback loop collecting thumbs-up/down signals for continuous improvement


## Key Trade-offs

- Streaming responses for perceived speed vs waiting for full generation to apply safety filters
- Long conversation history for coherence vs truncation to fit context limits and reduce cost
- Deterministic scripted flows for compliance vs open-ended LLM generation for flexibility


## Must Explain in Interview

- How you manage context window budget across system prompt, retrieved docs, and conversation history
- Why you need a separate guardrails pass and where it sits in the pipeline (pre-generation vs post-generation)
- How session memory works: what gets stored, what gets summarized, what gets evicted
- How you handle fallback when the model cannot answer confidently (escalation to human agent)
- How you evaluate chatbot quality: offline metrics (relevance, groundedness) vs online metrics (resolution rate, CSAT)
