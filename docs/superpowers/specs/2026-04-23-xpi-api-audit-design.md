# XPI API Audit & Unified PRD — Design

**Goal:** Audit every Zotero API call in the zotron XPI handlers, cross-reference with Zotero 8 official documentation, and produce a derived API Product Requirements Document (PRD) that captures:

1. Which Zotero conventions we adopt verbatim (parameter names, return shapes, method signatures, error semantics).
2. The JSON-RPC boundary conventions we add on top (JSON serialization rules, error code classes, what we normalize vs pass through).

## Why this audit

On 2026-04-23 the `export.bibliography` handler triggered a three-layer API mismatch:

1. CLI expected `{content}`; XPI returned `{html, text}` — internal inconsistency.
2. XPI called `Zotero.QuickCopy.getContentFromItems(items, "bibliography", style)` with a wrong signature — should have been `getContentFromItems(items, "bibliography=<style-uri>")`.
3. Even with the correct signature, Zotero 8's QuickCopy internal path crashed with `style.getCiteProc is not a function` — Zotero 8 API regression. We bypassed QuickCopy entirely.

Each layer was individually plausible. Together they produced 3 rounds of rebuild + reinstall + restart. Nothing in the handler would have warned us; TypeScript compiled, the method was registered, the call looked reasonable against training-data knowledge of Zotero 6/7.

The user's diagnosis: the root cause isn't bibliography specifically — it's that **the XPI's 77 handlers were written against *remembered* Zotero API, not *verified* Zotero 8 API**, and there is no internal consistency contract. bibliography exposed a pattern that probably exists elsewhere.

## Scope

**In scope:**

- All 9 handler files under `src/handlers/` (1049 lines, 77 registered RPC methods).
- ~20 Zotero.* namespaces touched: `Items`, `Collections`, `Libraries`, `Tags`, `Attachments`, `PDFWorker`, `File`, `HTTP`, `Styles`, `QuickCopy`, `Translate`, `Search`, `Searches`, `Prefs`, `DB`, `ItemTypes`, `ItemFields`, `CreatorTypes`, `Sync`, `getActiveZoteroPane`.
- JSON-RPC boundary behavior: serialization (`serializeItem`, `serializeCollection`, etc.), error throwing shape, parameter destructuring patterns.

**Out of scope:**

- CLI Python side (`claude-plugin/python/zotron/cli.py`) — already audited 2026-04-23.
- Zotero 6/7 back-compat — the XPI targets 6.999+ per manifest; Zotero 8 is the deployment reality. Findings will focus on Zotero 8 correctness.
- Feature requests (new methods, new commands) — only existing surface.

## Process

### Phase 1: Survey (read-only)

For each handler file, for each `Zotero.*` call:

1. Record current call shape: namespace, method, positional/keyword args, return usage.
2. Cross-reference against Zotero 8 documentation via context7 MCP (library `zotero/zotero`) and, where docs are thin, `WebFetch` against `www.zotero.org/support/dev/client_coding/javascript_api` and the public GitHub source (`zotero/zotero`).
3. Classify: `✓ correct`, `✗ wrong signature`, `⚠ deprecated-but-works`, `⚠ cumbersome-idiom`, `? unverifiable-from-docs`.

Output: `audit-findings-external.md` — table indexed by `handler:line`, one row per Zotero call.

### Phase 2: Internal consistency scan

For each RPC method (77 total):

1. Record return shape (keys, shape, optional fields).
2. Record parameter shape (names, required vs optional, types).
3. Record error patterns (`throw {code, message}` vs `throw new Error` vs silent false-return).

Group methods by family (`items.*`, `collections.*`, …). Flag intra-family shape divergences.

Output: `audit-findings-internal.md` — table grouped by family, one row per method.

### Phase 3: Derive the PRD

From Phase 1 + 2 findings, write `xpi-api-prd.md`:

