# Multi-stage Dockerfile for gateway-api
FROM node:22-alpine AS builder

WORKDIR /app

# Copy workspace files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/gateway-api/ ./apps/gateway-api/
COPY packages/ ./packages/

# Install pnpm
RUN npm install -g pnpm@9.0.0

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build gateway-api
RUN pnpm --filter gateway-api build

# Runtime stage
FROM node:22-alpine

WORKDIR /app

# Copy built application from builder
COPY --from=builder /app/apps/gateway-api/dist ./dist/
COPY --from=builder /app/apps/gateway-api/package.json ./

# Install minimal runtime dependencies (skip devDependencies)
RUN npm install --production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

ENV NODE_ENV=production

CMD ["node", "dist/index.js"]
