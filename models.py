"""
file: models.py
"""

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    '''
    class: User
    '''
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Journal(Base):
    '''
    class: Journal
    '''
    __tablename__ = "journals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    category = Column(String)
    date_created = Column(DateTime, default=datetime.now(timezone.utc))
    due_date = Column(DateTime, nullable=True)
    date_of_update = Column(DateTime, default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc))
    archive = Column(Boolean, default=False)
    on_delete = Column(Boolean, default=False)

# List of categories
categories = [
    {"id": "1", "name": "Personal"},
    {"id": "2", "name": "Work"},
    {"id": "3", "name": "Errands"},
    {"id": "4", "name": "Health"},
    {"id": "5", "name": "Entertainment"},
    {"id": "6", "name": "Hobbies"},
    {"id": "7", "name": "Education"},
    {"id": "8", "name": "Travel"},
    {"id": "9", "name": "Finance"},
    {"id": "10", "name": "Social"},
]

Base.metadata.create_all(bind=engine)
