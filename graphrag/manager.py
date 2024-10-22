# graphrag/manager.py
from typing import Dict, List, Optional, Any
import logging
from neo4j import GraphDatabase

from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
from neo4j_graphrag.retrievers import (
    VectorRetriever,
    VectorCypherRetriever,
    HybridRetriever,
    HybridCypherRetriever,
    Text2CypherRetriever
)
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.types import RetrieverResultItem

from .config import GraphRAGConfig

logger = logging.getLogger(__name__)

class GraphRAGManager:
    """GraphRAG manager supporting multiple retrieval strategies"""
    
    def __init__(self, config: GraphRAGConfig):
        self.config = config
        self.driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_username, config.neo4j_password)
        )
        self.embedder = OpenAIEmbeddings(
            model=config.embedding_model
        )
        self.llm = OpenAILLM(
            api_key=config.openai_api_key,
            model_name=config.llm_model,
            model_params={"temperature": config.temperature}
        )
        self._setup_retrievers()

    def _setup_retrievers(self):
        """Initialize different retrievers based on configuration"""
        # Basic vector retriever
        self.vector_retriever = VectorRetriever(
            driver=self.driver,
            index_name=self.config.vector_index_name,
            embedder=self.embedder,
            return_properties=["title", "text", "metadata"]
        )

        # Vector retriever with graph traversal
        cypher_query = """
        MATCH (n)-[r]-(related)
        WHERE id(n) = node.id
        WITH n, collect(DISTINCT type(r)) as relationships,
             collect(DISTINCT related) as related_nodes
        RETURN n.title as title, 
               n.text as text,
               relationships,
               related_nodes
        """
        
        self.vector_cypher_retriever = VectorCypherRetriever(
            driver=self.driver,
            index_name=self.config.vector_index_name,
            embedder=self.embedder,
            retrieval_query=cypher_query
        )

        # Hybrid retriever if fulltext index configured
        if self.config.fulltext_index_name:
            self.hybrid_retriever = HybridRetriever(
                driver=self.driver,
                vector_index_name=self.config.vector_index_name,
                fulltext_index_name=self.config.fulltext_index_name,
                embedder=self.embedder
            )
            
            # Hybrid Cypher retriever
            self.hybrid_cypher_retriever = HybridCypherRetriever(
                driver=self.driver,
                vector_index_name=self.config.vector_index_name,
                fulltext_index_name=self.config.fulltext_index_name,
                retrieval_query=cypher_query,
                embedder=self.embedder
            )

    def setup_text2cypher(self, schema: str, examples: List[str]):
        """Initialize Text2Cypher retriever with schema and examples"""
        self.text2cypher_retriever = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=schema,
            examples=examples
        )

    def setup_multimodal(self, image_model: str = "clip-ViT-B-32"):
        """Setup for multimodal retrieval with image support"""
        self.image_embedder = SentenceTransformerEmbeddings(image_model)
        
        # Custom formatter for image results
        def format_image_result(record: Any) -> RetrieverResultItem:
            return RetrieverResultItem(
                content=f"Title: {record.get('title')}, Content: {record.get('text')}",
                metadata={
                    "title": record.get("title"),
                    "image_url": record.get("image_url"),
                    "score": record.get("score"),
                }
            )
        
        self.image_retriever = VectorCypherRetriever(
            driver=self.driver,
            index_name="image_embeddings",
            embedder=self.image_embedder,
            result_formatter=format_image_result
        )

    async def search(self, 
                    query: str,
                    retriever_type: str = "vector",
                    **kwargs) -> Dict:
        """
        Perform search using specified retriever type
        
        Args:
            query: Search query text
            retriever_type: One of "vector", "vector_cypher", "hybrid", 
                          "hybrid_cypher", "text2cypher", "multimodal"
            **kwargs: Additional retriever-specific parameters
        """
        retrievers = {
            "vector": self.vector_retriever,
            "vector_cypher": self.vector_cypher_retriever,
            "hybrid": getattr(self, 'hybrid_retriever', None),
            "hybrid_cypher": getattr(self, 'hybrid_cypher_retriever', None),
            "text2cypher": getattr(self, 'text2cypher_retriever', None),
            "multimodal": getattr(self, 'image_retriever', None)
        }
        
        retriever = retrievers.get(retriever_type)
        if not retriever:
            raise ValueError(f"Invalid or unconfigured retriever type: {retriever_type}")

        rag = GraphRAG(
            retriever=retriever,
            llm=self.llm
        )
        
        response = await rag.search(
            query_text=query,
            retriever_config={"top_k": kwargs.get('top_k', self.config.top_k)}
        )
        
        return {
            "answer": response.answer,
            "items": [item.dict() for item in response.items] if response.items else []
        }

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
