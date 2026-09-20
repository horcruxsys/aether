import type { BrowserManager } from "../core/browser-manager.js";
import type { BrowserMCPToolInput, MCPToolResult } from "../types/index.js";

export class BrowserTools {
  constructor(private browserManager: BrowserManager) {}

  async handleTool(toolName: string, input: BrowserMCPToolInput): Promise<MCPToolResult> {
    try {
      switch (toolName) {
        // Session Management
        case "create_session":
          return await this.createSession(input);
        case "close_session":
          return await this.closeSession(input);
        case "list_sessions":
          return await this.listSessions(input);

        // Page Management
        case "create_page":
          return await this.createPage(input);
        case "close_page":
          return await this.closePage(input);
        case "list_pages":
          return await this.listPages(input);

        // Navigation
        case "navigate":
          return await this.navigate(input);
        case "go_back":
          return await this.goBack(input);
        case "go_forward":
          return await this.goForward(input);
        case "reload":
          return await this.reload(input);

        // Screenshot & Snapshots
        case "screenshot":
          return await this.screenshot(input);
        case "get_page_snapshot":
          return await this.getPageSnapshot(input);

        // Element Queries
        case "query_selector":
          return await this.querySelector(input);
        case "query_selectors":
          return await this.querySelectors(input);
        case "query_xpath":
          return await this.queryXpath(input);

        // Element Interaction
        case "click":
          return await this.click(input);
        case "double_click":
          return await this.doubleClick(input);
        case "right_click":
          return await this.rightClick(input);
        case "fill":
          return await this.fill(input);
        case "type":
          return await this.type(input);
        case "clear":
          return await this.clear(input);
        case "press":
          return await this.press(input);
        case "check":
          return await this.check(input);
        case "uncheck":
          return await this.uncheck(input);
        case "select":
          return await this.select(input);
        case "upload_file":
          return await this.uploadFile(input);

        // Keyboard & Mouse
        case "keyboard_press":
          return await this.keyboardPress(input);
        case "keyboard_type":
          return await this.keyboardType(input);
        case "mouse_move":
          return await this.mouseMove(input);
        case "mouse_click":
          return await this.mouseClick(input);
        case "mouse_drag":
          return await this.mouseDrag(input);

        // JavaScript Execution
        case "execute_script":
          return await this.executeScript(input);
        case "evaluate_expression":
          return await this.evaluateExpression(input);

        // Wait Operations
        case "wait_for_selector":
          return await this.waitForSelector(input);
        case "wait_for_navigation":
          return await this.waitForNavigation(input);
        case "wait_for_function":
          return await this.waitForFunction(input);
        case "wait_for_timeout":
          return await this.waitForTimeout(input);

        // Network Interception
        case "intercept_requests":
          return await this.interceptRequests(input);
        case "block_requests":
          return await this.blockRequests(input);

        // Cookies & Storage
        case "get_cookies":
          return await this.getCookies(input);
        case "set_cookies":
          return await this.setCookies(input);
        case "get_storage":
          return await this.getStorage(input);
        case "set_storage":
          return await this.setStorage(input);
        case "clear_cookies":
          return await this.clearCookies(input);
        case "clear_storage":
          return await this.clearStorage(input);

        // DevTools & Metrics
        case "get_metrics":
          return await this.getMetrics(input);
        case "get_console_messages":
          return await this.getConsoleMessages(input);

        default:
          return { success: false, error: `Tool not found: ${toolName}` };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  // Session Management
  async createSession(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    const sessionId = await this.browserManager.createSession(
      input.headless !== false,
      input.viewport as { width: number; height: number } | undefined
    );
    return { success: true, data: { sessionId } };
  }

  async closeSession(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId) return { success: false, error: "sessionId required" };
    await this.browserManager.closeSession(input.sessionId);
    return { success: true };
  }

  async listSessions(): Promise<MCPToolResult> {
    const sessions = this.browserManager.getSessions();
    return { success: true, data: { sessions } };
  }

  // Page Management
  async createPage(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId) return { success: false, error: "sessionId required" };
    const pageId = await this.browserManager.createPage(input.sessionId);
    return { success: true, data: { pageId } };
  }

  async closePage(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    await this.browserManager.closePage(input.sessionId, input.pageId);
    return { success: true };
  }

  async listPages(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId) return { success: false, error: "sessionId required" };
    const pages = this.browserManager.getPages(input.sessionId);
    return { success: true, data: { pages } };
  }

