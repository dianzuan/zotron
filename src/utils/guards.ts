// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
import { rpcError, INVALID_PARAMS } from "./errors";

/**
 * Fetch an Item by ID and throw a structured -32602 error if it doesn't
 * exist. Replaces the `getAsync(id) → null check → throw` pattern that
 * appeared at ~19 sites across the handlers.
 *
 * Standard error message format: `Item ${id} not found` (matches the
 * dominant convention; pre-guard outliers like `Item not found: ${id}`
 * are normalized to this form when adopted).
 */
export async function requireItem(id: number): Promise<Zotero.Item> {
  const item = await Zotero.Items.getAsync(id);
  if (!item) throw rpcError(INVALID_PARAMS, `Item ${id} not found`);
  return item as Zotero.Item;
}

/**
 * Fetch a Collection by ID and throw a structured -32602 error if it
 * doesn't exist. Same pattern as `requireItem` but for collections.
 */
export async function requireCollection(id: number): Promise<Zotero.Collection> {
  const col = await Zotero.Collections.getAsync(id);
  if (!col) throw rpcError(INVALID_PARAMS, `Collection ${id} not found`);
  return col as Zotero.Collection;
}
