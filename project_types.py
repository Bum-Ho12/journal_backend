"""
file: types.py
"""
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    Pydantic model for creating a new user.
    """
    email: str
    username: str
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

class JournalResponse(BaseModel):
    """
    Pydantic model for returning journal entry information.
    """
    title: str
    content: str
    category: str
    date: datetime
    date_of_update: datetime
    archive: bool
    on_delete: bool

    class Config:
        """
        class: Config
        """
        from_attributes = True
