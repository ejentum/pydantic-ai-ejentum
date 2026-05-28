# pydantic-ai-ejentum

A [PydanticAI](https://ai.pydantic.dev) toolset for the [Ejentum](https://ejentum.com) Reasoning Harness. `EjentumToolset` subclasses `pydantic_ai.FunctionToolset` and registers eight agent-callable tools the agent picks between before generating: four dynamic (`reasoning`, `code`, `anti-deception`, `memory`) plus four adaptive (`adaptive-reasoning`, `adaptive-code`, `adaptive-anti-deception`, `adaptive-memory`) that pre-fit the cognitive operation to the caller's task via an adapter LLM.

Each operation in the Ejentum library (679 of them, organized across four cognitive harnesses each with dynamic and adaptive variants) is engineered in **two layers**:

- a **natural-language procedure** the model can read, naming the steps to take and the failure pattern to refuse, and
- an **executable reasoning topology**: a graph-shaped plan over those steps. The plan names explicit decision points where the model branches, parallel branches that run and rejoin, bounded loops that run until convergence, named meta-cognitive moments where the model is asked to stop, look at its own working, and re-enter at a specific step, plus escape paths for when the prescribed plan stops fitting the task at hand.

The natural-language layer tells the model *what* to do. The topology layer pins down *how* those steps connect: where to decide, where to loop, where to stop and look at itself. Together they act as a persistent attention anchor that survives long context windows and multi-turn execution chains, which is precisely where a model's own reasoning template typically decays.

## Installation

```bash
pip install pydantic-ai-ejentum
```

## Configuration

Get an Ejentum API key at <https://ejentum.com/pricing>. The 30-day free trial (no card required) includes 1,000 dynamic reasoning calls; adaptive tools require Go or Super.

```bash
export EJENTUM_API_KEY="ej_..."
```

## Usage

```python
from pydantic_ai import Agent
from pydantic_ai_ejentum import EjentumToolset

agent = Agent(
    "anthropic:claude-sonnet-4-6",
    toolsets=[EjentumToolset()],  # reads EJENTUM_API_KEY from env
)

result = agent.run_sync(
    "We've spent three months on the GraphQL gateway. It's mostly done. "
    "Should we keep going or pivot to REST?"
)
print(result.output)
```

The toolset ships with PydanticAI `instructions` that nudge the agent to call the matching harness tool before generating. Pass `add_instructions=False` to suppress and supply your own routing guidance.

### Explicit API key

```python
toolset = EjentumToolset(api_key="ej_...")
```

### Composing with other toolsets

```python
from pydantic_ai import Agent
from pydantic_ai_ejentum import EjentumToolset
from my_other_package import my_toolset

agent = Agent(
    "anthropic:claude-sonnet-4-6",
    toolsets=[EjentumToolset(), my_toolset],
)
```

## The eight tools

### Dynamic (single retrieval, all tiers including the 30-day free trial)

| Tool name (LLM-visible) | Best for | Library size |
|---|---|---|
| `reasoning` | Analytical, diagnostic, planning, multi-step tasks spanning abstraction, time, causality, simulation, spatial, and metacognition | 311 operations |
| `code` | Code generation, refactoring, review, and debugging across the software-engineering layer | 128 operations |
| `anti-deception` | Prompts that pressure the agent to validate, certify, or soften an honest assessment | 139 operations |
| `memory` | Sharpening an observation already formed about cross-turn drift. Filter-oriented, not write-oriented. Format `query` as `"I noticed X. This might mean Y. Sharpen: Z."` | 101 operations |

### Adaptive (top-k retrieval + adapter LLM rewrites operation to fit the task; Go or Super tier required)

| Tool name | When to prefer over the dynamic version |
|---|---|
| `adaptive-reasoning` | High-stakes analytical work where every DAG node should be mapped to your specifics before generation. |
| `adaptive-code` | Security-critical reviews, refactor-heavy diffs, or any code work where every verification step should be concretized. |
| `adaptive-anti-deception` | When the stakes of a soft or sycophantic answer are high. |
| `adaptive-memory` | When the dynamic memory tool's general scaffold is not sharp enough for the perception being formed. |

> **Hyphenated tool names.** PydanticAI accepts hyphenated tool names via `@tool_plain(name=...)`. The Python method symbols use underscores (`adaptive_anti_deception`), but the registered LLM-facing names use canonical hyphens (`adaptive-anti-deception`).

## What an injection looks like

A real `reasoning` mode response on the query `investigate why our nightly ETL job has started failing intermittently over the past two weeks; nothing in the code or schema has changed`:

```
[NEGATIVE GATE]
The server's response time was accepted as average, despite a suspicious
rhythm break in its timing pattern.

[PROCEDURE]
Step 1: Establish baseline timing profiles by extracting historical
durations and intervals for each event type. Step 2: Compare each observed
timing against its baseline and compute deviation magnitude. ...

[REASONING TOPOLOGY]
S1:durations -> FIXED_POINT[baselines] -> N{dismiss_timing_deviations_
without_investigation} -> for_each: S2:compare -> S3:deviation ->
G1{>2sigma?} --yes-> S4:classify -> S5:probe_cause -> FLAG -> continue --no->
S6:validate -> continue -> all_checked -> OUT:anomaly_report

[FALSIFICATION TEST]
If no event timing is flagged as suspiciously fast or slow relative to
baseline, temporal anomaly detection was not active.

Amplify: timing baseline comparison; anomaly classification
Suppress: average timing acceptance; outlier normalization
```

The agent reads both the natural-language `[PROCEDURE]` and the graph-logic `[REASONING TOPOLOGY]` before generating its user-facing answer.

## API reference

```python
EjentumToolset(
    api_key: str | None = None,
    api_url: str = "https://api.ejentum.com/harness/",
    timeout_seconds: float = 10.0,
    add_instructions: bool = True,
)
```

| Field | Default | Description |
|---|---|---|
| `api_key` | `None` | If omitted, read from `EJENTUM_API_KEY` at call time. |
| `api_url` | `https://api.ejentum.com/harness/` | Override only if you self-host the Ejentum API gateway. |
| `timeout_seconds` | `10.0` | Per-call HTTP timeout shared across all tools. |
| `add_instructions` | `True` | When True, the toolset emits `FunctionToolset.instructions` that nudge the agent to call the matching harness before generating. Set False to provide routing guidance in your own system prompt. |

Each of the eight tools accepts a single `query: str` argument (1-2 sentences) and returns the injection as a string. Errors are returned as human-readable strings (no exceptions cross the tool boundary, so an agent step never crashes the run).

> **MCP alternative.** This package wraps the Ejentum API REST gateway. If you prefer the MCP route (to share one server across frameworks), the same eight harness tools are hosted at `https://api.ejentum.com/mcp` with Bearer auth. PydanticAI's MCP support can consume the hosted endpoint directly.

## Compatibility

- Python 3.10+
- `pydantic-ai>=0.0.20`
- `requests>=2.31.0`
- `pydantic>=2.0.0`

## Resources

- Ejentum homepage: <https://ejentum.com>
- Pricing: <https://ejentum.com/pricing>
- API reference: <https://ejentum.com/docs/api_reference>
- "Why LLM Agents Fail" essay: <https://ejentum.com/blog/why-llm-agents-fail>
- "Under Pressure" research paper: <https://doi.org/10.5281/zenodo.19392715>
- PydanticAI documentation: <https://ai.pydantic.dev>

## License

[MIT](./LICENSE)
