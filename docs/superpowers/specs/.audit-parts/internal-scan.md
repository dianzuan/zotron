# Internal consistency scan

Target: all 77 RPC methods across 9 handlers. Row format:
`| handler.method | return-shape | params | error-pattern | siblings-diverge |`.

- `return-shape`: top-level keys only, sorted. Object literals → `{key1, key2}`. Arrays → `[<element-shape>]`. Primitives → `int`/`str`/`bool`.
  - `(serializeItem)` = the full item shape produced by `src/utils/serialize.ts::serializeItem` — always `{collections, creators, dateAdded, dateModified, deleted, id, itemType, key, relations, tags, title, ...typedFields}`.
  - `(serializeCollection)` = `{childCollections, id, itemCount, key, name, parentID}`.
  - `multi: A OR_ELSE B` = method has multiple return paths with different shapes.
- `params`: destructured keys from the TS type signature. Optional marked with `?`. `none` = no params object.
- `error-pattern`: `throw {code,msg}` = `throw { code: -32602, message: ... }`; `throw Error` = `throw new Error(...)`; `silent-false` = returns sentinel without throwing; `no-error-path` = no `throw` in body.
- `siblings-diverge`: `yes` / `no` — compared to other rows in the same `handler.*` family. Judged on shape-family (ack / item / item-list / paginated / custom-record / etc.), not on leaf-key identity when different-kinds-of-data justify different keys.

**Pipe-safety legend** — none of the cells below embed a literal `|`, so no escaping is used. If a future edit needs to embed one, use `OR_ELSE` (already used for multi-return rows) or `&#124;`.

## Methods by family

### items.* (18 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| items.get | (serializeItem) | {id} | throw {code,msg} | no |
| items.create | (serializeItem) | {itemType, fields?, creators?, tags?, collections?} | no-error-path | no |
| items.update | (serializeItem) | {id, fields?, creators?, tags?} | throw {code,msg} | no |
| items.delete | {deleted, id} | {id} | throw {code,msg} | no |
| items.trash | {id, trashed} | {id} | throw {code,msg} | no |
| items.restore | {id, restored} | {id} | throw {code,msg} | no |
| items.getTrash | {items, limit, offset, total} | {limit?, offset?} | no-error-path | yes |
| items.batchTrash | {trashed} | {ids} | no-error-path | yes |
| items.getRecent | [(serializeItem)] | {limit?, type?} | no-error-path | yes |
| items.addByDOI | [(serializeItem)] | {doi, collection?} | throw {code,msg} | no |
| items.addByURL | [(serializeItem)] | {url, collection?} | throw {code,msg} | no |
| items.addByISBN | [(serializeItem)] | {isbn, collection?} | throw {code,msg} | no |
| items.addFromFile | [(serializeItem)] | {path, collection?} | throw {code,msg} | no |
| items.findDuplicates | {groups, totalGroups} | none | no-error-path | yes |
| items.mergeDuplicates | (serializeItem) | {ids} | throw {code,msg} | no |
| items.getRelated | [(serializeItem)] | {id} | throw {code,msg} | no |
| items.addRelated | {added} | {id, relatedId} | throw {code,msg} | yes |
| items.removeRelated | {removed} | {id, relatedId} | throw {code,msg} | yes |

### collections.* (12 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| collections.list | [(serializeCollection)] | none | no-error-path | no |
| collections.get | (serializeCollection) | {id} | throw {code,msg} | no |
| collections.getItems | {items, total} | {id, limit?, offset?} | throw {code,msg} | yes |
| collections.getSubcollections | [(serializeCollection)] | {id} | throw {code,msg} | no |
| collections.tree | [{children, ...serializeCollection}] | none | no-error-path | yes |
| collections.create | (serializeCollection) | {name, parentId?} | no-error-path | no |
| collections.rename | (serializeCollection) | {id, name} | throw {code,msg} | no |
| collections.delete | {deleted, id} | {id} | throw {code,msg} | no |
| collections.move | (serializeCollection) | {id, newParentId} | throw {code,msg} | no |
| collections.addItems | {added, collectionId} | {id, itemIds} | throw {code,msg} | no |
| collections.removeItems | {collectionId, removed} | {id, itemIds} | no-error-path | yes |
| collections.stats | {attachments, id, items, name, notes, subcollections} | {id} | throw {code,msg} | yes |

