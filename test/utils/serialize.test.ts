import { expect } from "chai";
import sinon from "sinon";
import { installZotero, resetZotero } from "../fixtures/zotero-mock";

describe("serializeItem", () => {
  beforeEach(() => {
    delete require.cache[require.resolve("../../src/utils/serialize")];
  });
  afterEach(() => resetZotero());

  it("includes note body via item.getNote() for note items", async () => {
    installZotero({
      ItemFields: {
        getItemTypeFields: () => [],
        getName: () => "",
      },
      CreatorTypes: { getName: () => "author" },
    });
    const noteItem: any = {
      id: 100, key: "NOTE100", itemType: "note", itemTypeID: 1,
      dateAdded: "2026-01-01", dateModified: "2026-01-01", deleted: false,
      getField: () => "",
      isNote: () => true,
      isAttachment: () => false,
      getNote: () => "<p>Hello note body</p>",
      getCreators: () => [],
      getTags: () => [],
      getCollections: () => [],
      getRelations: () => ({}),
    };
    const { serializeItem } = await import("../../src/utils/serialize");
    const out = serializeItem(noteItem);
    expect(out.note).to.equal("<p>Hello note body</p>");
    expect(out.id).to.equal(100);
    expect(out.itemType).to.equal("note");
  });

  it("does NOT include `note` field for regular items", async () => {
    installZotero({
      ItemFields: {
        getItemTypeFields: () => [],
        getName: () => "",
      },
      CreatorTypes: { getName: () => "author" },
    });
    const articleItem: any = {
      id: 200, key: "ART200", itemType: "journalArticle", itemTypeID: 2,
      dateAdded: "2026-01-01", dateModified: "2026-01-01", deleted: false,
      getField: (n: string) => n === "title" ? "An Article" : "",
      isNote: () => false,
      isAttachment: () => false,
      getNote: () => { throw new Error("should not be called for non-note"); },
      getCreators: () => [],
      getTags: () => [],
      getCollections: () => [],
      getRelations: () => ({}),
    };
    const { serializeItem } = await import("../../src/utils/serialize");
    const out = serializeItem(articleItem);
    expect(out).to.not.have.property("note");
    expect(out.title).to.equal("An Article");
  });
});
