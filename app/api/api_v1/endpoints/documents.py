"""
Document API Endpoints

This file provides endpoints for document ingestion and management.
It allows users to upload or create documents that will be processed and stored
in the vector database for RAG operations.
"""
from fastapi import APIRouter
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def create_document(doc: DocumentCreate):
    # Call ingestion service
    return DocumentResponse(id=1, title=doc.title, content=doc.content)