### attachments.* (7 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| attachments.list | [{contentType, id, key, linkMode, path, title}] | {parentId} | throw {code,msg} | yes |
| attachments.getFulltext | {content, id, indexedChars, totalChars} | {id} | throw {code,msg} | yes |
| attachments.getPDFOutline | {id, outline} | {id} | throw {code,msg} | yes |
| attachments.add | (serializeItem) | {parentId, path, title?} | throw {code,msg} | no |
| attachments.addByURL | (serializeItem) | {parentId, url, title?} | throw {code,msg} | no |
| attachments.getPath | {id, path} | {id} | throw {code,msg} | yes |
| attachments.findPDF | multi: {found:false} OR_ELSE {attachment, found:true} | {parentId} | throw {code,msg} | yes |

### notes.* (6 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| notes.get | [{content, dateAdded, dateModified, id, key, tags}] | {parentId} | throw {code,msg} | yes |
| notes.create | {id, key} | {parentId, content, tags?} | throw {code,msg} | no |
| notes.update | {id, updated} | {id, content} | throw {code,msg} | yes |
| notes.search | [{content, dateModified, id, parentId}] | {query, limit?} | no-error-path | yes |
| notes.getAnnotations | [{color, comment, dateAdded, id, pageLabel, position, tags, text, type}] | {parentId} | throw {code,msg} | yes |
| notes.createAnnotation | {id} | {parentId, type, text?, comment?, color?, position} | throw {code,msg} | yes |

### search.* (8 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| search.quick | {items, query, total} | {query, limit?} | no-error-path | no |
| search.advanced | {items, total} | {conditions} | no-error-path | yes |
| search.fulltext | {items, query, total} | {query, limit?} | no-error-path | no |
| search.byTag | {items, tag, total} | {tag, limit?} | no-error-path | no |
| search.byIdentifier | {items, total} | {doi?, isbn?, issn?, pmid?} | no-error-path | yes |
| search.savedSearches | [{conditions, id, key, name}] | none | no-error-path | yes |
| search.createSavedSearch | {id, name} | {name, conditions} | no-error-path | yes |
| search.deleteSavedSearch | {deleted, id} | {id} | throw {code,msg} | yes |

### tags.* (6 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| tags.list | [{tag, type}] | {limit?} | no-error-path | yes |
| tags.add | {added, itemId} | {itemId, tags} | throw {code,msg} | no |
| tags.remove | {itemId, removed} | {itemId, tags} | throw {code,msg} | no |
| tags.rename | {from, renamed, to} | {oldName, newName} | no-error-path | yes |
| tags.delete | {deleted, tag} | {tag} | throw {code,msg} | yes |
| tags.batchUpdate | {added, removed} | {operations} | no-error-path | yes |

### export.* (6 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| export.bibtex | {content, count, format} | {ids} | throw Error | no |
| export.cslJson | {content, count, format} | {ids} | throw Error | no |
| export.ris | {content, count, format} | {ids} | throw Error | no |
| export.csv | {content, count, format} | {ids, fields?} | throw Error | no |
| export.bibliography | {count, format, html, style, text} | {ids, style?} | throw {code,msg} | yes |
| export.citationKey | {citationKey, id} | {id} | throw {code,msg} | yes |

### settings.* (4 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| settings.get | multi: {[key]:val} OR_ELSE Record&lt;key,val&gt; | {key?} | no-error-path | yes |
| settings.set | {key, value} | {key, value} | throw {code,msg} | yes |
| settings.getAll | Record&lt;key,val&gt; | none | no-error-path | no |
| settings.setAll | {updated} | Record&lt;key,val&gt; | no-error-path | yes |

### system.* (10 methods)

