# Browser MCP - Complete Usage Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Workflow](#basic-workflow)
3. [Common Scenarios](#common-scenarios)
4. [Advanced Patterns](#advanced-patterns)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Getting Started

### Installation

```bash
# Install the package
pnpm add @aether/browser-mcp

# Or clone from repo
cd packages/browser-mcp
pnpm install
```

### Starting the Server

```bash
# Development mode with hot reload
pnpm dev

# Production build and run
pnpm build
node dist/index.js
```

The server outputs:
```
🚀 Browser Automation MCP Server is running...
```

Now it's ready to receive MCP tool calls.

## Basic Workflow

### 1. Create a Session

Every workflow starts with creating a browser session:

```json
{
  "name": "create_session",
  "arguments": {
    "headless": true,
    "viewport": {
      "width": 1280,
      "height": 720
    }
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

Save this `sessionId` - you'll use it for all subsequent operations.

### 2. Create a Page

Each session can have multiple pages. Create one:

```json
{
  "name": "create_page",
  "arguments": {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "pageId": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

### 3. Navigate to a Website

```json
{
  "name": "navigate",
  "arguments": {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "pageId": "550e8400-e29b-41d4-a716-446655440001",
    "url": "https://example.com",
    "waitUntil": "load",
    "timeout": 30000
  }
}
```

### 4. Interact with Elements

Query an element:
```json
{
  "name": "query_selector",
  "arguments": {
    "sessionId": "...",
    "pageId": "...",
    "selector": "button.submit"
  }
}
```

Click it:
```json
{
  "name": "click",
  "arguments": {
    "sessionId": "...",
    "pageId": "...",
    "selector": "button.submit"
  }
}
```

### 5. Take a Screenshot

```json
{
  "name": "screenshot",
  "arguments": {
    "sessionId": "...",
    "pageId": "...",
    "fullPage": false
  }
}
```

Response includes base64-encoded PNG:
```json
{
  "success": true,
  "data": {
    "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
  }
}
```

### 6. Close Resources

Close page:
```json
{
  "name": "close_page",
  "arguments": {
    "sessionId": "...",
    "pageId": "..."
  }
}
```

Close session:
```json
{
  "name": "close_session",
  "arguments": {
    "sessionId": "..."
  }
}
```

## Common Scenarios

### Scenario 1: Login Form

```javascript
// 1. Create session
const { sessionId } = await createSession({ headless: true });

// 2. Create page
const { pageId } = await createPage({ sessionId });

// 3. Navigate to login page
await navigate({
  sessionId,
  pageId,
  url: "https://example.com/login"
});

// 4. Fill email field
await fill({
  sessionId,
  pageId,
  selector: "input[name='email']",
  text: "user@example.com"
});

// 5. Fill password field
await fill({
  sessionId,
  pageId,
  selector: "input[name='password']",
  text: "secretpassword"
});

// 6. Click submit button
await click({
  sessionId,
  pageId,
  selector: "button[type='submit']"
});

// 7. Wait for redirect
await waitForNavigation({
  sessionId,
  pageId,
  timeout: 10000
});

// 8. Take screenshot of dashboard
const { screenshot } = await screenshot({ sessionId, pageId });

// 9. Cleanup
await closePage({ sessionId, pageId });
await closeSession({ sessionId });
```

### Scenario 2: Search Results

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

// Navigate to search page
await navigate({
  sessionId,
  pageId,
  url: "https://example.com/search"
});

// Fill search box
await fill({
  sessionId,
  pageId,
  selector: "input.search-box",
  text: "laptop"
});

// Click search button
await click({
  sessionId,
  pageId,
  selector: "button.search"
});

// Wait for results to load
await waitForSelector({
  sessionId,
  pageId,
  selector: ".search-results",
  timeout: 10000
});

// Get all result elements
const { elements, count } = await querySelectors({
  sessionId,
  pageId,
  selector: ".search-result"
});

console.log(`Found ${count} results`);

// Extract data from results using JavaScript
const data = await executeScript({
  sessionId,
  pageId,
  script: `
    return Array.from(document.querySelectorAll('.search-result')).map(el => ({
      title: el.querySelector('.title')?.textContent,
      price: el.querySelector('.price')?.textContent,
      url: el.querySelector('a')?.href
    }));
  `
});

console.log(data.result);
```

### Scenario 3: Form with Dynamic Content

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

await navigate({
  sessionId,
  pageId,
  url: "https://example.com/form"
});

// Select dropdown option
await select({
  sessionId,
  pageId,
  selector: "select.country",
  value: "US"
});

// Wait for dependent field to appear
await waitForSelector({
  sessionId,
  pageId,
  selector: "select.state",
  timeout: 5000
});

// Fill dependent field
await fill({
  sessionId,
  pageId,
  selector: "input.address",
  text: "123 Main St"
});

// Check checkbox
await check({
  sessionId,
  pageId,
  selector: "input[type='checkbox'].agree"
});

// Submit form
await click({
  sessionId,
  pageId,
  selector: "button.submit"
});

// Wait for success message
await waitForSelector({
  sessionId,
  pageId,
  selector: ".success-message",
  timeout: 10000
});
```

### Scenario 4: Pagination

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

const allResults = [];

for (let page = 1; page <= 5; page++) {
  await navigate({
    sessionId,
    pageId,
    url: `https://example.com/items?page=${page}`
  });

  // Get current page results
  const { elements } = await querySelectors({
    sessionId,
    pageId,
    selector: ".item"
  });

  // Extract data
  const pageData = await executeScript({
    sessionId,
    pageId,
    script: `
      return Array.from(document.querySelectorAll('.item')).map(el => ({
        name: el.querySelector('.name')?.textContent,
        price: el.querySelector('.price')?.textContent
      }));
    `
  });

  allResults.push(...pageData.result);
  
  console.log(`Page ${page}: ${pageData.result.length} items`);
}

console.log(`Total items: ${allResults.length}`);
```

### Scenario 5: File Upload

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

await navigate({
  sessionId,
  pageId,
  url: "https://example.com/upload"
});

// Upload file
await uploadFile({
  sessionId,
  pageId,
  selector: "input[type='file']",
  filePath: "/path/to/file.pdf"
});

// Click upload button
await click({
  sessionId,
  pageId,
  selector: "button.upload"
});

// Wait for upload to complete
await waitForSelector({
  sessionId,
  pageId,
  selector: ".upload-success",
  timeout: 30000
});
```

### Scenario 6: Handling Pop-ups and Modals

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

await navigate({
  sessionId,
  pageId,
  url: "https://example.com"
});

// Close cookie banner
try {
  await click({
    sessionId,
    pageId,
    selector: ".cookie-banner .close"
  });
} catch (e) {
  console.log("No cookie banner found");
}

// Handle modal dialog
const isModalVisible = await executeScript({
  sessionId,
  pageId,
  script: "return !!document.querySelector('.modal:not([style*='display: none'])')"
});

if (isModalVisible.result) {
  await click({
    sessionId,
    pageId,
    selector: ".modal .close-btn"
  });
}
```

## Advanced Patterns

### Pattern 1: Network Request Mocking

Mock API responses to test error scenarios:

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

// Set up request interception
await interceptRequests({
  sessionId,
  pageId,
  rules: [
    {
      urlPattern: "**/api/users**",
      action: "respond",
      statusCode: 500,
      responseBody: '{"error": "Server error"}'
    }
  ]
});

await navigate({
  sessionId,
  pageId,
  url: "https://example.com"
});

// Page will handle API error
const { screenshot } = await screenshot({ sessionId, pageId });
```

### Pattern 2: Performance Testing

Measure page load performance:

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

await navigate({
  sessionId,
  pageId,
  url: "https://example.com",
  waitUntil: "networkidle"
});

const metrics = await getMetrics({
  sessionId,
  pageId
});

const loadTime = metrics.data.loadEventEnd - metrics.data.navigationStart;
console.log(`Page load time: ${loadTime}ms`);
```

### Pattern 3: Complex Multi-Step Flow

```javascript
const { sessionId } = await createSession();
const pages = [];

// Open multiple pages
for (let i = 0; i < 3; i++) {
  const { pageId } = await createPage({ sessionId });
  pages.push(pageId);
}

// Perform different actions on each page
await navigate({
  sessionId,
  pageId: pages[0],
  url: "https://example.com/page1"
});

await navigate({
  sessionId,
  pageId: pages[1],
  url: "https://example.com/page2"
});

// Interact with first page while second page loads
await click({
  sessionId,
  pageId: pages[0],
  selector: "button.action"
});

// Get data from both pages
const page1Data = await getPageSnapshot({
  sessionId,
  pageId: pages[0]
});

const page2Data = await getPageSnapshot({
  sessionId,
  pageId: pages[1]
});

console.log("Page 1:", page1Data.data.title);
console.log("Page 2:", page2Data.data.title);
```

### Pattern 4: Waiting for Custom Conditions

```javascript
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

await navigate({
  sessionId,
  pageId,
  url: "https://example.com"
});

// Wait for JavaScript condition to be true
await waitForFunction({
  sessionId,
  pageId,
  script: `
    // Wait for React app to be ready
    return window.__APP_READY__ === true &&
           document.querySelectorAll('[data-loaded]').length > 0
  `,
  timeout: 30000
});

console.log("App is ready!");
```

## Troubleshooting

### Issue: "Session not found"

```
Error: Session <id> not found
```

**Solution**: Session IDs expire or need to be created fresh. Always create a new session:

```javascript
const { sessionId } = await createSession();
```

### Issue: "Timeout waiting for selector"

```
Error: Timeout waiting for selector '.my-element'
```

**Solutions**:
1. Check selector is correct
2. Increase timeout value
3. Wait for page to load first
4. Check for visibility wait

```javascript
// Use visibility wait
await waitForSelector({
  sessionId,
  pageId,
  selector: ".my-element",
  timeout: 60000 // Increase timeout
});
```

### Issue: "Navigation timeout"

```
Error: Timeout during navigation
```

**Solutions**:
1. Website is slow - increase timeout
2. Page loads with JavaScript - use `waitUntil: "networkidle"`
3. Check network connectivity
4. Try without wait

```javascript
await navigate({
  sessionId,
  pageId,
  url: "https://slow-site.com",
  waitUntil: "networkidle",
  timeout: 60000
});
```

### Issue: Element not interactive

```
Error: Element is not visible
```

**Solutions**:
1. Scroll element into view
2. Wait for element to be visible
3. Handle overlays/modals
4. Use mouse position-based click

```javascript
// Scroll to element
await executeScript({
  sessionId,
  pageId,
  script: `
    document.querySelector('.my-element').scrollIntoView();
  `
});

// Then click
await click({
  sessionId,
  pageId,
  selector: ".my-element"
});
```

## Best Practices

### 1. Resource Management

Always clean up resources:

```javascript
try {
  // Your automation code
} finally {
  // Always cleanup
  await closePage({ sessionId, pageId });
  await closeSession({ sessionId });
}
```

### 2. Error Handling

Implement proper error handling:

```javascript
try {
  const { sessionId } = await createSession();
  // ... operations
} catch (error) {
  console.error("Automation failed:", error.message);
  // Cleanup on error
}
```

### 3. Timeouts

Be reasonable with timeouts:

```javascript
// Too short - might fail on slow networks
await navigate({ ..., timeout: 1000 }); // ❌

// Reasonable - 30 seconds for most pages
await navigate({ ..., timeout: 30000 }); // ✅

// Very long - for problematic sites
await navigate({ ..., timeout: 120000 }); // ✅
```

### 4. Selectors

Use specific, stable selectors:

```javascript
// Too generic
await click({ selector: "button" }); // ❌

// Data attributes are stable
await click({ selector: "button[data-testid='submit']" }); // ✅

// CSS classes might change
await click({ selector: ".btn.btn-primary.mt-2" }); // ⚠️

// IDs are most stable
await click({ selector: "#submit-btn" }); // ✅
```

### 5. Wait Strategies

Use appropriate waits:

```javascript
// Wait for element to appear
await waitForSelector({ selector: ".results" });

// Wait for dynamic content
await waitForFunction({
  script: "return !!window.dataReady"
});

// Wait for navigation
await waitForNavigation();

// Simple delay as last resort
await waitForTimeout({ timeout: 1000 });
```

### 6. Testing Edge Cases

```javascript
// Handle missing elements gracefully
try {
  await click({ selector: ".optional-button" });
} catch (e) {
  console.log("Button not found, continuing...");
}

// Check element state before interaction
const element = await querySelector({
  sessionId,
  pageId,
  selector: ".my-element"
});

if (element.visible && element.enabled) {
  await click({ selector: ".my-element" });
}
```

### 7. Performance

Optimize performance:

```javascript
// Reuse session and pages when possible
const { sessionId } = await createSession();
const { pageId } = await createPage({ sessionId });

// Do multiple operations
await navigate({ sessionId, pageId, url: "..." });
await click({ sessionId, pageId, selector: "..." });
// ... more operations

// Don't create new session for each operation

// Block unnecessary resources
await blockRequests({
  sessionId,
  pageId,
  patterns: ["*.google-analytics.com/**", "*.ads.com/**"]
});
```

## Summary

The Browser MCP provides a complete, enterprise-grade browser automation solution. Key points:

- ✅ Simple MCP protocol for AI agents
- ✅ Comprehensive tool set (55+ tools)
- ✅ Robust error handling
- ✅ Performance monitoring
- ✅ Network control
- ✅ Storage management
- ✅ Full Playwright integration

Use it for testing, scraping, RPA, and any browser-based automation needs!
