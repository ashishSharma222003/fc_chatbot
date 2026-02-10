"""
RAG Service

This service orchestrates the Retrieval-Augmented Generation (RAG) workflow.
It coordinates interactions between the Vector Store (to find relevant context),
Memory Service (for history), Pandas Service (for structured data), and
the LLM Service (to generate answers based on that context).
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
from app.services.memory_service import MemoryService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.schemas.rag import RAGResponse, QueryPlan

class RAGService:
    def __init__(self):
        self.memory_service = MemoryService()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()

    async def generate_quick_answer(self, query: str, user_id: str, session_id: str, recent_history: List[Dict]) -> tuple[RAGResponse, List[Dict], Dict[str, int]]:
        """
        Generates a structured answer to the user query using RAG.
        Returns: (RAGResponse, source_chunks, token_usage)
        """
        # 1. Parallel Context Retrieval
        memory_task = self.memory_service.search_memory(query, user_id=user_id, session_id=session_id)
        vector_task = self.vector_store.mmr_search(query, top_k=5)
        
        memories, knowledge_chunks = await asyncio.gather(memory_task, vector_task)
        
        # 2. Format Context
        system_prompt, user_prompt = self._construct_prompts(query, memories, knowledge_chunks, recent_history)
        
        # 3. LLM Call for Structured Output
        # We need a schema for the LLM to follow. We can reuse the Pydantic model's JSON schema.
        response_schema = RAGResponse.model_json_schema()
        
        llm_response_dict, usage = await self.llm_service.get_structured_response(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            schema=response_schema
        )
        
        # 4. Parse Response
        rag_response = RAGResponse(**llm_response_dict)
        
        # 5. Update Memory (if needed)
        if rag_response.memory_to_save:
            # Fire and forget (or await if strict consistency needed)
            # await self.memory_service.add_memory(rag_response.memory_to_save, user_id, session_id)
             self.memory_service.add_memory(rag_response.memory_to_save, user_id, session_id)

        return rag_response, knowledge_chunks, usage

    async def generate_answer_stream(self, query: str, user_id: str, session_id: str, recent_history: List[Dict]) -> AsyncGenerator[str, None]:
        """
        Generates a streaming answer. 
        Note: True structured streaming is complex. This implementation streams the text content
        and appends metadata as a JSON string at the end.
        """
        # 1. Parallel Context Retrieval
        memory_task = self.memory_service.search_memory(query, user_id=user_id, session_id=session_id)
        vector_task = self.vector_store.mmr_search(query, top_k=5)
        
        memories, knowledge_chunks = await asyncio.gather(memory_task, vector_task)
        
        # 2. Format Context
        system_prompt, user_prompt = self._construct_prompts(query, memories, knowledge_chunks, recent_history)
        
        # 3. Stream Response
        # For streaming, we might not enforce JSON schema strictly on the whole stream if we want immediate text.
        # However, to maintain the "structured" requirement, we can ask the LLM to stream the answer first.
        # Simplified approach: Stream the raw text answer.
        # Future improvement: Use function calling stream or specialized parsing.
        
        async for chunk in self.llm_service.generate_stream(user_prompt, system_prompt):
            if chunk:
                yield chunk
    async def generate_detailed_answer(self, query: str, user_id: str, session_id: str, recent_history: List[Dict], metadata: Optional[Dict[str, Any]] = None) -> tuple[RAGResponse, List[Dict], Dict[str, int]]:
        """
        Generates a detailed answer using query expansion and parallel retrieval.
        Returns: (RAGResponse, source_chunks, token_usage)
        """
        total_tokens = {"input_tokens": 0, "output_tokens": 0}

        # 1. Generate Query Plan
        plan_system_prompt = """You are an expert information retriever. 
        Break down the user's complex query into distinct sub-queries to maximize retrieval coverage from the knowledge base.
        Also generate a specific query to check the user's personal memory.
        Generate metadata filters if the user mentions specific attributes (like dates, files, or types).
        """
        if metadata is not None:
            plan_user_prompt = f"User Query: {query}\n\nGenerate 5 sub-queries and 1 memory query.\n\nMetadata: {metadata}"
        else:
            plan_user_prompt = f"User Query: {query}\n\nGenerate 5 sub-queries and 1 memory query."
        
        plan_schema = RAGResponse.model_json_schema() # Placeholder, we need QueryPlan schema
        from app.schemas.rag import QueryPlan # Local import to avoid circular dependency if any
        plan_schema = QueryPlan.model_json_schema()

        plan_dict, plan_usage = await self.llm_service.get_structured_response(
            user_prompt=plan_user_prompt,
            system_prompt=plan_system_prompt,
            schema=plan_schema
        )
        total_tokens["input_tokens"] += plan_usage["input_tokens"]
        total_tokens["output_tokens"] += plan_usage["output_tokens"]
        
        query_plan = QueryPlan(**plan_dict)
        
        # 2. Parallel Execution
        # Memory Search
        memory_task = self.memory_service.search_memory(query_plan.memory_query, user_id=user_id, session_id=session_id)
        
        # Vector Searches (5 sub-queries)
        vector_tasks = []
        for sub_q in query_plan.sub_queries:
            vector_tasks.append(self.vector_store.mmr_search(
                query=sub_q.query, 
                top_k=2, 
                filter=sub_q.filter if sub_q.filter else None
            ))
            
        results = await asyncio.gather(memory_task, *vector_tasks)
        
        memories = results[0]
        vector_results_lists = results[1:]
        
        # 3. Aggregate & Deduplicate Knowledge Chunks
        unique_chunks = {}
        for res_list in vector_results_lists:
            for chunk in res_list:
                if chunk['id'] not in unique_chunks:
                    unique_chunks[chunk['id']] = chunk
        
        knowledge_chunks = list(unique_chunks.values())
        
        # 4. Format Context & Generate Final Answer
        system_prompt, user_prompt = self._construct_prompts(query, memories, knowledge_chunks, recent_history)
        
        response_schema = RAGResponse.model_json_schema()
        llm_response_dict, answer_usage = await self.llm_service.get_structured_response(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            schema=response_schema
        )
        total_tokens["input_tokens"] += answer_usage["input_tokens"]
        total_tokens["output_tokens"] += answer_usage["output_tokens"]
        
        rag_response = RAGResponse(**llm_response_dict)
        
        # 5. Update Memory
        if rag_response.memory_to_save:
             self.memory_service.add_memory(rag_response.memory_to_save, user_id, session_id)

        return rag_response, knowledge_chunks, total_tokens
    def _construct_prompts(self, query: str, memories: List[Dict], knowledge_chunks: List[Dict], recent_history: List[Dict]) -> tuple[str, str]:
        """
        Constructs system and user prompts with context.
        """
        # Format Memory
        memory_context = "\n".join([f"- {m['text']} (Date: {m['metadata'].get('date', 'N/A')})" for m in memories])
        
        # Format Knowledge Chunks with Indices
        knowledge_context = ""
        for i, chunk in enumerate(knowledge_chunks):
            knowledge_context += f"[{i}] {chunk['text']}\n"
            
        # Format History (Last 3 turns)
        history_context = ""
        for msg in recent_history[-3:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_context += f"{role}: {content}\n"
            
        system_prompt = """You are a helpful AI assistant for the Future Club chatbot.
        Use the provided context to answer the user's question.
        
        1. prioritize the 'Knowledge Base' for factual information.
        2. use 'User Memory' for personalization and context.
        3. maintain the conversation flow based on 'Conversation History'.
        
        When using information from the 'Knowledge Base', you MUST cite the chunk index (e.g., [0], [1]) in your `chunk_indices` field.
        If the user provides new important personal information (e.g., "I like red"), extract it into `memory_to_save`.
        """
        
        user_prompt = f"""
        # User Memory
        {memory_context}
        
        # Knowledge Base
        {knowledge_context}
        
        # Conversation History
        {history_context}
        
        # User Query
        {query}
        """
        
        return system_prompt, user_prompt
