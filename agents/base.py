# graphrag_platform/agents/base.py
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
from neo4j_graphrag.llm import OpenAILLM

class AgentState(BaseModel):
    """Shared state between agents"""
    query: str
    context: Optional[List[Dict]] = None
    intermediate_steps: List[Dict] = Field(default_factory=list)
    final_answer: Optional[str] = None

class BaseAgent:
    """Base agent implementation"""
    def __init__(self, llm: OpenAILLM):
        self.llm = llm
    
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state"""
        raise NotImplementedError
