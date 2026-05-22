"""pydantic-ai-ejentum: PydanticAI toolset for the Ejentum Reasoning Harness.

Exposes :class:`EjentumToolset`, a subclass of
:class:`pydantic_ai.FunctionToolset` that registers four agent-callable
tools (``harness_reasoning``, ``harness_code``, ``harness_anti_deception``,
``harness_memory``). Each call retrieves a task-matched cognitive operation
from a library of 679, engineered in two layers: a natural-language
procedure plus an executable reasoning topology (graph DAG with gates,
parallel branches, and meta-cognitive exit nodes).

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
__version__ = "0.1.0"
