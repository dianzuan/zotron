import { expect } from "chai";
import { rpcError, INVALID_PARAMS, INTERNAL_ERROR } from "../../src/utils/errors";

describe("rpcError", () => {
  it("builds an invalid-params (-32602) error", () => {
    const err = rpcError(INVALID_PARAMS, "Item not found: 42");
    expect(err).to.deep.equal({ code: -32602, message: "Item not found: 42" });
  });

  it("builds an internal (-32603) error", () => {
    const err = rpcError(INTERNAL_ERROR, "Translator failed");
    expect(err).to.deep.equal({ code: -32603, message: "Translator failed" });
  });

  it("INVALID_PARAMS constant equals -32602", () => {
    expect(INVALID_PARAMS).to.equal(-32602);
  });

  it("INTERNAL_ERROR constant equals -32603", () => {
    expect(INTERNAL_ERROR).to.equal(-32603);
  });
});
