"""
Chat API Endpoints

This file defines the endpoints for the chatbot functionality.
It handles incoming chat requests, interacts with the RAG service to generate
responses, and returns the answers to the client.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from app.api import deps
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.models import Chat, Session as DbSession, User
from app.db.session import get_db
import uuid

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Chat endpoint for RAG-based interaction.
    """
    rag_service = RAGService()
    
    # 1. Get or Create Session (Simple check)
    db_session = db.query(DbSession).filter(DbSession.id == request.session_id).first()
    if not db_session:
        # Check if user exists, if not create (Lazy creation for demo)
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            # Create a dummy user if not exists for this ID (or handle error)
            # ideally user creation is separate auth flow. 
            # For now assuming user exists or we create one just to make it work
            user = User(id=request.user_id, email=f"user{request.user_id}@example.com")
            db.add(user)
            db.commit()
            db.refresh(user)

        db_session = DbSession(id=request.session_id, user_id=request.user_id, title=request.query[:30])
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
    # 2. Save User Message
    user_msg = Chat(
        session_id=request.session_id,
        role="user",
        content=request.query
    )
    db.add(user_msg)
    db.commit()
    
    # 3. Retrieve History
    # Get last N messages for history
    full_history = db.query(Chat).filter(Chat.session_id == request.session_id).order_by(Chat.created_at).all()
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in full_history]
    
    # 4. Generate Answer
    str_user_id = str(request.user_id) # Service expects string
    
    chunks_used = []
    token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
    if request.mode == "detailed":
        rag_response, chunks, token_usage = await rag_service.generate_detailed_answer(
            query=request.query,
            user_id=str_user_id,
            session_id=request.session_id,
            recent_history=history_dicts,
            metadata=request.metadata
        )
        chunks_used = chunks
    else:
        # Default to simple/quick answer
        rag_response, chunks, token_usage = await rag_service.generate_quick_answer(
            query=request.query,
            user_id=str_user_id,
            session_id=request.session_id,
            recent_history=history_dicts
        )
        chunks_used = chunks

    # 5. Save Assistant Message
    # Convert chunks to list of dicts/indices for storage if needed, or just store IDs
    # The Chat model expects chunks_used as JSON
    assistant_msg = Chat(
        session_id=request.session_id,
        role="assistant",
        content=rag_response.answer,
        chunks_used=[c.get('id') for c in chunks_used] if chunks_used else [], # Storing IDs
        prompt_tokens=token_usage.get("input_tokens", 0),
        completion_tokens=token_usage.get("output_tokens", 0)
    )
    db.add(assistant_msg)
    db.commit()
    
    return ChatResponse(
        answer=rag_response.answer,
        session_id=request.session_id,
        chunks_used=chunks_used,
        memory_saved=rag_response.memory_to_save
    )
