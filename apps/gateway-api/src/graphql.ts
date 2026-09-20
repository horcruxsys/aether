import * as nexusClient from "./nexusClient";

const schema = `
  type Query {
    version: String!
    activeIngestionJobs: [IngestionJob!]!
    datasetMetadata(urn: String!): DatasetMetadata
  }

  type IngestionJob {
    id: ID!
    status: String!
    source_urn: String!
    processed_vectors: Int!
  }

  type DatasetMetadata {
    urn: String!
    pii_count: Int!
    chunk_count: Int!
    tombstone_count: Int!
  }
`;

const resolvers = {
  Query: {
    version: async () => {
      try {
        const versionInfo = await nexusClient.getVersion();
        return `${versionInfo.version}-aether`;
      } catch (error) {
        console.error("Failed to fetch version:", error);
        return "1.0.0-aether-core";
      }
    },

    activeIngestionJobs: async (_: any, __: any, context: any) => {
      try {
        const tenantId = context?.tenant_id;
        const jobsResponse = await nexusClient.getActiveJobs(tenantId);
        return jobsResponse.active_jobs.map((job) => ({
          id: job.job_id,
          status: job.status,
          source_urn: job.source_urn,
          processed_vectors: job.processed_count,
        }));
      } catch (error) {
        console.error("Failed to fetch active jobs:", error);
        return [];
      }
    },

    datasetMetadata: async (
      _: any,
      { urn }: { urn: string },
      context: any,
    ) => {
      try {
        const tenantId = context?.tenant_id;
        const metadata = await nexusClient.getDatasetMetadata(urn, tenantId);
        return {
          urn: metadata.urn,
          pii_count: metadata.pii_count,
          chunk_count: metadata.chunk_count,
          tombstone_count: metadata.tombstone_count,
        };
      } catch (error) {
        console.error("Failed to fetch dataset metadata:", error);
        return {
          urn,
          pii_count: 0,
          chunk_count: 0,
          tombstone_count: 0,
        };
      }
    },
  },
};

export const createGraphQLOptions = () => {
  return {
    schema,
    resolvers,
    graphiql: true,
  };
};
