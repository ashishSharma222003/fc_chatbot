"""
Security Utilities

This file contains helper functions for authentication and security,
such as password hashing and verification. It will eventually handle
JWT token generation and validation.
"""
# Security utilities (e.g., password hashing, JWT)

def get_password_hash(password: str) -> str:
    # Placeholder
    return password + "hashed"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Placeholder
    return plain_password + "hashed" == hashed_password
