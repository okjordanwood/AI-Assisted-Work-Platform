const neo4j = require("neo4j-driver");
require("dotenv").config();

const driver = neo4j.driver(
  `bolt://${process.env.NEO4J_HOST || "localhost"}:${
    process.env.NEO4J_PORT || 7687
  }`,
  neo4j.auth.basic(
    process.env.NEO4J_USER || "neo4j",
    process.env.NEO4J_PASSWORD || "knowledge_password"
  )
);

module.exports = driver;
