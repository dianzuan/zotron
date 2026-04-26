import { expect } from "chai";
import { wrapTranslatorError } from "../../src/utils/translator-error";

describe("wrapTranslatorError", () => {
  it("wraps a translator-thrown Error into RpcError shape", () => {
    const original = new Error("CSL parse failed");
    const wrapped = wrapTranslatorError("cslJson", original);
    expect(wrapped).to.deep.equal({
      code: -32603,
      message: "Export failed (cslJson): CSL parse failed",
    });
  });

  it("includes the format name in the message", () => {
    const wrapped = wrapTranslatorError("bibtex", new Error("boom"));
    expect(wrapped.message).to.include("bibtex");
    expect(wrapped.message).to.include("boom");
  });

  it("handles non-Error throws by stringifying", () => {
    const wrapped = wrapTranslatorError("ris", "raw string failure");
    expect(wrapped.code).to.equal(-32603);
    expect(wrapped.message).to.include("ris");
    expect(wrapped.message).to.include("raw string failure");
  });
});
