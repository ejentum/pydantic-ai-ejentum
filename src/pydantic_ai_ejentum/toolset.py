"""EjentumToolset: a configured PydanticAI FunctionToolset.

Subclasses :class:`pydantic_ai.FunctionToolset` and registers eight tools
the agent picks between before generating:

Four dynamic tools (all tiers, ~1s latency):

- ``reasoning``
- ``code``
- ``anti-deception``
- ``memory``

Four adaptive tools (Go or Super tier, ~2-3s latency). Same triggers as
the matching dynamic tool, but the returned cognitive operation is
rewritten by an adapter LLM to fit the caller's specific task:

- ``adaptive-reasoning``
- ``adaptive-code``
- ``adaptive-anti-deception``
- ``adaptive-memory``

Each tool returns a structured injection engineered in two layers: a
natural-language procedure (named failure pattern, executable steps,
suppression vectors, falsification test) plus an executable reasoning
topology (graph DAG with decision gates, parallel branches, bounded
loops, and meta-cognitive exit nodes). The bracketed labels in the
returned injection are instructions to the agent, not content to display.

Python rule: the tool name registered with PydanticAI uses the
hyphenated canonical form (the string the LLM sees); the Python method
identifier uses underscores.
"""

from __future__ import annotations

from typing import Optional

from pydantic_ai import FunctionToolset

from pydantic_ai_ejentum._api import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT_SECONDS,
    call_logic_api,
)


_INSTRUCTIONS = (
    "Before any analytical, planning, code, or integrity-sensitive step, "
    "call the matching Ejentum harness tool (reasoning, code, "
    "anti-deception, memory, or one of the adaptive-* variants) with a "
    "1-2 sentence framing of the task. Read the returned injection's "
    "[PROCEDURE] and [REASONING TOPOLOGY] before generating your "
    "user-facing answer; the bracketed labels are instructions to you, "
    "not content to display."
)


