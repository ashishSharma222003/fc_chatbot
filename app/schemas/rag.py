from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SubQuery(BaseModel):
    """A specific sub-query to retrieve relevant information."""
    query: str = Field(..., description="The search query.")
    filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter/s to apply (e.g. {'source_file': 'x', 'year': 2023})")

class QueryPlan(BaseModel):
    """Plan for retrieving information."""
    sub_queries: List[SubQuery] = Field(..., description="List of sub-queries to run against the knowledge base.")
    memory_query: str = Field(..., description="Query to search within the user's long-term memory.")

class RAGResponse(BaseModel):
    """Structured response from the RAG service."""
    answer: str = Field(..., description="The answer to the user's query.")
    memory_to_save: Optional[str] = Field(None, description="Important information from the interaction to be saved to long-term memory.")
    chunk_indices: List[int] = Field(default_factory=list, description="Indices of the context chunks used to generate the answer.")
