"""
AgentNode — a single node in the hierarchical agent tree.

WHY a tree:  Enterprise agent platforms decompose work into
             Supervisor → Specialist → Verifier chains.  A tree
             makes this hierarchy explicit, inspectable, and
             serialisable (for config-driven construction).

Ported from reference:  configurable_agent/agent_tree.py (AgentNode)
Adapted to add:
  - ToolCallable registry so tools are actual async functions, not just names
  - as_tool() to expose a child agent as a callable tool (agents-as-tools pattern
    from the reference's sdk_agents.py `agent.as_tool()`)
  - run_tool() to execute a registered tool with hook integration
"""

from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from .handoff_models import HandoffResult, ToolResult


# Type alias for a minimal async agent callable.
# Signature:  async (input: str) -> HandoffResult
AgentCallable = Callable[[str], Awaitable[HandoffResult]]

# Type alias for an async tool function.
# Signature:  async (**kwargs) -> Any
ToolCallable = Callable[..., Awaitable[Any]]


class AgentNode:
    """One node in the agent hierarchy.

    Can be a Supervisor (root), Specialist (internal), or Leaf agent.
    Each node optionally wraps an async *agent callable* that does the
    real work — the tree itself is just structure + metadata.

    Tools can be either string names (for display / config) or actual
    async callables registered via add_tool().
    """

    def __init__(
        self,
        node_id: str,
        *,
        name: str | None = None,
        agent: AgentCallable | None = None,
        tools: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.node_id = node_id
        self.name = name or node_id
        self.agent = agent  # async callable; set later if needed
        self.tools: list[str] = tools or []
        self.metadata: dict[str, Any] = metadata or {}

        # Tool registry: name → async callable.
        # WHY separate from self.tools:  self.tools is the display list (strings),
        # _tool_fns holds the actual implementations for execution.
        self._tool_fns: dict[str, ToolCallable] = {}

        # Tree linkage
        self.children: list[AgentNode] = []
        self.parent: AgentNode | None = None

    # ── Tree mutations ─────────────────────────────────────────────────

    def add_child(self, node: AgentNode) -> AgentNode:
        """Attach *node* as a child of this node.  Returns the child."""
        node.parent = self
        self.children.append(node)
        return node

    def add_tool(self, tool: str | ToolCallable, name: str | None = None) -> None:
        """Register a tool — either a name (str) or an async callable.

        If *tool* is a callable, its __name__ (or the explicit *name*) is
        added to the display list AND the function is stored in _tool_fns.
        If *tool* is a plain string, only the display list is updated.
        """
        if callable(tool):
            tool_name = name or getattr(tool, "__name__", "unknown_tool")
            if tool_name not in self.tools:
                self.tools.append(tool_name)
            self._tool_fns[tool_name] = tool
        else:
            if tool not in self.tools:
                self.tools.append(tool)

    def set_agent(self, agent: AgentCallable) -> None:
        """Bind an async callable that implements this agent's logic."""
        self.agent = agent

    # ── Agents-as-tools ────────────────────────────────────────────────
    # Mirrors the reference's `agent.as_tool()` pattern from sdk_agents.py.
    # WHY: The Supervisor can "call" a child agent the same way it calls
    # any tool — unifying the invocation model.

    def as_tool(self, tool_name: str | None = None) -> ToolCallable:
        """Wrap this agent's run() as an async tool callable.

        Returns an async function with signature (user_input: str) -> dict
        that the Supervisor (or any parent) can invoke as if it were a tool.
        The dict contains the HandoffResult fields for easy consumption.
        """
        resolved_name = tool_name or f"run_{self.node_id}"
        node = self  # capture for closure

        async def _agent_as_tool(user_input: str) -> dict[str, Any]:
            result = await node.run(user_input)
            return result.model_dump()

        _agent_as_tool.__name__ = resolved_name
        _agent_as_tool.__doc__ = f"Run child agent '{self.name}' and return its HandoffResult."
        return _agent_as_tool

    # ── Tool execution ─────────────────────────────────────────────────

    async def run_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool by name and return a typed ToolResult.

        WHY typed ToolResult:  Same reason the reference uses @function_tool
        with typed returns — callers get validated, structured data instead
        of raw strings.
        """
        fn = self._tool_fns.get(tool_name)
        if fn is None:
            return ToolResult(
                tool_name=tool_name,
                input_args=kwargs,
                status="error",
                error=f"Tool '{tool_name}' not registered on node '{self.name}'",
            )

        start = time.perf_counter()
        try:
            output = await fn(**kwargs)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ToolResult(
                tool_name=tool_name,
                input_args=kwargs,
                output=output,
                status="ok",
                latency_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ToolResult(
                tool_name=tool_name,
                input_args=kwargs,
                status="error",
                error=str(exc),
                latency_ms=elapsed_ms,
            )

    # ── Queries ────────────────────────────────────────────────────────

    def path(self) -> str:
        """Slash-separated path from root to this node.

        Example: "supervisor/triage/invoice-specialist"
        """
        parts: list[str] = []
        current: AgentNode | None = self
        while current is not None:
            parts.append(current.name)
            current = current.parent
        return "/".join(reversed(parts))

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        d = 0
        current: AgentNode | None = self.parent
        while current is not None:
            d += 1
            current = current.parent
        return d

    # ── Execution ──────────────────────────────────────────────────────

    async def run(self, user_input: str) -> HandoffResult:
        """Execute this node's agent callable.

        Raises RuntimeError if no agent is bound — callers should check
        before invoking.
        """
        if self.agent is None:
            raise RuntimeError(
                f"AgentNode '{self.name}' has no agent callable bound. "
                f"Call set_agent() first."
            )
        return await self.agent(user_input)

    # ── Display ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        tools_str = f", tools={self.tools}" if self.tools else ""
        children_str = f", children={len(self.children)}" if self.children else ""
        return f"AgentNode(id={self.node_id!r}{tools_str}{children_str})"
