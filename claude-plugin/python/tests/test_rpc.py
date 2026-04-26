"""Tests for ZoteroRPC JSON-RPC client."""
import json
import pytest
import httpx

from zotero_bridge.rpc import ZoteroRPC


def make_rpc(responses: list[dict]) -> ZoteroRPC:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        body = json.loads(request.content)
        resp = responses[call_count] if call_count < len(responses) else {}
        call_count += 1
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": resp, "id": body.get("id", 1)},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ZoteroRPC(url="http://test:23119/rpc", client=client)


def test_call_method():
    """Simple ping returns result dict."""
    rpc = make_rpc([{"pong": True}])
    result = rpc.call("ping")
    assert result == {"pong": True}


def test_call_with_params():
    """Params are forwarded and result is returned."""
    rpc = make_rpc([{"echo": "hello"}])
    result = rpc.call("echo", params={"message": "hello"})
    assert result == {"echo": "hello"}


def test_call_error():
    """JSON-RPC error response raises RuntimeError with code and message."""

    def error_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Method not found"},
                "id": body.get("id", 1),
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(error_handler))
    rpc = ZoteroRPC(url="http://test:23119/rpc", client=client)

    with pytest.raises(RuntimeError, match=r"\[-32601\] Method not found"):
        rpc.call("nonexistent_method")


def test_connection_error():
    """ConnectError raises ConnectionError mentioning Zotero."""

    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    client = httpx.Client(transport=httpx.MockTransport(failing_handler))
    rpc = ZoteroRPC(url="http://test:23119/rpc", client=client)

    with pytest.raises(ConnectionError, match="Zotero"):
        rpc.call("ping")
