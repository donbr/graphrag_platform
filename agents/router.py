# graphrag_platform/agents/router.py
from typing import Dict, List
from .base import BaseAgent, AgentState
from neo4j_graphrag.llm import OpenAILLM

ROUTER_PROMPT = """Given a user query, determine the best retrieval strategy:

1. Vector Search: For semantic similarity and concept understanding
2. Graph Traversal: For relationship exploration and connected information
3. Hybrid Search: For combining keyword matching with semantic search
4. Text2Cypher: For specific database queries

Query: {query}

Previous steps: {previous_steps}

Determine the best strategy and explain why.
"""

class RouterAgent(BaseAgent):
    """Agent for determining optimal retrieval strategy"""
    
    def __init__(self, llm: OpenAILLM):
        super().__init__(llm)
        self.prompt = PromptTemplate(
            template=ROUTER_PROMPT,
            input_variables=["query", "previous_steps"]
        )
    
    async def process(self, state: AgentState) -> AgentState:
        """Determine best retrieval strategy"""
        response = await self.llm.predict(
            self.prompt.format(
                query=state.query,
                previous_steps=state.intermediate_steps
            )
        )
        
        # Parse response to determine strategy
        strategy = self._parse_strategy(response)
