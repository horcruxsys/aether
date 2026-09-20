# Browser Automation MCP

A comprehensive Model Context Protocol (MCP) server for browser automation combining the power of **Playwright** and **Chrome DevTools Protocol**. This MCP enables AI agents to automate any browser-based workflow with full control over interaction, networking, storage, and performance metrics.

## Features

### 🎯 Core Capabilities

- **Session Management**: Create and manage isolated browser sessions
- **Page Management**: Open, close, and switch between multiple pages
- **Navigation**: Navigate to URLs, handle history, reload pages
- **Element Interaction**: Click, type, select, check/uncheck, drag & drop
- **Screenshot & Snapshots**: Capture full-page screenshots, get DOM snapshots
- **Query Elements**: CSS selectors, XPath, element introspection
- **JavaScript Execution**: Execute arbitrary scripts, evaluate expressions
- **Network Control**: Intercept, block, and modify network requests
- **Storage Management**: Control cookies, localStorage, sessionStorage
- **Wait Operations**: Wait for elements, navigation, functions, timeouts
- **Performance Metrics**: Get page load times and DevTools metrics
- **Keyboard & Mouse**: Direct keyboard and mouse input simulation

### 🚀 Playwright Integration

- Chromium browser automation
- Full DevTools Protocol support
- Multi-page context management
- Network request/response manipulation
- Performance monitoring
- File upload handling

### 🔌 MCP Protocol

All functionality exposed as MCP tools that can be called by AI agents and Claude Code plugins. Full standardized tool schema with proper input validation and error handling.

## Installation

```bash
pnpm add @aether/browser-mcp
# or
npm install @aether/browser-mcp
```

## Quick Start

### Starting the MCP Server

```bash
pnpm dev
# or
tsx src/index.ts
```

The server listens on stdio and will output:
```
🚀 Browser Automation MCP Server is running...
```

### Building for Production

```bash
pnpm build
node dist/index.js
```

## Tool Categories

### Session Management

#### `create_session`
Create a new browser session with Chrome.

```json
{
  "sessionId": "uuid",
  "headless": true,
  "viewport": { "width": 1280, "height": 720 }
}
```

#### `close_session`
Close a browser session and all its resources.

#### `list_sessions`
List all active browser sessions.

---

### Page Management

#### `create_page`
Create a new page in a session.

#### `close_page`
Close a specific page.

#### `list_pages`
List all pages in a session.

---

### Navigation

#### `navigate`
Navigate to a URL with customizable wait conditions.

```json
{
  "sessionId": "...",
  "pageId": "...",
  "url": "https://example.com",
  "waitUntil": "load",
  "timeout": 30000
}
```

#### `go_back` / `go_forward` / `reload`
Navigate through browser history or reload.

---

### Element Interaction

#### `query_selector`
Find a single element by CSS selector.

```json
{
  "sessionId": "...",
  "pageId": "...",
  "selector": "button.submit"
}
```

#### `query_selectors`
Find multiple elements by CSS selector.

#### `query_xpath`
Find elements by XPath expression.

#### `click`
Click an element.

#### `fill`
Fill an input with text (clears first if specified).

```json
{
  "selector": "input#email",
  "text": "user@example.com",
  "clearFirst": true
}
```

#### `type`
Type text character by character with custom delays.

#### `press`
Press a single key (Enter, Tab, Escape, etc.).

#### `check` / `uncheck`
Check or uncheck a checkbox.

#### `select`
Select an option in a dropdown.

#### `upload_file`
Upload a file to an input.

---

### Screenshot & Snapshots

#### `screenshot`
Capture a screenshot (viewport or full-page).

```json
{
  "fullPage": true,
  "mask": ["#password-field"],
  "maxWidth": 1920,
  "maxHeight": 1080
}
```

Returns base64-encoded PNG.

#### `get_page_snapshot`
Get page metadata and content.

```json
{
  "url": "https://...",
  "title": "Page Title",
  "content": "Text content...",
  "html": "<!DOCTYPE html>..."
}
```

---

### JavaScript Execution

#### `execute_script`
Execute arbitrary JavaScript on the page.

```json
{
  "script": "return document.querySelectorAll('button').length;"
}
```

#### `evaluate_expression`
Evaluate a JavaScript expression.

---

### Wait Operations

#### `wait_for_selector`
Wait for an element to appear (with timeout).

#### `wait_for_navigation`
Wait for page navigation to complete.

#### `wait_for_function`
Wait until a JavaScript function returns true.

```json
{
  "script": "() => document.body.classList.contains('loaded')"
}
```

#### `wait_for_timeout`
Wait for a specified duration.

