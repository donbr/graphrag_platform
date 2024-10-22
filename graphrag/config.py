# graphrag/config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class GraphRAGConfig:
    """Configuration for GraphRAG setup"""
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    openai_api_key: str
    vector_index_name: str
    fulltext_index_name: Optional[str] = None
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4-turbo-preview"
    temperature: float = 0
    top_k: int = 5
