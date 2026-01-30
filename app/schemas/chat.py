"""
Chat Schemas

This file defines Pydantic models for chat-related data transfer objects (DTOs).
It structures the request bodies for chat messages and the response format,
ensuring strict typing and validation for API interactions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: str = Field(..., description="Unique identifier for the chat session")

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    token_usage: int = Field(0, description="Total tokens used for this turn")
