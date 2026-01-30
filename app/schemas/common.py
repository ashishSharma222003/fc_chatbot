"""
Common Schemas

This file holds shared Pydantic models used across different parts of the application.
Examples include generic message responses or shared data structures.
"""
from pydantic import BaseModel

class Message(BaseModel):
    message: str
