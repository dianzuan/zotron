# XPI API PRD — 2026-04-23

Unified standards doc for the 77 RPC methods across the XPI's 9 handler
families. Every rule below traces to at least one row in
`2026-04-23-xpi-audit-external.md` (external) or
`2026-04-23-xpi-audit-internal.md` (internal). No speculative conventions.

Three sections:
1. **Zotero-adopted conventions** — rules we inherit from Zotero 8's own JS API.
2. **XPI-owned JSON-RPC boundary rules** — shape/serialization rules the XPI layer adds.
3. **Divergence acknowledgments** — the 36 `siblings-diverge=yes` rows, each classified as *violation → fix* or *PRD-granted exception*.

---

## 1. Zotero-adopted conventions

These rules mirror Zotero 8's internal API. The XPI does not translate them at the JSON-RPC boundary — handlers pass Zotero's own shapes through with minimal normalization.

### 1.1 Parameter naming — camelCase `parentId` / `newParentId` / `relatedId` at the wire; Zotero's uppercase-ID form stays internal

- The RPC wire format uses camelCase `parentId`, `newParentId`, `relatedId`, `itemId`, `itemIds` for all externally-facing params (from internal audit: `items.addRelated {id, relatedId}`, `collections.move {id, newParentId}`, `collections.addItems {id, itemIds}`, `attachments.list {parentId}`, `notes.get {parentId}`, `notes.createAnnotation {parentId}`, `tags.add {itemId, tags}`).
- Internally, handlers still pass Zotero's uppercase-ID names (`libraryID`, `parentItemID`, `itemTypeID`) through to Zotero's own methods unmodified (from external audit: `attachments.ts:62` passes `{file, parentItemID, title}` to `Zotero.Attachments.importFromFile`; `collections.ts:63` assigns `col.libraryID`; `notes.ts:44` reads `Zotero.Libraries.userLibraryID`).
- Rationale: 16 of 18 `items.*` methods, all 12 `collections.*` methods, all 7 `attachments.*` methods use camelCase `*Id` suffix params at the wire. Only `system.libraryStats` currently uses `libraryID` at the wire — a single-row outlier (from internal audit: `system.libraryStats {collections, items, libraryID}`). Majority wins: normalize to camelCase `libraryId` at the wire. This is a fix target, not an exception — see §3.9.
- Mandate: **new handlers MUST use camelCase at the wire**. Handlers MUST NOT rename a Zotero-internal param when calling Zotero; just pass `{parentItemID: params.parentId}` etc. (from external audit: `attachments.ts:62` `importFromFile({file, parentItemID, title})`; from internal audit: `system.libraryStats` is the sole wire-side `libraryID` outlier).

### 1.2 Async policy — `await` Zotero's async methods, do NOT `await` Zotero's sync methods

- Sync methods the handlers use (from external audit: see rows below for per-source-anchor evidence) — NO `await`:
  - `Zotero.Collections.getByLibrary(libraryID, recursive, includeTrashed)` — returns `Zotero.Collection[]` synchronously from the in-memory object cache (from external audit: `collections.ts:25`, `collections.ts:57`, `system.ts:19`).
  - `Zotero.Libraries.userLibraryID` / `Zotero.Libraries.get(id)` / `Zotero.Libraries.getAll()` — synchronous getters/cache reads (from external audit: `system.ts:7`, `system.ts:11`, `system.ts:17`).
  - `Zotero.Prefs.get(key, global)` / `Zotero.Prefs.set(key, value, global)` — synchronous pref-branch reads/writes (from external audit: `settings.ts:22`, `settings.ts:38`).
  - `Zotero.ItemTypes.getAll()` / `.getID(name)` / `.getLocalizedString(id)`, `Zotero.ItemFields.getItemTypeFields(id)` / `.getName(id)` / `.getLocalizedString(id)`, `Zotero.CreatorTypes.getTypesForItemType(id)` / `.getLocalizedString(id)` — all cachedTypes.js getters are sync (from external audit: `system.ts:23`, `system.ts:27`, `system.ts:29`, `system.ts:30`, `system.ts:35`, `system.ts:36`).
  - `Zotero.Tags.getID(name)` — sync cache lookup (from external audit: `tags.ts:43`).
  - `Zotero.Styles.get(id)` — sync cache read, returns `Zotero.Style` or `false` (from external audit: `export.ts:54`).
  - `item.getField("x")`, `item.getCreators()`, `item.isNote()`, `item.isAttachment()` — instance getters are sync (from external audit: `export.ts:91`, `export.ts:93`, `notes.ts:35`).
