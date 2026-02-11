# Design: Cost and Token Analytics

## Problem Statement

Design an observability system that tracks per-request and aggregate token usage, maps it to dollar cost, and provides alerting and budgeting controls across teams and products.


## Key Requirements

- Capture input/output token counts, model used, and computed cost for every LLM request with sub-second ingestion lag
- Provide per-team, per-product, and per-feature cost breakdowns with configurable budget alerts and hard spending caps
- Support cost forecasting based on traffic trends so teams can plan capacity and negotiate model pricing


## Core Components

- Instrumentation layer: middleware or SDK that logs token counts, model ID, latency, and request metadata on every call
- Cost calculator: maps (model, token count, request type) to dollar cost using a rate card that updates when pricing changes
- Aggregation pipeline: streaming aggregation (e.g., Flink or ClickHouse materialized views) for real-time dashboards and hourly rollups
- Budget enforcement service: compares running spend against per-team budgets and triggers alerts, throttling, or model downgrade at thresholds
- Forecasting module: projects future spend from recent trends and planned feature launches


## Key Trade-offs

- Real-time cost tracking vs. infrastructure cost: streaming aggregation gives instant visibility but is more expensive to run than batch ETL
- Hard budget caps vs. soft alerts: hard caps prevent overruns but can block user-facing traffic unexpectedly during spikes
- Per-request attribution vs. sampling: logging every request gives exact numbers but at high volume the telemetry pipeline itself becomes a cost center


## Must Explain in Interview

- How you handle multi-model chains where a single user request triggers several LLM calls (nested cost attribution)
- How budget enforcement avoids race conditions when many requests arrive simultaneously near a budget limit
- How you update the rate card when providers change pricing without reprocessing historical data
- How you design dashboards that let a team lead see cost-per-feature, not just cost-per-model
- How forecasting accounts for traffic seasonality and planned rollouts of new features
