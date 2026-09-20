# Browser MCP - Quick Start

## What is Browser MCP?

**Browser MCP** is a comprehensive MCP server that brings full browser automation to AI agents. It combines:
- **Playwright** for reliable browser automation
- **Chrome DevTools Protocol** for advanced control
- **55+ tools** for complete browser interaction
- **MCP Protocol** for AI agent compatibility

## Installation & Setup

### 1. Install Package

```bash
cd packages/browser-mcp
pnpm install
```

### 2. Build

```bash
pnpm build
```

### 3. Run Server

```bash
pnpm dev
```

You should see:
```
🚀 Browser Automation MCP Server is running...
```

## First Automation in 30 Seconds

### Code Example

```javascript
// 1. Create a session
let result = await callTool("create_session", { headless: true });
const sessionId = result.data.sessionId;

// 2. Create a page
result = await callTool("create_page", { sessionId });
const pageId = result.data.pageId;

// 3. Navigate
await callTool("navigate", {
  sessionId,
  pageId,
  url: "https://example.com"
});

// 4. Take screenshot
const screenshot = await callTool("screenshot", { sessionId, pageId });

// 5. Cleanup
await callTool("close_page", { sessionId, pageId });
await callTool("close_session", { sessionId });
```

## Key Features at a Glance

### Session & Page Management
```javascript
// Create isolated browser session
const { sessionId } = await createSession({ headless: true });

// Multiple pages per session
const { pageId } = await createPage({ sessionId });
```

### Navigation
```javascript
// Navigate with smart waits
await navigate({
  sessionId, pageId,
  url: "https://example.com",
  waitUntil: "load"
});
```

### Element Interaction
```javascript
// Query elements
const element = await querySelector({
  sessionId, pageId,
  selector: "button.submit"
});

// Click it
await click({ sessionId, pageId, selector: "button.submit" });

// Fill inputs
await fill({
  sessionId, pageId,
  selector: "input#email",
  text: "user@example.com"
});
```

### Screenshots & Snapshots
```javascript
// Full-page screenshot (base64)
const { screenshot } = await screenshot({
  sessionId, pageId,
  fullPage: true
});

// Page snapshot (HTML + metadata)
const { html, title, url } = await getPageSnapshot({
  sessionId, pageId
});
```

### JavaScript Execution
```javascript
// Execute any JavaScript
const result = await executeScript({
  sessionId, pageId,
  script: "return document.title;"
});
console.log(result.result); // Page title
```

### Network Control
```javascript
// Mock API responses
await interceptRequests({
  sessionId, pageId,
  rules: [
    {
      urlPattern: "**/api/**",
      action: "respond",
      statusCode: 200,
      responseBody: '{"data": []}'
    }
  ]
});
```

### Storage Management
```javascript
// Get/set cookies
const cookies = await getCookies({ sessionId, pageId });
await setCookies({
  sessionId, pageId,
  cookies: { session_id: "abc123" }
});

// LocalStorage
const data = await getStorage({
  sessionId, pageId,
  type: "localStorage"
});
```

### Wait Operations
```javascript
// Wait for element
await waitForSelector({
  sessionId, pageId,
  selector: ".loaded",
  timeout: 10000
});

// Wait for function
await waitForFunction({
  sessionId, pageId,
  script: "() => window.ready === true",
  timeout: 30000
});

// Wait for navigation
await waitForNavigation({ sessionId, pageId });
```

## Tool Categories

| Category | Tools | Use Cases |
|----------|-------|-----------|
| **Sessions** | create, close, list | Manage browser lifecycle |
| **Pages** | create, close, list | Multi-tab workflows |
| **Navigation** | navigate, go_back, go_forward, reload | Page traversal |
| **Screenshots** | screenshot, snapshot | Verification & debugging |
| **Element Queries** | querySelector, querySelectors, queryXpath | DOM inspection |
| **Interaction** | click, fill, type, select, upload | User actions |
| **Keyboard/Mouse** | press, type, move, click, drag | Input control |
| **JavaScript** | execute, evaluate | Custom logic |
| **Waits** | selector, navigation, function, timeout | Synchronization |
| **Network** | intercept, block | Request control |
| **Storage** | cookies, localStorage, sessionStorage | Data persistence |
| **Metrics** | performance, console | Debugging |

