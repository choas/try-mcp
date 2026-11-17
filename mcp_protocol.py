"""MCP protocol revision 2026-07-28 ("stateless", SDK v2) support.

The platform is dual-era:

* modern requests carry their protocol version in `params._meta` and in the
  `MCP-Protocol-Version` header and are served statelessly per request
* legacy clients open with `initialize` and keep working as before

Spec: https://modelcontextprotocol.io/specification/2026-07-28
"""

import base64
from typing import Any, Dict, List, Mapping, Optional, Tuple

MODERN_VERSION = "2026-07-28"
LEGACY_VERSION = "2025-06-18"
SUPPORTED_VERSIONS = [MODERN_VERSION, LEGACY_VERSION]

# Versions that use the initialize handshake. A legacy client sends one of
# these in the MCP-Protocol-Version header after it has initialized.
LEGACY_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}

META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"

HEADER_MISMATCH = -32020
UNSUPPORTED_PROTOCOL_VERSION = -32022
METHOD_NOT_FOUND = -32601

# Methods whose `params.name` is mirrored into the Mcp-Name header
NAMED_METHODS = {"tools/call": "name", "prompts/get": "name", "resources/read": "uri"}

DISCOVER_TTL_MS = 3600000


def _meta(body: Mapping[str, Any]) -> Dict[str, Any]:
    params = body.get("params")
    meta = params.get("_meta") if isinstance(params, dict) else None
    return meta if isinstance(meta, dict) else {}


def is_modern(body: Mapping[str, Any], headers: Mapping[str, str]) -> bool:
    """Decide how the client opened: per-request metadata or initialize."""
    if body.get("method") == "initialize":
        return False
    if META_VERSION in _meta(body):
        return True
    header = headers.get("mcp-protocol-version")
    return header is not None and header not in LEGACY_VERSIONS


def _error(request_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _decode(value: str) -> str:
    """Decode the `=?base64?...?=` form that header values may use."""
    if value.startswith("=?base64?") and value.endswith("?="):
        try:
            return base64.b64decode(value[9:-2]).decode("utf-8")
        except Exception:
            return value
    return value


def validate(body: Mapping[str, Any], headers: Mapping[str, str],
             supported: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Check a modern request. Returns a JSON-RPC error (HTTP 400) or None."""
    request_id = body.get("id")
    method = body.get("method")
    body_version = _meta(body).get(META_VERSION)
    header_version = headers.get("mcp-protocol-version")

    if header_version is None:
        return _error(request_id, HEADER_MISMATCH, "Header mismatch: MCP-Protocol-Version header is missing")
    if body_version is None:
        return _error(request_id, HEADER_MISMATCH,
                      f"Header mismatch: request body has no _meta['{META_VERSION}']")
    if header_version != body_version:
        return _error(request_id, HEADER_MISMATCH,
                      f"Header mismatch: MCP-Protocol-Version header value '{header_version}' "
                      f"does not match body value '{body_version}'")
    if body_version != MODERN_VERSION:
        return _error(request_id, UNSUPPORTED_PROTOCOL_VERSION, "Unsupported protocol version",
                      {"supported": supported or SUPPORTED_VERSIONS, "requested": body_version})

    header_method = headers.get("mcp-method")
    if header_method is None:
        return _error(request_id, HEADER_MISMATCH, "Header mismatch: Mcp-Method header is missing")
    if header_method != method:
        return _error(request_id, HEADER_MISMATCH,
                      f"Header mismatch: Mcp-Method header value '{header_method}' "
                      f"does not match body value '{method}'")

    field = NAMED_METHODS.get(method)
    if field:
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        expected = params.get(field)
        header_name = headers.get("mcp-name")
        if header_name is None:
            return _error(request_id, HEADER_MISMATCH, "Header mismatch: Mcp-Name header is missing")
        if _decode(header_name) != expected:
            return _error(request_id, HEADER_MISMATCH,
                          f"Header mismatch: Mcp-Name header value '{_decode(header_name)}' "
                          f"does not match body value '{expected}'")
    return None


def discover_result(request_id: Any, name: str, version: str, capabilities: Dict[str, Any],
                    instructions: Optional[str] = None,
                    supported: Optional[List[str]] = None) -> Dict[str, Any]:
    """Build the answer to `server/discover`."""
    result: Dict[str, Any] = {
        "resultType": "complete",
        "supportedVersions": supported or SUPPORTED_VERSIONS,
        "capabilities": capabilities,
        "_meta": {META_SERVER_INFO: {"name": name, "version": version}},
        "ttlMs": DISCOVER_TTL_MS,
        "cacheScope": "public",
    }
    if instructions:
        result["instructions"] = instructions
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def legacy_rejected(body: Mapping[str, Any], headers: Mapping[str, str]) -> Dict[str, Any]:
    """Answer of a modern-only endpoint to a client that opened the legacy way."""
    params = body.get("params") if isinstance(body.get("params"), dict) else {}
    requested = params.get("protocolVersion") or headers.get("mcp-protocol-version")
    return _error(body.get("id"), UNSUPPORTED_PROTOCOL_VERSION,
                  "Unsupported protocol version: this endpoint only speaks " + MODERN_VERSION,
                  {"supported": [MODERN_VERSION], "requested": requested})


def method_not_found(request_id: Any, method: Any, available: List[str]) -> Dict[str, Any]:
    return _error(request_id, METHOD_NOT_FOUND, f"Method '{method}' not found",
                  {"method": method, "available_methods": available})


def finish(response: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Turn a handler response into its modern shape and HTTP status."""
    if "error" in response:
        code = response["error"].get("code")
        return response, 404 if code == METHOD_NOT_FOUND else 200
    result = response.get("result")
    if isinstance(result, dict):
        result = dict(result)
        if "is_error" in result:  # the spec name is isError
            result["isError"] = result.pop("is_error")
        result.setdefault("resultType", "complete")
        response = {**response, "result": result}
    return response, 200
