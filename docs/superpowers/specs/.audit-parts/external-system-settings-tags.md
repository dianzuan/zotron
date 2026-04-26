# External audit: system.ts + settings.ts + tags.ts

Target: three handlers, Zotero 8.0.4. Row format / verdicts per design doc
(`2026-04-23-xpi-api-audit-design.md`).

**Pipe-safety legend** (applies to every row's `note` column):

- `OR_ELSE` stands in for the JS logical-OR operator (`||`), since a raw
  `|` would split the markdown table.
- `&#124;` is the HTML-entity form used when embedding a code snippet
  inline that needs to carry a literal pipe (e.g. a TS union type).

Scope note: this table may include calls on Zotero-returned instances
(`lib.editable`, `pane.getSelectedCollection`, `item.save`) that the narrow
`Zotero\.\w+\.\w+|new Zotero\.\w+` regex doesn't pick up. Such calls get
their own rows keyed on real line numbers when they carry findings or verify
load-bearing signatures.

**Actual enumeration totals declared here after Step 3:**

- `system.ts`: narrow-grep finds **15** `Zotero.*` call sites. The plan said
  "expected 17"; the 2-count gap is because the narrow regex `Zotero\.\w+\.\w+`
  requires two dots after `Zotero`, which excludes `Zotero.version` (line 5)
  and `Zotero.getActiveZoteroPane()` (line 41). Both are audited as rows.
  Two further splits from instance access: `lib.id` / `lib.libraryType` /
  `lib.name` / `lib.editable` share one row on line 8 (the narrow regex
  misses property access on a returned Library instance, and the
  `id`/`libraryID` alias is load-bearing per `library.js#L121-124`), and
  `pane.getSelectedCollection()` gets its own row on line 43 (UI-context-
  dependent, tied to the `getActiveZoteroPane` finding). Table has **19
  rows** — 15 narrow + 2 regex-missed (`version`, `getActiveZoteroPane`) +
  2 instance splits (line 8 Library props, line 43 ZoteroPane method).
- `settings.ts`: narrow-grep finds **5** `Zotero.*` call sites (matches
  plan). No instance-method splits; all 5 are audited in place. Table has
  **5 rows**.
- `tags.ts`: narrow-grep finds **10** `Zotero.*` call sites. The plan said
  "expected 11"; the gap is the narrow regex missing nothing semantically —
  all 10 are present. One extra split row: `item.save()` inside
  `Zotero.DB.executeTransaction` at tags.ts:64 (load-bearing — verifies the
  `save()` vs `saveTx()` contract per `dataObject.js#L913-924` (save emits
  the transaction-warning) and `dataObject.js#L1012` (saveTx), which is
  the exact idiom the bibliography-style mismatch would break). Table has
  **11 rows**.

Total rows across three sections: **35** (19 + 5 + 11). Narrow-grep total is
**30** (15 + 5 + 10). The +5 widening: 2 regex-missed in system.ts
(`version`, `getActiveZoteroPane`), 1 instance-property row in system.ts
(line 8 Library props), 1 instance-method row in system.ts (line 43
`pane.getSelectedCollection`), 1 instance-method row in tags.ts (line 64
`item.save` inside transaction).

## system.ts

| handler:line | zotero-call | doc-ref | verdict | note |
|---|---|---|---|---|
| system.ts:5 | `Zotero.version` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/zotero.js#L233 | ✓correct | Property set from `Services.appinfo.version` at zotero.js#L233 — stable global read, no signature to break. Narrow regex misses it (only one dot after `Zotero`). |
| system.ts:7 | `Zotero.Libraries.getAll()` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L154 | ✓correct | `this.getAll = function ()` (libraries.js#L154-165). Returns `Zotero.Library[]` sorted user-first then alphabetical. No args; handler calls it correctly. |
| system.ts:8 | `lib.id` / `lib.libraryType` / `lib.name` / `lib.editable` (instance props on Library) | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/library.js#L116 | ✓correct | Library instance exposes: `libraryID` getter (library.js#L116-119), `id` alias via `Zotero.defineProperty` (library.js#L121-124 — `get: function () { return this.libraryID; }`), `libraryType` (library.js#L126-129), `name` (library.js#L179-188 — computed/localized for user lib), `editable` (library.js#L212-220 — defined via an accessor loop over `['editable', 'filesEditable', 'storageVersion', 'archived', 'isAdmin']`). All four are public prototype properties. The `.id`-over-`.libraryID` choice is a defensible JSON-boundary convention (PRD's integer-ID rule) since Zotero itself defines `.id` as an alias. |
| system.ts:11 | `Zotero.Libraries.get(params.id)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L174 | ✓correct | `this.get = function (libraryID)` (libraries.js#L174-176). Returns `Zotero.Library` instance or `false` via `this._cache[libraryID] OR_ELSE false` — handler's `if (!lib)` guard is correct for the falsy-not-found contract. |
| system.ts:13 | `Zotero.Prefs.set("lastLibraryID", params.id)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L275 | ✗signature | `function set(pref, value, global)` at prefs.js#L275; `global` defaults to `false`, and when false the function prepends `ZOTERO_CONFIG.PREF_BRANCH` (= `"extensions.zotero."`) to the key (prefs.js#L277 — `pref = global ? pref : ZOTERO_CONFIG.PREF_BRANCH + pref`). This call therefore writes to `extensions.zotero.lastLibraryID` — **the handler is polluting Zotero's own pref branch**, not the plugin's branch. Correct form (matching settings.ts:38's convention): `Zotero.Prefs.set("extensions.zotero-bridge.lastLibraryID", params.id, true)` — pass the full absolute path with `global=true`. Note: `params.id` is a number, prefs accept number/string/bool at prefs.js#L281-302 (switch on `branch.getPrefType`), so the value type is fine; only the key namespace is wrong. |
| system.ts:17 | `Zotero.Libraries.userLibraryID` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L28 | ✓correct | Getter on `Zotero.Libraries` at libraries.js#L28-35 (defined via `Zotero.defineProperty(this, 'userLibraryID', { get: ... })`). Throws "Library data not yet loaded" if accessed before init — at RPC-call time libraries are always initialized, so this is safe. Integer return; matches PRD integer-ID rule. |
| system.ts:18 | `Zotero.Items.getAll(libraryID, false, false)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/items.js#L121 | ⚠cumbersome | `this.getAll = async function (libraryID, onlyTopLevel, includeDeleted, asIDs=false)` at items.js#L121-140. Positional args are correct. However for a **stats-only** count (handler only reads `items.length`), hydrating full `Zotero.Item` objects is wasteful on libraries of 10k+ items — with `asIDs` omitted the function ends with `return this.getAsync(ids)` (items.js#L139). Replace with `Zotero.Items.getAll(libraryID, false, false, true)` (fourth arg `asIDs=true`) to short-circuit to the raw integer-ID list (items.js#L136-138 `if (asIDs) return ids;`) — same `.length`, no object materialization. Non-blocking, but documented for the fix pass. |
| system.ts:19 | `Zotero.Collections.getByLibrary(libraryID, false)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/collections.js#L71 | ⚠cumbersome | `this.getByLibrary = function (libraryID, recursive, includeTrashed)` at collections.js#L71-73. Passing `recursive=false` returns only top-level collections; for a "library stats" display users expect **all** collections including nested. Replace with `Zotero.Collections.getByLibrary(libraryID, true)` (or document that `.collections` means "top-level collections only"). If the PRD picks "all", this is a shape divergence against `items` (which counts everything). Minor — confirm semantic intent in PRD. |
| system.ts:23 | `Zotero.ItemTypes.getAll()` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L119 | ✓correct | `this.getAll = this.getTypes = function ()` in the cached-types base class (cachedTypes.js#L119-125 — inherited by both `Zotero.ItemTypes` at cachedTypes.js#L341 and `Zotero.CreatorTypes` at cachedTypes.js#L218). Returns `this._typesArray` populated as `[{id, name}, ...]` — handler's `t.name` + `t.id` destructuring is correct. |
| system.ts:24 | `Zotero.ItemTypes.getLocalizedString(t.id)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L421 | ✓correct | `this.getLocalizedString = function (idOrName)` at cachedTypes.js#L421 (inside the `Zotero.ItemTypes` block at cachedTypes.js#L341+) accepts both int ID and string name. Handler passes int ID — correct. Returns localized label from `Zotero.Schema.globalSchemaLocale.itemTypes`, with custom-type and camelCase fallbacks. |
| system.ts:27 | `Zotero.ItemTypes.getID(params.itemType)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L98 | ✓correct | `this.getID = function (idOrName)` in the cached-types base class at cachedTypes.js#L98-116. Returns integer ID OR_ELSE `false` on unknown name (cachedTypes.js#L113 `return false;`). Handler's `if (!typeID)` guard matches the falsy-not-found contract. |
| system.ts:29 | `Zotero.ItemFields.getItemTypeFields(typeID)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/itemFields.js#L213 | ✓correct | `function getItemTypeFields(itemTypeID)` at itemFields.js#L213-229 (exposed on `this` at itemFields.js#L48). Returns `[..._itemTypeFields[itemTypeID]]` — a copy-array of numeric field IDs. Handler correctly types `fields.map((fid: number) => ...)` — no object wrapping needed. |
| system.ts:30 | `Zotero.ItemFields.getName(fid)` / `.getLocalizedString(fid)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/itemFields.js#L129 | ✓correct | `function getName(field)` at itemFields.js#L129-135 (exposed on `this` at itemFields.js#L44) returns the English programmatic name (e.g. `"title"`, `"publicationTitle"`) via `_fields[field]['name']`, OR_ELSE `false` when unknown. `this.getLocalizedString = function (field)` at itemFields.js#L143-167 returns the user-facing label; both accept ID or name. Handler passes numeric ID from `getItemTypeFields` — correct. |
| system.ts:33 | `Zotero.ItemTypes.getID(params.itemType)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L98 | ✓correct | Duplicate of line 27 — same contract, same guard, correct. |
| system.ts:35 | `Zotero.CreatorTypes.getTypesForItemType(typeID)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L280 | ✓correct | `this.getTypesForItemType = function (itemTypeID)` at cachedTypes.js#L280-285 (inside `Zotero.CreatorTypes` at cachedTypes.js#L218). Returns `_creatorTypesByItemType[itemTypeID]` (populated as `[{id, name}, ...]`), OR_ELSE an empty array. Handler's `t.name` + `t.id` destructuring is correct. The `getID` guard at line 33 prevents the unknown-itemType-id empty-array case. |
| system.ts:36 | `Zotero.CreatorTypes.getLocalizedString(t.id)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/cachedTypes.js#L310 | ✓correct | `this.getLocalizedString = function (idOrName)` at cachedTypes.js#L310-313 (inside the `Zotero.CreatorTypes` block). Resolves `this.getName(idOrName)` then returns `Zotero.Schema.globalSchemaLocale.creatorTypes[name]`. Handler passes int ID. Correct. |
| system.ts:38 | `Zotero.Sync.Runner.sync({ libraries: "all" })` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/sync/syncRunner.js#L116 | ✗signature | `this.sync = Zotero.serial(function (options = {}) { return this._sync(options); })` at syncRunner.js#L116-118. `options.libraries` is **documented as an integer array of library IDs** (syncRunner.js#L105-114 JSDoc `@param {Integer[]} [options.libraries] IDs of libraries to sync`). At syncRunner.js#L229-233 the value is fed through `options.libraries ? Array.from(options.libraries) : []` — `Array.from("all")` yields `["a","l","l"]` (three char elements), which then pass into `checkLibraries` as bogus library IDs. The `"all"` string is **not a documented sentinel**; the "sync every accessible library" behavior is triggered by **omitting** the key — at syncRunner.js#L418 `checkLibraries` computes `var syncAllLibraries = !libraries OR_ELSE !libraries.length;`. Correct form: `await Zotero.Sync.Runner.sync({})` — or, if the RPC needs to be explicit, `await Zotero.Sync.Runner.sync()`. Pass integer IDs only when scoping to specific libraries. |
| system.ts:41 | `Zotero.getActiveZoteroPane()` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/zotero.js#L93 | ⚠cumbersome | `this.getActiveZoteroPane = function () { var win = Services.wm.getMostRecentWindow("navigator:browser"); return win ? win.ZoteroPane : null; };` at zotero.js#L93-96. **UI-dependent:** returns `null` whenever no navigator:browser window is active (headless startup, minimized-to-tray, Zotero started but no window yet shown, backend RPC fired before window init). The handler's `if (!pane) return null;` guard correctly handles the null case, so the call is not unsafe — but `system.currentCollection` silently becomes `null` for any caller hitting the XPI before the user opens the main window. For a bootstrap-plugin backend this is "works on developer's machine, sometimes null in production". Alternatives: (a) iterate `Zotero.getZoteroPanes()` at zotero.js#L98-108 (enumerates every `navigator:browser` window that has a `.ZoteroPane`) and pick the first; (b) explicitly document that `system.currentCollection` requires the main window to be foregrounded. Narrow regex misses this call (only one dot). |
| system.ts:43 | `pane.getSelectedCollection()` (instance method on ZoteroPane) | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/zoteroPane.js | ?unverifiable | `ZoteroPane.getSelectedCollection` is a frontend (chrome/content/zotero/zoteroPane.js) method, not an xpcom backend module. Signature/return type is documented only by usage convention: returns a `Zotero.Collection` instance, or `null`/`false` if the selected row is a library/tag/saved-search rather than a collection. Handler's `if (!col) return null;` guard covers both falsy paths. Cannot verify against a specific `#L<n>` anchor from the xpcom layer; cite bare-file URL. Pattern is consistent with how Zotero's own reader/quickCopy code reads the pane (many call sites in `chrome/content/zotero/*.js`). Mark unverifiable-from-docs, not blocking. |

## settings.ts

| handler:line | zotero-call | doc-ref | verdict | note |
|---|---|---|---|---|
| settings.ts:22 | `Zotero.Prefs.get(PREF_PREFIX + params.key, true)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L233 | ✓correct | `function get(pref, global)` at prefs.js#L233. `global=true` bypasses the `extensions.zotero.` prefix (prefs.js#L235 `pref = global ? pref : ZOTERO_CONFIG.PREF_BRANCH + pref;`), so the full absolute path `extensions.zotero-bridge.<key>` is used — **this is the correct pattern** for plugin-owned prefs. Return is `undefined` for missing keys (handler applies `?? null` explicitly, matching PRD null-for-absent rule). |
| settings.ts:28 | `Zotero.Prefs.get(PREF_PREFIX + key, true) ?? null` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L233 | ✓correct | Same contract as line 22, iterating over `SETTINGS_KEYS`. Correct. |
| settings.ts:38 | `Zotero.Prefs.set(PREF_PREFIX + params.key, params.value, true)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L275 | ✓correct | `function set(pref, value, global)` at prefs.js#L275. `global=true` + full path = plugin-owned branch (prefs.js#L277 prepend guard). Accepts `string/number/bool` via the `switch (branch.getPrefType(pref))` block at prefs.js#L281-302, and creates new prefs in the appropriate type automatically for the unknown case (prefs.js#L289-302) — handler passes `params.value: any`, which is fine for valid Firefox pref types; invalid types (object/array) will throw from nsIPrefBranch at prefs.js#L302 `throw new Error("Invalid preference value ...")`, not silently corrupt. Matches the convention system.ts:13 violates. |
| settings.ts:45 | `Zotero.Prefs.get(PREF_PREFIX + key, true) ?? null` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L233 | ✓correct | Duplicate of line 28 (dead-code wrapper — `getAll()` duplicates the fall-through of `get()` with no `params.key`; consolidation is an internal-audit concern, not external-API). |
| settings.ts:54 | `Zotero.Prefs.set(PREF_PREFIX + key, value, true)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/prefs.js#L275 | ✓correct | Batch set, same contract as line 38. Correct. Note: whitelist filter on line 53 (`SETTINGS_KEYS.includes(key)`) silently drops unknown keys — single-key `set()` throws on unknown, `setAll()` does not. Shape divergence flagged here; internal-audit will catalog. |

## tags.ts

| handler:line | zotero-call | doc-ref | verdict | note |
|---|---|---|---|---|
| tags.ts:7 | `Zotero.Libraries.userLibraryID` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L28 | ✓correct | Integer getter at libraries.js#L28-35. Safe at RPC-call time. Note: `tags.list` / `tags.rename` / `tags.delete` all hard-default to the user library only — no `libraryID` param is accepted. For group-library tags these methods silently miss. Shape divergence (PRD should enforce `libraryID?` param family-wide); internal-audit will catalog. |
| tags.ts:8 | `Zotero.Tags.getAll(libraryID)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/tags.js#L145 | ✓correct | `this.getAll = async function (libraryID, types)` at tags.js#L145-147 (delegates to `this.getAllWithin({ libraryID, types })` at tags.js#L160). Returns `[{tag: "foo"}, {tag: "bar", type: 1}]` — API-JSON shape where `type` is absent for manual tags (type 0). Handler maps `{tag: t.tag, type: t.type}` — for manual tags `t.type` is `undefined`, which JSON.stringify drops. Correct but inconsistent with PRD null-for-absent rule; consider `type: t.type ?? 0` to explicit-zero manual tags. Minor. |
| tags.ts:16 | `Zotero.Items.getAsync(params.itemId)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/dataObjects.js#L152 | ✓correct | `Zotero.DataObjects.prototype.getAsync = async function (ids, options)` at dataObjects.js#L152. Scalar form is wrapped into a single-element array at dataObjects.js#L164-170 and returned via `return toReturn.length ? toReturn[0] : false;` at dataObjects.js#L207. Handler's `if (!item)` guard matches the falsy-not-found contract. Correct. |
| tags.ts:26 | `Zotero.Items.getAsync(params.itemId)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/dataObjects.js#L152 | ✓correct | Duplicate of line 16 in `tags.remove`. Correct. |
| tags.ts:36 | `Zotero.Libraries.userLibraryID` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L28 | ✓correct | Same as line 7 — user-lib-only limitation noted once, not re-flagged here. |
| tags.ts:37 | `Zotero.Tags.rename(libraryID, oldName, newName)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/tags.js#L279 | ✓correct | `this.rename = async function (libraryID, oldName, newName)` at tags.js#L279-360. Positional args match. Handler returns `{renamed: true, from, to}` without awaiting the rename throwing — if the old tag doesn't exist, `Zotero.Tags.rename` is a no-op (early-returns after the `oldName == newName` / missing-tag guards at tags.js#L285-290), so `renamed: true` may be misleading. Internal-audit shape concern; external-API call itself is correct. |
| tags.ts:42 | `Zotero.Libraries.userLibraryID` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/libraries.js#L28 | ✓correct | Same as line 7. |
| tags.ts:43 | `Zotero.Tags.getID(params.tag)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/tags.js#L83 | ✓correct | `this.getID = function (name)` at tags.js#L83-96. Returns integer tagID OR_ELSE `false` via `return id !== undefined ? id : false;` (tags.js#L95). Handler's `if (!tagID)` guard matches falsy-not-found contract. Correct. Note: tags.js#L87-89 now throws if a second argument is passed (`"no longer takes a second parameter"`) — handler passes one arg, so safe. |
| tags.ts:45 | `(Zotero.Tags as any).removeFromLibrary(libraryID, tagID)` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/tags.js#L370 | ✓correct | `this.removeFromLibrary = async function (libraryID, tagIDs, onProgress, types)` at tags.js#L370-463. **Public method** (no underscore prefix). Handler passes `(libraryID, tagID)` — `tagIDs` accepts Integer OR_ELSE Integer-array, scalar form valid. The `as any` cast is a **typings gap** (`typings/` has no `Zotero.Tags` ambient type), not an API-shape problem — Zotero exposes the method publicly. Fix direction: add ambient types, drop the cast. Not a signature bug. |
| tags.ts:54 | `Zotero.DB.executeTransaction(async () => { ... })` | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/db.js#L432 | ✓correct | `Zotero.DBConnection.prototype.executeTransaction = async function (func, options = {})` at db.js#L432. `func` must be async — db.js#L472-475 throws `"Zotero.DB.executeTransaction() no longer takes a generator function -- pass an async function instead"` for `GeneratorFunction`. Serializes concurrent transactions via the `while (this._transactionID)` wait-loop at db.js#L439-447 (with `waitTimeout` default 30s). Handler's `async () => {...}` wrapper is the right shape. Correct. |
| tags.ts:64 | `item.save()` inside `executeTransaction` (instance method on Item) | https://github.com/zotero/zotero/blob/main/chrome/content/zotero/xpcom/data/dataObject.js#L913 | ✓correct | `Zotero.DataObject.prototype.save = async function (options = {})` at dataObject.js#L913 emits `Zotero.logError("save() called on Zotero.<type> without a wrapping transaction -- use saveTx() instead")` at dataObject.js#L919-924 whenever `!env.options.tx && !Zotero.DB.inTransaction()`. Here the call is inside `executeTransaction`, so `Zotero.DB.inTransaction()` is true and the warning does not fire — this is exactly the sanctioned pattern. `saveTx` is defined at dataObject.js#L1012. By contrast `tags.add` (line 21) and `tags.remove` (line 31) call `item.saveTx()` outside any transaction, which is also correct. `batchUpdate` is the only path where `save()` is appropriate; swapping it back to `saveTx()` would nest transactions and trip the wait-loop at db.js#L439-447. |

## End of table.

Verdict counts (from final table data — recounted after commit):

- system.ts (19 rows): ✓correct = 13, ✗signature = 2, ⚠cumbersome = 3, ⚠deprecated = 0, ?unverifiable = 1
- settings.ts (5 rows): ✓correct = 5
- tags.ts (11 rows): ✓correct = 11

Total: 35 rows, ✓=29, ✗=2, ⚠=3, ?=1.

✗signature findings (2):

- `system.ts:13` — `Zotero.Prefs.set("lastLibraryID", params.id)` writes to
  `extensions.zotero.lastLibraryID` (Zotero's own branch), not the plugin
  branch. Fix: full path + `global=true`.
- `system.ts:38` — `Zotero.Sync.Runner.sync({libraries: "all"})` feeds
  `Array.from("all")` → `["a","l","l"]` into `checkLibraries`. Fix: drop
  the key or pass an integer array.

?unverifiable findings (1):

- `system.ts:43` — `pane.getSelectedCollection()` is a frontend ZoteroPane
  method; no xpcom `#L<n>` anchor. Behavior inferred from Zotero's own
  usage, guarded by the handler.
