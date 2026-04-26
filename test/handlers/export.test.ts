import { expect } from "chai";
import sinon from "sinon";
import { installZotero, resetZotero } from "../fixtures/zotero-mock";

describe("export handler", () => {
  beforeEach(() => {
    delete require.cache[require.resolve("../../src/handlers/export")];
  });

  afterEach(() => resetZotero());

  describe("bibtex (fix #14)", () => {
    it("throws structured {code:-32603, message} when translator fails", async () => {
      // Zotero.Translate.Export constructor — the handler calls:
      //   const translate = new Zotero.Translate.Export();
      //   translate.setItems(items);
      //   translate.setTranslator(translatorID);
      //   translate.setHandler("done", cb);
      //   translate.translate();
      // We simulate a failure by firing the "done" handler with status=false.

      const handlers: Record<string, Function> = {};
      const FakeExport = function () {};
      FakeExport.prototype.setItems = sinon.stub();
      FakeExport.prototype.setTranslator = sinon.stub();
      FakeExport.prototype.setHandler = function (event: string, cb: Function) {
        handlers[event] = cb;
      };
      FakeExport.prototype.translate = function () {
        // Fire the done callback synchronously with failure status
        handlers["done"]?.(null, false);
      };

      installZotero({
        Items: { getAsync: sinon.stub().resolves([{ id: 1 }]) },
        Translate: { Export: FakeExport },
      });

      const { exportHandlers } = await import("../../src/handlers/export");

      try {
        await exportHandlers.bibtex({ ids: [1] });
        expect.fail("should have thrown");
      } catch (e: any) {
        expect(e.code).to.equal(-32603);
        expect(e.message).to.include("bibtex");
        expect(e.message).to.include("translator returned failure status");
      }
    });
  });
});
