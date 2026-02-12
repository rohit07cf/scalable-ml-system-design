"""
Structured handoff models for agent-to-agent communication.

WHY Pydantic:  Every child→Supervisor result is validated at the boundary.
               Downstream code never handles untyped dicts — schema failures
               surface immediately with actionable error messages.

Ported from reference:  configurable_agent/models.py (SubtaskResult, SupervisorOutput)
Adapted to keep our richer HandoffResult contract while adding ToolResult
for typed tool outputs (same pattern the reference uses with @function_tool).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Tool output — every tool call returns this ─────────────────────────────

class ToolResult(BaseModel):
    """Typed result from a single tool invocation.

    WHY separate from HandoffResult:  Tool calls happen *within* an agent's
    run — they are sub-steps, not agent-to-agent transfers.  Keeping them
    typed lets us validate tool outputs independently (same idea as the
    reference's @function_tool return types).
    """

    model_config = ConfigDict(strict=True)

    tool_name: str
    input_args: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    status: Literal["ok", "error"] = "ok"
    error: str | None = None
    latency_ms: int = 0


# ── Observability bag attached to every handoff ────────────────────────────

class HandoffTraces(BaseModel):
    """Optional observability bag attached to every handoff."""

    model_config = ConfigDict(strict=True)

    step_id: str | None = None
    tool_calls: list[str] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    token_usage: int = 0
    latency_ms: int = 0
    reasoning_steps: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Handoff payload returned by every child agent ──────────────────────────

class HandoffResult(BaseModel):
    """Structured result a child agent hands back to the Supervisor.

    All child outputs MUST be wrapped in this model so the Supervisor
    can make routing decisions on typed, validated data.
    """

    model_config = ConfigDict(strict=True)

    from_agent: str = Field(
        ..., description="Name/ID of the child agent that produced this result"
    )
    to_agent: str = Field(
        default="supervisor",
        description="Receiving agent — almost always the Supervisor",
    )
    status: Literal["ok", "needs_more_info", "failed"] = Field(
        ..., description="Outcome of the child's work"
    )
    summary: str = Field(
        ...,
        max_length=300,
        description="1–2 line human-readable summary of what was done",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured data the child wants to pass back",
    )
    artifacts: list[str] = Field(
        default_factory=list,
        description="References to produced artifacts (file paths, URLs, IDs)",
    )
    traces: HandoffTraces = Field(
        default_factory=lambda: HandoffTraces(),
        description="Observability metadata for this handoff",
    )


# ── Supervisor's final aggregated output ───────────────────────────────────

class SupervisorResult(BaseModel):
    """Final answer the Supervisor returns after aggregating child handoffs.

    Mirrors reference's SupervisorOutput but keeps our richer handoff list.
    """

    model_config = ConfigDict(strict=True)

    answer: str
    plan: dict[str, Any] | None = None
    handoffs_received: list[HandoffResult] = Field(default_factory=list)
    status: Literal["completed", "partial", "failed"] = "completed"
    total_steps: int = 0
    total_tokens: int = 0
