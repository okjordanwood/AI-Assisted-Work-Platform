import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseManager
import logging

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def test_postgresql_operations(db_manager):
    print("\n=== Testing PostgreSQL Operations ===")
    
    try:
        # Test basic query
        result = await db_manager.postgres.execute_one("SELECT version()")
        print(f"PostgreSQL version: {result['version']}")

        # Test pgvector extension
        result = await db_manager.postgres.execute_one("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        if result:
            print("pgvector extension is installed")
        else:
            print("pgvector extension is not installed")

        # Test custom types
        result = await db_manager.postgres.execute_one("SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')")
        if result:
            print(f"Custom types created: {[row['enumlabel'] for row in await db_manager.postgres.execute_query('SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = \'user_role\')')]}")

        # Test tables exist
        tables = await db_manager.postgres.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        print(f"Tables created: {[table['table_name'] for table in tables]}")
        
        # Test default data
        org_count = await db_manager.postgres.execute_one("SELECT COUNT(*) as count FROM organizations")
        user_count = await db_manager.postgres.execute_one("SELECT COUNT(*) as count FROM users")
        print(f"Default data: {org_count['count']} organizations, {user_count['count']} users")

        return True

    except Exception as e:
        print(f"PostgreSQL test failed: {e}")
        return False

async def test_neo4j_operations(db_manager):
    print("\n=== Testing Neo4j Operations ===")

    try:
        # Test basic query
        result = await db_manager.neo4j.execute_query("RETURN 'Neo4j is working!' as message")
        print(f"Neo4j message: {result[0]['message']}")
        
        # Test APOC procedures
        try:
            result = await db_manager.neo4j.execute_query("CALL apoc.version()")
            print(f"APOC procedures available: {result[0]['version']}")
        except Exception as e:
            print(f"APOC procedures not available: {e}")
        
        # Test constraints and indexes
        constraints = await db_manager.neo4j.execute_query("SHOW CONSTRAINTS")
        print(f"Constraints created: {len(constraints)}")

        indexes = await db_manager.neo4j.execute_query("SHOW INDEXES")
        print(f"Indexes created: {len(indexes)}")

        # Test initial nodes
        node_count = await db_manager.neo4j.execute_query("MATCH (n) RETURN count(n) as count")
        print(f"Initial nodes created: {node_count[0]['count']}")

        # Test relationships
        rel_count = await db_manager.neo4j.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        print(f"Initial relationships created: {rel_count[0]['count']}")

        return True
        
    except Exception as e:
        print(f"Neo4j test failed: {e}")
        return False

async def test_vector_operations(db_manager):
    print("\n=== Testing Vector Operations ===")

    try:
        # Test vector creation and similarity
        await db_manager.postgres.execute_command("""
            CREATE TEMP TABLE test_vectors (
                id SERIAL PRIMARY KEY,
                embedding vector(3)
            )
        """)
        
        # Insert test vectors
        await db_manager.postgres.execute_command("""
            INSERT INTO test_vectors (embedding) VALUES 
            ('[1,2,3]'),
            ('[1,2,4]'),
            ('[2,3,4]')
        """)
        
        # Test cosine similarity
        result = await db_manager.postgres.execute_query("""
            SELECT id, embedding <=> '[1,2,3]' as distance
            FROM test_vectors
            ORDER BY distance
        """)
        
        print("Vector similarity test:")
        for row in result:
            print(f"   Vector {row['id']}: distance = {row['distance']:.4f}")
        
        # Clean up
        await db_manager.postgres.execute_command("DROP TABLE test_vectors")
        
        return True
        
    except Exception as e:
        print(f"Vector operations test failed: {e}")
        return False

async def main():
    print("Starting Database Connection Tests")
    print("=" * 50)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    db_manager = DatabaseManager()
    
    try:
        # Initialize database connections
        print("📡 Initializing database connections...")
        await db_manager.initialize()
        
        # Run tests
        postgres_ok = await test_postgresql_operations(db_manager)
        neo4j_ok = await test_neo4j_operations(db_manager)
        vector_ok = await test_vector_operations(db_manager)
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"   PostgreSQL: {'PASS' if postgres_ok else 'FAIL'}")
        print(f"   Neo4j: {'PASS' if neo4j_ok else 'FAIL'}")
        print(f"   Vector Operations: {'PASS' if vector_ok else 'FAIL'}")

        if all([postgres_ok, neo4j_ok, vector_ok]):
            print("\nAll database tests passed! Your setup is ready.")
            return 0
        else:
            print("\nSome tests failed. Please check the configuration.")
            return 1
            
    except Exception as e:
        print(f"\nTest initialization failed: {e}")
        return 1
        
    finally:
        # Cleanup
        await db_manager.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)