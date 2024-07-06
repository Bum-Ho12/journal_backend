"""
file: types.py
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Pydantic model for creating a new user.
    """
    email: str
    username: str
    password: str

class UserUpdate(BaseModel):
    """
    Pydantic model for updating user information.
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    """
    Pydantic model for receiving user login credentials.
    """
    email: str
    password: str

class UserResponse(BaseModel):
    """
    Pydantic model for returning user information.
    """
    email: str
    username: str

class Token(BaseModel):
    """
    Pydantic model for returning the JWT token.
    """
    access_token: str
    token_type: str

class CredentialResponse(BaseModel):
    """
    Pydantic model for returning the JWT token.
    """
    token:Token
    user: UserResponse

class JournalCreate(BaseModel):
    """
    Pydantic model for creating a new journal entry.
    """
    title: str
    content: str
    category: str
    due_date: Optional[datetime] = None

class JournalResponse(BaseModel):
    """
    Pydantic model for returning journal entry information.
    """
    id:int
    title: str
    content: str
    category: str
    date_created: datetime
    due_date:Optional[datetime] = None
    date_of_update: datetime
    archive: bool
    on_delete: bool

    class Config:
        """
        class: Config
        """
        from_attributes = True
