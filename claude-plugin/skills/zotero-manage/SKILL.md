---
name: zotero-manage
description: Add papers to Zotero, update metadata, organize collections and tags. Use when the user wants to save a paper (by DOI, URL, ISBN, or PDF file), create or organize collections, add/remove tags, or update paper information. Also triggers when user says "save this to Zotero", "add this paper", "organize my library", or "tag these papers".
argument-hint: "add DOI 10.1016/j.jfineco.2024.01.001"
---

# Zotero Manage

Add, update, and organize papers in the user's Zotero library.

> All commands here invoke the unified `zotero-bridge` CLI's generic `rpc` subcommand.
> Form: `zotero-bridge rpc <method.name> '<json-params>'`. This covers all 77 XPI methods.
> For typed/friendly subcommands like `zotero-bridge search quick "X" --limit 10`,
> see `zotero-bridge --help`.

## Adding papers

Choose the method based on what the user provides:

| User gives you | Method | Example |
|---------------|--------|---------|
| DOI | `items.addByDOI` | `'{"doi":"10.1016/j.jfineco.2024.01.001"}'` |
| URL (CNKI, journal site) | `items.addByURL` | `'{"url":"https://..."}'` |
| ISBN | `items.addByISBN` | `'{"isbn":"978-7-..."}'` |
| Local PDF file | `items.addFromFile` | `'{"path":"/path/to/paper.pdf"}'` |
| Manual entry | `items.create` | See below |

```bash
# By DOI (most reliable)
zotero-bridge rpc items.addByDOI '{"doi":"10.1016/j.jfineco.2024.01.001"}'

# Import local PDF
zotero-bridge rpc items.addFromFile '{"path":"/mnt/f/经济学期刊/paper.pdf","collection":5}'

# Manual creation
zotero-bridge rpc items.create '{"itemType":"journalArticle","fields":{"title":"论文标题","date":"2024","publicationTitle":"经济研究"},"creators":[{"firstName":"三","lastName":"张","creatorType":"author"}],"tags":["核心"]}'
```

## Updating metadata

```bash
zotero-bridge rpc items.update '{"id":ITEM_ID,"fields":{"title":"修正后的标题","date":"2024-06"}}'
```

## Collections (folders)

```bash
# Create
zotero-bridge rpc collections.create '{"name":"数字经济文献","parentId":null}'

# Add papers to collection
zotero-bridge rpc collections.addItems '{"id":COL_ID,"itemIds":[10,13,16]}'

# Remove from collection (doesn't delete paper)
zotero-bridge rpc collections.removeItems '{"id":COL_ID,"itemIds":[10]}'

# Rename
zotero-bridge rpc collections.rename '{"id":COL_ID,"name":"新名称"}'
```

## Tags

```bash
# Add tags
zotero-bridge rpc tags.add '{"itemId":ITEM_ID,"tags":["核心","待读"]}'

# Remove tags
zotero-bridge rpc tags.remove '{"itemId":ITEM_ID,"tags":["待读"]}'

# Batch: tag multiple papers at once
zotero-bridge rpc tags.batchUpdate '{"operations":[{"itemId":10,"add":["已读"],"remove":["待读"]},{"itemId":13,"add":["已读"]}]}'
```

## Duplicates

```bash
# Find duplicate papers
zotero-bridge rpc items.findDuplicates

# Merge duplicates (keeps first, merges others into it)
zotero-bridge rpc items.mergeDuplicates '{"ids":[10,25]}'
```

## After adding

Report to user: "已添加到 Zotero: {title} — {authors} ({year}) {journal}"
