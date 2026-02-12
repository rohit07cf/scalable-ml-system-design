# Environment-Aware Agents

## What It Is

- Agents that **perceive, adapt to, and act within their environment** in real-time
- They don't just process prompts — they monitor conditions, react to changes, and maintain situational awareness
- Inspired by the **OODA loop** (Observe-Orient-Decide-Act) from military strategy
- Examples: monitoring agents, trading agents, DevOps agents, security agents

## Why It Matters (Interview Framing)

> "Environment-aware agents are the next evolution beyond task-based agents. Interviewers ask about them when discussing real-time systems, autonomous operations, and continuous monitoring. This shows you understand agents that live in the world, not just respond to prompts."

---

## Simple Mental Model

> A task-based agent is like a **freelancer** — you give them a job, they do it, they're done.
> An environment-aware agent is like a **security guard** — they're always watching, always ready to act when something changes.

---

## How They Differ from Task-Based Agents

| Dimension | Task-Based Agent | Environment-Aware Agent |
|---|---|---|
| **Trigger** | User request | Environmental change / event |
| **Lifecycle** | Start → Execute → End | Always running (daemon) |
| **Input** | Prompt from user | Sensor data, metrics, events, feeds |
| **Awareness** | Task context only | Full environmental state |
| **Adaptation** | None (fixed task) | Adjusts behavior based on conditions |
| **Example** | "Summarize this doc" | "Alert me if server latency > 500ms" |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│         ENVIRONMENT-AWARE AGENT                   │
│                                                  │
│  ┌──────────┐                                    │
│  │ OBSERVE  │ ← Sensors / APIs / Events          │
│  │          │   (metrics, logs, feeds, state)     │
│  └────┬─────┘                                    │
│       │                                          │
│  ┌────▼─────┐                                    │
│  │  ORIENT  │ ← Context + Memory + Rules         │
│  │          │   "Is this normal? What changed?"   │
│  └────┬─────┘                                    │
│       │                                          │
│  ┌────▼─────┐                                    │
│  │  DECIDE  │ ← Policy + LLM Reasoning           │
│  │          │   "What should I do about this?"    │
│  └────┬─────┘                                    │
│       │                                          │
│  ┌────▼─────┐                                    │
│  │   ACT    │ ← Tools / Actions / Alerts         │
│  │          │   (scale infra, alert team, fix)    │
│  └────┬─────┘                                    │
│       │                                          │
│       └──────── continuous loop ─────────────────┘
└──────────────────────────────────────────────────┘
```

---

## The OODA Loop in Detail

| Phase | What the Agent Does | Example (DevOps Agent) |
|---|---|---|
| **Observe** | Collect data from sensors, APIs, events | Read Prometheus metrics, check logs |
| **Orient** | Contextualize — compare to baselines, history, rules | "Latency is 2x above 95th percentile for this time of day" |
| **Decide** | Choose action based on policy + reasoning | "This is likely a traffic spike. Scale up by 3 replicas." |
| **Act** | Execute the chosen action | `kubectl scale deployment --replicas=6` |

---

## Types of Environment-Aware Agents

### 1. Monitoring Agents

```
Metrics Stream → [Agent] → Detect Anomaly → Alert / Action
```

- Watch infrastructure, application, or business metrics
- Detect anomalies, threshold breaches, trend changes
- Alert humans or take automated remediation actions

### 2. Trading / Financial Agents

```
Market Feed → [Agent] → Analyze → Trade Decision → Execute
```

- Monitor market data, news, social sentiment
- Make trading decisions based on strategy + conditions
- Extreme latency and safety requirements

### 3. Security Agents

```
Log Stream → [Agent] → Threat Detection → Response
```

- Monitor security logs, network traffic, access patterns
- Detect suspicious activity, potential breaches
- Automated incident response (block IP, revoke token)

### 4. DevOps / SRE Agents

```
Infra State → [Agent] → Health Check → Auto-remediate
```

- Monitor infrastructure health
- Auto-scale, restart services, rollback deployments
- Reduce mean time to recovery (MTTR)

---

## Key Design Considerations

| Consideration | Details |
|---|---|
| **Observation frequency** | How often to check (1s? 1min? 5min?) — balance freshness vs cost |
| **State representation** | How to represent environment state for the LLM (structured vs natural language) |
| **Anomaly detection** | Statistical (threshold), ML-based (trained model), or LLM-based (reasoning) |
| **Action safety** | Automated actions must be reversible. Human approval for destructive actions. |
| **Feedback loops** | Agent's actions change the environment — must account for this |
| **Cost** | Continuous LLM calls are expensive. Use rule-based pre-filters. |

---

## Hybrid Architecture (Recommended)

```
┌─────────────────────────────────────────────────┐
│  Rule Engine (fast, cheap)                       │
│  - Threshold checks                             │
│  - Pattern matching                             │
│  - Known issue detection                        │
│                                                 │
│  Handles 90% of cases → Auto-action             │
│                                                 │
│  Escalates 10% to:                              │
│  ┌─────────────────────────────────────────┐    │
│  │  LLM Agent (smart, expensive)            │    │
│  │  - Complex reasoning                     │    │
│  │  - Novel situations                      │    │
│  │  - Root cause analysis                   │    │
│  │  - Natural language reporting             │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

