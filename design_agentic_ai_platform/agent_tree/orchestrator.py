"""
Supervisor orchestration loop — the async runtime that drives the agent tree.

Ported from reference:
  - configurable_agent/hooks.py        → OrchestratorHooks (two-tier: agent + tool + reasoning)
  - configurable_agent/main.py         → plan-then-execute pipeline
  - configurable_agent/sdk_agents.py   → supervisor calls children as tools
  - configurable_agent/workflows.py    → two-phase workflow (plan → orchestrate)

Flow:
  1. (Optional) Planner produces a structured plan from user input
  2. Supervisor receives input (+ plan if available)
  3. Routes to a child agent (keyword routing — swap for LLM routing later)
  4. Child executes (may call tools internally), returns validated HandoffResult
  5. Supervisor inspects result, decides: done / re-route / enrich input / fail
  6. Returns a SupervisorResult with all collected handoffs + the plan

WHY async:  LLM + tool calls are I/O-bound.  Async keeps the event loop
            free for streaming hooks and concurrent activities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from .agent_node import AgentNode
from .agent_tree import AgentTree
from .handoff_models import HandoffResult, ToolResult, SupervisorResult


# ── Hook protocol ──────────────────────────────────────────────────────────
# Two-tier hooks mirroring the reference's MyAgentHooks + MyRunHooks +
# ReasoningHooks.  All optional — unset hooks are zero-cost no-ops.

@dataclass
class OrchestratorHooks:
    """Lifecycle hooks fired during orchestration.

    Three tiers (matching the reference):
      1. Agent-level:  on_node_start, on_node_end, on_handoff
      2. Tool-level:   on_tool_start, on_tool_end
      3. Reasoning:    on_reasoning_step

    Set any of these to an async callable to receive events.
    Unset hooks are no-ops (zero overhead).
    """

    # -- Agent lifecycle (reference: MyAgentHooks)
    on_node_start: Callable[[AgentNode, str], Awaitable[None]] | None = None
    on_node_end: Callable[[AgentNode, HandoffResult], Awaitable[None]] | None = None
    on_handoff: Callable[[HandoffResult], Awaitable[None]] | None = None

    # -- Tool lifecycle (reference: MyRunHooks.on_tool_start / on_tool_end)
    on_tool_start: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None
    on_tool_end: Callable[[str, ToolResult], Awaitable[None]] | None = None

    # -- Reasoning lifecycle (reference: ReasoningHooks.on_reasoning_step)
    on_reasoning_step: Callable[[str, str], Awaitable[None]] | None = None

    # ── Fire helpers (null-safe dispatch) ──────────────────────────────

    async def fire_node_start(self, node: AgentNode, user_input: str) -> None:
        if self.on_node_start:
            await self.on_node_start(node, user_input)

    async def fire_node_end(self, node: AgentNode, result: HandoffResult) -> None:
        if self.on_node_end:
            await self.on_node_end(node, result)

    async def fire_handoff(self, result: HandoffResult) -> None:
        if self.on_handoff:
            await self.on_handoff(result)

    async def fire_tool_start(self, tool_name: str, args: dict[str, Any]) -> None:
        if self.on_tool_start:
            await self.on_tool_start(tool_name, args)

    async def fire_tool_end(self, tool_name: str, result: ToolResult) -> None:
        if self.on_tool_end:
            await self.on_tool_end(tool_name, result)

    async def fire_reasoning_step(self, agent_name: str, thought: str) -> None:
        if self.on_reasoning_step:
            await self.on_reasoning_step(agent_name, thought)


# ── Planner type ───────────────────────────────────────────────────────────
# Mirrors the reference's call_reasoner() / planner_activity.
# Signature:  async (user_input: str) -> dict
#   Returns a JSON-serialisable plan that gets prepended to the user input.
PlannerCallable = Callable[[str], Awaitable[dict[str, Any]]]


# ── Supervisor Orchestrator ────────────────────────────────────────────────

@dataclass
class SupervisorOrchestrator:
    """Drives the Plan→Act→Observe loop across the agent tree.

    Two execution phases (matching the reference's workflow):
      Phase 1 (optional): Planner produces a structured plan
      Phase 2: Supervisor routes input (+plan) to children, collects handoffs

    Routing strategy (intentionally simple):
      - Match keywords in user input against child node names / tools
      - Fall back to first child if no match
      - Replace with LLM-based routing for production use

    Loop termination:
      - A child returns status "ok"           → aggregate and finish
      - A child returns "needs_more_info"     → enrich context, try next child
      - A child returns "failed"              → try next child
      - All children exhausted                → return partial result
      - Step limit reached                    → return partial result
    """

    tree: AgentTree
    hooks: OrchestratorHooks = field(default_factory=OrchestratorHooks)
    max_steps: int = 10
    planner: PlannerCallable | None = None

    async def run(self, user_input: str) -> SupervisorResult:
        """Execute the full orchestration loop and return the final result."""

        # ── Phase 1: Plan (optional) ──────────────────────────────────
        # Mirrors reference's planner_activity → call_reasoner()
        plan: dict[str, Any] | None = None
        if self.planner is not None:
            plan = await self.planner(user_input)

        # Prepend plan to input if available (same pattern as reference's
        # main.py: "SYSTEM PLAN:\n{plan}\n\nUSER QUERY:\n{msg}")
        execution_input = user_input
        if plan is not None:
            plan_text = "\n".join(f"  - {k}: {v}" for k, v in plan.items())
            execution_input = f"SYSTEM PLAN:\n{plan_text}\n\nUSER QUERY:\n{user_input}"

        # ── Phase 2: Route + Execute ──────────────────────────────────
        root = self.tree.root
        handoffs: list[HandoffResult] = []
        total_tokens = 0
        step = 0

        # WHY ordered: try best-match child first, then fall through.
        ordered_children = self._route(execution_input, root.children)

        # Context accumulator — enriched between steps so the next child
        # can see what previous children found.  Mirrors the reference's
        # pattern of prepending previous results to the input.
        enriched_input = execution_input

        for child in ordered_children:
            if step >= self.max_steps:
                break

            step += 1

            # -- Hook: node start
            await self.hooks.fire_node_start(child, enriched_input)

            # -- Execute child agent
            try:
                result: HandoffResult = await child.run(enriched_input)
            except Exception as exc:
                # Wrap unexpected errors into a failed handoff
                result = HandoffResult(
                    from_agent=child.name,
                    to_agent="supervisor",
                    status="failed",
                    summary=f"Agent raised an exception: {exc}",
                )

            # -- Validate (Pydantic already enforces schema at construction,
            #    but we re-validate here to catch any manual dict→model issues)
            result = HandoffResult.model_validate(result.model_dump())

            # -- Hook: node end + handoff
            await self.hooks.fire_node_end(child, result)
            await self.hooks.fire_handoff(result)

            handoffs.append(result)
            total_tokens += result.traces.token_usage

            # -- Supervisor decision: is the answer good enough?
            if result.status == "ok":
                return SupervisorResult(
                    answer=result.summary,
                    plan=plan,
                    handoffs_received=handoffs,
                    status="completed",
                    total_steps=step,
                    total_tokens=total_tokens,
                )

            # -- "needs_more_info": enrich context for next child
            #    (append what this child found so the next one can build on it)
            if result.status == "needs_more_info":
                enriched_input = (
                    f"{enriched_input}\n\n"
                    f"[Previous step from {result.from_agent}]: {result.summary}"
                )
            # else "failed": try next child with same input

        # ── All children tried or step limit hit ──────────────────────
        final_summary = "; ".join(h.summary for h in handoffs) or "No children executed."
        return SupervisorResult(
            answer=f"Partial result — {final_summary}",
            plan=plan,
            handoffs_received=handoffs,
            status="partial" if handoffs else "failed",
            total_steps=step,
            total_tokens=total_tokens,
        )

    # ── Routing helper ────────────────────────────────────────────────

    @staticmethod
    def _route(user_input: str, children: list[AgentNode]) -> list[AgentNode]:
        """Order children by relevance to *user_input*.

        Strategy: score each child by keyword overlap between the input
        and the child's name + tools.  Higher score → tried first.
        This is a placeholder — swap with LLM-based routing in production.
        """
        input_lower = user_input.lower()

        def score(node: AgentNode) -> int:
            keywords = [node.name.lower()] + [t.lower() for t in node.tools]
            return sum(1 for kw in keywords if kw in input_lower)

        return sorted(children, key=score, reverse=True)
