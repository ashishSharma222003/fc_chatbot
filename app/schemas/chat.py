from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    user_id: int # Assuming Int ID based on models, but check if user wants string/int. Model says Integer.
    session_id: str
    mode: str = Field("simple", pattern="^(simple|detailed)$") # 'simple' or 'detailed'
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    chunks_used: List[Dict[str, Any]] = []
    memory_saved: Optional[str] = None
