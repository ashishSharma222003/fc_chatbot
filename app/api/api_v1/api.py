"""
Main API Router

This file configures the main API router for the application.
It aggregates different route modules (e.g., chat, documents) into a single
Application Programming Interface (API) structure, enabling versioned endpoints.
"""
from fastapi import APIRouter
from app.api.api_v1.endpoints import chat, documents

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
