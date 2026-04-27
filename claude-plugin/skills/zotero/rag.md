# RAG (semantic search)

Find relevant paragraphs across papers in a Zotero collection using semantic search. Saves ~90% tokens vs. reading full papers. Requires the collection to be OCR'd and indexed first.

## Workflow

```bash
# 1. First, OCR the collection (if not done)
zotron-ocr --collection "数字经济"

# 2. Build the search index
zotron-rag index --collection "数字经济"

# 3. Search for relevant paragraphs
zotron-rag search --collection "数字经济" "就业效应的异质性分析方法"

# 4. Emit academic-zh retrieval hits via Zotero XPI JSON-RPC
zotron-rag hits "就业效应的异质性分析方法" --collection "数字经济" --zotero --output jsonl
```

## Search

```bash
zotron-rag search --collection "数字经济" "数字经济对劳动力市场的影响机制"
```

Returns JSON array of relevant paragraphs with score, paper title, authors, section name.

## Retrieval hits

```bash
zotron-rag hits "贸易中心性 金融风险 识别策略" \
  --collection "中国工业经济" \
  --zotero \
  --top-spans-per-item 3 \
  --output jsonl
```

`--zotero` calls the XPI `rag.searchHits` method, so callers do not need to know where item-attached `.zotron-chunks.jsonl` artifacts live. The output is one academic-zh retrieval hit per line with span provenance (`item_key`, `title`, `text`, `chunk_id`, `block_ids`, `section_heading`, `query`, `score`).

## Index management

```bash
zotron-rag status --collection "数字经济"
zotron-rag index --collection "数字经济" --rebuild
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
