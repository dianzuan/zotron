// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
/**
 * JSON-RPC 2.0 error code constants used at the handler boundary.
 *
 * Per PRD §1.3:
 *   -32602 invalid params — caller's fault (unknown id, missing field,
 *          wrong item type, validation failure).
 *   -32603 internal error — XPI's fault or Zotero's fault (unexpected
 *          exception during execution).
 *
 * Handlers MUST `throw` these structured objects, never `throw new Error(...)`.
 * server.ts maps `err.code || INTERNAL_ERROR` to the response envelope.
 */
export const INVALID_PARAMS = -32602;
export const INTERNAL_ERROR = -32603;

export interface RpcError {
  code: number;
  message: string;
}

export function rpcError(code: number, message: string): RpcError {
  return { code, message };
}
