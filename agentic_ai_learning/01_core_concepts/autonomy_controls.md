# Autonomy Controls

## What It Is

- **Autonomy controls** = mechanisms that constrain what an agent can do, when, and how much
- The spectrum from "fully supervised" to "fully autonomous"
- Includes guardrails, human-in-the-loop (HITL), safety layers, and ethical constraints
- The goal: **maximize agent capability while minimizing risk**

## Why It Matters (Interview Framing)

> "Any engineer can build an agent that works in a demo. The interview question is: how do you make it safe for production? Autonomy controls are the difference between a cool prototype and a deployable system."

---

## Simple Mental Model

> Think of autonomy controls like **driver assistance levels:**
>
> | Level | Driving Analogy | Agent Analogy |
> |---|---|---|
> | L0 | Manual driving | User does everything, LLM just suggests |
> | L1 | Cruise control | Agent executes simple tasks, user approves |
> | L2 | Lane assist + cruise | Agent handles routine tasks, escalates edge cases |
> | L3 | Conditional autonomy | Agent works independently in defined scope |
> | L4 | Full self-driving (limited area) | Agent fully autonomous in constrained domain |
> | L5 | Full autonomy anywhere | Fully autonomous agent (not recommended today) |

💡 **Most production agents are L2-L3.** L5 is aspirational, not practical.

---

## The Four Control Mechanisms

### 1. Guardrails

```
User Input → [Input Guardrail] → Agent → [Output Guardrail] → Response
                  │                              │
                  ▼                              ▼
            Block/modify                   Block/modify
            harmful input                  harmful output
```

**Types of guardrails:**

| Guardrail | What It Does | Example |
|---|---|---|
| **Input validation** | Block harmful/out-of-scope prompts | Reject prompt injection attempts |
| **Output filtering** | Block harmful/incorrect responses | Filter PII, profanity, hallucinations |
| **Tool restrictions** | Limit which tools agent can call | No DELETE operations, read-only DB access |
| **Budget limits** | Cap token/API/cost spend | Max $0.50 per agent run |
| **Scope boundaries** | Restrict agent to specific domains | Customer support agent can't access HR data |

```python
# Example: Guardrail configuration
guardrails = {
    "max_tokens_per_run": 50000,
    "max_tool_calls": 20,
    "max_cost_usd": 1.00,
    "allowed_tools": ["search_kb", "get_order", "send_email"],
    "blocked_actions": ["delete_*", "admin_*"],
    "pii_filter": True,
    "content_filter": True
}
```

---

### 2. Human-in-the-Loop (HITL)

```
Agent works autonomously
    │
    ├── Low-risk action → Execute automatically
    │
    ├── Medium-risk action → Notify human, continue
    │
    └── High-risk action → PAUSE, wait for human approval
                              │
                              ├── Human approves → Continue
                              └── Human rejects → Abort or modify
```

**HITL patterns:**

| Pattern | Description | Use Case |
|---|---|---|
| **Approval gates** | Agent pauses for human approval before critical actions | Financial transactions, data deletion |
| **Escalation** | Agent hands off to human when confidence is low | Customer support edge cases |
| **Audit trail** | Human reviews after-the-fact | Compliance, regulated industries |
| **Collaborative** | Human and agent work together in real-time | Code review, document editing |

💡 **HITL is not a failure of the agent — it's a design feature.** The best agents know when to ask for help.

---

### 3. Safety Layers

```
┌───────────────────────────────────────┐
│           SAFETY STACK                 │
├───────────────────────────────────────┤
│  Layer 4: Business Rules              │
│   "Never offer refunds > $500"        │
├───────────────────────────────────────┤
│  Layer 3: Content Safety              │
│   PII detection, toxicity filter      │
├───────────────────────────────────────┤
│  Layer 2: Tool Safety                 │
│   Permission checks, rate limits      │
├───────────────────────────────────────┤
│  Layer 1: Prompt Safety               │
│   Injection detection, jailbreak      │
│   detection                           │
└───────────────────────────────────────┘
```

