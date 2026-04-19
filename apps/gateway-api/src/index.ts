import Fastify from "fastify";
import {
  serializerCompiler,
  validatorCompiler,
  jsonSchemaTransform,
} from "fastify-type-provider-zod";
import { z } from "zod";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import path from "path";
import { semanticRoutes } from "./routes/semantic.js";
import mercurius from "mercurius";
import fastifyWebsocket from "@fastify/websocket";
import { createGraphQLOptions } from "./graphql.js";
import { webrtcRoutes } from "./webrtc.js";
import { billableInterceptor } from "./billing.js";

// Load gRPC definition
const PROTO_PATH = path.resolve(
  __dirname,
  "../../../packages/semantic-spec/proto/aether.proto",
);
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});
const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
const aether = protoDescriptor.aether;

// Create gRPC client
const refineryClient = new aether.RefineryService(
  "localhost:50051",
  grpc.credentials.createInsecure(),
);

const fastify = Fastify({
  logger: true,
});

fastify.setValidatorCompiler(validatorCompiler);
fastify.setSerializerCompiler(serializerCompiler);

fastify.get("/health", async (request, reply) => {
  return { status: "ok", timestamp: new Date().toISOString() };
});

fastify.addHook("preHandler", billableInterceptor);

fastify.register(fastifyWebsocket);
fastify.register(mercurius, createGraphQLOptions());
fastify.register(webrtcRoutes);

fastify.register(async function (fastify) {
  fastify.get("/ws/telemetry", { websocket: true }, (connection, req) => {
    connection.socket.on("message", (message: any) => {
      connection.socket.send(
        JSON.stringify({ event: "telemetry_diff", timestamp: Date.now() }),
      );
    });
  });
});

fastify.register(semanticRoutes);

const MigrationRequestSchema = z.object({
  source: z.string().url(),
  destination: z.string(),
});

fastify.post(
  "/migrate",
  {
    schema: {
      body: MigrationRequestSchema,
    },
  },
  async (request, reply) => {
    const { source, destination } = request.body as any;

    return new Promise((resolve, reject) => {
      refineryClient.StartMigration(
        { source, destination, options: {} },
        (err: any, response: any) => {
          if (err) {
            request.log.error(err);
            reply.status(500).send({ error: "gRPC call failed" });
            resolve(null);
          } else {
            resolve({
              success: true,
              job_id: response.job_id,
              status: response.status,
              message: response.message,
            });
          }
        },
      );
    });
  },
);

const start = async () => {
  try {
    await fastify.listen({ port: 3000, host: "0.0.0.0" });
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

if (process.env.NODE_ENV !== "test") {
  start();
}

export { fastify };
