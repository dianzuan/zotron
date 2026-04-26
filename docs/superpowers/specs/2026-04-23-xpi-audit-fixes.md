> **Next step:** Run `superpowers:writing-plans` against this file to
> produce a TDD-structured implementation plan that applies each fix.
> The downstream plan should group `blocker` + `correctness` fixes
> into a first release (required before XPI 1.1); `consistency` +
> `cleanup` fixes can batch into a follow-up.

# XPI Audit — Fix Catalog

Concrete code changes required to align the XPI with the 2026-04-23 PRD.
Each fix flows into a downstream implementation plan. Severity legend:

- `blocker` — breaks current workflow (silent data loss, wrong result, 500s).
- `correctness` — works today but is Zotero API abuse; fragile across versions.
- `consistency` — follows PRD formatting / naming rules.
- `cleanup` — removes cumbersome idiom when a simpler Zotero helper exists.

Fix row format:

| # | file:line | severity | current | target | prd-rule | risk |
|---|---|---|---|---|---|---|

- `current` — one-line summary of existing code.
- `target` — one-line summary of the fix.
- `prd-rule` — short cite of the PRD section or bullet that prescribes the fix.
- `risk` — what could go wrong; `low` if it's a pure rename.

---

| # | file:line | severity | current | target | prd-rule | risk |
|---|---|---|---|---|---|---|
| 1 | src/handlers/collections.ts:57 | blocker | `getByLibrary(libraryID, false)` returns top-level only so buildTree always emits a flat tree | `getByLibrary(libraryID, true)` so subcollections are fetched and the tree is nested | PRD §3.2 / external ✗signature | low — pure recursive flag flip; existing tree consumers already expect nesting |
| 2 | src/handlers/attachments.ts:33 | blocker | `Zotero.Fulltext.getItemContent(id)` does not exist in Zotero 8 — silently returns `{content:"",indexedChars:0,totalChars:0}` for every call | read cache file via `Zotero.File.getContentsAsync(Zotero.Fulltext.getItemCacheFile(item).path)` + read chars/pages from `fulltextItems` SQL row | PRD §3.3 / external ✗signature | medium — replacement spans 2 calls + DB query; needs sanity check on un-indexed items |
| 3 | src/handlers/attachments.ts:53 | blocker | `Zotero.PDFWorker.getOutline(id)` does not exist — throws TypeError at runtime | remove the method, OR extract via in-worker `pdfjs-dist`; confirm against Zotero 8.0.4 runtime | PRD §3.3 / external ✗signature | **FIXED (2026-04-25)** — Option A applied: method deleted from attachments.ts. Callers now get -32601 Method not found instead of -32603 TypeError. See notes/2026-04-25-pdfoutline-decision.md |
| 4 | src/handlers/items.ts:200 | blocker | `processDocuments(url, p=>p)` assigns the returned `Promise<Array>` to `doc` then `setDocument(doc)` — translation silently fails | `const [doc] = await Zotero.HTTP.processDocuments(url, d => d)` | PRD §4 (external ✗signature) | low — destructure-only |
| 5 | src/handlers/items.ts:257 | blocker | `duplicates.getSetItemsByItemID()` called with zero args (Zotero 8 expects one itemID) — `findDuplicates` always returns `{groups:[],totalGroups:0}` | rebuild enumeration: `const search = await duplicates.getSearchObject(); const ids = await search.search(); const seen = new Set(); const groups = []; for (const id of ids) { if (seen.has(id)) continue; const set = duplicates.getSetItemsByItemID(id); set.forEach(x => seen.add(x)); groups.push(set); }` | PRD §4 (external ✗signature) | medium — rewriting the duplicate-walk; needs test against a real duplicate-set |
| 6 | src/handlers/notes.ts:71 | blocker | `pdfItem.getAnnotations()` returns `Zotero.Item[]` but the cast `as unknown as number[]` lies; downstream `Zotero.Items.getAsync(annotationIDs)` runs `Number.isInteger(item)` → false → every annotation dropped | call `getAnnotations(false, true)` to get IDs (then keep current `getAsync`), OR drop the cast + extra `getAsync` and use returned items directly | PRD §3.4 / external ✗signature | low — single call shape change; covered by annotation listing tests |
| 7 | src/handlers/notes.ts:72 | blocker | downstream of fix #6 — once #6 lands this row becomes ✓correct | (no separate fix; resolved by #6) | PRD §3.4 / external ✗signature | low — verify-only |
| 8 | src/handlers/system.ts:13 | blocker | `Zotero.Prefs.set("lastLibraryID", id)` defaults `global=false` → writes to `extensions.zotero.lastLibraryID` polluting Zotero's own pref branch | `Zotero.Prefs.set("extensions.zotero-bridge.lastLibraryID", id, true)` matching settings.ts:38 convention | PRD §3.9 / external ✗signature | low — namespace fix; switchLibrary is rarely persisted today so no migration needed |
| 9 | src/handlers/system.ts:38 | blocker | `Zotero.Sync.Runner.sync({libraries:"all"})` — `Array.from("all")` yields `["a","l","l"]` so checkLibraries gets bogus IDs; "sync all" semantic is *omit* the key | `Zotero.Sync.Runner.sync()` (or `sync({})`) | PRD §3.9 / external ✗signature | low — single literal change; matches Zotero's documented sentinel |
| 10 | src/handlers/search.ts:85 | blocker | `Zotero.Searches.getByLibrary(libraryID)` reads `_objectCache` only — returns `[]` on cold cache, so `search.savedSearches` is empty after every XPI reload until the user opens a saved search in the UI | `Zotero.Searches.getAll(libraryID)` — DB-backed, async, sorted by name | PRD §3.5 / external ⚠cumbersome (cold-cache bug) | low — drop `as any` cast, replace name, add `await` |
| 11 | src/handlers/items.ts:152 | correctness | `batchTrash` returns `{trashed: count}` only — id trail lost | `{trashed: count, ids: number[]}` | PRD §3.1 / §2.3 batch-ack | low — shape extension, additive |
| 12 | src/handlers/collections.ts:106 | correctness | `removeItems` has `no-error-path` — silently skips missing collection while sibling `addItems` throws `-32602` | throw `{code:-32602, message:"Collection not found: <id>"}` on missing collection | PRD §3.2 / §1.3 | low — symmetry with addItems pattern |
| 13 | src/handlers/notes.ts:104 | correctness | `createAnnotation` forwards `params.text` / `params.color` unconditionally — Zotero throws raw errors for non-highlight/underline types or non-hex color, surfacing as `-32603` | gate `annotationText` assignment on `params.type ∈ {highlight, underline}`; validate hex regex on color; throw `-32602` up-front for both | PRD §2.6 / §3.4 | low — pure validation layer |
| 14 | src/handlers/export.ts:27 | correctness | `bibtex` uses `throw new Error("Export failed")` → `-32603` | `throw {code:-32603, message:"Export failed: <translator error>"}` | PRD §1.3 / §3.7 | low — error wrapper change |
| 15 | src/handlers/export.ts:32 | correctness | `cslJson` same as #14 | `throw {code,message}` | PRD §1.3 / §3.7 | low |
| 16 | src/handlers/export.ts:37 | correctness | `ris` same as #14 | `throw {code,message}` | PRD §1.3 / §3.7 | low |
| 17 | src/handlers/export.ts:42 | correctness | `csv` same as #14 | `throw {code,message}` | PRD §1.3 / §3.7 | low |
| 18 | src/handlers/tags.ts:8 | correctness | `tags.list` maps `{tag, type: t.type}` — `type` is `undefined` for manual tags and gets dropped by `JSON.stringify`, so the field appears intermittently | `type: t.type ?? 0` | PRD §2.5 / §3.6 | low |
| 19 | src/handlers/settings.ts:50 | correctness | `setAll` silently drops unknown keys while `set` throws | throw `-32602` on first unknown key (consistent with `set`) | PRD §1.3 / §3.8 | low — strictness increase; document in CHANGELOG |
| 20 | src/handlers/system.ts:19 | correctness | `Zotero.Collections.getByLibrary(libraryID, false)` for libraryStats counts top-level only | pass `recursive=true` to count library-wide | PRD §3.9 / external ⚠cumbersome | low — semantic alignment with `items` count |
| 21 | src/handlers/export.ts:93 | correctness | citation-key fallback uses `item.getField("year")` — `"year"` is not a primary field; often returns empty | `Zotero.Date.strToDate(item.getField("date")).year` | PRD §3.7 / external ⚠cumbersome | low — field rename + parse |
| 22 | src/handlers/items.ts:165 | consistency | `getRecent` returns bare `[(serializeItem)]` despite accepting `limit?` | paginated envelope `{items, total, limit?}` (no offset — method has no offset param) | PRD §2.2 / §3.1 | low — shape change, breaking for callers |
| 23 | src/handlers/items.ts:294 | consistency | `addRelated` returns `{added}` — no id echo | `{added, id}` per scalar-ack convention | PRD §2.3 / §3.1 | low |
| 24 | src/handlers/items.ts:305 | consistency | `removeRelated` returns `{removed}` — no id echo | `{removed, id}` per scalar-ack convention | PRD §2.3 / §3.1 | low |
| 25 | src/handlers/collections.ts:35 | consistency | `getItems` returns `{items, total}` despite accepting `{limit?, offset?}` | echo cursor: `{items, total, offset?, limit?}` like `items.getTrash` | PRD §2.2 / §3.2 | low |
| 26 | src/handlers/attachments.ts:6 | consistency | `attachments.list` returns custom `[{contentType, id, key, linkMode, path, title}]` | `[(serializeItem)]` — attachments ARE items | PRD §2.1 / §3.3 | medium — breaking shape change for any consumer; serializeItem already covers all fields |
| 27 | src/handlers/attachments.ts:90 | consistency | `findPDF` returns boolean-discriminated multi `{found:false} OR_ELSE {attachment, found:true}` | `{attachment: (serializeItem) | null}` per §2.5 null-policy | PRD §2.5 / §3.3 | medium — breaking; callers must null-check instead of branching `found` |
| 28 | src/handlers/notes.ts:5 | consistency | `notes.get` returns custom `[{content, dateAdded, dateModified, id, key, tags}]` | `[(serializeItem)]` with note body exposed via a typed `content` field | PRD §2.1 / §3.4 | medium — breaking; serializeItem must learn note `content` |
| 29 | src/handlers/notes.ts:42 | consistency | `notes.search` returns custom `[{content, dateModified, id, parentId}]`, no envelope | paginated envelope `{items, total, limit?}` of `[(serializeItem)]`; truncated content can stay as a typed field | PRD §2.1 / §2.2 / §3.4 | medium — breaking |
| 30 | src/handlers/notes.ts:34 | consistency | `notes.update` returns `{id, updated}` — asymmetric with `notes.create {id, key}` and `items.update (serializeItem)` | `(serializeItem)` | PRD §2.1 / §3.4 | low — shape upgrade |
| 31 | src/handlers/notes.ts:86 | consistency | `createAnnotation` returns `{id}` only — asymmetric with `notes.create {id, key}` | `{id, key}` | PRD §3.4 | low |
| 32 | src/handlers/search.ts:6 | consistency | `search.quick` echoes `query` into envelope `{items, query, total}` | drop `query` echo: `{items, total, limit?}` | PRD §2.2 / §3.5 | low |
| 33 | src/handlers/search.ts:38 | consistency | `search.fulltext` echoes `query` | drop `query` echo | PRD §2.2 / §3.5 | low |
| 34 | src/handlers/search.ts:54 | consistency | `search.byTag` echoes `tag` | drop `tag` echo | PRD §2.2 / §3.5 | low |
| 35 | src/handlers/search.ts:22 | consistency | `search.advanced` has no `limit?` param — fetches every match | accept `limit?`; envelope `{items, total, limit?}` | PRD §3.5 / external ⚠cumbersome | low — additive param, default unbounded |
| 36 | src/handlers/search.ts:70 | consistency | `search.byIdentifier` has no `limit?` param | accept `limit?` | PRD §3.5 / external ⚠cumbersome | low — additive |
| 37 | src/handlers/search.ts:94 | consistency | `createSavedSearch` returns `{id, name}` — `key` missing while `savedSearches` list entries include it | `{id, key, name}` | PRD §3.5 | low |
| 38 | src/handlers/settings.ts:20 | consistency | `settings.get` is the only multi-shape method (`{[key]:val} OR_ELSE Record<key,val>` based on whether `key?` provided) — no-key branch duplicates `getAll` | make `key` required; single-pair return only | PRD §3.8 | medium — breaking for callers using `get()` as `getAll()` |
| 39 | src/handlers/settings.ts:50 | consistency | `setAll` returns `{updated: [keys]}` (key list) | `{updated: Record<key,val>}` echoing applied pairs | PRD §3.8 | low |
| 40 | src/handlers/system.ts:16 | consistency | `libraryStats` returns `{libraryID, ...}` — only wire-side `libraryID` outlier | `libraryId` (camelCase) per majority rule | PRD §1.1 / §3.9 | low — pure rename |
| 41 | src/handlers/system.ts:39 | consistency | `currentCollection` returns `{id, key, libraryID, name}` | `libraryID` → `libraryId` | PRD §1.1 / §3.9 | low — pure rename |
| 42 | src/handlers/tags.ts:5 | consistency | `tags.list` hard-defaults to user library — no `libraryId?` param | accept `libraryId?` | PRD §3.6 (cross-cutting) | low — additive |
| 43 | src/handlers/tags.ts:35 | consistency | `tags.rename` hard-defaults to user library | accept `libraryId?` | PRD §3.6 | low — additive |
| 44 | src/handlers/tags.ts:41 | consistency | `tags.delete` hard-defaults to user library | accept `libraryId?` | PRD §3.6 | low — additive |
| 45 | src/handlers/attachments.ts:93 | cleanup | `Zotero.Attachments.addAvailablePDF(parent)` is a deprecated shim that emits a `Zotero.warn(...)` on every call | `Zotero.Attachments.addAvailableFile(item, options?)` — identical signature | PRD §3.3 / external ⚠deprecated | low — drop-in rename |
| 46 | src/handlers/search.ts:12 | cleanup | `s.addCondition("noChildren", "true", "")` — Zotero's own callers use 2-arg form | drop the empty third arg (5 occurrences in search.ts) | PRD §3.5 / external ⚠cumbersome | low — `replace_all` |
| 47 | src/handlers/search.ts:29 | cleanup | same as #46 | drop third arg | PRD §3.5 | low |
| 48 | src/handlers/search.ts:44 | cleanup | same as #46 | drop third arg | PRD §3.5 | low |
| 49 | src/handlers/search.ts:60 | cleanup | same as #46 | drop third arg | PRD §3.5 | low |
| 50 | src/handlers/search.ts:77 | cleanup | same as #46 | drop third arg | PRD §3.5 | low |
| 51 | src/handlers/export.ts:65 | cleanup | `style.getCiteProc()` called twice in 2-iter loop — rebuilds engine each time, no `cache:true` | build engine once, switch output format with `engine.setOutputFormat(fmt)` | PRD §3.7 / external ⚠cumbersome | low — perf cleanup, behavior unchanged |
| 52 | src/handlers/export.ts:87 | cleanup | `export.citationKey` is a per-item metadata lookup mis-filed under `export.*` | relocate to `items.citationKey`; same shape `{citationKey, id}` | PRD §3.7 (relocation) | medium — breaking; downstream callers must update method name |
| 53 | src/handlers/collections.ts:97 | cleanup | `addItems` loop-fetches each item then `addToCollection + saveTx` (N round-trips, N transactions) | `Zotero.Collection.prototype.addItems(itemIDs)` — single transactional call | PRD §3.2 / external ⚠cumbersome | low — Zotero already has the batch helper |
| 54 | src/handlers/collections.ts:108 | cleanup | symmetric to #53 — `removeItems` is N+1 | `col.removeItems(itemIDs)` | PRD §3.2 / external ⚠cumbersome | low |
| 55 | src/handlers/items.ts:184 | cleanup | translate-then-loop pattern: `translate.translate({libraryID})` then second-pass `addToCollection + saveTx` per item | pass `collections: [params.collection]` option to `translate.translate` to fold into one transaction | PRD §4 / external ⚠cumbersome | low — option supported by translate.js#L2188 |
| 56 | src/handlers/items.ts:207 | cleanup | same pattern as #55 (URL flow) | pass `collections` option | PRD §4 / external ⚠cumbersome | low |
| 57 | src/handlers/items.ts:222 | cleanup | same pattern as #55 (ISBN flow) | pass `collections` option | PRD §4 / external ⚠cumbersome | low |
| 58 | src/handlers/items.ts:141 | cleanup | `getTrash` loads every library item then JS-filters by `deleted && !isNote && !isAttachment` — O(library size) for a bounded query | `Zotero.Items.getDeleted(libraryID, asIDs, days)` returns trashed IDs in one call | PRD §4 / external ⚠cumbersome | low — Zotero ships the helper |
| 59 | src/handlers/items.ts:169 | cleanup | `getRecent` loads every library item then JS-sorts to grab top 20 — O(library size) for a `limit=20` query | `Zotero.Search` with sort conditions OR direct `Zotero.DB.queryAsync` for top-N IDs | PRD §4 / external ⚠cumbersome | medium — replacement is more code; the wins are real on big libraries |
| 60 | src/handlers/items.ts:242 | cleanup | `Array.isArray(importedItems)` branch is dead code — `importFromFile` always returns a single Item | drop the array branch; `return [serializeItem(importedItems)]` | PRD §4 / external ✗signature | low — dead-code removal |
| 61 | src/handlers/system.ts:18 | cleanup | `getAll(libraryID, false, false)` hydrates full Items for a count-only call | pass `asIDs=true` to short-circuit to integer-ID list | PRD §3.9 / external ⚠cumbersome | low — fourth arg flip |

---

## Notes for the downstream implementation plan

- Fixes #6 and #7 land together — #7 is the verify step on the same call site.
- Fixes #14–17 are textually identical; bundle as one commit.
- Fixes #46–50 are textually identical (`replace_all` on `addCondition` 3-arg form); one commit.
- Fixes #42–44 are the `libraryId?` cross-cutting param across `tags.*`; one commit covering all three signatures.
- Fixes #1, #6, and notes.ts:72 (#7) are the highest-impact silent-data-loss fixes — schedule them first in the implementation plan.
- Fix #3 (PDFOutline) needs an upstream decision before implementation: remove method, or build pdfjs-in-worker extraction. Don't block other work on it.
- Fix #58 (`getDeleted`) and #59 (recent-via-Search) overlap with the §3.1 shape change for `getRecent` (#22) — sequence them together so the new envelope and the new query land in one commit.
