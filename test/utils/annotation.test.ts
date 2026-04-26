import { expect } from "chai";
import { validateAnnotationParams } from "../../src/utils/annotation";

describe("validateAnnotationParams", () => {
  it("accepts highlight with text", () => {
    const r = validateAnnotationParams({
      type: "highlight", text: "hi", color: "#ffd400", position: {},
    });
    expect(r.ok).to.equal(true);
  });

  it("accepts underline with text", () => {
    const r = validateAnnotationParams({
      type: "underline", text: "hi", color: "#ffd400", position: {},
    });
    expect(r.ok).to.equal(true);
  });

  it("accepts image without text", () => {
    const r = validateAnnotationParams({
      type: "image", color: "#ffd400", position: {},
    });
    expect(r.ok).to.equal(true);
  });

  it("rejects image WITH text — text only valid for highlight/underline", () => {
    const r = validateAnnotationParams({
      type: "image", text: "nope", color: "#ffd400", position: {},
    });
    expect(r.ok).to.equal(false);
    if (!r.ok) expect(r.message).to.match(/text.*highlight.*underline/i);
  });

  it("rejects 3-char hex color", () => {
    const r = validateAnnotationParams({
      type: "highlight", color: "#fff", position: {},
    });
    expect(r.ok).to.equal(false);
    if (!r.ok) expect(r.message).to.match(/color/i);
  });

  it("rejects color without #", () => {
    const r = validateAnnotationParams({
      type: "highlight", color: "ffd400", position: {},
    });
    expect(r.ok).to.equal(false);
  });

  it("rejects unknown type", () => {
    const r = validateAnnotationParams({
      type: "scribble" as any, color: "#ffd400", position: {},
    });
    expect(r.ok).to.equal(false);
    if (!r.ok) expect(r.message).to.match(/type/i);
  });

  it("accepts missing color (defaults applied later)", () => {
    const r = validateAnnotationParams({ type: "highlight", position: {} });
    expect(r.ok).to.equal(true);
  });
});