💡 **Don't use LLM calls for every observation.** Use a rule engine for known patterns, escalate to LLM for novel situations. This cuts costs by 90%.

---

## Practical Example: SRE Agent

```python
class SREAgent:
    def __init__(self):
        self.rules = RuleEngine()
        self.llm = LLMAgent(model="gpt-4o-mini")
        self.memory = StateHistory(window="24h")

    def observe(self):
        """Collect current environment state"""
        return {
            "cpu": prometheus.query("avg(cpu_usage)"),
            "latency_p99": prometheus.query("histogram_quantile(0.99, ...)"),
            "error_rate": prometheus.query("rate(http_errors[5m])"),
            "active_pods": k8s.get_pod_count("production"),
            "recent_deploys": k8s.get_recent_deploys("1h")
        }

    def orient(self, state):
        """Compare to baselines and history"""
        baseline = self.memory.get_baseline(hour=now.hour, day=now.weekday())
        return {
            "cpu_deviation": state["cpu"] / baseline["cpu"],
            "latency_deviation": state["latency_p99"] / baseline["latency_p99"],
            "error_spike": state["error_rate"] > baseline["error_rate"] * 2,
            "recent_change": len(state["recent_deploys"]) > 0
        }

    def decide_and_act(self, state, context):
        """Rule engine first, LLM for complex cases"""
        # Rule-based (fast, cheap)
        action = self.rules.evaluate(state, context)
        if action:
            return self.execute(action)

        # LLM-based (smart, expensive)
        analysis = self.llm.reason(state, context, self.memory)
        if analysis.confidence > 0.8:
            return self.execute(analysis.action)
        else:
            return self.alert_human(analysis)
```

---

## Interview Questions They Will Ask

1. **"How do you design an agent that monitors infrastructure?"**
   → OODA loop: observe metrics, orient against baselines, decide action, act. Use rule engine for known patterns, LLM for novel situations. Continuous loop with configurable frequency.

2. **"How do you handle the cost of continuous LLM calls?"**
   → Hybrid architecture: rule engine handles 90% of observations (fast, cheap). LLM only invoked for complex, novel situations. Batch observations when possible.

3. **"What's the risk of agents taking automated actions?"**
   → Actions can cascade: agent scales up → costs spike. Always: reversible actions first, human approval for destructive actions, rollback capability, cost limits.

4. **"How does an environment-aware agent differ from a cron job?"**
   → Cron job runs fixed logic on a schedule. An environment-aware agent reasons about context, adapts to conditions, and makes judgment calls. The LLM enables handling novel situations a cron job can't.

5. **"What is the OODA loop?"**
   → Observe-Orient-Decide-Act. Military-origin decision loop. Key insight: the Orient phase (contextualizing data) is what makes it effective. Without context, raw data is useless.

---

## Common Mistakes

⚠️ **LLM for every observation** — Extremely expensive. Use rules for known patterns, LLM for novelty only.

⚠️ **No feedback loop awareness** — Agent's actions change the environment. If it scales up, metrics improve, it may scale down immediately. Account for action lag.

⚠️ **No action safety limits** — Agent can scale to 100 replicas or restart services in a loop. Always set action limits and cooldowns.

⚠️ **Stale baselines** — Environment-aware agents need up-to-date baselines. A baseline from 6 months ago may not reflect current normal behavior.

⚠️ **No human escalation** — Some situations are genuinely novel and dangerous. The agent must know when to escalate instead of acting.

---

## TL;DR

- Environment-aware agents **continuously monitor and react** to their environment
- Core loop: **Observe → Orient → Decide → Act** (OODA)
- Use **hybrid architecture:** rule engine (90%) + LLM (10%) to control costs
- Always have **action safety limits, cooldowns, and human escalation paths**
- Key difference from task agents: **always running, event-driven, context-aware**
