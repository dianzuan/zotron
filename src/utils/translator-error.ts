// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
import { INTERNAL_ERROR, type RpcError } from "./errors";

/**
 * Wrap an unknown translator failure into a JSON-RPC -32603 error
 * so handlers throw structured {code, message} instead of raw `Error`.
 *
 * Usage:
 *   try { ... translator code ... }
 *   catch (e) { throw wrapTranslatorError("bibtex", e); }
 */
export function wrapTranslatorError(format: string, err: unknown): RpcError {
  const detail = err instanceof Error ? err.message : String(err);
  return {
    code: INTERNAL_ERROR,
    message: `Export failed (${format}): ${detail}`,
  };
}
