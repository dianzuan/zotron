import { expect } from "chai";
import { installZotero, resetZotero } from "./fixtures/zotero-mock";

describe("processRequest fuzzy suggestions", () => {
  beforeEach(() => {
    // Clear all handler and server caches to get fresh handlers map
    for (const key of Object.keys(require.cache)) {
      if (key.includes("/src/")) delete require.cache[key];
    }
  });
  afterEach(() => resetZotero());

  it("suggests closest method when calling unknown method", async () => {
    installZotero({});
    // Import server first, then notes handler registers with the same handlers map
    const server = await import("../src/server");
    await import("../src/handlers/notes");

    // Verify notes methods are registered
    const methods = server.getRegisteredMethods();
    expect(methods).to.include("notes.create");

    const Handler = server.createEndpointHandler();
    const h = new (Handler as any)();
    const [status, , body] = await h.init({
      jsonrpc: "2.0", id: 1, method: "notes.creates", params: {},
    });
    const parsed = JSON.parse(body);
    expect(parsed.error.code).to.equal(-32601);
    expect(parsed.error.message).to.contain("Did you mean");
    expect(parsed.error.message).to.contain("notes.create");
  });

  it("does NOT suggest when distance is too large", async () => {
    installZotero({});
    const server = await import("../src/server");
    await import("../src/handlers/notes");

    const Handler = server.createEndpointHandler();
    const h = new (Handler as any)();
    const [status, , body] = await h.init({
      jsonrpc: "2.0", id: 1, method: "completely.wrong.method.name.xyz", params: {},
    });
    const parsed = JSON.parse(body);
    expect(parsed.error.code).to.equal(-32601);
    expect(parsed.error.message).to.not.contain("Did you mean");
  });
});
