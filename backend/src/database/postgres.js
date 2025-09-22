const { Pool } = require("pg");
require("dotenv").config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || "localhost",
  port: process.env.POSTGRES_PORT || 5432,
  databse: process.env.POSTGRES_DB || "knowledge_platform",
  user: process.env.POSTGRES_USER || "knowledge_user",
  password: process.env.POSTGRES_PASSWORD || "knowledge_password",
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

module.exports = pool;
