const fastify = require("fastify")({ logger: true });
const cors = require("@fastify/cors");
const rateLimit = require("@fastify/rate-limit");
const swagger = require("@fastify/swagger");
const swaggerUi = require("@fastify/swagger-ui");

// Register plugins
fastify.register(cors, { origin: true });
fastify.register(rateLimit, { max: 100, timeWindow: "1 minute" });
fastify.register(swagger, {
  swagger: {
    info: {
      title: "AI-Assisted Work Platform API",
      version: "1.0.0",
    },
  },
});
fastify.register(swaggerUi, { routePrefix: "/docs" });

// Register routes
fastify.register(require("./src/routes/auth"), { prefix: "/api/auth" });
fastify.register(require("./src/routes/documents"), {
  prefix: "/api/documents",
});
fastify.register(require("./src/routes/ai"), { prefix: "/api/ai" });

// Start the server
const start = async () => {
  try {
    await fastify.listen({ port: 3000, host: "0.0.0.0" });
    console.log("Server running on http://localhost:3000");
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