| handler.method | return-shape | params | error-pattern | siblings-diverge |
|---|---|---|---|---|
| system.ping | {status, timestamp} | none | no-error-path | no |
| system.version | {methods, plugin, zotero} | none | no-error-path | no |
| system.libraries | [{editable, id, name, type}] | none | no-error-path | no |
| system.switchLibrary | {id, name} | {id} | throw {code,msg} | no |
| system.libraryStats | {collections, items, libraryID} | {id?} | no-error-path | yes |
| system.itemTypes | [{itemType, itemTypeID, localized}] | none | no-error-path | no |
| system.itemFields | [{field, fieldID, localized}] | {itemType} | throw {code,msg} | no |
| system.creatorTypes | [{creatorType, creatorTypeID, localized}] | {itemType} | throw {code,msg} | no |
| system.sync | {status} | none | no-error-path | no |
| system.currentCollection | multi: null OR_ELSE {id, key, libraryID, name} | none | silent-false | yes |

## Divergence summary

Baseline: a family is **uniform** when its methods cluster into a small set of principled shape-families (e.g. "single item", "item list", "ack with entity id", "paginated list") and every method obeys its cluster's conventions consistently. An outlier is a method that either uses a keystyle inconsistent with its peers OR sits in a one-off shape that doesn't fit a principled cluster.

Totals: **0 families uniform**, **9 families divergent**, **36 outlier-rows** (`siblings-diverge=yes`). The `system.*` divergence is mild (2 rows, both with domain-justified keys); attachments.*, notes.*, and items.* are the heaviest and will dominate Task 7 (PRD) and Task 8 (fix catalog) effort.

### items.*: diverges — getTrash, batchTrash, getRecent, findDuplicates, addRelated, removeRelated

- `items.getTrash` returns the only paginated envelope in the family (`{items, total, offset, limit}` echoing the input cursor). Siblings that also return item-lists (`getRecent`, `addByDOI`, `addByURL`, `addByISBN`, `addFromFile`, `getRelated`) return a bare `[(serializeItem)]` with no envelope at all. Decide once: always-enveloped or always-bare, pick a side.
- `items.batchTrash` returns `{trashed: count}` (no id list, no per-id success map) while the scalar sibling `items.trash` returns `{trashed: true, id}`. Same verb, incompatible shapes.
- `items.getRecent` is a bare item-list where callers might reasonably expect `{items, total}` like `collections.getItems` or `items.getTrash`.
- `items.findDuplicates` returns `{groups, totalGroups}` — not an item-list shape at all, so it doesn't cluster with anything else; this is fine domain-wise but worth calling out.
- `items.addRelated` / `removeRelated` return `{added: true}` / `{removed: true}` with no id echo, while their scalar cousins (`delete` / `trash` / `restore`) all echo `id`. Paired add/remove verbs consistent with each other, but inconsistent with the wider items.* ack convention.

### collections.*: diverges — getItems, tree, removeItems, stats

- `collections.getItems` returns `{items, total}` with NO `offset`/`limit` echo. `items.getTrash` (same intent — paginate a list) echoes both. Pagination-envelope contract diverges between the two most-similar methods in the whole API.
- `collections.tree` returns a nested-children structure that's unique in the family. Justified by domain but worth flagging for PRD — consumers need to know tree is a distinct shape, not just "list with extra fields".
- `collections.removeItems` has no error path while its mirror `addItems` throws `{code,msg}` for missing collection id. Identical safety surface, different enforcement.
- `collections.stats` has per-family-unique keys (`attachments`, `notes`, `subcollections`). Domain-justified but sits outside any cluster.

### attachments.*: diverges — list, getFulltext, getPDFOutline, getPath, findPDF

Attachments is the most fragmented family. Every read method has a bespoke shape:
- `attachments.list` returns a custom record `{id, key, title, contentType, path, linkMode}` instead of `[(serializeItem)]`, even though attachments ARE items.
- `attachments.getFulltext`, `getPDFOutline`, `getPath` each have their own `{id, <one-or-two-payload-keys>}` shape.
- `attachments.findPDF` is the only method in the whole API with a boolean-discriminated multi-return: `{found:false}` or `{found:true, attachment}`. Encourages callers to branch on a sentinel field rather than rely on thrown errors.
- Only `add`/`addByURL` use `(serializeItem)` like the rest of the API does for "I just created a thing".

### notes.*: diverges — get, update, search, getAnnotations, createAnnotation

