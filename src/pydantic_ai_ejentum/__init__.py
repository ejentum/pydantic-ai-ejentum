"""pydantic-ai-ejentum: PydanticAI toolset for the Ejentum Reasoning Harness.

Exposes :class:`EjentumToolset`, a subclass of
:class:`pydantic_ai.FunctionToolset` that registers eight agent-callable
tools: four dynamic (``reasoning``, ``code``, ``anti-deception``,
``memory``) plus four adaptive variants (``adaptive-reasoning``,
``adaptive-code``, ``adaptive-anti-deception``, ``adaptive-memory``)
that pre-fit the cognitive operation to the caller's task via an adapter
LLM.

Each call retrieves a task-matched cognitive operation engineered in two
layers: a natural-language procedure plus an executable reasoning
topology (graph DAG with gates, parallel branches, and meta-cognitive
exit nodes). Adaptive tools require the Go or Super tier and add ~2-3s
of latency vs ~1s for dynamic tools.

Free and paid tiers at https://ejentum.com/pricing.
"""

from pydantic_ai_ejentum.toolset import EjentumToolset
from pydantic_ai_ejentum._api import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT_SECONDS,
    VALID_MODES,
)

__all__ = [
    "EjentumToolset",
    "DEFAULT_API_URL",
    "DEFAULT_TIMEOUT_SECONDS",
    "VALID_MODES",
]
__version__ = "0.2.0"
