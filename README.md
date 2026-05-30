# pydantic-ai-ejentum

[PydanticAI](https://ai.pydantic.dev) toolset for the Ejentum Reasoning Harness. `EjentumToolset` subclasses `pydantic_ai.FunctionToolset` and registers eight agent-callable tools.

Use the harness before the agent generates on complex, multi-step, or multi-constraint tasks where the model's default reasoning template would miss a constraint, take a shortcut, or drift across turns. Each call returns a *cognitive operation*: a structured procedure (numbered steps with a failure pattern to refuse and a falsification test) paired with an executable reasoning topology (a DAG of those steps with decision gates, parallel branches, bounded loops, and meta-cognitive exit nodes). The agent reads both layers before producing its response.

Four dynamic tools (`reasoning`, `code`, `anti-deception`, `memory`) are available on all tiers including the 30-day free trial. Four adaptive tools (`adaptive-reasoning`, `adaptive-code`, `adaptive-anti-deception`, `adaptive-memory`) additionally run an adapter LLM that rewrites the matched operation with task-specific identifiers; they require the Go or Super tier.

PydanticAI accepts hyphenated tool names via `@tool_plain(name="anti-deception")`. The Python method symbols use underscores (`anti_deception`), but the LLM-facing names registered with the agent use the canonical hyphenated form.

## Install

```bash
pip install pydantic-ai-ejentum
```

## Configuration

```bash
export EJENTUM_API_KEY="ej_..."
```

Or pass `api_key=` to `EjentumToolset(...)`. Get a key at [ejentum.com/pricing](https://ejentum.com/pricing).

## Usage

```python
from pydantic_ai import Agent
from pydantic_ai_ejentum import EjentumToolset

agent = Agent(
    "anthropic:claude-sonnet-4-6",
    toolsets=[EjentumToolset()],
)

result = agent.run_sync(
    "We have spent three months on the GraphQL gateway. It's mostly done. "
    "Should we keep going or pivot to REST?"
)
print(result.output)
```

`EjentumToolset` ships with `FunctionToolset.instructions` that nudge the agent to call the matching tool before generating. Pass `add_instructions=False` to suppress and supply routing guidance in your own system prompt.

### Explicit API key

```python
toolset = EjentumToolset(api_key="ej_...")
```

### Composing with other toolsets

```python
agent = Agent(
    "anthropic:claude-sonnet-4-6",
    toolsets=[EjentumToolset(), my_other_toolset],
)
```

## Tool inventory

### Dynamic (all tiers)

| Tool name (LLM-visible) | Mode string | Library size |
|---|---|---:|
| `reasoning` | `reasoning` | 311 |
| `code` | `code` | 128 |
| `anti-deception` | `anti-deception` | 139 |
| `memory` | `memory` | 101 |

### Adaptive (Go or Super tier)

| Tool name | Mode string |
|---|---|
| `adaptive-reasoning` | `adaptive-reasoning` |
| `adaptive-code` | `adaptive-code` |
| `adaptive-anti-deception` | `adaptive-anti-deception` |
| `adaptive-memory` | `adaptive-memory` |

Each tool accepts a single `query: str` argument. Returns the injection as a string. For `memory` and `adaptive-memory`, format the query as `"I noticed X. This might mean Y. Sharpen: Z."`.

Errors return as strings; tools do not raise.

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
| `api_key` | `None` | If unset, read from `EJENTUM_API_KEY` at call time. |
| `api_url` | `https://api.ejentum.com/harness/` | Override for self-hosted gateway. |
| `timeout_seconds` | `10.0` | Per-call HTTP timeout. |
| `add_instructions` | `True` | Emit `FunctionToolset.instructions` nudging the agent to call the matching tool before generating. |

## Wire contract

```
POST https://api.ejentum.com/harness/
Headers: Authorization: Bearer <key>, Content-Type: application/json
Body:    { "query": <string>, "mode": <one of 8 mode strings> }
Response (200): [ { "<mode>": "<injection string>" } ]
Response (401|403|429): { "error": "..." }
```

Full wire contract, field structure of an injection, DAG syntax, and a canonical dynamic-vs-adaptive comparison on the same query are documented in the [ejentum-mcp README](https://github.com/ejentum/ejentum-mcp#wire-contract).

## ejentum-mcp alternative

The same eight tools are hosted as an MCP server at `https://api.ejentum.com/mcp`. PydanticAI's MCP support can consume the endpoint directly.

## Compatibility

- Python 3.10+
- `pydantic-ai>=0.0.20`
- `requests>=2.31.0`
- `pydantic>=2.0.0`

## License

[MIT](./LICENSE)


## Measured effects

The Ejentum harness is benchmarked publicly under CC BY 4.0 at [github.com/ejentum/benchmarks](https://github.com/ejentum/benchmarks):

- **ELEPHANT** sycophancy: 5.8% composite on GPT-4o (40 real Reddit scenarios)
- **LiveCodeBench Hard**: 85.7% to 100% on Claude Opus (28 competitive programming tasks)
- **Memory retention**: 50% fewer stale facts served (20-turn implicit state changes)
- Plus per-harness numbers across BBH/CausalBench/MuSR, ARC-AGI-3, SciCode, and perception tasks

Methodology, scenarios, run scripts, and raw outputs are all in-repo.
