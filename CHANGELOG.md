# Changelog

All notable changes to `pydantic-ai-ejentum` are documented here. This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-22

### Added

- Initial release.
- `EjentumToolset` subclasses `pydantic_ai.FunctionToolset` and registers four agent-callable tools (`harness_reasoning`, `harness_code`, `harness_anti_deception`, `harness_memory`).
- Each tool takes a single `query: str` argument and returns the structured scaffold from the Ejentum Logic API. Errors are returned as human-readable strings so the calling agent never crashes the run.
- Toolset emits PydanticAI `instructions` that nudge the agent to call the matching harness before generating. Pass `add_instructions=False` to suppress and provide routing guidance from your own system prompt.
- Construction-time and call-time validation: empty/whitespace query returns an actionable error without spending a paid API call. Missing `EJENTUM_API_KEY` returns an actionable error pointing to https://ejentum.com/pricing.
- Unit tests cover the toolset surface (subclass identity, tool name set, instructions string), the call helper failure surface (missing key, empty/whitespace/non-string query, invalid mode, 401, non-200, invalid JSON, unexpected shape, non-string scaffold, network error), and per-mode dispatch.
- Published to PyPI with OIDC trusted-publisher provenance attestation via GitHub Actions.

### Background

PydanticAI's canonical pattern for grouping multiple related tools with shared configuration is a `FunctionToolset` (or subclass) passed to `Agent(toolsets=[...])`. This package subclasses `FunctionToolset` so the shared API key, URL, and timeout live as instance attributes and the four `harness_*` tools close over them. Aligns with the four-tool surface of `ejentum-mcp` so a PydanticAI agent gets the same affordances available to MCP-native clients.