- Async methods the handlers use (from external audit: see rows below for per-source-anchor evidence) — MUST `await`:
  - `Zotero.Items.getAsync(id | ids)` — DB-backed fetch (from external audit: 25+ call sites across items/collections/attachments/notes/search/export).
  - `Zotero.Collections.getAsync(id)`, `Zotero.Searches.getAsync(id)` — DataObjects.getAsync (from external audit: `collections.ts:30`, `search.ts:109`).
  - `Zotero.Items.getAll(libraryID, onlyTopLevel, includeDeleted, asIDs)` — async DB fetch (from external audit: `items.ts:141`, `items.ts:169`, `system.ts:18`).
  - `Zotero.Tags.getAll(libraryID)`, `Zotero.Tags.rename(...)`, `Zotero.Tags.removeFromLibrary(...)` — all async (from external audit: `tags.ts:8`, `tags.ts:37`, `tags.ts:45`).
  - `Zotero.DB.executeTransaction(async () => {...})` — async transaction wrapper (from external audit: `items.ts:157`, `tags.ts:54`).
  - `Zotero.Attachments.importFromFile(...)` / `.importFromURL(...)` / `.addAvailableFile(...)` — async imports (from external audit: `attachments.ts:62`, `attachments.ts:73`, `attachments.ts:93`).
  - `item.saveTx()` / `item.save()` (inside transaction) / `item.eraseTx()`, `col.saveTx()` / `.eraseTx()`, `search.search()` — all async (from external audit: `tags.ts:64`, `search.ts:13`).
- Mandate: handlers MUST NOT add `await` in front of a sync Zotero call (from external audit: `collections.ts:25`, `system.ts:7`, `settings.ts:22`, `tags.ts:43` — all documented as synchronous cache reads in their respective Zotero source anchors).

### 1.3 Error format — `throw { code: -32602 | -32603, message: string }` at the RPC boundary