## Common Workflows

### Login Automation
```javascript
const session = await createSession();
const page = await createPage(session);
await navigate({ ...session, page, url: "https://example.com/login" });
await fill({ ...session, page, selector: "input[name='user']", text: "admin" });
await fill({ ...session, page, selector: "input[name='pass']", text: "secret" });
await click({ ...session, page, selector: "button[type='submit']" });
await waitForNavigation({ ...session, page });
```

### Data Scraping
```javascript
const session = await createSession();
const page = await createPage(session);
await navigate({ ...session, page, url: "https://example.com" });
const results = await executeScript({
  ...session, page,
  script: `
    return Array.from(document.querySelectorAll('.item')).map(el => ({
      title: el.textContent,
      link: el.href
    }));
  `
});
console.log(results.result);
```

### Form Testing
```javascript
const session = await createSession();
const page = await createPage(session);
await navigate({ ...session, page, url: "https://example.com/form" });
await fill({ ...session, page, selector: "input.name", text: "John" });
await select({ ...session, page, selector: "select.country", value: "US" });
await check({ ...session, page, selector: "input[type='checkbox']" });
await click({ ...session, page, selector: "button.submit" });
```

### API Response Mocking
```javascript
const session = await createSession();
const page = await createPage(session);

// Mock API before navigation
await interceptRequests({
  ...session, page,
  rules: [
    {
      urlPattern: "**/api/users**",
      action: "respond",
      statusCode: 200,
      responseBody: JSON.stringify([{ id: 1, name: "Test" }])
    }
  ]
});

await navigate({ ...session, page, url: "https://example.com" });
// App will use mocked API response
```

## Documentation

### Full Documentation
- **[README.md](./README.md)** - Complete feature reference
- **[FEATURES.md](./FEATURES.md)** - Detailed tool descriptions
- **[USAGE_GUIDE.md](./USAGE_GUIDE.md)** - Advanced usage patterns

### API Reference
- Check `src/types/index.ts` for TypeScript interfaces
- All tools return consistent `MCPToolResult` format

## Troubleshooting

### Browser Not Found
```bash
npx playwright install chromium
```

### Connection Issues
Ensure the MCP server is running:
```bash
pnpm dev
```

### Timeout Errors
Increase timeout:
```javascript
await navigate({
  sessionId, pageId,
  url: "...",
  timeout: 60000  // 60 seconds
});
```

### Element Not Found
Check selector is correct:
```javascript
const element = await querySelector({
  sessionId, pageId,
  selector: "#button"  // Use specific selectors
});

if (!element.visible) {
  // Wait for visibility
  await waitForSelector({ ... });
}
```

## Architecture

```
Browser MCP Server
  ├── MCP Protocol (stdio transport)
  ├── Tool Handlers (BrowserTools)
  ├── Browser Manager (BrowserManager)
  └── Playwright (Chromium)
```

## Performance Tips

1. **Reuse sessions** - Don't create new session for each operation
2. **Block ads/analytics** - Speeds up page loads
3. **Use headless mode** - Faster than headed
4. **Optimize timeouts** - Don't wait longer than needed
5. **Cache selectors** - Query once, reuse multiple times

## Next Steps

1. ✅ Read [USAGE_GUIDE.md](./USAGE_GUIDE.md) for advanced patterns
2. ✅ Check [FEATURES.md](./FEATURES.md) for complete tool list
3. ✅ Explore `src/` directory for implementation details
4. ✅ Run tests: `pnpm test`
5. ✅ Build for production: `pnpm build`

## Support

For issues or questions:
1. Check [USAGE_GUIDE.md](./USAGE_GUIDE.md) troubleshooting section
2. Review tool schema in [README.md](./README.md)
3. Check test examples in `src/index.test.ts`

---

**Happy Automating!** 🚀