---

### Network Control

#### `intercept_requests`
Set up network request interception rules.

```json
{
  "rules": [
    {
      "urlPattern": "**/api/**",
      "action": "respond",
      "statusCode": 200,
      "responseBody": "{\"status\": \"ok\"}"
    },
    {
      "urlPattern": "**/analytics/**",
      "action": "block"
    }
  ]
}
```

#### `block_requests`
Block specific requests by URL pattern.

---

### Storage Management

#### `get_cookies`
Get all cookies from the session.

#### `set_cookies`
Set cookies.

```json
{
  "cookies": {
    "session_id": "abc123",
    "preferences": "dark_mode=true"
  }
}
```

#### `get_storage`
Get localStorage or sessionStorage data.

```json
{
  "type": "localStorage"
}
```

#### `set_storage`
Set localStorage or sessionStorage data.

#### `clear_cookies` / `clear_storage`
Clear all cookies or storage data.

---

### Performance & Metrics

#### `get_metrics`
Get page performance metrics.

```json
{
  "navigationStart": 1234567890,
  "responseStart": 1234567900,
  "domContentLoadedEventStart": 1234567950,
  "loadEventStart": 1234568000,
  "loadEventEnd": 1234568050
}
```

#### `get_console_messages`
Get console messages (logs, warnings, errors).

---

## Example Workflow

```json
// 1. Create a session
{
  "tool": "create_session",
  "input": {
    "headless": true,
    "viewport": { "width": 1280, "height": 720 }
  }
}

// 2. Create a page
{
  "tool": "create_page",
  "input": { "sessionId": "session-uuid" }
}

// 3. Navigate to website
{
  "tool": "navigate",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "url": "https://example.com",
    "waitUntil": "load"
  }
}

// 4. Query and interact with elements
{
  "tool": "query_selector",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "selector": "input#search"
  }
}

{
  "tool": "fill",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "selector": "input#search",
    "text": "query"
  }
}

{
  "tool": "click",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "selector": "button[type='submit']"
  }
}

// 5. Wait and verify
{
  "tool": "wait_for_selector",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "selector": ".results",
    "timeout": 10000
  }
}

// 6. Take screenshot
{
  "tool": "screenshot",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid",
    "fullPage": false
  }
}

// 7. Close
{
  "tool": "close_page",
  "input": {
    "sessionId": "session-uuid",
    "pageId": "page-uuid"
  }
}

{
  "tool": "close_session",
  "input": { "sessionId": "session-uuid" }
}
```

## Advanced Usage

### Network Request Mocking

```json
{
  "tool": "intercept_requests",
  "input": {
    "sessionId": "...",
    "pageId": "...",
    "rules": [
      {
        "urlPattern": "**/api/users**",
        "action": "respond",
        "statusCode": 200,
        "responseBody": "{\"users\": []}"
      }
    ]
  }
}
```

### Complex Wait Conditions

```json
{
  "tool": "wait_for_function",
  "input": {
    "sessionId": "...",
    "pageId": "...",
    "script": "() => window.dataLoaded && document.querySelectorAll('.item').length > 0",
    "timeout": 30000
  }
}
```

### Performance Testing

```json
{
  "tool": "get_metrics",
  "input": {
    "sessionId": "...",
    "pageId": "..."
  }
}
```

## Architecture

### Components

- **BrowserManager**: Core browser lifecycle and Playwright integration
- **BrowserTools**: MCP tool handlers that map to BrowserManager methods
- **Types**: TypeScript interfaces for all data structures

### Design Pattern

```
MCP Server (index.ts)
    ↓
BrowserTools (handles tool calls)
    ↓
BrowserManager (Playwright abstraction)
    ↓
Playwright (Browser automation)
```

## Error Handling

All tool calls return a consistent response:

```json
{
  "success": true|false,
  "data": { /* tool-specific data */ },
  "error": "Error message if success=false",
  "metadata": { /* optional metadata */ }
}
```

## Performance Considerations

- Sessions persist until explicitly closed
- Pages are isolated within a session context
- Network interception applies per-page
- JavaScript execution is page-scoped
- Screenshots are memory-intensive; use sparingly in production

## Troubleshooting

### Chrome Not Found

Ensure Chromium is installed:
```bash
npx playwright install chromium
```

### Session/Page Not Found

Verify you're using correct IDs from previous tool calls. IDs are UUIDs returned by creation tools.

### Timeout Errors

Increase timeout values for slower networks:
```json
{
  "navigate": { "timeout": 60000 }
}
```

## API Reference

See `src/types/index.ts` for complete TypeScript interfaces.

## License

ISC
