# Aether Integration Tests

End-to-end integration tests for the Aether autonomous data fabric pipeline.

## Prerequisites

- Docker and Docker Compose installed
- Node.js 22+ and pnpm installed
- Rust toolchain (for building refinery-core)
- Python 3.10+ with uv (for other packages)

## Running Tests

### Local Testing with Docker Compose

```bash
# Start all services
docker-compose up -d --wait

# Run integration tests
pnpm turbo run integration

# Stop services
docker-compose down
```

### Full CI Pipeline

```bash
# Lint, type-check, build, and test
pnpm turbo lint check-types build test integration
```

### Individual Service Testing

```bash
# Test just nexus-manager routes
pnpm turbo run integration -- tests/integration/e2e.test.ts -t "Nexus Manager Routes"

# Test just GraphQL resolvers
pnpm turbo run integration -- tests/integration/e2e.test.ts -t "GraphQL"
```

## Test Coverage

The e2e test suite covers:

1. **Service Health Checks** — Verify all services are running
2. **GraphQL Resolvers** — version, activeIngestionJobs, datasetMetadata
3. **Vector Projection (Semantic Search)** — Text and embedding-based search
4. **Graph RAG Queries** — Graph traversal with optional node filtering
5. **Nexus Manager Routes** — Direct REST API testing
6. **Error Handling** — Malformed requests, missing parameters

## Debugging

### View service logs
```bash
docker-compose logs nexus-manager
docker-compose logs gateway-api
docker-compose logs refinery-core
```

### Test a single endpoint
```bash
# Check nexus-manager health
curl http://localhost:8000/health

# Query gateway-api GraphQL
curl -X POST http://localhost:3000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ version }"}'

# Call vector search
curl -X POST http://localhost:3000/api/semantic/vector-projection \
  -H "Content-Type: application/json" \
  -d '{
    "text": "customer data",
    "threshold": 0.5,
    "top_k": 5
  }'
```

### Vitest UI
```bash
pnpm turbo run integration -- --ui
```

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests against `main` or `develop`

See `.github/workflows/ci.yml` for the full pipeline.

## Notes

- Tests assume services are healthy and reachable
- Integration tests are non-destructive (read-only operations)
- Docker Compose provides embedded Qdrant; production uses remote Qdrant
- Timeout: 10 seconds per request, 30 seconds per condition wait
