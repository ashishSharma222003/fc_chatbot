"""
Memory Service

This service manages long-term memory for chat sessions.
It stores and retrieves conversation history, allowing the chatbot to maintain
context across multiple turns of conversation.
"""
from typing import List, Dict

class MemoryService:
    def __init__(self):
        # In-memory storage for demonstration. Replace with Redis or DB in production.
        self._storage: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves chat history for a given session."""
        return self._storage.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to the session history."""
        if session_id not in self._storage:
            self._storage[session_id] = []
        self._storage[session_id].append({"role": role, "content": content})
