"""Unit tests for pydantic-ai-ejentum."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import FunctionToolset

from pydantic_ai_ejentum import EjentumToolset
from pydantic_ai_ejentum._api import call_logic_api


def _mock_response(
    status_code: int = 200, json_data=None, text: str = ""
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or (str(json_data) if json_data else "")
    resp.json.return_value = json_data if json_data is not None else []
    return resp


# ---------------------------------------------------------------------------
# Toolset surface
# ---------------------------------------------------------------------------


def test_ejentum_toolset_is_function_toolset_subclass():
    assert issubclass(EjentumToolset, FunctionToolset)


def test_toolset_registers_four_tools():
    toolset = EjentumToolset(api_key="test-key")
    tool_names = set(toolset.tools.keys()) if hasattr(toolset, "tools") else None
    if tool_names is None:
        # Fallback: pull from the toolset's internal tool registry
        tool_names = {
            t.name if hasattr(t, "name") else getattr(t, "_name", str(t))
            for t in toolset._tools.values()  # type: ignore[attr-defined]
        }
    assert "harness_reasoning" in tool_names
    assert "harness_code" in tool_names
    assert "harness_anti_deception" in tool_names
    assert "harness_memory" in tool_names


def test_toolset_has_instructions_by_default():
    toolset = EjentumToolset(api_key="test-key")
    # PydanticAI stores instructions as a list of str-or-functions in _instructions
    assert toolset._instructions, "default toolset must carry routing instructions"
    joined = " ".join(s for s in toolset._instructions if isinstance(s, str))
    assert "harness" in joined.lower()


def test_toolset_can_suppress_instructions():
    toolset = EjentumToolset(api_key="test-key", add_instructions=False)
    assert toolset._instructions == [], "add_instructions=False must clear the instructions list"


def test_toolset_stores_config():
    toolset = EjentumToolset(
        api_key="cfg-key",
        api_url="https://example.com/api/",
        timeout_seconds=42.0,
    )
    assert toolset._api_key == "cfg-key"
    assert toolset._api_url == "https://example.com/api/"
    assert toolset._timeout_seconds == 42.0


# ---------------------------------------------------------------------------
# call_logic_api: failure surface (the helper every tool delegates to)
# ---------------------------------------------------------------------------


def test_call_logic_api_empty_query_returns_validation_error(monkeypatch):
    monkeypatch.setenv("EJENTUM_API_KEY", "test-key")
    with patch("pydantic_ai_ejentum._api.requests.post") as mock_post:
        result = call_logic_api(
            mode="reasoning",
            query="",
            api_key=None,
            api_url="https://example.com",
            timeout_seconds=10.0,
        )
    assert "query" in result.lower()
    assert "required" in result.lower()
    mock_post.assert_not_called()


def test_call_logic_api_whitespace_query_returns_validation_error(monkeypatch):
    """Whitespace-only input must NOT trigger a paid external request."""
    monkeypatch.setenv("EJENTUM_API_KEY", "test-key")
    with patch("pydantic_ai_ejentum._api.requests.post") as mock_post:
        result = call_logic_api(
            mode="reasoning",
            query="   \t\n  ",
            api_key=None,
            api_url="https://example.com",
            timeout_seconds=10.0,
        )
    assert "query" in result.lower()
    assert "required" in result.lower()
    mock_post.assert_not_called()


def test_call_logic_api_non_string_query_returns_validation_error(monkeypatch):
    monkeypatch.setenv("EJENTUM_API_KEY", "test-key")
    with patch("pydantic_ai_ejentum._api.requests.post") as mock_post:
        result = call_logic_api(
            mode="reasoning",
            query=None,
            api_key=None,
            api_url="https://example.com",
            timeout_seconds=10.0,
        )
    assert "query" in result.lower()
    mock_post.assert_not_called()


def test_call_logic_api_invalid_mode_returns_validation_error():
    result = call_logic_api(
        mode="not-a-mode",
        query="anything",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "mode" in result.lower()
    assert "reasoning" in result.lower()


def test_call_logic_api_missing_api_key_returns_actionable_error(monkeypatch):
    monkeypatch.delenv("EJENTUM_API_KEY", raising=False)
    result = call_logic_api(
        mode="reasoning",
        query="diagnose 503s under load",
        api_key=None,
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "EJENTUM_API_KEY" in result
    assert "ejentum.com/pricing" in result


@pytest.mark.parametrize(
    "mode",
    ["reasoning", "code", "anti-deception", "memory"],
)
@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_each_mode_round_trips(mock_post, mode):
    mock_post.return_value = _mock_response(
        status_code=200,
        json_data=[{mode: f"[NEGATIVE GATE] sample {mode} scaffold"}],
    )
    result = call_logic_api(
        mode=mode,
        query="sample task",
        api_key="test-key",
        api_url="https://example.com/api/",
        timeout_seconds=10.0,
    )
    assert f"sample {mode} scaffold" in result
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["mode"] == mode
    assert kwargs["json"]["query"] == "sample task"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_explicit_key_overrides_env(mock_post, monkeypatch):
    monkeypatch.setenv("EJENTUM_API_KEY", "env-key")
    mock_post.return_value = _mock_response(
        status_code=200,
        json_data=[{"reasoning": "scaffold"}],
    )
    call_logic_api(
        mode="reasoning",
        query="anything",
        api_key="explicit-key",
        api_url="https://example.com/api/",
        timeout_seconds=10.0,
    )
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer explicit-key"


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_401_returns_actionable_error(mock_post):
    mock_post.return_value = _mock_response(status_code=401, text="Unauthorized")
    result = call_logic_api(
        mode="anti-deception",
        query="anything",
        api_key="bad-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "401" in result
    assert "EJENTUM_API_KEY" in result


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_non_200_returns_status_and_body(mock_post):
    mock_post.return_value = _mock_response(status_code=500, text="boom")
    result = call_logic_api(
        mode="code",
        query="anything",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "500" in result
    assert "boom" in result


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_invalid_json_response_is_handled(mock_post):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = "<html>not json</html>"
    resp.json.side_effect = ValueError("not json")
    mock_post.return_value = resp
    result = call_logic_api(
        mode="reasoning",
        query="anything",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "not valid json" in result.lower()


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_unexpected_response_shape_is_handled(mock_post):
    mock_post.return_value = _mock_response(
        status_code=200, json_data={"wrong": "shape"}
    )
    result = call_logic_api(
        mode="code",
        query="anything",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "unexpected response shape" in result.lower()


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_non_string_scaffold_is_handled(mock_post):
    mock_post.return_value = _mock_response(
        status_code=200,
        json_data=[{"reasoning": ["not", "a", "string"]}],
    )
    result = call_logic_api(
        mode="reasoning",
        query="anything",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "unexpected response shape" in result.lower()


@patch("pydantic_ai_ejentum._api.requests.post")
def test_call_logic_api_network_error_is_caught(mock_post):
    import requests

    mock_post.side_effect = requests.ConnectionError("simulated")
    result = call_logic_api(
        mode="memory",
        query="I noticed drift. This might mean Y. Sharpen: Z.",
        api_key="test-key",
        api_url="https://example.com",
        timeout_seconds=10.0,
    )
    assert "network error" in result.lower()
    assert "simulated" in result
