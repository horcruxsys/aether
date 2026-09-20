import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ToolSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { BrowserManager } from "./core/browser-manager.js";
import { BrowserTools } from "./tools/browser-tools.js";

const browserManager = new BrowserManager();
const browserTools = new BrowserTools(browserManager);

const server = new Server(
  {
    name: "Browser Automation MCP",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const TOOLS: ToolSchema[] = [
  // Session Management
  {
    name: "create_session",
    description: "Create a new browser session with Chrome",
    inputSchema: {
      type: "object",
      properties: {
        headless: {
          type: "boolean",
          description: "Run browser in headless mode (default: true)",
        },
        viewport: {
          type: "object",
          description: "Viewport size {width, height}",
          properties: {
            width: { type: "number" },
            height: { type: "number" },
          },
        },
      },
    },
  },
  {
    name: "close_session",
    description: "Close a browser session",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: {
          type: "string",
          description: "Session ID to close",
        },
      },
      required: ["sessionId"],
    },
  },
  {
    name: "list_sessions",
    description: "List all active browser sessions",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },

  // Page Management
  {
    name: "create_page",
    description: "Create a new page in a session",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: {
          type: "string",
          description: "Session ID",
        },
      },
      required: ["sessionId"],
    },
  },
  {
    name: "close_page",
    description: "Close a specific page",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "list_pages",
    description: "List all pages in a session",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: {
          type: "string",
          description: "Session ID",
        },
      },
      required: ["sessionId"],
    },
  },

  // Navigation
  {
    name: "navigate",
    description: "Navigate to a URL",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        url: {
          type: "string",
          description: "URL to navigate to",
        },
        waitUntil: {
          type: "string",
          enum: ["load", "domcontentloaded", "networkidle"],
          description: "Wait until this condition",
        },
        timeout: {
          type: "number",
          description: "Timeout in milliseconds",
        },
      },
      required: ["sessionId", "pageId", "url"],
    },
  },
  {
    name: "go_back",
    description: "Navigate back in history",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        timeout: { type: "number" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "go_forward",
    description: "Navigate forward in history",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        timeout: { type: "number" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "reload",
    description: "Reload the page",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        waitUntil: {
          type: "string",
          enum: ["load", "domcontentloaded", "networkidle"],
        },
      },
      required: ["sessionId", "pageId"],
    },
  },

  // Screenshots & Snapshots
  {
    name: "screenshot",
    description: "Take a screenshot of the page",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        fullPage: {
          type: "boolean",
          description: "Capture full page or viewport",
        },
        mask: {
          type: "array",
          description: "CSS selectors to mask",
          items: { type: "string" },
        },
        maxWidth: { type: "number" },
        maxHeight: { type: "number" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "get_page_snapshot",
    description: "Get page HTML, text content, and metadata",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },

  // Element Queries
  {
    name: "query_selector",
    description: "Query a single element by CSS selector",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: {
          type: "string",
          description: "CSS selector",
        },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "query_selectors",
    description: "Query multiple elements by CSS selector",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "query_xpath",
    description: "Query elements by XPath",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        xpath: {
          type: "string",
          description: "XPath expression",
        },
      },
      required: ["sessionId", "pageId", "xpath"],
    },
  },

  // Element Interaction
  {
    name: "click",
    description: "Click an element",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        delay: { type: "number" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "double_click",
    description: "Double-click an element",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "right_click",
    description: "Right-click an element",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "fill",
    description: "Fill an input field with text",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        text: { type: "string" },
        clearFirst: { type: "boolean" },
        delay: { type: "number" },
      },
      required: ["sessionId", "pageId", "selector", "text"],
    },
  },
  {
    name: "type",
    description: "Type text character by character",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        text: { type: "string" },
        delay: { type: "number", description: "Delay between keystrokes in ms" },
      },
      required: ["sessionId", "pageId", "selector", "text"],
    },
  },
  {
    name: "clear",
    description: "Clear an input field",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "press",
    description: "Press a single key",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        key: {
          type: "string",
          description: "Key name (e.g., Enter, Tab, Escape)",
        },
      },
      required: ["sessionId", "pageId", "selector", "key"],
    },
  },
  {
    name: "check",
    description: "Check a checkbox",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "uncheck",
    description: "Uncheck a checkbox",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "select",
    description: "Select an option in a dropdown",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        value: {
          type: "string",
          description: "Option value to select",
        },
      },
      required: ["sessionId", "pageId", "selector", "value"],
    },
  },
  {
    name: "upload_file",
    description: "Upload a file to an input",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        filePath: {
          type: "string",
          description: "Path to file to upload",
        },
      },
      required: ["sessionId", "pageId", "selector", "filePath"],
    },
  },

  // Keyboard & Mouse
  {
    name: "keyboard_press",
    description: "Press a key on the keyboard",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        key: { type: "string" },
      },
      required: ["sessionId", "pageId", "key"],
    },
  },
  {
    name: "keyboard_type",
    description: "Type text using keyboard",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        text: { type: "string" },
        delay: { type: "number" },
      },
      required: ["sessionId", "pageId", "text"],
    },
  },
  {
    name: "mouse_move",
    description: "Move mouse to coordinates",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        x: { type: "number" },
        y: { type: "number" },
      },
      required: ["sessionId", "pageId", "x", "y"],
    },
  },
  {
    name: "mouse_click",
    description: "Click at mouse coordinates",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        x: { type: "number" },
        y: { type: "number" },
      },
      required: ["sessionId", "pageId", "x", "y"],
    },
  },
  {
    name: "mouse_drag",
    description: "Drag mouse from one position to another",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        x: { type: "number" },
        y: { type: "number" },
        targetX: { type: "number" },
        targetY: { type: "number" },
      },
      required: ["sessionId", "pageId", "x", "y", "targetX", "targetY"],
    },
  },

  // JavaScript Execution
  {
    name: "execute_script",
    description: "Execute arbitrary JavaScript on the page",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        script: {
          type: "string",
          description: "JavaScript code to execute",
        },
      },
      required: ["sessionId", "pageId", "script"],
    },
  },
  {
    name: "evaluate_expression",
    description: "Evaluate a JavaScript expression",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        script: { type: "string" },
      },
      required: ["sessionId", "pageId", "script"],
    },
  },

  // Wait Operations
  {
    name: "wait_for_selector",
    description: "Wait for an element to appear",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        selector: { type: "string" },
        timeout: { type: "number" },
      },
      required: ["sessionId", "pageId", "selector"],
    },
  },
  {
    name: "wait_for_navigation",
    description: "Wait for page navigation",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        timeout: { type: "number" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "wait_for_function",
    description: "Wait until a JavaScript function returns true",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        script: {
          type: "string",
          description: "JavaScript function that returns boolean",
        },
        timeout: { type: "number" },
      },
      required: ["sessionId", "pageId", "script"],
    },
  },
  {
    name: "wait_for_timeout",
    description: "Wait for a specified duration",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        timeout: {
          type: "number",
          description: "Duration in milliseconds",
        },
      },
      required: ["sessionId", "pageId", "timeout"],
    },
  },

  // Network Interception
  {
    name: "intercept_requests",
    description: "Intercept and modify network requests",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        rules: {
          type: "array",
          description: "Array of interception rules",
        },
      },
      required: ["sessionId", "pageId", "rules"],
    },
  },
  {
    name: "block_requests",
    description: "Block specific network requests by pattern",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        patterns: {
          type: "array",
          description: "URL patterns to block",
          items: { type: "string" },
        },
      },
      required: ["sessionId", "pageId", "patterns"],
    },
  },

  // Cookies & Storage
  {
    name: "get_cookies",
    description: "Get all cookies from the session",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "set_cookies",
    description: "Set cookies",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        cookies: {
          type: "object",
          description: "Cookie key-value pairs",
        },
      },
      required: ["sessionId", "pageId", "cookies"],
    },
  },
  {
    name: "get_storage",
    description: "Get localStorage or sessionStorage data",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        type: {
          type: "string",
          enum: ["localStorage", "sessionStorage"],
        },
      },
      required: ["sessionId", "pageId", "type"],
    },
  },
  {
    name: "set_storage",
    description: "Set localStorage or sessionStorage data",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
        type: {
          type: "string",
          enum: ["localStorage", "sessionStorage"],
        },
        data: {
          type: "object",
          description: "Storage key-value pairs",
        },
      },
      required: ["sessionId", "pageId", "type", "data"],
    },
  },
  {
    name: "clear_cookies",
    description: "Clear all cookies",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "clear_storage",
    description: "Clear all localStorage and sessionStorage",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },

  // DevTools & Metrics
  {
    name: "get_metrics",
    description: "Get page performance metrics",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },
  {
    name: "get_console_messages",
    description: "Get console messages from the page",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: { type: "string" },
        pageId: { type: "string" },
      },
      required: ["sessionId", "pageId"],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const result = await browserTools.handleTool(name, args as any);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result),
      },
    ],
  };
});

export { server, browserManager, browserTools };

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("🚀 Browser Automation MCP Server is running...");
}

if (process.env.NODE_ENV !== "test") {
  main().catch((error) => {
    console.error("Fatal Error:", error);
    process.exit(1);
  });
}
