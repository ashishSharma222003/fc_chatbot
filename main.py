"""
Main Application Entry Point

This file initializes the FastAPI application, includes the API router,
and defines the root endpoint. It serves as the starting point for running the server.
"""
from fastapi import FastAPI
from app.core.config import settings
from app.api.api_v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to FC Chatbot API"}
