"""
Supervisor orchestration loop — the async runtime that drives the agent tree.

Flow:
  1. Supervisor receives user input
  2. Routes to a child agent (simple keyword routing — swap for LLM routing later)
  3. Child executes, returns a validated HandoffResult
  4. Supervisor inspects result, decides: done / try another child / fail
  5. Returns a SupervisorResult with all collected handoffs

WHY async:  LLM + tool calls are I/O-bound.  Async keeps the event loop
            free for streaming hooks and concurrent activities.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from .agent_node import AgentNode
from .agent_tree import AgentTree
from .handoff_models import HandoffResult, SupervisorResult


# ── Hook protocol ──────────────────────────────────────────────────────────
# Hooks are optional async callables.  The orchestrator calls them at
# well-defined points so external systems (streaming, logging, tracing)
# can observe the run without coupling to internals.

@dataclass
class OrchestratorHooks:
    """Lifecycle hooks fired during orchestration.

    Set any of these to an async callable to receive events.
    Unset hooks are no-ops (zero overhead).
    """

    on_node_start: Callable[[AgentNode, str], Awaitable[None]] | None = None
    on_node_end: Callable[[AgentNode, HandoffResult], Awaitable[None]] | None = None
    on_handoff: Callable[[HandoffResult], Awaitable[None]] | None = None

    async def fire_node_start(self, node: AgentNode, user_input: str) -> None:
        if self.on_node_start:
            await self.on_node_start(node, user_input)

    async def fire_node_end(self, node: AgentNode, result: HandoffResult) -> None:
        if self.on_node_end:
            await self.on_node_end(node, result)

    async def fire_handoff(self, result: HandoffResult) -> None:
        if self.on_handoff:
            await self.on_handoff(result)


# ── Supervisor Orchestrator ────────────────────────────────────────────────

@dataclass
class SupervisorOrchestrator:
    """Drives the Plan→Act→Observe loop across the agent tree.

    Routing strategy (intentionally simple):
      - Match keywords in user input against child node names / tools
      - Fall back to first child if no match
      - Replace with LLM-based routing for production use

    Loop termination:
      - A child returns status "ok"           → aggregate and finish
      - A child returns "needs_more_info"     → try next child
      - A child returns "failed"              → try next child
      - All children exhausted                → return partial result
      - Step limit reached                    → return partial result
    """

    tree: AgentTree
    hooks: OrchestratorHooks = field(default_factory=OrchestratorHooks)
    max_steps: int = 10

    async def run(self, user_input: str) -> SupervisorResult:
        """Execute the full orchestration loop and return the final result."""
        root = self.tree.root
        handoffs: list[HandoffResult] = []
        total_tokens = 0
        step = 0

        # ── Route to children one at a time ────────────────────────────
        # Simple strategy: try best-match child first, then fall through.
        ordered_children = self._route(user_input, root.children)

        for child in ordered_children:
            if step >= self.max_steps:
                break

            step += 1

            # -- Hook: node start
            await self.hooks.fire_node_start(child, user_input)

            # -- Execute child agent
            try:
                result: HandoffResult = await child.run(user_input)
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
                    handoffs_received=handoffs,
                    status="completed",
                    total_steps=step,
                    total_tokens=total_tokens,
                )
            # else: try the next child ("needs_more_info" or "failed")

        # ── All children tried or step limit hit ───────────────────────
        final_summary = "; ".join(h.summary for h in handoffs) or "No children executed."
        return SupervisorResult(
            answer=f"Partial result — {final_summary}",
            handoffs_received=handoffs,
            status="partial" if handoffs else "failed",
            total_steps=step,
            total_tokens=total_tokens,
        )

    # ── Routing helper ─────────────────────────────────────────────────

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
