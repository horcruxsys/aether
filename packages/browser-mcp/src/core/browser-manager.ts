import {
  chromium,
  Browser,
  BrowserContext,
  Page,
  CDPSession,
} from "playwright";
import { randomUUID } from "crypto";
import type {
  BrowserSession,
  PageSnapshot,
  ElementInfo,
  NavigationWaitOptions,
  ScreenshotOptions,
  JavaScriptExecutionResult,
  NetworkInterceptRule,
  WaitCondition,
  DevToolsMetrics,
  CDPSession as CDPSessionType,
} from "../types/index.js";

export class BrowserManager {
  private sessions: Map<string, BrowserSession> = new Map();
  private defaultTimeout = 30000; // 30 seconds

  async createSession(headless = true, viewport?: { width: number; height: number }): Promise<string> {
    const sessionId = randomUUID();

    const browser = await chromium.launch({
      headless,
      args: [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
      ],
    });

    const context = await browser.newContext({
      viewport: viewport || { width: 1280, height: 720 },
      ignoreHTTPSErrors: true,
    });

    const session: BrowserSession = {
      id: sessionId,
      browser,
      context,
      pages: new Map(),
      activePage: null,
      createdAt: new Date(),
    };

    this.sessions.set(sessionId, session);
    return sessionId;
  }

  async closeSession(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) throw new Error(`Session ${sessionId} not found`);

