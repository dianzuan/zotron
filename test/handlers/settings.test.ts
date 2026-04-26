import { expect } from "chai";
import sinon from "sinon";
import { installZotero, resetZotero } from "../fixtures/zotero-mock";

describe("settings handler", () => {
  afterEach(() => resetZotero());

  describe("setAll (fix #19)", () => {
    it("throws -32602 on unknown key", async () => {
      installZotero({
        Prefs: { set: sinon.stub() },
      });

      delete require.cache[require.resolve("../../src/handlers/settings")];
      const { settingsHandlers } = await import("../../src/handlers/settings");

      try {
        await settingsHandlers.setAll({ bogusKey: 1 });
        expect.fail("should have thrown");
      } catch (e: any) {
        expect(e.code).to.equal(-32602);
        expect(e.message).to.match(/bogusKey/);
      }
    });
  });

  describe("get requires key (fix #38)", () => {
    it("throws -32602 when key is missing", async () => {
      installZotero({
        Prefs: { get: sinon.stub() },
      });
      const { settingsHandlers } = await import("../../src/handlers/settings");
      try {
        await settingsHandlers.get({} as any);
        expect.fail("should have thrown");
      } catch (e: any) {
        expect(e.code).to.equal(-32602);
        expect(e.message).to.match(/key/i);
      }
    });

    it("returns single-pair {[key]: val} when key provided", async () => {
      installZotero({
        Prefs: { get: sinon.stub().withArgs("extensions.zotero-bridge.ocr.provider", true).returns("openai") },
      });
      const { settingsHandlers } = await import("../../src/handlers/settings");
      const result = await settingsHandlers.get({ key: "ocr.provider" });
      expect(result).to.deep.equal({ "ocr.provider": "openai" });
    });
  });

  describe("setAll Record echo (fix #39)", () => {
    it("returns {updated: Record<key,val>} echoing the applied pairs", async () => {
      installZotero({
        Prefs: { set: sinon.stub() },
      });
      const { settingsHandlers } = await import("../../src/handlers/settings");
      const result = await settingsHandlers.setAll({ "ocr.provider": "openai", "rag.topK": 5 });
      expect(result).to.have.property("updated");
      expect(result.updated).to.deep.equal({ "ocr.provider": "openai", "rag.topK": 5 });
    });
  });
});
