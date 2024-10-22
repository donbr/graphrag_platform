# Neo4j Aura Setup for GraphRAG Platform

This notebook guides you through setting up the required database objects in Neo4j Aura for the GraphRAG platform using a safe namespacing approach that allows coexistence with existing data. We'll:
1. Connect to the database
2. Analyze existing data
3. Create namespaced constraints and indexes
4. Verify the setup and add test data

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
            
    def analyze_database(self):
        """Analyze existing database structure"""
        queries = [
            {
                "name": "Label Statistics",
                "query": """
                CALL db.labels() YIELD label
                RETURN label, size([(n) WHERE n:`${label}`|1]) as count
                ORDER BY count DESC
                """
            },
            {
                "name": "Relationship Types",
                "query": """
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN relationshipType, 
                       size([:${relationshipType}]()) as count
                ORDER BY count DESC
                """
            }
        ]
        
        results = {}
        for query in queries:
            results[query["name"]] = self.run_query_to_df(query["query"])
        return results
```

## Connect and Analyze Database

```python
# Create connection
conn = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

try:
    # Test connectivity
    conn.verify_connectivity()
    print("Successfully connected to Neo4j Aura!")
    
    # Analyze existing database
    analysis = conn.analyze_database()
    print("\nExisting Database Analysis:")
    for name, df in analysis.items():
        print(f"\n{name}:")
        display(df)
    
except Exception as e:
    print(f"Connection failed: {str(e)}")
```

## Create Namespaced Constraints

```python
constraints = [
    """
    CREATE CONSTRAINT graphrag_content_id IF NOT EXISTS
    FOR (n:GraphRAG_Content) 
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT graphrag_speaker_id IF NOT EXISTS
    FOR (n:GraphRAG_Speaker) 
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT graphrag_topic_id IF NOT EXISTS
    FOR (n:GraphRAG_Topic) 
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
WHERE name STARTS WITH 'graphrag'
""")

display(constraints_df)
```

## Create Namespaced Vector Index

```python
vector_indexes = [
    """
    CREATE VECTOR INDEX graphrag_video_content IF NOT EXISTS
    FOR (n:GraphRAG_Content) 
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
WHERE type = 'VECTOR' AND name STARTS WITH 'graphrag'
""")

display(vector_indexes_df)
```

## Create Namespaced Full-text Index

```python
fulltext_indexes = [
    """
    CREATE FULLTEXT INDEX graphrag_video_text IF NOT EXISTS
    FOR (n:GraphRAG_Content)
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
WHERE type = 'FULLTEXT' AND name STARTS WITH 'graphrag'
""")

display(fulltext_indexes_df)
```

## Create Additional Namespaced Indexes

```python
indexes = [
    """
    CREATE INDEX graphrag_content_title IF NOT EXISTS
    FOR (n:GraphRAG_Content) 
    ON (n.title)
    """,
    """
    CREATE INDEX graphrag_content_type IF NOT EXISTS
    FOR (n:GraphRAG_Content) 
    ON (n.type)
    """,
    """
    CREATE INDEX graphrag_speaker_name IF NOT EXISTS
    FOR (n:GraphRAG_Speaker) 
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
WHERE name STARTS WITH 'graphrag'
""")

display(all_indexes_df)
```

## Add Sample Test Data

```python
# Create a test content node with proper embedding
sample_content = """
CREATE (c:GraphRAG_Content {
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
# Enhanced test queries with proper vector testing and namespacing
test_queries = [
    {
        "name": "Vector Index Test",
        "query": """
        CALL db.index.vector.queryNodes('graphrag_video_content', 3, $vector)
        YIELD node, score
        RETURN count(*) as count
        """,
        "params": {"vector": np.zeros(3072).tolist()}
    },
    {
        "name": "Full-text Index Test",
        "query": """
        CALL db.index.fulltext.queryNodes('graphrag_video_text', 'test')
        YIELD node, score
        RETURN count(*) as count
        """
    },
    {
        "name": "GraphRAG Content Node Check",
        "query": """
        MATCH (n:GraphRAG_Content)
        RETURN 
            count(n) as totalContent,
            count(n.embedding) as withEmbedding,
            count(n.title) as withTitle,
            count(n.text) as withText
        """
    },
    {
        "name": "Namespaced Statistics",
        "query": """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'GraphRAG_')
        RETURN 
            count(n) as totalNodes,
            collect(distinct labels(n)) as nodeTypes
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

Your Neo4j Aura database is now configured with a namespaced setup for the GraphRAG platform. Key points:

1. All GraphRAG objects are prefixed with `GraphRAG_` to isolate them from existing data
2. Existing database data remains untouched
3. Vector index is configured for OpenAI text-embedding-3-large (3072 dimensions)
4. All indexes and constraints are namespaced

To use this setup:

1. Update your GraphRAG configuration:
```python
config = GraphRAGConfig(
    neo4j_uri=NEO4J_URI,
    neo4j_username=NEO4J_USERNAME,
    neo4j_password=NEO4J_PASSWORD,
    vector_index_name="graphrag_video_content",
    fulltext_index_name="graphrag_video_text"
)
```

2. Ensure all queries use the namespaced labels:
   - GraphRAG_Content instead of Content
   - GraphRAG_Speaker instead of Speaker
   - GraphRAG_Topic instead of Topic

Remember to update the vector index dimensions if you change the embedding model:
- text-embedding-3-large: 3072 dimensions
- text-embedding-3-small: 1536 dimensions
- text-embedding-ada-002: 1536 dimensions