**Zotero-adopted conventions** (we follow Zotero's own rules):

- Parameter naming: uppercase-ID suffix (`parentID`, `libraryID`, `itemID`) matching Zotero's internal JS API. RPC wire format preserves these — no translation layer in the XPI. Python-side callers get raw Zotero field names.
- Async semantics: methods that touch the DB are async (`getAsync`, `saveTx`); read-by-cache methods are sync (`getByLibrary`). The RPC handler mirrors this — no artificial `await` on sync calls.
- Errors: throw `{code: <jsonrpc-code>, message: string}` — the server.ts dispatcher converts to JSON-RPC error response. `-32602` = invalid params (caller's fault), `-32603` = internal error (our fault or Zotero's fault).

**XPI-owned conventions** (the JSON-RPC boundary layer):

- Return shapes per family:
  - Items: always through `serializeItem` — `{id, key, version, itemType, title, creators, tags, collections, dateAdded, dateModified, ...}`. No handler returns raw `Zotero.Item` objects.
  - Collections: always through `serializeCollection` — `{id, key, name, parentID, childCollections, itemCount}`.
  - Export (bibtex/ris/cslJson/csv): `{format: string, content: string, count: int}`. `bibliography` extends to `{format, style, html, text, count}` only because it has two output variants; CLI knows to pick `.text` or `.html`.
  - List operations (`list`, `search.*`, `getTrash`, `getAll`): `{items: [...], total: int, offset?: int, limit?: int}`.
  - Mutation operations (`create`, `update`, `delete`, `trash`, `restore`): return the affected entity via its serializer, or `{affected: N}` for batch ops.
- JSON encoding: integers for IDs (never strings), ISO-8601 strings for dates, null for absent optional fields.
- Avoid `as any` casts in handlers unless commented with the reason.

### Phase 4: Catalog fixes

For each finding in Phase 1 + 2 that violates the derived PRD, write a fix entry: file:line, current code, target code, rationale, risk. These flow into the writing-plans step.

## Deliverables

All four artifacts land under `docs/superpowers/specs/` alongside this design, dated `2026-04-23-`:

1. `2026-04-23-xpi-audit-external.md` — one row per Zotero call, verdict against Zotero 8 docs.
2. `2026-04-23-xpi-audit-internal.md` — one row per RPC method, shape/param/error record.
3. `2026-04-23-xpi-api-prd.md` — the derived standards doc.
4. `2026-04-23-xpi-audit-fixes.md` — ordered list of code changes the implementation plan will execute.

## What this design does NOT cover

- The writing-plans skill will produce the implementation plan (step-by-step code changes) from `audit-fixes.md`. This design only defines the audit, not the fix order or test strategy.
- No new features. If the audit surfaces missing functionality (e.g. group library support for `items.create`), it goes into the fix list only if it's already partially implemented and broken. True feature work is a separate spec.
- No Zotero 6/7 back-compat. The handlers already target 6.999+ in `manifest.json` but the deployment reality is Zotero 8. We verify against 8 only; 6/7 regressions are a separate concern if they come up.

## Risks and how we manage them

**R1: Zotero doc incomplete.** Zotero's official client coding docs cover the big API surfaces but many internal helpers have no documentation — we read Zotero source (`chrome/content/zotero/xpcom/*.js` in the GitHub repo) as fallback. Where even that's unclear, mark `? unverifiable-from-docs` and live-test via `curl` against the running XPI.

**R2: Audit surfaces too many bugs for one fix pass.** Phase 4 catalogs fixes with severity. The implementation plan can split into blocker-only (must fix before next release) vs cleanup (nice-to-have).

**R3: PRD invents rules we don't need.** YAGNI check in Phase 3: every PRD rule must trace back to at least one finding in Phase 1 or 2. No speculative conventions.

**R4: XPI rebuild + restart cycle during verification.** For any fix that requires live Zotero to confirm, batch so Zotero restarts happen at natural checkpoints — not per-fix.

---

**Ready to proceed?** After user approval: transition to the writing-plans skill to produce the step-by-step implementation plan.
