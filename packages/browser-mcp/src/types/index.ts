import { Page, Browser, BrowserContext, Locator } from "playwright";

export interface BrowserSession {
  id: string;
  browser: Browser;
  context: BrowserContext;
  pages: Map<string, Page>;
  activePage: Page | null;
  createdAt: Date;
}

export interface PageSnapshot {
  url: string;
  title: string;
  content: string;
  html: string;
}

export interface ElementInfo {
  tagName: string;
  text: string;
  attributes: Record<string, string>;
  visible: boolean;
  enabled: boolean;
  checked?: boolean;
  value?: string;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface NetworkInterceptRule {
  urlPattern: string | RegExp;
  action: "block" | "respond" | "continue";
  statusCode?: number;
  responseBody?: string;
  headers?: Record<string, string>;
}

export interface NavigationWaitOptions {
  waitUntil?: "load" | "domcontentloaded" | "networkidle";
  timeout?: number;
}

export interface ScreenshotOptions {
  fullPage?: boolean;
  mask?: string[]; // CSS selectors to mask
  includeAnnotation?: boolean;
  maxWidth?: number;
  maxHeight?: number;
}

export interface JavaScriptExecutionResult {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTime: number;
}

export interface MouseAction {
  type: "click" | "dblclick" | "moveTo";
  selector?: string;
  x?: number;
  y?: number;
  button?: "left" | "right" | "middle";
  clickCount?: number;
}

export interface TextInputOptions {
  delay?: number; // milliseconds between keystrokes
  clearFirst?: boolean;
}

export interface WaitCondition {
  type: "selector" | "navigation" | "timeout" | "function" | "visible";
  selector?: string;
  timeout?: number;
  visible?: boolean;
  fn?: string; // JavaScript function as string
}

export interface DevToolsMetrics {
  navigationStart: number;
  responseStart: number;
  domContentLoadedEventStart: number;
  loadEventStart: number;
  loadEventEnd: number;
}

export interface CDPSession {
  sessionId: string;
  pageId: string;
  domain: string;
  enabled: boolean;
}

export interface BrowserMCPToolInput {
  sessionId?: string;
  pageId?: string;
  selector?: string;
  text?: string;
  url?: string;
  html?: string;
  script?: string;
  timeout?: number;
  options?: Record<string, unknown>;
  xpath?: string;
  delay?: number;
  value?: string;
  x?: number;
  y?: number;
  [key: string]: unknown;
}

export interface MCPToolResult {
  success: boolean;
  data?: unknown;
  error?: string;
  metadata?: Record<string, unknown>;
}
