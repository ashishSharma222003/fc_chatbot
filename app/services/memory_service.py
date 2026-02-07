"""
Memory Service

This service manages long-term memory for chat sessions.
It stores and retrieves conversation history, allowing the chatbot to maintain
context across multiple turns of conversation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class MemoryService:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        
        # Initialize embedding model
        # Using the same model as ingestion for consistency
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_memory(self, text: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Adds a new memory to the vector store.
        """
        memory_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Create metadata
        metadata = {
            "text": text,
            "user_id": user_id,
            "session_id": session_id,
            "date": datetime.now().isoformat(),
            "type": "conversation_history"
        }
        
        # Upsert to Pinecone
        self.index.upsert(vectors=[(memory_id, embedding, metadata)])
        
        return {
            "id": memory_id,
            "metadata": metadata
        }

    def search_memory(self, query: str, user_id: str, session_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves relevant memories based on a query.
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build filter
        metadata_filter = {"user_id": user_id}
        if session_id:
            metadata_filter["session_id"] = session_id
            
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter
        )
        
        memories = []
        for match in results.matches:
            memories.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata,
                "text": match.metadata.get("text", "")
            })
            
        return memories
