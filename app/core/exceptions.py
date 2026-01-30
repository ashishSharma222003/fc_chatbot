"""
Custom Exceptions

This file defines custom exception classes to handle specific error scenarios
in the application. These exceptions map to standard HTTP status codes
to provide meaningful error responses to API clients.
"""
from fastapi import HTTPException

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class AuthorizationException(HTTPException):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=401, detail=detail)
