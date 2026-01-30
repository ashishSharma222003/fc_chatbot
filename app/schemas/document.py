"""
Document Schemas

This file defines Pydantic models for document management.
It schemas for creating new documents (requests) and returning document details (responses),
ensuring consistent data structure for document ingestion.
"""
from pydantic import BaseModel
from typing import Optional

class DocumentBase(BaseModel):
    title: str
    content: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    # Metadata
