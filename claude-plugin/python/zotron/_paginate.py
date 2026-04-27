"""Auto-pagination loop for the rpc escape hatch.

Used when the user passes `--paginate`. Loops {offset, limit: page_size}
until a short page (< page_size) is returned, the response shape is
non-paginatable, or a 10k-item safety cap is hit.

Not part of the SDK public surface.
"""
from __future__ import annotations

from typing import Any

SAFETY_CAP = 10000
_LIST_KEYS = ("items", "tags", "results", "data")


def paginate(rpc: Any, method: str, params: dict[str, Any],
             page_size: int = 100) -> list[Any]:
    """Loop `method` with offset/limit injection, return concatenated rows.

    rpc:        ZoteroRPC-like object with .call(method, params)
    method:     RPC method name
    params:     User-supplied params (will not be mutated)
    page_size:  Items per page request (default 100)
    """
    out: list[Any] = []
    prev_page: list[Any] | None = None
    offset = 0
    while True:
        page_params = {**params, "offset": offset, "limit": page_size}
        resp = rpc.call(method, page_params)

        # Extract the page list
        page: list[Any] | None
        if isinstance(resp, list):
            page = resp
        elif isinstance(resp, dict):
            page = None
            for key in _LIST_KEYS:
                v = resp.get(key)
                if isinstance(v, list):
                    page = v
                    break
            if page is None:
                # Method isn't paginated. Only acceptable on first call.
                if not out:
                    return resp  # type: ignore[return-value]
                raise RuntimeError(
                    f"paginate: {method!r} returned a non-paginated dict "
                    f"after {len(out)} accumulated rows; aborting"
                )
        else:
            # Scalar / other shape. Same logic.
            if not out:
                return resp  # type: ignore[return-value]
            raise RuntimeError(
                f"paginate: {method!r} returned non-list/non-dict shape "
                f"after {len(out)} accumulated rows; aborting"
            )
        assert page is not None

        # No-progress detector: if this page is identical to the previous
        # one, the method is ignoring offset (XPI bug). Bail out loudly
        # rather than silently spin to SAFETY_CAP with duplicate rows.
        if prev_page is not None and page == prev_page:
            raise RuntimeError(
                f"paginate: {method!r} returned identical pages — method "
                f"likely ignores offset; aborting after {len(out)} rows"
            )

        out.extend(page)
        if len(page) < page_size:
            return out
        if len(out) >= SAFETY_CAP:
            return out[:SAFETY_CAP]
        prev_page = page
        offset += page_size