- `-32602` = JSON-RPC "invalid params" — caller's fault (unknown id, malformed input, missing required field, wrong item type for the operation) (from internal audit: `items.get`, `items.update`, `items.delete`, `collections.get`, `attachments.list`, `notes.create` — all use `throw {code: -32602, message: "...not found: <id>"}` on missing entity).
- `-32603` = JSON-RPC "internal error" — XPI's fault or Zotero's fault (unexpected exception during execution) (from internal audit: `export.bibtex` / `cslJson` / `ris` / `csv` currently raise via `throw new Error` → `-32603`; PRD §3.7 migrates these to structured form).
- Evidence this is the dominant convention: 44 of 77 methods use `throw {code,msg}`; 23 use `no-error-path`; 4 use `throw new Error` (all in `export.*` — see §3.7); 1 uses `silent-false` (from internal audit: `system.currentCollection` error-pattern = `silent-false`; all 77 method rows' `error-pattern` column gives the raw counts).
- Falsy-return contracts from Zotero (e.g. `getAsync(id)` → `false` for missing, `Styles.get(id)` → `false` for unknown, `Tags.getID(name)` → `false` for unknown) MUST be translated to `throw {code: -32602, message: "<Entity> not found: <id>"}` by the handler (from external audit: `items.ts:23` null-guard, `collections.ts:30` null-guard, `export.ts:54` null-guard, `tags.ts:43` null-guard).
- Mandate: the 4 `throw new Error(...)` call sites in `export.*` translator handlers MUST migrate to `throw {code, message}` (from internal audit: `export.bibtex`, `export.cslJson`, `export.ris`, `export.csv` all `throw Error`). See §3.7.

---

## 2. XPI-owned JSON-RPC boundary rules

Rules the XPI adds on top of Zotero's raw API. Every rule below cites the internal audit rows that establish the dominant pattern.

### 2.1 Serialization — every item-returning handler MUST pass the result through `serializeItem`; same for collections via `serializeCollection`

- **Items:** 11 of 18 `items.*` methods return `(serializeItem)` or `[(serializeItem)]` (from internal audit: `items.get`, `items.create`, `items.update`, `items.getTrash` → items-field, `items.getRecent`, `items.addByDOI/URL/ISBN`, `items.addFromFile`, `items.mergeDuplicates`, `items.getRelated`). Non-item returns (`items.delete`, `items.trash`, `items.restore`, `items.batchTrash`, `items.findDuplicates`, `items.addRelated`, `items.removeRelated`) are domain-justified acks, not item data.
- **Collections:** 7 of 12 `collections.*` methods return `(serializeCollection)` or `[(serializeCollection)]` (from internal audit: `collections.list`, `collections.get`, `collections.getSubcollections`, `collections.create`, `collections.rename`, `collections.move`; `collections.tree` extends the shape with `children`). Non-collection returns (`delete`, `addItems`, `removeItems`, `stats`, `getItems` payload) are acks or per-domain data.
- Mandate: a handler MUST NOT return a raw `Zotero.Item` or `Zotero.Collection` instance over RPC; always go through `serializeItem` / `serializeCollection` (from internal audit: 11 of 18 `items.*` and 7 of 12 `collections.*` methods already use the serializers — dominant pattern).
- Exception: **`attachments.list` currently returns a custom `[{contentType, id, key, linkMode, path, title}]` shape** (from internal audit: `attachments.list`). Attachments ARE items — this is a fix target, not an exception. See §3.3.
- Exception: **`notes.get` / `notes.search` return custom note-shaped records** (from internal audit: `notes.get [{content, dateAdded, dateModified, id, key, tags}]`, `notes.search [{content, dateModified, id, parentId}]`). Notes ARE items — fix targets. See §3.4.

### 2.2 Return-shape per family — one mandate per family

- **`items.*` — paginated-vs-bare list split is a violation.** The "items list" shape MUST be one of two forms chosen per-method based on whether the caller can scope the result (from internal audit: `items.getTrash` is paginated, `items.getRecent/addByDOI/URL/ISBN/addFromFile/getRelated` are bare arrays):
  - Paginated envelope `{items, total, offset?, limit?}` when the handler accepts `limit`/`offset` (from internal audit: `items.getTrash {items, limit, offset, total}`).
  - Bare `[(serializeItem)]` when the handler is a scoped read by identifier (from internal audit: `items.getRelated`, `items.addByDOI/URL/ISBN`, `items.addFromFile`).
  - `items.getRecent` accepts `limit?` but returns a bare array — this is a fix target. See §3.1.
- **`collections.*` — paginated envelope omits `offset`/`limit` echo (violation).** `collections.getItems` returns `{items, total}` but accepts `{limit?, offset?}` (from internal audit: `collections.getItems {items, total} / {id, limit?, offset?}`). Must echo the cursor like `items.getTrash`. See §3.2.
- **`attachments.*` — five bespoke shapes across 7 methods (violation).** Every read method has a one-off shape (from internal audit: `attachments.list`, `getFulltext`, `getPDFOutline`, `getPath`, `findPDF`). Only `add` / `addByURL` match the rest of the API. See §3.3.
- **`notes.*` — two different custom list shapes + asymmetric create/update (violations).** `notes.get` and `notes.search` return different custom shapes; `notes.create` returns `{id, key}` while `notes.update` returns `{id, updated}` (from internal audit: `notes.create {id, key}`, `notes.update {id, updated}`). See §3.4.
- **`search.*` — search-spec echo is inconsistent (violation).** `search.quick` / `fulltext` / `byTag` echo their primary input (`query` / `tag`) into the envelope; `search.advanced` / `byIdentifier` do not (from internal audit: `search.quick {items, query, total}`, `search.advanced {items, total}`, `search.byIdentifier {items, total}`). PRD mandate: **never echo the search spec** — callers already know what they sent. Drop `query` from `quick` / `fulltext`, drop `tag` from `byTag`. See §3.5.
- **`tags.*` — scalar-vs-batch asymmetry (justified exception).** `tags.add` / `remove` return `{added|removed, itemId}`; `tags.batchUpdate` returns `{added, removed}` without `itemId` because it spans multiple items (from internal audit: `tags.batchUpdate {added, removed}`). Justified — see §3.6.
- **`export.*` — `bibliography` is a justified dual-output exception; everything else returns `{format, content, count}`.** The four translator exports (`bibtex`, `cslJson`, `ris`, `csv`) all return `{content, count, format}` (from internal audit: `export.bibtex`, `export.cslJson`, `export.ris`, `export.csv`). `export.bibliography` returns `{count, format, html, style, text}` because citeproc-js can render both HTML and plain text from the same engine in one call (from internal audit: `export.bibliography {count, format, html, style, text}`; from external audit: `export.ts:65` `style.getCiteProc()` + `export.ts:67` `engine.setOutputFormat(fmt)` iterated twice). Keep both `html` + `text` — PRD-granted exception. See §3.7.
- **`settings.*` — `settings.get` multi-shape is a violation; `getAll` already exists.** `settings.get {[key]: val} OR_ELSE Record<key,val>` based on whether `key?` is provided (from internal audit: `settings.get multi: {[key]:val} OR_ELSE Record<key,val>`). The no-key case duplicates `settings.getAll`. Fix: remove the no-key branch, make `key` required. See §3.8.
- **`system.*` — heterogeneous by design.** `ping`, `version`, `sync`, `libraries`, `itemTypes`, `itemFields`, `creatorTypes` serve genuinely different data requests; shape uniformity is not the right bar (from internal audit: §"system.* ... heterogeneous-by-design").

### 2.3 Mutation acks — `delete` / `trash` / `restore` return `{<verb>, id}`; `add*` / `remove*` for relations return bare `{<verb>}` WITHOUT an id echo (fix target)

- Dominant pattern: `items.delete {deleted, id}`, `items.trash {id, trashed}`, `items.restore {id, restored}`, `collections.delete {deleted, id}`, `search.deleteSavedSearch {deleted, id}` (from internal audit: all 5 rows).
- Outlier: `items.addRelated {added}`, `items.removeRelated {removed}` — no id echo (from internal audit: both rows flagged `siblings-diverge: yes`). PRD mandate: **add `id` echo to match the scalar-ack convention**. See §3.1.
- Batch ack: `items.batchTrash {trashed: count}` returns a count, not an array (from internal audit: `items.batchTrash {trashed}`). Fix target — should return `{trashed: count, ids: number[]}` to preserve the id trail. See §3.1.

### 2.4 ID encoding — integers for numeric IDs, strings for Zotero keys, ISO-8601 strings for dates

- Numeric IDs MUST be serialized as JSON integers (from external audit: `system.ts:7` `lib.id` is `libraryID` alias returning integer per `library.js#L121-124`; from external audit: `search.ts:13` `s.search()` returns `Promise<number[]>`).
- `key` fields (Zotero's 8-char alphanumeric) MUST be serialized as strings (from internal audit: `collections.get (serializeCollection)` includes `key`; `notes.create {id, key}`).
- Dates MUST be ISO-8601 strings (from internal audit: `notes.get [{content, dateAdded, dateModified, id, key, tags}]` passes Zotero's own ISO-string `dateAdded` / `dateModified` through).
- Mandate: handlers MUST NOT coerce integer IDs to strings. No `String(id)` or `id.toString()` at the serialization boundary (from internal audit: every `{id}` param across 77 methods is destructured as a number; `key` fields are distinct string-typed keys in `serializeItem`/`serializeCollection`).

### 2.5 Null policy — absent optional fields serialize as `null`, never omitted

- `Zotero.Prefs.get(key, true)` returns `undefined` for missing keys; handlers apply `?? null` (from external audit: `settings.ts:22`, `settings.ts:28`, `settings.ts:45`).
- `system.currentCollection` returns `null` when no collection is selected — the one PRD-sanctioned `null` success return (from external audit: `system.ts:43` `pane.getSelectedCollection()`; from internal audit: `system.currentCollection multi: null OR_ELSE {id, key, libraryID, name}`). See §3.9 — the null semantic is retained but `libraryID` → `libraryId` and `silent-false` stays an exception for this method only.
- Mandate: `JSON.stringify` drops `undefined` keys by default. Handlers MUST use `?? null` explicitly at the boundary to force serialization as `null` (from external audit: `settings.ts:22`, `settings.ts:28`, `settings.ts:45` already follow this; `tags.ts:8` violates it).
- Exception-in-disguise: `tags.list` maps `{tag: t.tag, type: t.type}` — for manual tags `t.type` is `undefined` and gets dropped by `JSON.stringify` (from external audit: `tags.ts:8`). Violates the null rule. Fix: `type: t.type ?? 0`. See §3.6.

### 2.6 Parameter validation — handlers MUST validate invariants Zotero enforces, and throw `-32602` with a clearer message before Zotero throws

- `notes.createAnnotation` currently forwards `params.text` unconditionally; Zotero's `annotationText` setter throws for non-highlight/underline types (from external audit: `notes.ts:104`). Handler MUST gate on `params.type ∈ {highlight, underline}`.
- `notes.createAnnotation` currently forwards `params.color` unconditionally; Zotero requires 6-char hex (from external audit: `notes.ts:104`). Handler MUST validate before the setter call.
- Mandate: where a Zotero setter has an invariant that the CLI caller cannot know about, the handler MUST translate to `-32602` up-front. No bare Zotero errors leaking through as `-32603` (from external audit: `notes.ts:104` — `annotationType` ordering, `annotationText` type-gating, `annotationColor` hex-validation are all Zotero invariants the handler silently forwards).

---

## 3. Divergence acknowledgments (36 `siblings-diverge=yes` rows)

Each sub-section lists the divergent rows in a family, and classifies each as:
- **VIOLATION → FIX** — diverges from PRD rules in §1–2; fix in Task 8 (from internal audit: classification applies to rows with `siblings-diverge=yes` that don't fit a principled cluster).
- **EXCEPTION** — PRD-granted, rationale stated (from internal audit: classification applies to rows with `siblings-diverge=yes` that have domain-justified shape like `collections.stats`, `export.bibliography`).

### 3.1 items.* (6 outlier rows)

- `items.getTrash` (from internal audit: `items.getTrash {items, limit, offset, total}`) — **EXCEPTION**. Paginated envelope is correct per §2.2; siblings should move toward this shape, not away from it.
- `items.batchTrash` (from internal audit: `items.batchTrash {trashed}`) — **VIOLATION → FIX**. Must return `{trashed: count, ids: number[]}` to preserve the id trail and align with §2.3 batch-ack rule.
- `items.getRecent` (from internal audit: `items.getRecent [(serializeItem)]`) — **VIOLATION → FIX**. Accepts `limit?` but returns bare array; must return paginated envelope `{items, total, limit?}` per §2.2 (no `offset` since the method has no offset param).
- `items.findDuplicates` (from internal audit: `items.findDuplicates {groups, totalGroups}`) — **EXCEPTION**. Domain-specific shape (grouped item IDs) doesn't fit any list cluster.
- `items.addRelated` (from internal audit: `items.addRelated {added}`) — **VIOLATION → FIX**. Must return `{added, id}` per §2.3.
- `items.removeRelated` (from internal audit: `items.removeRelated {removed}`) — **VIOLATION → FIX**. Must return `{removed, id}` per §2.3.

### 3.2 collections.* (4 outlier rows)

- `collections.getItems` (from internal audit: `collections.getItems {items, total}`) — **VIOLATION → FIX**. Accepts `{limit?, offset?}` but doesn't echo the cursor; must return `{items, total, offset?, limit?}` per §2.2.
- `collections.tree` (from internal audit: `collections.tree [{children, ...serializeCollection}]`) — **EXCEPTION**. Tree shape is domain-justified. **BUT** the underlying `getByLibrary(libraryID, false)` call is broken — subcollections are never fetched, so the tree is flat (from external audit: `collections.ts:57` ✗signature). **VIOLATION → FIX** on the Zotero call, shape stays.
- `collections.removeItems` (from internal audit: `collections.removeItems {collectionId, removed} / no-error-path`) — **VIOLATION → FIX**. Mirror `collections.addItems {added, collectionId} / throw {code,msg}` — same safety surface (unknown collection id), must throw `-32602` per §1.3.
- `collections.stats` (from internal audit: `collections.stats {attachments, id, items, name, notes, subcollections}`) — **EXCEPTION**. Per-family unique stats shape is domain-justified.

### 3.3 attachments.* (5 outlier rows — heaviest family)

- `attachments.list` (from internal audit: `attachments.list [{contentType, id, key, linkMode, path, title}]`) — **VIOLATION → FIX**. Attachments ARE items; must use `[(serializeItem)]` per §2.1.
- `attachments.getFulltext` (from internal audit: `attachments.getFulltext {content, id, indexedChars, totalChars}`) — **EXCEPTION** on the shape (domain-justified: fulltext-specific metadata). **BUT** the underlying `Zotero.Fulltext.getItemContent` call does not exist in Zotero 8 (from external audit: `attachments.ts:33` ✗signature). **VIOLATION → FIX** on the Zotero call.
- `attachments.getPDFOutline` (from internal audit: `attachments.getPDFOutline {id, outline}`) — **EXCEPTION** on shape. **BUT** `Zotero.PDFWorker.getOutline` does not exist in Zotero 8 (from external audit: `attachments.ts:53` ✗signature). **VIOLATION → FIX** on the Zotero call (or remove the method).
- `attachments.getPath` (from internal audit: `attachments.getPath {id, path}`) — **EXCEPTION**. Simple lookup shape, domain-justified.
- `attachments.findPDF` (from internal audit: `attachments.findPDF multi: {found:false} OR_ELSE {attachment, found:true}`) — **VIOLATION → FIX**. Boolean-discriminated multi-return encourages sentinel-branching over exception handling. Fix: return `{attachment: (serializeItem) | null}` — callers null-check the attachment field, aligning with §2.5 null rule. Also: `addAvailablePDF` at `attachments.ts:93` is deprecated, switch to `addAvailableFile` (from external audit: `attachments.ts:93` ⚠deprecated).

### 3.4 notes.* (5 outlier rows)

- `notes.get` (from internal audit: `notes.get [{content, dateAdded, dateModified, id, key, tags}]`) — **VIOLATION → FIX**. Notes are items; use `[(serializeItem)]` per §2.1 and expose the note body via a `content`-typed field in `serializeItem` output.
- `notes.search` (from internal audit: `notes.search [{content, dateModified, id, parentId}]`) — **VIOLATION → FIX**. Same as `notes.get` — use `[(serializeItem)]`. The truncated `content` (500 chars) can remain as a typed field, but the envelope must be `{items, total, limit?}` per §2.2.
- `notes.update` (from internal audit: `notes.update {id, updated}`) — **VIOLATION → FIX**. Asymmetric with `notes.create {id, key}`. Align: both should return the updated note via `serializeItem` (same contract as `items.update`).
- `notes.getAnnotations` (from internal audit: `notes.getAnnotations [{color, comment, dateAdded, id, pageLabel, position, tags, text, type}]`) — **EXCEPTION** on shape (annotations have distinct fields that don't fit `serializeItem`). **BUT** the underlying `pdfItem.getAnnotations()` cast is a lie — returns `Zotero.Item[]` not `number[]` (from external audit: `notes.ts:71` ✗signature). **VIOLATION → FIX** on the Zotero call.
- `notes.createAnnotation` (from internal audit: `notes.createAnnotation {id}`) — **VIOLATION → FIX**. Asymmetric with `notes.create {id, key}`. Align: return `{id, key}`. Also add param validation per §2.6 (from external audit: `notes.ts:104` ⚠cumbersome).

### 3.5 search.* (5 outlier rows)

- `search.advanced` (from internal audit: `search.advanced {items, total}`) — **VIOLATION → FIX**. Must add `limit?` param for consistency with `quick` / `fulltext` / `byTag` (from external audit: `search.ts:31` ⚠cumbersome). Return shape stays `{items, total, limit?}`.
- `search.byIdentifier` (from internal audit: `search.byIdentifier {items, total}`) — **VIOLATION → FIX**. Same as `advanced` — add `limit?` (from external audit: `search.ts:79` ⚠cumbersome).
- `search.savedSearches` / `createSavedSearch` / `deleteSavedSearch` (from internal audit: all 3 rows) — **EXCEPTION**. These are a separate CRUD subfamily on saved-searches (not the result-set search methods). Their divergence from `quick/advanced/fulltext/byTag/byIdentifier` is by-design.
- Sub-divergence: `createSavedSearch {id, name}` omits `key` while `savedSearches [{conditions, id, key, name}]` list entries include it (from internal audit: both rows). **VIOLATION → FIX**. Align `createSavedSearch` to return `{id, key, name}` per §2.1 symmetry.
- Also: `Zotero.Searches.getByLibrary` has a cold-cache bug (from external audit: `search.ts:85` ⚠cumbersome). **VIOLATION → FIX** — use `Zotero.Searches.getAll(libraryID)` which hits the DB.
- Also: `search.*` all use the `s.addCondition("noChildren", "true", "")` form (from external audit: `search.ts:12` ⚠cumbersome). Minor style — `replace_all` to 2-arg form per Zotero's own convention.

### 3.6 tags.* (4 outlier rows)

- `tags.list` (from internal audit: `tags.list [{tag, type}]`) — **EXCEPTION** on the shape (tags are not items). **BUT** `type` serializes as `undefined` for manual tags and gets dropped by JSON.stringify (from external audit: `tags.ts:8`). **VIOLATION → FIX** — use `type: t.type ?? 0` per §2.5.
- `tags.rename` (from internal audit: `tags.rename {from, renamed, to}`) — **EXCEPTION**. Unique shape is domain-justified (rename semantics need both from/to).
- `tags.delete` (from internal audit: `tags.delete {deleted, tag}`) — **EXCEPTION**. Takes `{tag}` (string name) instead of `{id}` because tags don't have caller-exposed numeric IDs in the RPC. Documented constraint.
- `tags.batchUpdate` (from internal audit: `tags.batchUpdate {added, removed}`) — **EXCEPTION**. Batch mirror of `tags.add` / `tags.remove`; no `itemId` because the op spans multiple items.
- Cross-cutting: `tags.list` / `rename` / `delete` hard-default to the user library — no `libraryId?` param (from external audit: `tags.ts:7` note). **VIOLATION → FIX** — accept `libraryId?` across the family for group-library support.

### 3.7 export.* (2 outlier rows)

- `export.bibliography` (from internal audit: `export.bibliography {count, format, html, style, text}`) — **EXCEPTION**. Dual-output (html + text) is justified by citeproc-js supporting both formats from one engine (from external audit: `export.ts:65` `style.getCiteProc()` + `export.ts:67` `engine.setOutputFormat(fmt)`). CLI knows to pick `.text` or `.html` based on user flag.
- `export.citationKey` (from internal audit: `export.citationKey {citationKey, id}`) — **VIOLATION → FIX (relocation)**. This is a per-item metadata lookup, not a bibliographic export. Should move to `items.citationKey`. Classified as low-priority refactor.
- Cross-cutting: 4 translator methods (`bibtex`/`cslJson`/`ris`/`csv`) use `throw new Error("Export failed")` yielding `-32603` (from internal audit: all 4 rows with `throw Error`). **VIOLATION → FIX** — migrate to `throw {code, message}` per §1.3.

### 3.8 settings.* (3 outlier rows)

- `settings.get multi: {[key]:val} OR_ELSE Record<key,val>` (from internal audit: `settings.get`) — **VIOLATION → FIX**. Make `key` required; the no-key branch duplicates `settings.getAll`. Post-fix shape: single-pair `{[key]: val}` only.
- `settings.set {key, value}` vs `settings.setAll {updated}` (from internal audit: both rows) — **VIOLATION → FIX**. Scalar-vs-batch asymmetry like `items.trash` vs `items.batchTrash`. Align: `setAll` should return `{updated: Record<key,val>}` echoing the applied pairs, not a key list.
- Also: `settings.setAll` silently drops unknown keys while `settings.set` throws (from external audit: `settings.ts:54` note). **VIOLATION → FIX** — `setAll` must throw `-32602` on first unknown key, consistent with `set`.

### 3.9 system.* (2 outlier rows)

- `system.libraryStats {collections, items, libraryID}` (from internal audit: `system.libraryStats`) — **VIOLATION → FIX**. Only method using `libraryID` (uppercase-ID) at the wire; rename to `libraryId` per §1.1 majority rule. Also: accepts `{id?}` as input but returns `{libraryID}` — key casing mismatch on input vs output.
- `system.currentCollection multi: null OR_ELSE {id, key, libraryID, name}` (from internal audit: `system.currentCollection`) — **EXCEPTION** on the `null`-success return (no-selection is a valid success state, not an error). **VIOLATION → FIX** on the `libraryID` → `libraryId` rename per §1.1.
- Cross-cutting: `system.switchLibrary {id}` (from internal audit: `system.switchLibrary`) triggers `Zotero.Prefs.set("lastLibraryID", params.id)` which writes to Zotero's own pref branch (from external audit: `system.ts:13` ✗signature). **VIOLATION → FIX** — use `("extensions.zotron.lastLibraryID", params.id, true)` per §1.2 settings pattern.
- Cross-cutting: `system.sync {status}` (from internal audit: `system.sync`) calls `Zotero.Sync.Runner.sync({libraries: "all"})` which yields `Array.from("all") → ["a","l","l"]` (from external audit: `system.ts:38` ✗signature). **VIOLATION → FIX** — drop the key, pass `{}`.
- Cross-cutting: `system.libraryStats` uses `Zotero.Items.getAll(libraryID, false, false)` (hydrates full items) for a count-only use case (from external audit: `system.ts:18` ⚠cumbersome). **VIOLATION → FIX** — pass `asIDs=true` for the count path.
- Cross-cutting: `system.libraryStats` uses `Zotero.Collections.getByLibrary(libraryID, false)` (top-level only) while stats should be library-wide (from external audit: `system.ts:19` ⚠cumbersome). **VIOLATION → FIX** — pass `recursive=true`.

---

## 4. Summary — fix counts for Task 8

- **Exceptions granted** (14) (from internal audit: each row classified as EXCEPTION in §3.1–3.9): `items.getTrash` shape; `items.findDuplicates` shape; `collections.tree` shape (call fix separate); `collections.stats` shape; `attachments.getFulltext` shape; `attachments.getPDFOutline` shape; `attachments.getPath` shape; `notes.getAnnotations` shape; `search.savedSearches/create/delete` subfamily presence; `tags.rename` shape; `tags.delete` id-by-name; `tags.batchUpdate` shape; `export.bibliography` dual output; `system.currentCollection` null-success.
- **Violations** (fix targets for Task 8, roughly grouped) (from external audit: all ✗signature + ⚠deprecated + load-bearing ⚠cumbersome rows; from internal audit: §3.1–3.9 entries classified VIOLATION → FIX):
  - External-audit ✗signature bugs: 6 (`items.ts` processDocuments, importFromFile Array.isArray, getSetItemsByItemID; `collections.ts:57` tree; `attachments.ts:33` getItemContent; `attachments.ts:53` getOutline; `notes.ts:71` getAnnotations cast; `system.ts:13` Prefs.set; `system.ts:38` Sync.Runner — 8 total).
  - External-audit ⚠deprecated: 1 (`attachments.ts:93` addAvailablePDF).
  - External-audit ⚠cumbersome worth fixing: ~6 (getTrash via getDeleted; getRecent via Search; translate with `collections` option; searches.getByLibrary cold-cache; noChildren arg form; libraryStats asIDs/recursive).
  - Internal-audit shape violations: ~17 across families (listed in §3.1–3.9).
  - Internal-audit cross-cutting: 4 (`items.getRecent` pagination, `collections.removeItems` error path, `export.*` `throw Error` → `{code,msg}`, `settings.setAll` unknown-key behavior, `tags.*` libraryId param, wire-format `libraryID`→`libraryId`).
- **?unverifiable rows deferred** (from external audit: `system.ts:43` is the sole `?unverifiable` row in the 158-row external audit): 1 — `pane.getSelectedCollection()` is a frontend method with no xpcom anchor; inferred-correct via usage convention, no fix needed.

Total fix targets feeding Task 8: **approximately 35** discrete code changes across 9 handler files.
