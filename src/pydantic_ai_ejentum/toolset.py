"""EjentumToolset: a configured PydanticAI FunctionToolset.

Subclasses :class:`pydantic_ai.FunctionToolset` and registers four tools
(``harness_reasoning``, ``harness_code``, ``harness_anti_deception``,
``harness_memory``) the agent picks between before generating. Each tool
returns a structured scaffold engineered in two layers:

- a natural-language procedure (named failure pattern, executable steps,
  suppression vectors, falsification test), and
- an executable reasoning topology (graph DAG with decision gates,
  parallel branches, bounded loops, and meta-cognitive exit nodes).

The bracketed labels in the returned scaffold are instructions to the
agent, not content to display. The agent reads both layers before
generating its user-facing answer.
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
    "call the matching harness_* tool with a 1-2 sentence framing of the "
    "task. Read the returned scaffold's [PROCEDURE] and [REASONING TOPOLOGY] "
    "before generating your user-facing answer; the bracketed labels are "
    "instructions to you, not content to display."
)


class EjentumToolset(FunctionToolset):
    """A PydanticAI FunctionToolset wrapping the Ejentum Reasoning Harness.

    Registers four agent-callable tools:

    - ``harness_reasoning`` for analytical, diagnostic, planning, or
      multi-step tasks (311 operations spanning abstraction, time,
      causality, simulation, spatial, metacognition).
    - ``harness_code`` for code generation, refactoring, review, debugging
      (128 operations in the software-engineering layer).
    - ``harness_anti_deception`` when a prompt pressures the agent to
      validate, certify, or soften an honest assessment (139 operations
      spanning sycophancy, hallucination, deception, adversarial framing,
      judgment, executive control).
    - ``harness_memory`` only when sharpening an observation already formed
      about cross-turn drift (101 operations in the perception layer;
      filter-oriented, not write-oriented).

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
    :param timeout_seconds: Per-call HTTP timeout shared across all four
        tools.
    :param add_instructions: If True (default), the toolset's
        ``instructions`` field nudges the agent to call the matching
        harness before generating. Set to False if you'd rather provide
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
        @self.tool_plain
        def harness_reasoning(query: str) -> str:
            """Retrieve a reasoning scaffold before any analytical, diagnostic, planning, or multi-step task.

            Call BEFORE the agent performs analysis, diagnosis, planning,
            or any multi-step task. Returns a structured scaffold with a
            named failure pattern, an executable procedure, a reasoning
            topology (graph DAG), and a falsification test from a library
            of 311 reasoning operations.

            :param query: A 1-2 sentence description of the task the agent
                is about to work on. Be specific about the failure mode to
                avoid.
            """
            return self._call("reasoning", query)

        @self.tool_plain
        def harness_code(query: str) -> str:
            """Retrieve a code scaffold before any code generation, refactoring, review, or debugging task.

            Call BEFORE the agent produces or reviews code. Returns a
            structured scaffold with a named code-failure pattern, an
            engineering procedure, a reasoning topology (graph DAG), and a
            verification step from a library of 128 code operations.

            :param query: A 1-2 sentence description of what the agent is
                coding or reviewing. Be specific about the failure risk to
                avoid (silent contract change, hallucinated API, lost edge
                case, etc.).
            """
            return self._call("code", query)

        @self.tool_plain
        def harness_anti_deception(query: str) -> str:
            """Retrieve an anti-deception scaffold before responding to any prompt that pressures the agent to validate, certify, or soften an honest assessment.

            Call BEFORE the agent responds to prompts that pressure
            validation, manufactured agreement, authority appeals,
            fabricated commitments, or any setup where the obvious helpful
            answer would compromise honesty. Returns a structured scaffold
            with a named deception pattern, an integrity procedure, a
            detection topology (graph DAG with omission-bias gates), and
            an integrity check from a library of 139 anti-deception
            operations.

            :param query: A 1-2 sentence description of the integrity
                dynamic at play.
            """
            return self._call("anti-deception", query)

        @self.tool_plain
        def harness_memory(query: str) -> str:
            """Retrieve a memory-mode scaffold ONLY when sharpening an observation already formed about cross-turn drift.

            Filter-oriented, not write-oriented; do not call for fact
            extraction, summarization, or storing structured data, those
            produce scaffold paralysis.

            The query MUST be in the format: "I noticed [observation].
            This might mean [tentative interpretation]. Sharpen: [what to
            see deeper into]." Calling with an empty mind defeats the
            harness. Observe first.

            :param query: A 1-2 sentence framing in the "I noticed / This
                might mean / Sharpen" structure described above.
            """
            return self._call("memory", query)
