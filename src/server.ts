// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
type HandlerFn = (params: any) => Promise<any>;
type HandlerMap = Record<string, HandlerFn>;
const handlers: HandlerMap = {};

export function registerHandlers(namespace: string, methods: Record<string, HandlerFn>) {
  for (const [name, fn] of Object.entries(methods)) {
    handlers[`${namespace}.${name}`] = fn;
  }
}

const INVALID_REQUEST = -32600;
const METHOD_NOT_FOUND = -32601;
const INTERNAL_ERROR = -32603;

function jsonRpcError(id: any, code: number, message: string) {
  return JSON.stringify({ jsonrpc: "2.0", error: { code, message }, id });
}
function jsonRpcResult(id: any, result: any) {
  return JSON.stringify({ jsonrpc: "2.0", result, id });
}

async function processRequest(req: any): Promise<string> {
  if (!req || req.jsonrpc !== "2.0" || !req.method) {
    return jsonRpcError(req?.id ?? null, INVALID_REQUEST, "Invalid JSON-RPC 2.0 request");
  }
  const handler = handlers[req.method];
  if (!handler) return jsonRpcError(req.id, METHOD_NOT_FOUND, `Method not found: ${req.method}`);
  try {
    const result = await handler(req.params || {});
    return jsonRpcResult(req.id, result);
  } catch (err: any) {
    return jsonRpcError(req.id, err.code || INTERNAL_ERROR, err.message || "Internal error");
  }
}

export function createEndpointHandler() {
  const Handler = function () {};
  Handler.prototype = {
    supportedMethods: ["POST"],
    supportedDataTypes: ["application/json", "text/plain"],
    permitBookmarklet: false,
    async init(request: any) {
      // Zotero HTTP server passes a request object with .data (parsed JSON)
      const parsed = request.data || request;

      if (Array.isArray(parsed)) {
        const results = await Promise.all(parsed.map(processRequest));
        return [200, "application/json", `[${results.join(",")}]`];
      }
      const result = await processRequest(parsed);
      return [200, "application/json", result];
    },
  };
  return Handler;
}

export function registerEndpoint() {
  Zotero.Server.Endpoints["/zotero-bridge/rpc"] = createEndpointHandler();
  Zotero.log("[ZoteroBridge] JSON-RPC endpoint registered at /zotero-bridge/rpc");
}
export function unregisterEndpoint() {
  delete Zotero.Server.Endpoints["/zotero-bridge/rpc"];
}
export function getRegisteredMethods(): string[] {
  return Object.keys(handlers).sort();
}
