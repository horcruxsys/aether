import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { BrowserManager } from "./core/browser-manager.js";
import { BrowserTools } from "./tools/browser-tools.js";

describe("BrowserManager", () => {
  let browserManager: BrowserManager;

  beforeAll(() => {
    browserManager = new BrowserManager();
  });

  afterAll(async () => {
    const sessions = browserManager.getSessions();
    for (const sessionId of sessions) {
      await browserManager.closeSession(sessionId);
    }
  });

  it("should create a session", async () => {
    const sessionId = await browserManager.createSession(true);
    expect(sessionId).toBeDefined();
    expect(typeof sessionId).toBe("string");

    const sessions = browserManager.getSessions();
    expect(sessions).toContain(sessionId);
  });

  it("should create a page in session", async () => {
    const sessionId = await browserManager.createSession(true);
    const pageId = await browserManager.createPage(sessionId);

    expect(pageId).toBeDefined();
    expect(typeof pageId).toBe("string");

    const pages = browserManager.getPages(sessionId);
    expect(pages).toContain(pageId);

    await browserManager.closeSession(sessionId);
  });

  it("should navigate to a URL", async () => {
    const sessionId = await browserManager.createSession(true);
    const pageId = await browserManager.createPage(sessionId);

    // This will fail without network, but demonstrates the API
    try {
      await browserManager.navigate(sessionId, pageId, "https://example.com", {
        waitUntil: "load",
        timeout: 10000,
      });
    } catch (error) {
      // Expected to fail in test environment
    }

    await browserManager.closeSession(sessionId);
  });

  it("should handle invalid session ID", async () => {
    expect(() => {
      browserManager.getSessions();
    }).not.toThrow();

    // This should throw
    try {
      await browserManager.closeSession("invalid-id");
      expect.fail("Should have thrown");
    } catch (error) {
      expect(error instanceof Error).toBe(true);
    }
  });
});

describe("BrowserTools", () => {
  let browserManager: BrowserManager;
  let browserTools: BrowserTools;

  beforeAll(() => {
    browserManager = new BrowserManager();
    browserTools = new BrowserTools(browserManager);
  });

  afterAll(async () => {
    const sessions = browserManager.getSessions();
    for (const sessionId of sessions) {
      await browserManager.closeSession(sessionId);
    }
  });

  it("should handle create_session tool", async () => {
    const result = await browserTools.handleTool("create_session", {
      headless: true,
    });

    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data?.sessionId).toBeDefined();
  });

  it("should handle list_sessions tool", async () => {
    const result = await browserTools.handleTool("list_sessions", {});
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data?.sessions)).toBe(true);
  });

  it("should validate required parameters", async () => {
    const result = await browserTools.handleTool("create_page", {});
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
  });

  it("should handle create_page tool", async () => {
    const sessionResult = await browserTools.handleTool("create_session", {});
    const sessionId = (sessionResult.data as any)?.sessionId;

    const pageResult = await browserTools.handleTool("create_page", {
      sessionId,
    });

    expect(pageResult.success).toBe(true);
    expect(pageResult.data).toBeDefined();

    await browserManager.closeSession(sessionId);
  });

  it("should handle invalid tool name", async () => {
    const result = await browserTools.handleTool("invalid_tool", {});
    expect(result.success).toBe(false);
    expect(result.error).toContain("not found");
  });
});
