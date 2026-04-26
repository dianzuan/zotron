import { expect } from "chai";
import { findUnknownKey } from "../../src/utils/settings-validate";

describe("findUnknownKey", () => {
  const known = new Set(["theme", "fontSize", "lastLibraryID"]);

  it("returns null when all keys are known", () => {
    expect(findUnknownKey({ theme: "dark", fontSize: 14 }, known)).to.equal(null);
  });

  it("returns the first unknown key", () => {
    expect(findUnknownKey({ theme: "dark", bogus: 1 }, known)).to.equal("bogus");
  });

  it("returns the first unknown key in iteration order", () => {
    expect(findUnknownKey({ a: 1, b: 2 }, known)).to.equal("a");
  });

  it("returns null for empty input", () => {
    expect(findUnknownKey({}, known)).to.equal(null);
  });
});
