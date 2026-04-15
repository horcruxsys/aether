# Stage 1: Build Environment
FROM rust:1.94-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y pkg-config libssl-dev protobuf-compiler curl

# Create a new empty rust project to cache dependencies
WORKDIR /usr/src/aether
COPY . .

# Build the specific high-performance binary natively utilizing release optimizations
RUN cd apps/refinery-core && cargo build --release

# Stage 2: Minimal Runtime Environment
FROM debian:bookworm-slim

# Install runtime dependencies if needed, e.g. for native-tls, although rustls sidesteps it
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Run as non-root user for enterprise security
RUN useradd -ms /bin/bash aether_user
USER aether_user

WORKDIR /app

# Copy the statically compiled heavy lifter from the builder stage
COPY --from=builder /usr/src/aether/target/release/refinery-core /app/refinery-core

# Expose gRPC port for the API control-plane
EXPOSE 50051

# Launch the infinite async processing stream natively 
CMD ["./refinery-core"]
