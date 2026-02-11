# Design: Enterprise Knowledge Copilot

## Problem Statement

Design a copilot that helps employees find, reason over, and act on information spread across an enterprise's internal tools, documents, and databases.


## Key Requirements

- Unified access across heterogeneous sources: wikis, Slack, Jira, Google Drive, SQL databases
- Strict access control: users must only see information they are authorized to access
- Actionable outputs: not just answers, but drafts, tickets, summaries, and workflow triggers


## Core Components

- Connector layer ingesting and indexing content from 10+ enterprise data sources
- Permission-aware retrieval that filters results based on the requesting user's access rights
- Agentic orchestrator that decomposes complex queries into retrieval, reasoning, and action steps
- Action execution layer: creating tickets, drafting emails, updating documents via tool integrations
- Audit and compliance module logging every query, retrieval, and action for governance


## Key Trade-offs

- Real-time sync with source systems for freshness vs batch indexing for cost and simplicity
- Per-query permission checks (accurate, slow) vs pre-filtered per-user indexes (fast, storage-heavy)
- Open-ended agent actions for power vs constrained action sets for safety and auditability


## Must Explain in Interview

- How you enforce access control at retrieval time across sources with different permission models
- How the connector layer handles schema differences and update frequencies across 10+ sources
- How the agent decides whether to retrieve, reason, or take an action, and how you constrain it
- Why audit logging is non-negotiable and what you capture (query, sources accessed, actions taken, user)
- How you handle stale data: what happens when a retrieved document has been updated or deleted since indexing
