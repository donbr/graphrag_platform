# Neo4j Aura Setup for GraphRAG Platform

This notebook guides you through setting up the required database objects in Neo4j Aura for the GraphRAG platform. We'll:
1. Connect to the database
2. Create necessary constraints and indexes
3. Verify the setup and add test data
4. Validate functionality

## Prerequisites
- Neo4j Aura Enterprise account
- Database connection details
- Required Python packages

## Install Required Packages

```python
# Install required packages if not already installed
!pip install neo4j python-dotenv pandas numpy
```

## Import Dependencies and Load Environment Variables

```python
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import logging
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database credentials
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

print(f"Using database URI: {NEO4J_URI}")
```

## Create Enhanced Database Connection Helper

```python
class Neo4jConnection:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        if self.driver is not None:
            self.driver.close()
            
    def verify_connectivity(self):
        self.driver.verify_connectivity()
        
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
        
    def run_query_to_df(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            records = list(result)
            if not records:
                return pd.DataFrame()
            return pd.DataFrame([r.values() for r in records], columns=result.keys())
            
    def check_schema_compatibility(self):
        """Check if existing schema is compatible with GraphRAG"""
        query = """
        CALL db.schema.visualization()
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        return self.run_query_to_df(query)
    
    def get_database_stats(self):
        """Get detailed database statistics"""
        query = """
        CALL apoc.meta.stats()
        YIELD nodeCount, relCount, labels, relTypes
        RETURN nodeCount, relCount, labels, relTypes
        """
        return self.run_query_to_df(query)
```

## Connect and Test Database

```python
# Create connection
conn = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

try:
    # Test connectivity
    conn.verify_connectivity()
    print("Successfully connected to Neo4j Aura!")
    
    # Get database info
    info_df = conn.run_query_to_df("""
    CALL dbms.components()
    YIELD name, versions, edition
    RETURN name, versions, edition
    """)
    
    display(info_df)
    
    # Check existing schema
    schema_df = conn.check_schema_compatibility()
    display(schema_df)
    
except Exception as e:
    print(f"Connection failed: {str(e)}")
```

## Clean Up Existing Data (Optional)

Only run this if you need to remove existing data that might conflict with GraphRAG.

```python
cleanup_query = """
MATCH (n)
WHERE NOT n:Content AND NOT n:Speaker AND NOT n:Topic
DELETE n
"""

try:
    conn.run_query(cleanup_query)
    print("Cleanup completed successfully")
except Exception as e:
    print(f"Cleanup error: {str(e)}")
```

## Create Constraints

```python
constraints = [
    """
    CREATE CONSTRAINT content_id IF NOT EXISTS
    FOR (n:Content) 
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT speaker_id IF NOT EXISTS
    FOR (n:Speaker) 
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT topic_id IF NOT EXISTS
    FOR (n:Topic) 
    REQUIRE n.id IS UNIQUE
    """
]

for constraint in constraints:
    try:
        conn.run_query(constraint)
        print(f"Successfully created constraint")
    except Exception as e:
        print(f"Error creating constraint: {str(e)}")

# Verify constraints
constraints_df = conn.run_query_to_df("""
SHOW CONSTRAINTS
""")

display(constraints_df)
```

## Create Vector Index

```python
vector_indexes = [
    """
    CREATE VECTOR INDEX video_content IF NOT EXISTS
    FOR (n:Content) 
    ON (n.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 3072,
            `vector.similarity_function`: 'cosine'
        }
    }
    """
]

for index in vector_indexes:
    try:
        conn.run_query(index)
        print(f"Successfully created vector index")
    except Exception as e:
        print(f"Error creating vector index: {str(e)}")

# Verify vector indexes
vector_indexes_df = conn.run_query_to_df("""
SHOW INDEXES
WHERE type = 'VECTOR'
""")

display(vector_indexes_df)
```

## Create Full-text Index

