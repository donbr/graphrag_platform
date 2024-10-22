# main.py
import asyncio
import os
from dotenv import load_dotenv
from graphrag import GraphRAGConfig, EnhancedGraphRAGManager

async def main():
    """
    Example usage of the GraphRAG platform
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize configuration
    config = GraphRAGConfig(
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_username=os.getenv("NEO4J_USERNAME"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        vector_index_name="video_content",
        fulltext_index_name="video_text"
    )
    
    # Create manager instance
    manager = EnhancedGraphRAGManager(config)
    
    try:
        # Example: Process a video
        print("Testing video search...")
        result = await manager.search(
            "What are the key components of GraphRAG?",
            retriever_type="vector"
        )
        print("\nVector Search Result:")
        print(result['answer'])
        
        # Example: Graph traversal
        print("\nTesting graph traversal...")
        result = await manager.search(
            "How is GraphRAG used in healthcare?",
            retriever_type="vector_cypher"
        )
        print("\nGraph Traversal Result:")
        print(result['answer'])
        
        # Example: Hybrid search
        print("\nTesting hybrid search...")
        result = await manager.search(
            "Find examples of BioChatter integration from 2024",
            retriever_type="hybrid"
        )
        print("\nHybrid Search Result:")
        print(result['answer'])
        
    finally:
        manager.close()

if __name__ == "__main__":
    asyncio.run(main())
