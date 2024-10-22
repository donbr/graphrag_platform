# main.py
import asyncio
import os
import logging
from dotenv import load_dotenv, find_dotenv
from graphrag import GraphRAGConfig, GraphRAGManager
from neo4j import GraphDatabase

# Setup logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_connection(uri, username, password):
    """Test Neo4j connection"""
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        logger.info("Testing Neo4j connection...")
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j!")
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        raise
    finally:
        driver.close()

async def main():
    """Example usage of the GraphRAG platform"""
    # Debug current directory
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Debug .env loading
    env_path = find_dotenv()
    logger.info(f"Looking for .env file at: {env_path}")
    
    if not env_path:
        logger.error(".env file not found!")
        return
        
    # Load environment variables
    load_dotenv(env_path)

    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    api_key = os.getenv('OPENAI_API_KEY')

    # Debug environment variables
    logger.info("Environment variables:")
    logger.info(f"NEO4J_URI: {uri}")
    logger.info(f"NEO4J_USERNAME: {username}")
    logger.info(f"OPENAI_API_KEY set: {'Yes' if {api_key} else 'No'}")

    # Log connection attempt
    logger.info(f"Attempting to connect to: {uri}")
    
    # Test connection first
    # await test_connection(uri, username, password)
    
    # Initialize configuration
    config = GraphRAGConfig(
        neo4j_uri=uri,
        neo4j_username=username,
        neo4j_password=password,
        openai_api_key=api_key,
        vector_index_name="video_content",
        fulltext_index_name="video_text"
    )
    
    # Create manager instance
    manager = GraphRAGManager(config)
    
    try:
        # Example: Process a video
        logger.info("Testing video search...")
        result = await manager.search(
            "What are the key components of GraphRAG?",
            retriever_type="vector"
        )
        print("\nVector Search Result:")
        print(result['answer'])
        
    finally:
        manager.close()

if __name__ == "__main__":
    asyncio.run(main())
