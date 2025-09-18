// Create constraints and indexes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT workspace_id_unique IF NOT EXISTS FOR (w:Workspace) REQUIRE w.id IS UNIQUE;
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_email_index IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX user_username_index IF NOT EXISTS FOR (u:User) ON (u.username);
CREATE INDEX document_title_index IF NOT EXISTS FOR (d:Document) ON (d.title);
CREATE INDEX document_slug_index IF NOT EXISTS FOR (d:Document) ON (d.slug);
CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name);
CREATE INDEX concept_type_index IF NOT EXISTS FOR (c:Concept) ON (c.type);

// Create full-text search indexes
CREATE FULLTEXT INDEX document_content_fulltext IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content];
CREATE FULLTEXT INDEX concept_description_fulltext IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.description];

// Create initial nodes for the knowledge graph structure
// These will be populated when documents are created/updated

// Create relationship types and their properties
// Document relationships
// - REFERENCES: Document A references Document B
// - CONTAINS: Document A contains concept B
// - SIMILAR_TO: Document A is similar to Document B
// - VERSION_OF: Document A is a version of Document B
// - PARENT_OF: Document A is a parent of Document B (hierarchical)

// Concept relationships
// - RELATED_TO: Concept A is related to Concept B
// - PART_OF: Concept A is part of Concept B
// - SYNONYM_OF: Concept A is a synonym of Concept B
// - OPPOSITE_OF: Concept A is opposite to Concept B

// User relationships
// - CREATED: User created Document/Concept
// - EDITED: User edited Document/Concept
// - VIEWED: User viewed Document/Concept
// - COLLABORATED_WITH: User collaborated with User

// Workspace relationships
// - CONTAINS: Workspace contains Document
// - BELONGS_TO: Document belongs to Workspace

// Create APOC procedures for advanced graph operations
// These will be used for:
// - Finding orphaned documents
// - Calculating document centrality
// - Detecting knowledge gaps
// - Suggesting content improvements
// - Building knowledge topology

// Example queries that will be available:

// Find orphaned documents (documents with no incoming references)
// MATCH (d:Document) 
// WHERE NOT (d)<-[:REFERENCES]-(:Document) 
// RETURN d.title, d.slug

// Find most referenced documents
// MATCH (d:Document)<-[:REFERENCES]-(ref:Document)
// RETURN d.title, count(ref) as reference_count
// ORDER BY reference_count DESC

// Find knowledge gaps (concepts mentioned but not documented)
// MATCH (d:Document)-[:CONTAINS]->(c:Concept)
// WHERE NOT (c)<-[:CONTAINS]-(:Document)
// RETURN c.name, collect(d.title) as mentioned_in

// Find similar documents based on shared concepts
// MATCH (d1:Document)-[:CONTAINS]->(c:Concept)<-[:CONTAINS]-(d2:Document)
// WHERE d1 <> d2
// RETURN d1.title, d2.title, count(c) as shared_concepts
// ORDER BY shared_concepts DESC

// Calculate document centrality (PageRank-like algorithm)
// CALL gds.pageRank.stream('knowledge-graph')
// YIELD nodeId, score
// RETURN gds.util.asNode(nodeId).title as document, score
// ORDER BY score DESC

// Create initial system nodes
CREATE (system:System {
    id: 'system',
    name: 'Knowledge Platform System',
    description: 'Root system node for the knowledge platform',
    created_at: datetime(),
    version: '1.0.0'
});

// Create a root organization node
CREATE (rootOrg:Organization {
    id: 'default-org',
    name: 'Default Organization',
    description: 'Default organization for the knowledge platform',
    slug: 'default',
    created_at: datetime()
});

// Create a root workspace node
CREATE (rootWorkspace:Workspace {
    id: 'default-workspace',
    name: 'General',
    description: 'General workspace for documentation',
    slug: 'general',
    created_at: datetime()
});

// Create relationships
CREATE (rootOrg)-[:CONTAINS]->(rootWorkspace);
CREATE (system)-[:MANAGES]->(rootOrg);

// Create some initial concept categories
CREATE (category1:Concept {
    id: 'concept-category-general',
    name: 'General Concepts',
    type: 'category',
    description: 'General knowledge concepts',
    created_at: datetime()
});

CREATE (category2:Concept {
    id: 'concept-category-technical',
    name: 'Technical Concepts',
    type: 'category',
    description: 'Technical knowledge concepts',
    created_at: datetime()
});

CREATE (category3:Concept {
    id: 'concept-category-process',
    name: 'Process Concepts',
    type: 'category',
    description: 'Process and workflow concepts',
    created_at: datetime()
});

// Link categories to workspace
CREATE (rootWorkspace)-[:CONTAINS]->(category1);
CREATE (rootWorkspace)-[:CONTAINS]->(category2);
CREATE (rootWorkspace)-[:CONTAINS]->(category3);

// Create relationships between categories
CREATE (category1)-[:RELATED_TO {strength: 0.7}]->(category2);
CREATE (category2)-[:RELATED_TO {strength: 0.6}]->(category3);
CREATE (category3)-[:RELATED_TO {strength: 0.5}]->(category1);
