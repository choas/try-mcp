"""Tests for MCP protocol revision 2026-07-28 (stateless) next to the legacy handshake."""

import pytest
from fastapi.testclient import TestClient

from multi_service_server import app

V2 = "2026-07-28"
META = {
    "io.modelcontextprotocol/protocolVersion": V2,
    "io.modelcontextprotocol/clientInfo": {"name": "test-client", "version": "1.0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}
ENDPOINTS = ["/mcp", "/services/weather/v1"]


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def call(client, url, method, params=None, headers=None, meta=META):
    params = dict(params or {})
    if meta is not None:
        params["_meta"] = meta
    base = {"MCP-Protocol-Version": V2, "Mcp-Method": method}
    if "name" in params:
        base["Mcp-Name"] = params["name"]
    base.update(headers or {})
    base = {k: v for k, v in base.items() if v is not None}
    return client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, headers=base)


@pytest.mark.parametrize("url", ENDPOINTS)
def test_discover(client, url):
    r = call(client, url, "server/discover")
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["resultType"] == "complete"
    assert V2 in result["supportedVersions"]
    assert "tools" in result["capabilities"]
    assert result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"]


@pytest.mark.parametrize("url", ENDPOINTS)
def test_tools_list_without_initialize(client, url):
    r = call(client, url, "tools/list")
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["tools"]
    assert result["resultType"] == "complete"


def test_tools_call_service(client):
    r = call(client, "/services/weather/v1", "tools/call",
             {"name": "get_weather_forecast", "arguments": {"location": "Berlin"}})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["content"][0]["text"]
    assert result["isError"] is False
    assert "is_error" not in result


def test_tools_call_platform(client):
    r = call(client, "/mcp", "tools/call",
             {"name": "weather_get_weather_forecast", "arguments": {"location": "Berlin"}})
    assert r.status_code == 200
    assert r.json()["result"]["content"][0]["text"]


def test_unsupported_version(client):
    meta = {**META, "io.modelcontextprotocol/protocolVersion": "2027-01-01"}
    r = call(client, "/mcp", "tools/list", headers={"MCP-Protocol-Version": "2027-01-01"}, meta=meta)
    assert r.status_code == 400
    error = r.json()["error"]
    assert error["code"] == -32022
    assert V2 in error["data"]["supported"]
    assert error["data"]["requested"] == "2027-01-01"


@pytest.mark.parametrize("headers", [
    {"MCP-Protocol-Version": None},
    {"Mcp-Method": None},
    {"Mcp-Method": "tools/call"},
    {"MCP-Protocol-Version": "2027-01-01"},
])
def test_header_mismatch(client, headers):
    r = call(client, "/mcp", "tools/list", headers=headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == -32020


def test_mcp_name_mismatch(client):
    r = call(client, "/services/weather/v1", "tools/call",
             {"name": "get_weather_forecast", "arguments": {"location": "Berlin"}},
             headers={"Mcp-Name": "something_else"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == -32020


def test_mcp_name_base64(client):
    r = call(client, "/services/weather/v1", "tools/call",
             {"name": "get_weather_forecast", "arguments": {"location": "Berlin"}},
             headers={"Mcp-Name": "=?base64?Z2V0X3dlYXRoZXJfZm9yZWNhc3Q=?="})
    assert r.status_code == 200


def test_unknown_method_is_404(client):
    r = call(client, "/mcp", "completion/complete")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == -32601


@pytest.mark.parametrize("url", ENDPOINTS)
def test_legacy_initialize_still_works(client, url):
    r = client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert r.status_code == 200
    assert r.json()["result"]["protocolVersion"] == "2025-06-18"


def test_legacy_tools_list_still_works(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    headers={"MCP-Protocol-Version": "2025-06-18"})
    assert r.status_code == 200
    assert "resultType" not in r.json()["result"]


# ---------- /v2: the same services, modern only ----------

def test_v2_discover_lists_only_modern(client):
    r = call(client, "/services/weather/v2", "server/discover")
    assert r.status_code == 200
    assert r.json()["result"]["supportedVersions"] == ["2026-07-28"]


def test_v2_tools_list(client):
    r = call(client, "/services/weather/v2", "tools/list")
    assert r.status_code == 200
    assert r.json()["result"]["tools"]


def test_v2_rejects_initialize(client):
    r = client.post("/services/weather/v2", json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                                  "params": {"protocolVersion": "2025-06-18"}})
    assert r.status_code == 400
    error = r.json()["error"]
    assert error["code"] == -32022
    assert error["data"] == {"supported": ["2026-07-28"], "requested": "2025-06-18"}


def test_v2_rejects_legacy_request_without_meta(client):
    r = client.post("/services/weather/v2", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == -32022


def test_v2_unknown_service_is_404(client):
    r = call(client, "/services/nope/v2", "tools/list")
    assert r.status_code == 404


# ---------- prompts and resources ----------

SERVICES = ["mindful", "weather", "emoji-oracle", "timestamp", "fortune", "lucky-numbers"]


@pytest.mark.parametrize("service", SERVICES)
def test_every_service_has_prompts_and_resources(client, service):
    url = f"/services/{service}/v2"
    capabilities = call(client, url, "server/discover").json()["result"]["capabilities"]
    assert "prompts" in capabilities and "resources" in capabilities

    prompts = call(client, url, "prompts/list").json()["result"]["prompts"]
    assert prompts
    arguments = {a["name"]: "lottery" for a in prompts[0].get("arguments", []) if a.get("required")}
    name = prompts[0]["name"]
    r = call(client, url, "prompts/get", {"name": name, "arguments": arguments}, headers={"Mcp-Name": name})
    assert r.status_code == 200, r.text
    message = r.json()["result"]["messages"][0]
    assert message["role"] == "user" and message["content"]["text"]

    resources = call(client, url, "resources/list").json()["result"]["resources"]
    assert resources
    for resource in resources:
        uri = resource["uri"]
        r = call(client, url, "resources/read", {"uri": uri}, headers={"Mcp-Name": uri})
        assert r.status_code == 200, r.text
        content = r.json()["result"]["contents"][0]
        assert content["uri"] == uri and content["text"]


def test_prompt_missing_required_argument(client):
    r = call(client, "/services/weather/v2", "prompts/get", {"name": "plan_my_day"}, headers={"Mcp-Name": "plan_my_day"})
    assert r.json()["error"]["code"] == -32602


def test_unknown_prompt_and_resource(client):
    r = call(client, "/services/weather/v2", "prompts/get", {"name": "nope"}, headers={"Mcp-Name": "nope"})
    assert r.json()["error"]["code"] == -32602
    r = call(client, "/services/weather/v2", "resources/read", {"uri": "x://y"}, headers={"Mcp-Name": "x://y"})
    assert r.json()["error"]["code"] == -32002


def test_platform_serves_all_prompts_and_resources(client):
    prompts = call(client, "/mcp", "prompts/list").json()["result"]["prompts"]
    names = [p["name"] for p in prompts]
    assert len(names) == len(set(names))
    assert {"mindful_pause", "plan_my_day", "ask_the_oracle", "surprise_schedule", "blessed_numbers_reading"} <= set(names)
    resources = call(client, "/mcp", "resources/list").json()["result"]["resources"]
    assert len(resources) == 7
    r = call(client, "/mcp", "resources/read", {"uri": "mindful://sentences"}, headers={"Mcp-Name": "mindful://sentences"})
    assert r.json()["result"]["contents"][0]["mimeType"] == "application/json"


def test_legacy_prompts_get_and_resources(client):
    r = client.post("/services/timestamp/v1", json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert "resources" in r.json()["result"]["capabilities"]
    r = client.post("/services/timestamp/v1", json={"jsonrpc": "2.0", "id": 2, "method": "resources/read",
                                                    "params": {"uri": "timestamp://day-periods"}})
    assert "morning" in r.json()["result"]["contents"][0]["text"]
    r = client.post("/services/timestamp/v1", json={"jsonrpc": "2.0", "id": 3, "method": "prompts/get",
                                                    "params": {"name": "surprise_schedule", "arguments": {"activity": "a walk"}}})
    assert "a walk" in r.json()["result"]["messages"][0]["content"]["text"]
