import { expect } from "chai";
import sinon from "sinon";
import { installZotero, resetZotero, fakeItem, fakeCollection } from "./zotero-mock";

describe("zotero-mock harness", () => {
  afterEach(() => resetZotero());

  it("installs a stub onto globalThis.Zotero", () => {
    installZotero({ Items: { getAsync: sinon.stub().resolves("ok") } });
    expect(typeof globalThis.Zotero).to.equal("object");
    expect(globalThis.Zotero.Items.getAsync).to.be.a("function");
  });

  it("rejects double-install", () => {
    installZotero({});
    expect(() => installZotero({})).to.throw(/already installed/);
  });

  it("resetZotero removes the global", () => {
    installZotero({ Items: {} });
    resetZotero();
    expect(globalThis.Zotero).to.equal(undefined);
  });

  it("fakeItem produces a plausible Zotero.Item shape", () => {
    const item = fakeItem({ id: 7, fields: { title: "Hello" } });
    expect(item.id).to.equal(7);
    expect(item.getField("title")).to.equal("Hello");
    expect(item.getField("date")).to.equal("");
    expect(item.isAttachment()).to.equal(false);
  });

  it("fakeCollection produces a plausible Zotero.Collection shape", () => {
    const col = fakeCollection({ id: 11, name: "Bib" });
    expect(col.id).to.equal(11);
    expect(col.name).to.equal("Bib");
    expect(col.getChildCollections()).to.deep.equal([]);
  });
});
