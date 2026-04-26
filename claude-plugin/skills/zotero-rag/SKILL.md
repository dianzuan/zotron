---
name: zotero-rag
description: Semantic search inside Zotero papers to find relevant paragraphs. Use when the user needs literature review support, asks "前人研究怎么说", "找相关段落", "语义搜索", "文献综述", "哪篇论文提到了X", or wants to find specific content across papers without reading them all. This saves ~90% tokens compared to reading full papers. Requires a collection to be OCR'd and indexed first.
argument-hint: "search --collection 数字经济 \"就业效应的异质性\""
---

# Zotero RAG Search

Find relevant paragraphs across papers in a Zotero collection using semantic search.

## Workflow

```bash
# 1. First, OCR the collection (if not done)
zotero-ocr --collection "数字经济"

# 2. Build the search index
zotero-rag index --collection "数字经济"

# 3. Search for relevant paragraphs
zotero-rag search --collection "数字经济" "就业效应的异质性分析方法"
```

## Search

```bash
zotero-rag search --collection "数字经济" "数字经济对劳动力市场的影响机制"
```

Returns JSON array of relevant paragraphs with score, paper title, authors, section name.

## Index management

```bash
zotero-rag status --collection "数字经济"
zotero-rag index --collection "数字经济" --rebuild
```

## Why RAG saves tokens

Without RAG: read 5 full papers → ~50K tokens per query
With RAG: get 10 relevant paragraphs → ~5K tokens per query

## Configuration

Default: Ollama with Qwen3-Embedding locally.
```bash
export EMBEDDING_PROVIDER=ollama
export EMBEDDING_MODEL=qwen3-embedding:4b
```
Cloud alternatives: zhipu, doubao, openai, deepseek (need API key).
