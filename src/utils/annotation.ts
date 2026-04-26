// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
export type AnnotationType = "highlight" | "underline" | "note" | "image" | "ink";

const VALID_TYPES: ReadonlySet<AnnotationType> = new Set([
  "highlight", "underline", "note", "image", "ink",
]);

const TEXT_TYPES: ReadonlySet<AnnotationType> = new Set(["highlight", "underline"]);

const HEX_COLOR = /^#[0-9a-fA-F]{6}$/;

export interface AnnotationParams {
  type: AnnotationType;
  text?: string;
  color?: string;
  comment?: string;
  position: any;
}

export type ValidationResult =
  | { ok: true }
  | { ok: false; message: string };

/**
 * Validate annotation params against Zotero 8 invariants:
 * - type must be one of the 5 known annotation types
 * - text is only valid for highlight/underline (item.js#L4243)
 * - color must be #RRGGBB hex (item.js#L4249)
 *
 * Returns {ok:true} on success, {ok:false, message} on failure.
 * The handler maps {ok:false} to throw {code: -32602, message}.
 */
export function validateAnnotationParams(p: AnnotationParams): ValidationResult {
  if (!VALID_TYPES.has(p.type)) {
    return {
      ok: false,
      message: `Invalid annotation type: ${p.type} (expected one of: ${[...VALID_TYPES].join(", ")})`,
    };
  }
  if (p.text !== undefined && p.text !== "" && !TEXT_TYPES.has(p.type)) {
    return {
      ok: false,
      message: `annotationText is only valid for highlight or underline annotations (got type=${p.type})`,
    };
  }
  if (p.color !== undefined && !HEX_COLOR.test(p.color)) {
    return {
      ok: false,
      message: `Invalid annotation color: ${p.color} (expected #RRGGBB 6-char hex)`,
    };
  }
  return { ok: true };
}
