"""
Database Models Base

This file defines the base class for all SQLAlchemy ORM models.
All database models in the application should inherit from this class
to be correctly registered and mapped to the database tables.
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
