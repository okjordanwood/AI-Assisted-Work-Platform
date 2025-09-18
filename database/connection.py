import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
import asyncio
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable
import json

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database config class"""

    def __init__(self):
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'knowledge_platform'),
            'user': os.getenv('POSTGRES_USER', 'knowledge_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'knowledge_password'),
        }
        self.neo4j_config = {
            'uri': f"bolt://{os.getenv('NEO4J_HOST', 'localhost')}:{os.getenv('NEO4J_PORT', 7687)}",
            'user': os.getenv('NEO4J_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'knowledge_password'),
            'database': os.getenv('NEO4J_DATABASE', 'neo4j'),
        }

class PostgreSQLManager:
    """PostgreSQL db manager w connection pooling"""

    def __init__(self, config: DatabaseConfig):
        self.config = config.postgres_config
        self.pool: Optional[asyncpg.Pool] = None

    # Create connection pool
    async def create_pool(self, min_size: int = 10, max_size: int = 20):
        try:
            self.pool = await asyncpg.create_pool(
                **self.config,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
            )
            logger.info("PostgreSQL connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise

    # Close connection pool
    async def close_pool(self):
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed.")

    @asynccontextmanager

    # Get db connection from pool
    async def get_connection(self):
        if not self.pool:
            raise RuntimeError("Database pool is not initialized.")

        async with self.pool.acquire() as connection:
            yield connection

    # Execute a query and return results
    async def execute_query(self, query: str, *args) -> Any:
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    # Execute a query and return a single result
    async def execute_one(self, query: str, *args) -> Any:
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)

    # Execute a command and return status
    async def execute_command(self, command: str, *args) -> str:
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)

    # Test db connection
    async def test_connection(self) -> bool:
        try:
            result = await self.execute_one("SELECT 1 as test")
            return result['test'] == 1
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False

class Neo4jManager:
    """Neo4j db manager"""

    def __init__(self, config: DatabaseConfig):
        self.config = config.neo4j_config
        self.driver = None

    # Connect to Neo4j db
    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.config['uri'],
                auth=(self.config['user'], self.config['password'])
            )
            await self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    # Close Neo4j connection
    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed.")

    @asynccontextmanager

    # Get Neo4j connection
    async def get_session(self):
        if not self.driver:
            raise RuntimeError("Neo4j driver is not initialized.")

        async with self.driver.session(database=self.config['database']) as session:
            yield session

    # Execute a Cypher query and return results
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> list:
        async with self.get_session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    # Execute a write Cypher query
    async def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> list:
        async with self.get_session() as session:
            result = await session.run(query, parameters or {})
            await session.commit()
            return await result.data()

    # Test Neo4j connection
    async def test_connection(self) -> bool:
        try:
            result = await self.execute_query("RETURN 1 as test")
            return len(result) > 0 and result[0]['test'] == 1
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False

class DatabaseManager:
    """Main database manager coordinating PostgreSQL and Neo4j"""

    def __init__(self):
        self.config = DatabaseConfig()
        self.postgres = PostgreSQLManager(self.config)
        self.neo4j = Neo4jManager(self.config)
        self._initialized = False

    # Initialize both db connections
    async def initialize(self):
        if self._initialized:
            return

        try:
            # Initialize PostgreSQL
            await self.postgres.create_pool()
            # Initialize Neo4j
            await self.neo4j.connect()

            # Test connections
            postgres_ok = await self.postgres.test_connection()
            neo4j_ok = await self.neo4j.test_connection()

            if not postgres_ok or not neo4j_ok:
                raise RuntimeError("One or more database connections failed.")

            self._initialized = True
            logger.info("All database connections initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            await self.cleanup()
            raise

    # Cleanup db connections
    async def cleanup(self):
        try:
            await self.postgres.close_pool()
            await self.neo4j.close()
            self._initialized = False
            logger.info("Database manager cleaned up successfully.")
        except Exception as e:
            logger.error(f"Error during database manager cleanup: {e}")

    # Check health of both dbs
    async def health_check(self) -> Dict[str, bool]:
        return {
            'postgres': await self.postgres.test_connection(),
            'neo4j': await self.neo4j.test_connection()
        }

# Global db manager instance
db_manager = DatabaseManager()

# Get the global db manager instance
async def get_database_manager() -> DatabaseManager:
    if not db_manager._initialized:
        await db_manager.initialize()
    return db_manager