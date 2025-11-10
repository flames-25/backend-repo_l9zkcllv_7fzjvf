"""
Database Schemas for Book Marketplace

Each Pydantic model maps to a MongoDB collection named after the class in lowercase.
Example: class User -> collection "user"
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="SHA256 hash of the user's password")

class Listing(BaseModel):
    """
    Book listings posted by users
    Collection name: "listing"
    """
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    isbn: Optional[str] = Field(None, description="ISBN (10 or 13)")
    price: float = Field(..., ge=0, description="Price in USD")
    condition: str = Field(..., description="Condition label, e.g., New, Like New, Very Good, Good")
    cover: Optional[str] = Field(None, description="Cover image URL")
    description: Optional[str] = Field(None, description="Listing description")
    seller_email: EmailStr = Field(..., description="Email of the seller (must match a user)")
    status: str = Field("active", description="Listing status: active, sold, archived")