    await session.context.close();
    await session.browser.close();
    this.sessions.delete(sessionId);
  }

  async createPage(sessionId: string): Promise<string> {
    const session = this.getSession(sessionId);
    const pageId = randomUUID();
    const page = await session.context.newPage();

    session.pages.set(pageId, page);
    session.activePage = page;

    return pageId;
  }

  async closePage(sessionId: string, pageId: string): Promise<void> {
    const session = this.getSession(sessionId);
    const page = session.pages.get(pageId);

    if (!page) throw new Error(`Page ${pageId} not found`);

    await page.close();
    session.pages.delete(pageId);

    if (session.activePage === page) {
      session.activePage = session.pages.size > 0 ? Array.from(session.pages.values())[0] : null;
    }
  }

  async navigate(
    sessionId: string,
    pageId: string,
    url: string,
    options?: NavigationWaitOptions
  ): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    await page.goto(url, {
      waitUntil: options?.waitUntil || "load",
      timeout: options?.timeout || this.defaultTimeout,
    });
  }

  async getPageSnapshot(sessionId: string, pageId: string): Promise<PageSnapshot> {
    const page = this.getPage(sessionId, pageId);

    return {
      url: page.url(),
      title: await page.title(),
      content: await page.textContent("body"),
      html: await page.content(),
    };
  }

  async screenshot(
    sessionId: string,
    pageId: string,
    options?: ScreenshotOptions
  ): Promise<Buffer> {
    const page = this.getPage(sessionId, pageId);

    return await page.screenshot({
      fullPage: options?.fullPage || false,
      mask: options?.mask?.map((selector) => page.locator(selector)) || [],
      maxWidth: options?.maxWidth,
      maxHeight: options?.maxHeight,
    });
  }

  async querySelector(sessionId: string, pageId: string, selector: string): Promise<ElementInfo> {
    const page = this.getPage(sessionId, pageId);
    const locator = page.locator(selector).first();

    return {
      tagName: await locator.evaluate((el: Element) => el.tagName.toLowerCase()),
      text: await locator.textContent(),
      attributes: await locator.evaluate((el: Element) =>
        Object.fromEntries(Array.from(el.attributes).map((a) => [a.name, a.value]))
      ),
      visible: await locator.isVisible(),
      enabled: await locator.isEnabled(),
      checked: await locator.isChecked().catch(() => undefined),
      value: await locator.inputValue().catch(() => undefined),
      boundingBox: await locator.boundingBox(),
    };
  }

  async queryElements(sessionId: string, pageId: string, selector: string): Promise<ElementInfo[]> {
    const page = this.getPage(sessionId, pageId);
    const locators = await page.locator(selector).all();

    return Promise.all(
      locators.map(async (locator) => ({
        tagName: await locator.evaluate((el: Element) => el.tagName.toLowerCase()),
        text: await locator.textContent(),
        attributes: await locator.evaluate((el: Element) =>
          Object.fromEntries(Array.from(el.attributes).map((a) => [a.name, a.value]))
        ),
        visible: await locator.isVisible(),
        enabled: await locator.isEnabled(),
        checked: await locator.isChecked().catch(() => undefined),
        value: await locator.inputValue().catch(() => undefined),
        boundingBox: await locator.boundingBox(),
      }))
    );
  }

  async click(sessionId: string, pageId: string, selector: string, options?: { delay?: number }): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    await page.click(selector, { delay: options?.delay });
  }

  async fill(
    sessionId: string,
    pageId: string,
    selector: string,
    text: string,
    options?: { delay?: number; clearFirst?: boolean }
  ): Promise<void> {
    const page = this.getPage(sessionId, pageId);

    if (options?.clearFirst) {
      await page.locator(selector).clear();
    }

    await page.fill(selector, text);

    if (options?.delay) {
      await page.waitForTimeout(options.delay);
    }
  }

  async type(
    sessionId: string,
    pageId: string,
    selector: string,
    text: string,
    delay = 50
  ): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    await page.locator(selector).type(text, { delay });
  }

  async press(sessionId: string, pageId: string, selector: string, key: string): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    await page.locator(selector).press(key);
  }

  async keyboard(sessionId: string, pageId: string, key: string): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    await page.keyboard.press(key);
  }

  async mouse(sessionId: string, pageId: string, x: number, y: number, action = "move"): Promise<void> {
    const page = this.getPage(sessionId, pageId);

    if (action === "move") {
      await page.mouse.move(x, y);
    } else if (action === "click") {
      await page.mouse.click(x, y);
    } else if (action === "dblclick") {
      await page.mouse.dblclick(x, y);
    }
  }

  async executeScript(
    sessionId: string,
    pageId: string,
    script: string
  ): Promise<JavaScriptExecutionResult> {
    const page = this.getPage(sessionId, pageId);
    const startTime = Date.now();

    try {
      const result = await page.evaluate((code) => {
        return (0, eval)(code);
      }, script);

      return {
        success: true,
        result,
        executionTime: Date.now() - startTime,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        executionTime: Date.now() - startTime,
      };
    }
  }

  async waitForCondition(
    sessionId: string,
    pageId: string,
    condition: WaitCondition
  ): Promise<void> {
    const page = this.getPage(sessionId, pageId);
    const timeout = condition.timeout || this.defaultTimeout;

    if (condition.type === "selector") {
      await page.waitForSelector(condition.selector!, { timeout });
    } else if (condition.type === "navigation") {
      await page.waitForNavigation({ waitUntil: "load", timeout });
    } else if (condition.type === "timeout") {
      await page.waitForTimeout(timeout);
    } else if (condition.type === "function") {
      await page.waitForFunction((code) => (0, eval)(code), condition.fn, { timeout });
    } else if (condition.type === "visible") {
      await page.locator(condition.selector!).waitFor({
        state: "visible",
        timeout,
      });
    }
  }

  async interceptNetwork(
    sessionId: string,
    pageId: string,
    rules: NetworkInterceptRule[]
  ): Promise<void> {
    const page = this.getPage(sessionId, pageId);

    for (const rule of rules) {
      await page.route(rule.urlPattern, (route) => {
        if (rule.action === "block") {
          route.abort();
        } else if (rule.action === "respond") {
          route.abort("blockedbyclient");
        } else {
          route.continue();
        }
      });
    }
  }

  async getMetrics(sessionId: string, pageId: string): Promise<DevToolsMetrics> {
    const page = this.getPage(sessionId, pageId);

    return await page.evaluate(() => {
      const metrics = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
      return {
        navigationStart: metrics.navigationStart,
        responseStart: metrics.responseStart,
        domContentLoadedEventStart: metrics.domContentLoadedEventStart,
        loadEventStart: metrics.loadEventStart,
        loadEventEnd: metrics.loadEventEnd,
      };
    });
  }

  async getCookies(sessionId: string, pageId: string): Promise<{ [key: string]: string }> {
    const session = this.getSession(sessionId);
    const cookies = await session.context.cookies();

    return Object.fromEntries(cookies.map((c) => [c.name, c.value]));
  }

  async setCookies(sessionId: string, pageId: string, cookies: Record<string, string>): Promise<void> {
    const session = this.getSession(sessionId);
    const cookiesToSet = Object.entries(cookies).map(([name, value]) => ({
      name,
      value,
      url: "https://example.com", // Placeholder
    }));

    await session.context.addCookies(cookiesToSet);
  }

  async setUserAgent(sessionId: string, pageId: string, userAgent: string): Promise<void> {
    // User agent must be set at context creation, but we can document this limitation
    throw new Error("User Agent must be set when creating the browser context");
  }

  async getStorageData(sessionId: string, pageId: string, type: "localStorage" | "sessionStorage"): Promise<Record<string, string>> {
    const page = this.getPage(sessionId, pageId);

    return await page.evaluate((storageType) => {
      const storage = storageType === "localStorage" ? window.localStorage : window.sessionStorage;
      const data: Record<string, string> = {};

      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key) {
          data[key] = storage.getItem(key) || "";
        }
      }

      return data;
    }, type);
  }

  async setStorageData(sessionId: string, pageId: string, type: "localStorage" | "sessionStorage", data: Record<string, string>): Promise<void> {
    const page = this.getPage(sessionId, pageId);

    await page.evaluate(
      ({ storageType, storageData }) => {
        const storage = storageType === "localStorage" ? window.localStorage : window.sessionStorage;
        Object.entries(storageData).forEach(([key, value]) => {
          storage.setItem(key, value);
        });
      },
      { storageType: type, storageData: data }
    );
  }

  private getSession(sessionId: string): BrowserSession {
    const session = this.sessions.get(sessionId);
    if (!session) throw new Error(`Session ${sessionId} not found`);
    return session;
  }

  private getPage(sessionId: string, pageId: string): Page {
    const session = this.getSession(sessionId);
    const page = session.pages.get(pageId);
    if (!page) throw new Error(`Page ${pageId} not found in session ${sessionId}`);
    return page;
  }

  getSessions(): string[] {
    return Array.from(this.sessions.keys());
  }

  getPages(sessionId: string): string[] {
    const session = this.getSession(sessionId);
    return Array.from(session.pages.keys());
  }
}