class EjentumToolset(FunctionToolset):
    """A PydanticAI FunctionToolset wrapping the Ejentum Reasoning Harness.

    Registers eight agent-callable tools:

    Dynamic (all tiers):

    - ``reasoning`` for analytical, diagnostic, planning, or multi-step
      tasks (311 operations spanning abstraction, time, causality,
      simulation, spatial, metacognition).
    - ``code`` for code generation, refactoring, review, debugging (128
      operations in the software-engineering layer).
    - ``anti-deception`` when a prompt pressures the agent to validate,
      certify, or soften an honest assessment (139 operations spanning
      sycophancy, hallucination, deception, adversarial framing,
      judgment, executive control).
    - ``memory`` only when sharpening an observation already formed
      about cross-turn drift (101 operations in the perception layer;
      filter-oriented, not write-oriented).

    Adaptive (Go or Super tier; ~2-3s latency vs ~1s for dynamic):

    - ``adaptive-reasoning``, ``adaptive-code``,
      ``adaptive-anti-deception``, ``adaptive-memory``. Same triggers as
      the matching dynamic tool, but the returned cognitive operation
      (procedure + topology DAG) is rewritten by an adapter LLM to fit
      the caller's specific task before delivery.

    Usage::

        from pydantic_ai import Agent
        from pydantic_ai_ejentum import EjentumToolset

        agent = Agent(
            "anthropic:claude-sonnet-4-6",
            toolsets=[EjentumToolset()],
        )
        result = agent.run_sync(
            "We've spent three months on the GraphQL gateway. "
            "Should we keep going or pivot to REST?"
        )

    :param api_key: Ejentum Logic API key. If omitted, read from the
        ``EJENTUM_API_KEY`` environment variable at call time. Free and
        paid tiers at https://ejentum.com/pricing.
    :param api_url: Override only if you self-host the Ejentum Logic API
        gateway.
    :param timeout_seconds: Per-call HTTP timeout shared across all
        tools.
    :param add_instructions: If True (default), the toolset's
        ``instructions`` field nudges the agent to call the matching
        harness before generating. Set to False if you prefer to provide
        the routing guidance in your own system prompt.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        add_instructions: bool = True,
    ) -> None:
        super().__init__(
            instructions=_INSTRUCTIONS if add_instructions else None,
        )
        self._api_key = api_key
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds
        self._register_tools()

    def _call(self, mode: str, query: str) -> str:
        return call_logic_api(
            mode=mode,
            query=query,
            api_key=self._api_key,
            api_url=self._api_url,
            timeout_seconds=self._timeout_seconds,
        )

    def _register_tools(self) -> None:
        # Dynamic tools (all tiers).
        @self.tool_plain(name="reasoning")
        def reasoning(query: str) -> str:
            """Retrieve a reasoning injection before any analytical, diagnostic, planning, or multi-step task.

            Call BEFORE the agent performs analysis, diagnosis, planning,
            or any multi-step task. Returns a structured injection with a
            named failure pattern, an executable procedure, a reasoning
            topology (graph DAG), and a falsification test from a library
            of 311 reasoning operations.

            :param query: A 1-2 sentence description of the task the agent
                is about to work on. Be specific about the failure mode to
                avoid.
            """
            return self._call("reasoning", query)

        @self.tool_plain(name="code")
        def code(query: str) -> str:
            """Retrieve a code injection before any code generation, refactoring, review, or debugging task.

            Call BEFORE the agent produces or reviews code. Returns a
            structured injection with a named code-failure pattern, an
            engineering procedure, a reasoning topology (graph DAG), and a
            verification step from a library of 128 code operations.

            :param query: A 1-2 sentence description of what the agent is
                coding or reviewing. Be specific about the failure risk to
                avoid (silent contract change, hallucinated API, lost edge
                case, etc.).
            """
            return self._call("code", query)

        @self.tool_plain(name="anti-deception")
        def anti_deception(query: str) -> str:
            """Retrieve an anti-deception injection before responding to any prompt that pressures the agent to validate, certify, or soften an honest assessment.

            Call BEFORE the agent responds to prompts that pressure
            validation, manufactured agreement, authority appeals,
            fabricated commitments, or any setup where the obvious helpful
            answer would compromise honesty. Returns a structured
            injection with a named deception pattern, an integrity
            procedure, a detection topology (graph DAG with omission-bias
            gates), and an integrity check from a library of 139
            anti-deception operations.

            :param query: A 1-2 sentence description of the integrity
                dynamic at play.
            """
            return self._call("anti-deception", query)

        @self.tool_plain(name="memory")
        def memory(query: str) -> str:
            """Retrieve a memory-mode injection ONLY when sharpening an observation already formed about cross-turn drift.

            Filter-oriented, not write-oriented; do not call for fact
            extraction, summarization, or storing structured data, those
            produce paralysis.

            The query MUST be in the format: "I noticed [observation].
            This might mean [tentative interpretation]. Sharpen: [what to
            see deeper into]." Calling with an empty mind defeats the
            harness. Observe first.

            :param query: A 1-2 sentence framing in the "I noticed / This
                might mean / Sharpen" structure described above.
            """
            return self._call("memory", query)

        # Adaptive tools (Go or Super tier). Same triggers as the matching
        # dynamic tool, but the returned operation is rewritten by an
        # adapter LLM to fit the caller's specific task. Costs ~2-3s vs
        # ~1s for the dynamic tools.
        @self.tool_plain(name="adaptive-reasoning")
        def adaptive_reasoning(query: str) -> str:
            """Same triggers as `reasoning`, but the returned cognitive operation is REWRITTEN by an adapter LLM to fit the specific task.

            Procedure steps and reasoning topology DAG nodes are
            concretized with task-specific language before delivery. Use
            when the dynamic `reasoning` tool is too generic, or for
            high-stakes analytical work where every DAG node should
            already be mapped to the task before generation. Requires Go
            or Super tier (250 or 1500 adaptive calls per month). Latency
            ~2-3s vs ~1s for `reasoning`.

            :param query: A 1-2 sentence description of the task the
                agent is about to work on, same as `reasoning`.
            """
            return self._call("adaptive-reasoning", query)

        @self.tool_plain(name="adaptive-code")
        def adaptive_code(query: str) -> str:
            """Same triggers as `code`, but the returned cognitive operation is REWRITTEN by an adapter LLM to fit the specific code task.

            Engineering procedure and reasoning topology DAG nodes are
            concretized with the language, framework, and failure mode of
            the caller's code. Use for security-critical reviews,
            refactor-heavy diffs, or any code work where every
            verification step should already be mapped to the specifics.
            Requires Go or Super tier. Latency ~2-3s vs ~1s for `code`.

            :param query: A 1-2 sentence description of what the agent is
                coding or reviewing.
            """
            return self._call("adaptive-code", query)

        @self.tool_plain(name="adaptive-anti-deception")
        def adaptive_anti_deception(query: str) -> str:
            """Same triggers as `anti-deception`, but the returned cognitive operation is REWRITTEN by an adapter LLM to fit the specific integrity dynamic.

            Detection topology DAG nodes are concretized to the specific
            pressure, authority appeal, or framing trap at play. Use when
            stakes of a soft or sycophantic answer are high. Requires Go
            or Super tier. Latency ~2-3s vs ~1s for `anti-deception`.

            :param query: A 1-2 sentence description of the integrity
                dynamic at play.
            """
            return self._call("adaptive-anti-deception", query)

        @self.tool_plain(name="adaptive-memory")
        def adaptive_memory(query: str) -> str:
            """Same triggers as `memory`, but the returned cognitive operation is REWRITTEN by an adapter LLM to fit the specific observation.

            Perception topology DAG nodes are concretized to the specific
            signal being sharpened. Use when the dynamic `memory` tool's
            general scaffold is not sharp enough for the perception being
            formed. Observe FIRST, then call. Requires Go or Super tier.
            Latency ~2-3s vs ~1s for `memory`.

            :param query: A 1-2 sentence framing in the "I noticed / This
                might mean / Sharpen" structure.
            """
            return self._call("adaptive-memory", query)
