"""
RAG Service

This service orchestrates the Retrieval-Augmented Generation (RAG) workflow.
It coordinates interactions between the Vector Store (to find relevant context),
Memory Service (for history), Pandas Service (for structured data), and
the LLM Service (to generate answers based on that context).
"""
from app.schemas.chat import ChatResponse
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.pandas_service import PandasService

class RAGService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.pandas_service = PandasService()

    async def get_answer(self, query: str, session_id: str) -> ChatResponse:
        # 1. Retrieve history
        history = self.memory_service.get_history(session_id)
        
        # 2. Add current query to memory
        self.memory_service.add_message(session_id, "user", query)

        # 3. Decision Logic: RAG or Pandas? (Simplified)
        # In a real app, an LLM router would decide.
        context = ""
        # if "table" in query or "data" in query:
        #     context = self.pandas_service.execute_query(query)
        # else:
        #     docs = await self.vector_store.search(query)
        #     context = "\n".join([d.content for d in docs])

        # 4. Construct prompt with history and context
        full_prompt = f"History: {history}\nContext: {context}\nUser: {query}"

        # 5. Get answer from LLM
        answer, tokens = await self.llm_service.generate_response(full_prompt)

        # 6. Add answer to memory
        self.memory_service.add_message(session_id, "assistant", answer)

        return ChatResponse(answer=answer, token_usage=tokens)