- `notes.get` returns a custom `[{id, key, content, dateAdded, dateModified, tags}]` rather than `[(serializeItem)]`. Notes are items; this is lossy for no reason.
- `notes.search` returns ANOTHER custom shape `[{id, parentId, content(truncated to 500 chars), dateModified}]`. Two read methods in the same family, two different custom shapes, neither is `[(serializeItem)]`.
- `notes.update` returns `{id, updated: true}` while `notes.create` returns `{id, key}` (no ack flag, no symmetry with update).
- `notes.getAnnotations` returns a full custom annotation record, while `notes.createAnnotation` returns just `{id}` — no key, no symmetry with `notes.create`.

### search.*: diverges — advanced, byIdentifier, savedSearches, createSavedSearch, deleteSavedSearch

- `search.quick` / `fulltext` / `byTag` echo their primary input (`query` or `tag`) into the envelope. `search.advanced` / `byIdentifier` do not. Pick one — either always echo the search spec or never echo it.
- `search.savedSearches` / `createSavedSearch` / `deleteSavedSearch` are a separate CRUD subfamily on a different entity; their presence in the same handler creates apparent divergence. `createSavedSearch` returns `{id, name}` with no `key`, unlike `savedSearches` list entries which include `key`.

### tags.*: diverges — list, rename, delete, batchUpdate

- `tags.rename` uses unique `{from, to, renamed}` shape — no sibling returns `{from, to}`. Consistent with rename semantics but sits outside any ack cluster.
- `tags.delete` takes `{tag}` (the name) instead of `{id}`, and returns `{deleted, tag}` instead of `{deleted, id}` used by `items.delete` / `collections.delete` / `search.deleteSavedSearch`. Tags don't have numeric ids exposed to callers, which is a real constraint — but worth documenting as PRD exception.
- `tags.batchUpdate` returns `{added, removed}` with no `itemId` since it spans multiple items; its scalar mirrors (`tags.add` / `tags.remove`) return `{added|removed, itemId}`. Justified but non-uniform.
- `tags.list` returns a custom `[{tag, type}]` shape. Tags are not items so this is fine, but flagged for completeness.

### export.*: diverges — bibliography, citationKey

- `export.bibliography` returns `{format, style, html, text, count}` while `export.bibtex` / `cslJson` / `ris` / `csv` return `{format, content, count}`. PRD baseline decision: retain as exception because bibliography has two output variants (HTML + plain text). Flagged here for completeness.
- `export.citationKey` returns `{id, citationKey}` — a per-item metadata lookup, not a bibliographic export. Different domain entirely; sitting in `export.*` makes it look divergent but it's really just mis-filed. Consider relocating to `items.citationKey`.
- Error pattern differs: the four translator-based exports wrap Zotero failures as `throw new Error("Export failed")` (yields JSON-RPC -32603), while `bibliography` and `citationKey` use `throw {code:-32602,...}`. The former should migrate to the structured pattern for consistency.

### settings.*: diverges — get, set, setAll

- `settings.get` is the only method in the entire audit with a multi-shape return based on whether `key?` is provided: single-pair `{[key]: val}` vs full `Record<key,val>`. `getAll` exists for the no-key case, which makes `get` without a key redundant AND shape-divergent.
- `settings.set` returns `{key, value}` (echo of input); `settings.setAll` returns `{updated: [keys]}` (a list). Scalar-vs-batch asymmetry similar to `items.trash` vs `items.batchTrash`.

### system.*: diverges — libraryStats, currentCollection

- `system.libraryStats` uses the key `libraryID` (not `id`), inconsistent with `system.switchLibrary` which returns `{id, name}` for the same concept. Pick one casing.
- `system.currentCollection` is the only method in the whole API that returns `null` as a valid success value (no active pane / no selected collection). Every other "not found" surface throws `{code:-32602,...}`. This is the one `silent-false` error pattern in the audit.
- Otherwise system.* is heterogeneous-by-design — `ping`, `version`, `sync`, `libraries`, `itemTypes`, `itemFields`, `creatorTypes` serve genuinely different-kind-of-data requests, so pure-shape uniformity isn't the right bar here.

### Uniform families

(None — every family has at least one outlier flagged above.)
