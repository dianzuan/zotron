// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
/**
 * Return the first key in `updates` that is not in `known`, or null
 * if every key is known.
 *
 * Used by settings.setAll to refuse silent drops of unknown keys —
 * symmetric with settings.set which throws -32602 for unknown keys.
 */
export function findUnknownKey(
  updates: Record<string, unknown>,
  known: ReadonlySet<string>,
): string | null {
  for (const key of Object.keys(updates)) {
    if (!known.has(key)) return key;
  }
  return null;
}
