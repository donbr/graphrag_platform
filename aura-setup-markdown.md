# Neo4j Aura Setup for GraphRAG Platform

This notebook guides you through setting up the required database objects in Neo4j Aura for the GraphRAG platform. We'll:
1. Connect to the database
2. Create necessary constraints and indexes
3. Verify the setup

## Prerequisites
- Neo4j Aura Enterprise account
- Database connection details
- Required Python packages

## Install Required Packages

```python
# Install required packages if not already installed
!pip install neo4j python-dotenv pandas
```

## Import Dependencies and Load Environment Variables

```python
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import logging
import pandas as pd

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

## Create Database Connection Helper

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
    
except Exception as e:
    print(f"Connection failed: {str(e)}")
```

## Create Constraints

First, we'll create constraints to ensure data integrity.

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

Now we'll create the vector index required for semantic search. Note that the dimensions should match your embedding model:
- OpenAI text-embedding-3-large: 3072 dimensions
- OpenAI text-embedding-3-small: 1536 dimensions
- OpenAI text-embedding-ada-002: 1536 dimensions

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

This index will support keyword-based searching.

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

These indexes will improve query performance.

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

## Verify Database Setup

Let's run some test queries to verify everything is working.

```python
# Test queries
test_queries = [
    {
        "name": "Vector Index Test",
        "query": """
        CALL db.index.vector.queryNodes('video_content', 3, [])
        YIELD node, score
        RETURN count(*) as count
        """
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
        result_df = conn.run_query_to_df(test['query'])
        display(result_df)
    except Exception as e:
        print(f"Error: {str(e)}")
```

## Cleanup

Close the database connection.

```python
conn.close()
print("Database connection closed.")
```

## Next Steps

Your Neo4j Aura database is now configured for the GraphRAG platform. You can:
1. Start ingesting video content
2. Test vector similarity searches
3. Run hybrid queries combining vector and keyword search

Remember to update the vector index dimensions if you change the embedding model.
