"""JSON-RPC client for Zotron XPI."""
import httpx


class ZoteroRPC:
    def __init__(self, url: str, client: httpx.Client | None = None):
        self.url = url
        self._client = client or httpx.Client(timeout=30.0)
        self._id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._id,
        }
        try:
            resp = self._client.post(self.url, json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise ConnectionError(
                "Cannot connect to Zotero. Is it running with zotron plugin?"
            )
        data = resp.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"[{err['code']}] {err['message']}")
        return data.get("result")