- Safety is **defense in depth** — multiple layers, each catches different threats
- No single layer is sufficient on its own
- Each layer should fail independently

---

### 4. Ethical Constraints

- **Fairness:** Agent doesn't discriminate based on protected attributes
- **Transparency:** Agent explains its reasoning when asked
- **Privacy:** Agent respects data minimization and retention policies
- **Accountability:** Every action is logged and attributable
- **Harm prevention:** Agent refuses requests that could cause harm

---

## Designing Autonomy Levels

```
┌─────────────────────────────────────────────────┐
│         AUTONOMY DECISION MATRIX                 │
├──────────┬──────────┬──────────┬────────────────┤
│          │ Low Risk │ Med Risk │ High Risk      │
├──────────┼──────────┼──────────┼────────────────┤
│High Conf │ Auto     │ Auto +   │ Approval gate  │
│          │ execute  │ notify   │                │
├──────────┼──────────┼──────────┼────────────────┤
│Med Conf  │ Auto +   │ Approval │ Escalate to    │
│          │ log      │ gate     │ human          │
├──────────┼──────────┼──────────┼────────────────┤
│Low Conf  │ Approval │ Escalate │ BLOCK          │
│          │ gate     │ to human │                │
└──────────┴──────────┴──────────┴────────────────┘
```

- **Confidence** = how sure the agent is about its decision
- **Risk** = potential impact if the action is wrong
- Combine both to determine the right autonomy level

---

## Practical Example: Financial Agent Controls

```python
class FinancialAgentControls:
    def check_action(self, action):
        # Layer 1: Scope check
        if action.type not in ALLOWED_ACTIONS:
            return Block("Action not in scope")

        # Layer 2: Amount check
        if action.amount > 500:
            return RequireApproval(
                reason=f"Transaction ${action.amount} exceeds $500 limit"
            )

        # Layer 3: Anomaly check
        if self.is_anomalous(action):
            return Escalate(
                reason="Unusual pattern detected",
                to="risk_team"
            )

        # Layer 4: Rate limit
        if self.daily_total + action.amount > 10000:
            return Block("Daily limit exceeded")

        return Approve()
```

---

## Interview Questions They Will Ask

1. **"How do you decide how much autonomy to give an agent?"**
   → Risk-based matrix: combine action risk level with agent confidence. High risk + low confidence = human approval required.

2. **"What guardrails would you put on a production agent?"**
   → Input validation, output filtering, tool restrictions, budget caps, PII detection, scope boundaries, rate limits.

3. **"How do you implement human-in-the-loop?"**
   → Approval gates for high-risk actions. Escalation paths for low-confidence situations. Async approval via Slack/email for non-blocking flows.

4. **"What happens when an agent tries to do something it shouldn't?"**
   → Defense in depth: the guardrail closest to the action blocks it. Log the attempt. Alert the team. The agent receives an error and re-plans.

5. **"How do you balance autonomy with safety?"**
   → Start restrictive (L1-L2), measure failure rates, gradually increase autonomy. Always keep a human escalation path. Never go full L5 in regulated domains.

---

## Common Mistakes

⚠️ **No guardrails at all** — "It works in the demo" is not a production safety strategy.

⚠️ **Binary thinking** — It's not "autonomous" vs "not autonomous." Design a spectrum with appropriate gates at each level.

⚠️ **Guardrails only on output** — You need input validation too. Prompt injection is real.

⚠️ **HITL that blocks everything** — If every action needs approval, the agent is useless. Reserve HITL for genuinely high-risk actions.

⚠️ **No logging** — If you can't audit what the agent did and why, you can't debug, improve, or comply with regulations.

---

## TL;DR

- **Autonomy is a spectrum** (L0-L5) — most production agents are L2-L3
- Four control mechanisms: **Guardrails, HITL, Safety Layers, Ethical Constraints**
- Use a **risk × confidence matrix** to set autonomy levels per action
- **Defense in depth** — multiple safety layers, each independent
- Start restrictive, **gradually increase autonomy** based on measured reliability
