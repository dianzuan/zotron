import { expect } from "chai";
import sinon from "sinon";
import { extractYear } from "../../src/utils/citation-key";

describe("extractYear", () => {
  afterEach(() => {
    delete (globalThis as any).Zotero;
  });

  it("extracts year from ISO-ish date via Zotero.Date.strToDate", () => {
    (globalThis as any).Zotero = {
      Date: {
        strToDate: sinon.stub().callsFake((s: string) => ({
          year: parseInt(s.slice(0, 4), 10),
        })),
      },
    };
    const item = { getField: sinon.stub().returns("2023-05-12") } as any;
    expect(extractYear(item)).to.equal(2023);
  });

  it("returns empty string when date field is missing", () => {
    (globalThis as any).Zotero = {
      Date: { strToDate: sinon.stub().returns({}) },
    };
    const item = { getField: sinon.stub().returns("") } as any;
    expect(extractYear(item)).to.equal("");
  });

  it("returns empty string when strToDate returns no year", () => {
    (globalThis as any).Zotero = {
      Date: { strToDate: sinon.stub().returns({ year: undefined }) },
    };
    const item = { getField: sinon.stub().returns("garbage") } as any;
    expect(extractYear(item)).to.equal("");
  });
});
