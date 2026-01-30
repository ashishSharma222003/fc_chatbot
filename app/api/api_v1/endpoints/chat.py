"""
Chat API Endpoints

This file defines the endpoints for the chatbot functionality.
It handles incoming chat requests, interacts with the RAG service to generate
responses, and returns the answers to the client.
"""
from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    service = RAGService()
    return await service.get_answer(request.messages[-1].content, request.session_id)
