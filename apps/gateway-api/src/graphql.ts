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
    tombstone_count: Int!
  }
`;

const resolvers = {
  Query: {
    version: async () => "1.0.0-aether-core",
    activeIngestionJobs: async () => [
      {
        id: "job-101",
        status: "RUNNING",
        source_urn: "cdc://postgres-legacy",
        processed_vectors: 43210,
      },
    ],
    datasetMetadata: async (_: any, { urn }: { urn: String }) => ({
      urn,
      pii_count: 54,
      tombstone_count: 12,
    }),
  },
};

export const createGraphQLOptions = () => {
  return {
    schema,
    resolvers,
    graphiql: true,
  };
};