  // Navigation
  async navigate(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.url) {
      return { success: false, error: "sessionId, pageId, and url required" };
    }
    await this.browserManager.navigate(input.sessionId, input.pageId, input.url, {
      waitUntil: input.waitUntil as any,
      timeout: input.timeout,
    });
    return { success: true };
  }

  async goBack(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.goBack({ timeout: input.timeout });
    return { success: true };
  }

  async goForward(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.goForward({ timeout: input.timeout });
    return { success: true };
  }

  async reload(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.reload({ waitUntil: input.waitUntil || "load" });
    return { success: true };
  }

  // Screenshot & Snapshots
  async screenshot(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    const buffer = await this.browserManager.screenshot(input.sessionId, input.pageId, {
      fullPage: input.fullPage as boolean,
      mask: input.mask as string[] | undefined,
      maxWidth: input.maxWidth as number | undefined,
      maxHeight: input.maxHeight as number | undefined,
    });
    return { success: true, data: { screenshot: buffer.toString("base64") } };
  }

  async getPageSnapshot(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) return { success: false, error: "sessionId and pageId required" };
    const snapshot = await this.browserManager.getPageSnapshot(input.sessionId, input.pageId);
    return { success: true, data: snapshot };
  }

  // Element Queries
  async querySelector(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const element = await this.browserManager.querySelector(input.sessionId, input.pageId, input.selector);
    return { success: true, data: element };
  }

  async querySelectors(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const elements = await this.browserManager.queryElements(input.sessionId, input.pageId, input.selector);
    return { success: true, data: { elements, count: elements.length } };
  }

  async queryXpath(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.xpath) {
      return { success: false, error: "sessionId, pageId, and xpath required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    const elements = await page.locator(`xpath=${input.xpath}`).all();
    const data = await Promise.all(
      elements.map(async (el) => ({
        text: await el.textContent(),
        visible: await el.isVisible(),
      }))
    );
    return { success: true, data: { elements: data } };
  }

  // Element Interaction
  async click(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    await this.browserManager.click(input.sessionId, input.pageId, input.selector, {
      delay: input.delay as number | undefined,
    });
    return { success: true };
  }

  async doubleClick(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.dblclick(input.selector);
    return { success: true };
  }

  async rightClick(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.click(input.selector, { button: "right" });
    return { success: true };
  }

  async fill(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector || !input.text) {
      return { success: false, error: "sessionId, pageId, selector, and text required" };
    }
    await this.browserManager.fill(input.sessionId, input.pageId, input.selector, input.text, {
      delay: input.delay as number | undefined,
      clearFirst: input.clearFirst as boolean | undefined,
    });
    return { success: true };
  }

  async type(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector || !input.text) {
      return { success: false, error: "sessionId, pageId, selector, and text required" };
    }
    await this.browserManager.type(input.sessionId, input.pageId, input.selector, input.text, input.delay as number);
    return { success: true };
  }

  async clear(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.locator(input.selector).clear();
    return { success: true };
  }

  async press(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector || !input.key) {
      return { success: false, error: "sessionId, pageId, selector, and key required" };
    }
    await this.browserManager.press(input.sessionId, input.pageId, input.selector, input.key as string);
    return { success: true };
  }

  async check(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.check(input.selector);
    return { success: true };
  }

  async uncheck(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.uncheck(input.selector);
    return { success: true };
  }

  async select(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector || !input.value) {
      return { success: false, error: "sessionId, pageId, selector, and value required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.selectOption(input.selector, input.value as string);
    return { success: true };
  }

  async uploadFile(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector || !input.filePath) {
      return { success: false, error: "sessionId, pageId, selector, and filePath required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.locator(input.selector).setInputFiles(input.filePath as string);
    return { success: true };
  }

  // Keyboard & Mouse
  async keyboardPress(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.key) {
      return { success: false, error: "sessionId, pageId, and key required" };
    }
    await this.browserManager.keyboard(input.sessionId, input.pageId, input.key as string);
    return { success: true };
  }

  async keyboardType(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.text) {
      return { success: false, error: "sessionId, pageId, and text required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.keyboard.type(input.text as string, { delay: input.delay as number || 50 });
    return { success: true };
  }

  async mouseMove(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || input.x === undefined || input.y === undefined) {
      return { success: false, error: "sessionId, pageId, x, and y required" };
    }
    await this.browserManager.mouse(input.sessionId, input.pageId, input.x as number, input.y as number, "move");
    return { success: true };
  }

  async mouseClick(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || input.x === undefined || input.y === undefined) {
      return { success: false, error: "sessionId, pageId, x, and y required" };
    }
    await this.browserManager.mouse(input.sessionId, input.pageId, input.x as number, input.y as number, "click");
    return { success: true };
  }

  async mouseDrag(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || input.x === undefined || input.y === undefined) {
      return { success: false, error: "sessionId, pageId, x, and y required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    const targetX = input.targetX as number;
    const targetY = input.targetY as number;
    if (targetX === undefined || targetY === undefined) {
      return { success: false, error: "targetX and targetY required for drag" };
    }
    await page.mouse.drag(input.x as number, input.y as number, targetX, targetY);
    return { success: true };
  }

  // JavaScript Execution
  async executeScript(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.script) {
      return { success: false, error: "sessionId, pageId, and script required" };
    }
    const result = await this.browserManager.executeScript(input.sessionId, input.pageId, input.script as string);
    return { success: result.success, data: result, error: result.error };
  }

  async evaluateExpression(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.script) {
      return { success: false, error: "sessionId, pageId, and script required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    const result = await page.evaluate(input.script);
    return { success: true, data: { result } };
  }

  // Wait Operations
  async waitForSelector(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.selector) {
      return { success: false, error: "sessionId, pageId, and selector required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.waitForSelector(input.selector, { timeout: input.timeout || 30000 });
    return { success: true };
  }

  async waitForNavigation(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.waitForNavigation({ timeout: input.timeout || 30000 });
    return { success: true };
  }

  async waitForFunction(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.script) {
      return { success: false, error: "sessionId, pageId, and script required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.waitForFunction(input.script, { timeout: input.timeout || 30000 });
    return { success: true };
  }

  async waitForTimeout(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.timeout) {
      return { success: false, error: "sessionId, pageId, and timeout required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.waitForTimeout(input.timeout as number);
    return { success: true };
  }

  // Network Interception
  async interceptRequests(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.rules) {
      return { success: false, error: "sessionId, pageId, and rules required" };
    }
    await this.browserManager.interceptNetwork(input.sessionId, input.pageId, input.rules as any);
    return { success: true };
  }

  async blockRequests(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.patterns) {
      return { success: false, error: "sessionId, pageId, and patterns required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    for (const pattern of input.patterns as string[]) {
      await page.route(pattern, (route) => route.abort());
    }
    return { success: true };
  }

  // Cookies & Storage
  async getCookies(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const cookies = await this.browserManager.getCookies(input.sessionId, input.pageId);
    return { success: true, data: { cookies } };
  }

  async setCookies(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.cookies) {
      return { success: false, error: "sessionId, pageId, and cookies required" };
    }
    await this.browserManager.setCookies(input.sessionId, input.pageId, input.cookies as Record<string, string>);
    return { success: true };
  }

  async getStorage(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.type) {
      return { success: false, error: "sessionId, pageId, and type required" };
    }
    const data = await this.browserManager.getStorageData(input.sessionId, input.pageId, input.type as "localStorage" | "sessionStorage");
    return { success: true, data };
  }

  async setStorage(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId || !input.type || !input.data) {
      return { success: false, error: "sessionId, pageId, type, and data required" };
    }
    await this.browserManager.setStorageData(input.sessionId, input.pageId, input.type as "localStorage" | "sessionStorage", input.data as Record<string, string>);
    return { success: true };
  }

  async clearCookies(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.context().clearCookies();
    return { success: true };
  }

  async clearStorage(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    return { success: true };
  }

  // DevTools & Metrics
  async getMetrics(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const metrics = await this.browserManager.getMetrics(input.sessionId, input.pageId);
    return { success: true, data: metrics };
  }

  async getConsoleMessages(input: BrowserMCPToolInput): Promise<MCPToolResult> {
    if (!input.sessionId || !input.pageId) {
      return { success: false, error: "sessionId and pageId required" };
    }
    const page = (this.browserManager as any).getPage(input.sessionId, input.pageId);
    const messages: any[] = [];
    page.on("console", (msg) => {
      messages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location(),
      });
    });
    return { success: true, data: { messages } };
  }
}
