import { expect } from "chai";
import { splitChineseName } from "../src/utils/chinese-name";

describe("splitChineseName", () => {
  it("splits single-char surname", () => {
    expect(splitChineseName("张三")).to.deep.equal({ lastName: "张", firstName: "三" });
  });
  it("splits compound surname 欧阳", () => {
    expect(splitChineseName("欧阳修")).to.deep.equal({ lastName: "欧阳", firstName: "修" });
  });
  it("splits compound surname 司马", () => {
    expect(splitChineseName("司马迁")).to.deep.equal({ lastName: "司马", firstName: "迁" });
  });
  it("splits minority name with dot", () => {
    expect(splitChineseName("阿卜杜拉·买买提")).to.deep.equal({ lastName: "阿卜杜拉", firstName: "买买提" });
  });
  it("handles single character name", () => {
    expect(splitChineseName("某")).to.deep.equal({ lastName: "某", firstName: "" });
  });
  it("returns full name for non-Chinese", () => {
    expect(splitChineseName("John Smith")).to.deep.equal({ lastName: "John Smith", firstName: "" });
  });
  it("splits compound surname 纳兰 (in extended table)", () => {
    expect(splitChineseName("纳兰性德")).to.deep.equal({ lastName: "纳兰", firstName: "性德" });
  });
  it("splits compound surname 夏侯 (only in source's extended list)", () => {
    expect(splitChineseName("夏侯惇")).to.deep.equal({ lastName: "夏侯", firstName: "惇" });
  });
  it("splits compound surname 诸葛 (only in source's extended list)", () => {
    expect(splitChineseName("诸葛亮")).to.deep.equal({ lastName: "诸葛", firstName: "亮" });
  });
  it("splits compound surname 司空 (only in source's extended list)", () => {
    expect(splitChineseName("司空图")).to.deep.equal({ lastName: "司空", firstName: "图" });
  });
});
