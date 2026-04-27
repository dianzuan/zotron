// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
// zotron/src/handlers/rag.ts
import { registerHandlers } from "../server";
import { rpcError, INVALID_PARAMS } from "../utils/errors";

const CHUNKS_SUFFIX = ".zotron-chunks.jsonl";

type SearchHitsParams = {
  query: string;
  collection?: string | number;
  collectionId?: number;
  itemIds?: number[];
  limit?: number;
  top_spans_per_item?: number;
  include_fulltext_spans?: boolean;
};

type RetrievalHit = {
  item_key: string;
  title: string;
  text: string;
  authors?: string[];
  year?: number;
  venue?: string;
  doi?: string;
  zotero_uri: string;
  section_heading?: string;
  chunk_id: string;
  block_ids?: string[];
  query: string;
  score: number;
};

function parseJsonl(text: string, source: string): Record<string, any>[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (err: any) {
        throw rpcError(INVALID_PARAMS, `Invalid JSONL in ${source} at line ${index + 1}: ${err.message}`);
      }
    });
}

function queryTerms(query: string): string[] {
  const terms = query
    .toLowerCase()
    .split(/[\s,;，；、]+/)
    .map((term) => term.trim())
    .filter(Boolean);
  return terms.length > 0 ? Array.from(new Set(terms)) : [query.toLowerCase()];
}

function lexicalScore(text: string, query: string): number {
  const haystack = text.toLowerCase();
  const needle = query.trim().toLowerCase();
  if (!haystack || !needle) return 0;

  let score = haystack.includes(needle) ? 1 : 0;
  for (const term of queryTerms(query)) {
    if (term && haystack.includes(term)) score += 1;
  }
  return score;
}

function creatorName(creator: any): string {
  if (creator.name) return creator.name;
  if (
    creator.firstName
    && creator.lastName
    && /[\u3400-\u9fff]/.test(`${creator.firstName}${creator.lastName}`)
  ) {
    return `${creator.lastName}${creator.firstName}`;
  }
  return [creator.firstName, creator.lastName].filter(Boolean).join(" ").trim();
}

function itemAuthors(item: any): string[] {
  return (item.getCreators?.() || [])
    .map(creatorName)
    .filter((name: string) => name.length > 0);
}

function itemYear(item: any): number | undefined {
  const date = String(item.getField?.("date") || "");
  const match = date.match(/\b(18|19|20|21)\d{2}\b/);
  return match ? Number(match[0]) : undefined;
}

function itemVenue(item: any): string {
  return String(
    item.getField?.("publicationTitle")
    || item.getField?.("journalAbbreviation")
    || item.getField?.("conferenceName")
    || item.getField?.("publisher")
    || "",
  );
}

async function resolveCollectionItems(params: SearchHitsParams): Promise<any[]> {
  if (params.itemIds?.length) {
    const items = await Zotero.Items.getAsync(params.itemIds);
    return (Array.isArray(items) ? items : [items]).filter(Boolean);
  }

  const collectionRef = params.collectionId ?? params.collection;
  if (collectionRef === undefined || collectionRef === null || collectionRef === "") {
    throw rpcError(INVALID_PARAMS, "rag.searchHits requires collection, collectionId, or itemIds");
  }

  let collection: any = null;
  if (typeof collectionRef === "number") {
    collection = await Zotero.Collections.getAsync(collectionRef);
  } else {
    const collections = Zotero.Collections.getByLibrary(Zotero.Libraries.userLibraryID, true);
    collection = collections.find((col: any) => col.name === collectionRef);
  }
  if (!collection) {
    throw rpcError(INVALID_PARAMS, `Collection not found: ${collectionRef}`);
  }
  return (collection.getChildItems(false) || []).filter((item: any) => !item.isNote?.() && !item.isAttachment?.());
}

async function readChunkArtifacts(item: any): Promise<Record<string, any>[]> {
  const rows: Record<string, any>[] = [];
  const attachmentIds = item.getAttachments?.() || [];
  for (const attachmentId of attachmentIds) {
    const attachment = await Zotero.Items.getAsync(attachmentId);
    if (!attachment?.isAttachment?.()) continue;
    const title = String(attachment.getField?.("title") || "");
    if (!title.endsWith(CHUNKS_SUFFIX)) continue;
    const path = await attachment.getFilePathAsync?.();
    if (!path) continue;
    const content = String((await Zotero.File.getContentsAsync(path)) || "");
    rows.push(...parseJsonl(content, title));
  }
  return rows;
}

function hitFromChunk(item: any, chunk: Record<string, any>, query: string, score: number): RetrievalHit {
  const itemKey = String(chunk.item_key || item.key || item.id);
  const title = String(chunk.title || item.getField?.("title") || "");
  const chunkId = String(chunk.chunk_id || `${itemKey}:c${chunk.chunk_index ?? 0}`);
  const hit: RetrievalHit = {
    item_key: itemKey,
    title,
    text: String(chunk.text || ""),
    authors: Array.isArray(chunk.authors) ? chunk.authors : itemAuthors(item),
    zotero_uri: String(chunk.zotero_uri || `zotero://select/library/items/${itemKey}`),
    section_heading: String(chunk.section_heading || chunk.section || ""),
    chunk_id: chunkId,
    query,
    score,
  };
  const year = Number(chunk.year) || itemYear(item);
  if (year) hit.year = year;
  const venue = String(chunk.venue || itemVenue(item));
  if (venue) hit.venue = venue;
  const doi = String(chunk.doi || item.getField?.("DOI") || "");
  if (doi) hit.doi = doi;
  if (Array.isArray(chunk.block_ids)) hit.block_ids = chunk.block_ids;
  return hit;
}

async function searchChunkArtifacts(params: SearchHitsParams): Promise<RetrievalHit[]> {
  const query = params.query?.trim();
  if (!query) throw rpcError(INVALID_PARAMS, "rag.searchHits requires query");

  const limit = Math.max(1, params.limit ?? 50);
  const topSpansPerItem = Math.max(1, params.top_spans_per_item ?? 3);
  const items = await resolveCollectionItems(params);
  const scored: RetrievalHit[] = [];

  for (const item of items) {
    for (const chunk of await readChunkArtifacts(item)) {
      const text = String(chunk.text || "");
      const score = lexicalScore(text, query);
      if (score <= 0) continue;
      scored.push(hitFromChunk(item, chunk, query, score));
    }
  }

  scored.sort((a, b) => b.score - a.score || a.chunk_id.localeCompare(b.chunk_id));
  const perItem = new Map<string, number>();
  const hits: RetrievalHit[] = [];
  for (const hit of scored) {
    const seen = perItem.get(hit.item_key) || 0;
    if (seen >= topSpansPerItem) continue;
    perItem.set(hit.item_key, seen + 1);
    hits.push(hit);
    if (hits.length >= limit) break;
  }
  return hits;
}

export const ragHandlers = {
  async searchHits(params: SearchHitsParams) {
    const hits = await searchChunkArtifacts(params);
    return { hits, total: hits.length };
  },

  async searchCards(params: SearchHitsParams) {
    const hits = await searchChunkArtifacts(params);
    return { hits, total: hits.length };
  },
};

registerHandlers("rag", ragHandlers);