```python
fulltext_indexes = [
    """
    CREATE FULLTEXT INDEX video_text IF NOT EXISTS
    FOR (n:Content)
    ON EACH [n.title, n.text]
    """
]

for index in fulltext_indexes:
    try:
        conn.run_query(index)
        print(f"Successfully created full-text index")
    except Exception as e:
        print(f"Error creating full-text index: {str(e)}")

# Verify full-text indexes
fulltext_indexes_df = conn.run_query_to_df("""
SHOW INDEXES
WHERE type = 'FULLTEXT'
""")

display(fulltext_indexes_df)
```

## Create Additional Indexes

```python
indexes = [
    """
    CREATE INDEX content_title IF NOT EXISTS
    FOR (n:Content) 
    ON (n.title)
    """,
    """
    CREATE INDEX content_type IF NOT EXISTS
    FOR (n:Content) 
    ON (n.type)
    """,
    """
    CREATE INDEX speaker_name IF NOT EXISTS
    FOR (n:Speaker) 
    ON (n.name)
    """
]

for index in indexes:
    try:
        conn.run_query(index)
        print(f"Successfully created index")
    except Exception as e:
        print(f"Error creating index: {str(e)}")

# Verify all indexes
all_indexes_df = conn.run_query_to_df("""
SHOW INDEXES
""")

display(all_indexes_df)
```

## Add Sample Test Data

```python
# Create a test content node with proper embedding
sample_content = """
CREATE (c:Content {
    id: 'test-content-1',
    title: 'Test Content',
    text: 'This is a test content item for GraphRAG validation',
    type: 'test',
    embedding: $embedding
})
RETURN c
"""

try:
    # Create zero vector with correct dimensions
    test_embedding = np.zeros(3072).tolist()
    conn.run_query(sample_content, parameters={"embedding": test_embedding})
    print("Successfully created test content")
except Exception as e:
    print(f"Error creating test content: {str(e)}")
```

## Verify Database Setup

```python
# Enhanced test queries with proper vector testing
test_queries = [
    {
        "name": "Vector Index Test",
        "query": """
        CALL db.index.vector.queryNodes('video_content', 3, $vector)
        YIELD node, score
        RETURN count(*) as count
        """,
        "params": {"vector": np.zeros(3072).tolist()}
    },
    {
        "name": "Full-text Index Test",
        "query": """
        CALL db.index.fulltext.queryNodes('video_text', 'test')
        YIELD node, score
        RETURN count(*) as count
        """
    },
    {
        "name": "Content Node Check",
        "query": """
        MATCH (n:Content)
        RETURN 
            count(n) as totalContent,
            count(n.embedding) as withEmbedding,
            count(n.title) as withTitle,
            count(n.text) as withText
        """
    },
    {
        "name": "Database Statistics",
        "query": """
        CALL apoc.meta.stats()
        YIELD nodeCount, relCount, labels, relTypes
        RETURN nodeCount, relCount, labels, relTypes
        """
    }
]

for test in test_queries:
    print(f"\nRunning {test['name']}:")
    try:
        result_df = conn.run_query_to_df(
            test['query'], 
            parameters=test.get('params', {})
        )
        display(result_df)
    except Exception as e:
        print(f"Error: {str(e)}")
```

## Cleanup

```python
conn.close()
print("Database connection closed.")
```

## Next Steps

Your Neo4j Aura database is now configured and validated for the GraphRAG platform. You can:
1. Start ingesting video content
2. Test vector similarity searches with actual content
3. Run hybrid queries combining vector and keyword search
4. Add more content nodes and relationships

Key points to remember:
- Vector index is configured for OpenAI text-embedding-3-large (3072 dimensions)
- Full-text index is available for keyword searches
- Basic test content has been added for validation
- Monitor the database statistics as you add more content

Remember to update the vector index dimensions if you change the embedding model:
- text-embedding-3-large: 3072 dimensions
- text-embedding-3-small: 1536 dimensions
- text-embedding-ada-002: 1536 dimensions
