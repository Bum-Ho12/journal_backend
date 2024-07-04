"""
file: main.py
"""
import os
from datetime import datetime, timedelta, timezone, date
from typing import Optional, List
import fastapi
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, extract
# pylint:disable=import-error
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext # type: ignore
from jose import jwt # type: ignore
from dotenv import load_dotenv
from pydantic import BaseModel
from models import User, Journal

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
if not DATABASE_URL or not SECRET_KEY:
    raise ValueError("DATABASE_URL and SECRET_KEY must be set in the environment variables")

# Create database engine and session local
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    """
    Dependency function to get a database session.
    This will ensure that the database session is closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    """
    Verify if the provided plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash the provided password using bcrypt algorithm.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
    - data (dict): Data to be encoded in the token.
    - expires_delta (Optional[timedelta]): Token expiration time. Defaults to 15 minutes.
    
    Returns:
    - str: Encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

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
        from_attributes = True

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    
    Args:
    - user (UserCreate): Pydantic model with user details.
    - db (Session): Database session.
    
    Returns:
    - UserResponse: Created user information.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(email: str, password: str, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Args:
    - email (str): User's email.
    - password (str): User's password.
    - db (Session): Database session.
    
    Returns:
    - Token: JWT token and token type.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/journals/", response_model=List[JournalResponse])
def read_journals(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch a list of journal entries.
    
    Args:
    - skip (int): Number of records to skip.
    - limit (int): Maximum number of records to return.
    - db (Session): Database session.
    
    Returns:
    - List[JournalResponse]: List of journal entries.
    """
    journals = db.query(Journal).offset(skip).limit(limit).all()
    return journals

@app.post("/journals/", response_model=dict)
def create_journal(journal: JournalCreate, db: Session = Depends(get_db)):
    """
    Create a new journal entry.
    
    Args:
    - journal (JournalCreate): Pydantic model with journal entry details.
    - db (Session): Database session.
    
    Returns:
    - dict: Success message.
    """
    new_journal = Journal(**journal.dict())
    db.add(new_journal)
    db.commit()
    db.refresh(new_journal)
    return {"message": "Journal entry created successfully"}

@app.put("/journals/{journal_id}", response_model=dict)
def update_journal(
    journal_id: int, title: Optional[str] = None, content: Optional[str] = None,
    category: Optional[str] = None, archive: Optional[bool] = None,
    db: Session = Depends(get_db)):
    """
    Update an existing journal entry.
    Args:
    - journal_id (int): ID of the journal entry to update.
    - title (Optional[str]): New title of the journal entry.
    - content (Optional[str]): New content of the journal entry.
    - category (Optional[str]): New category of the journal entry.
    - archive (Optional[bool]): Archive status of the journal entry.
    - db (Session): Database session.
    Returns:
    - dict: Success message.
    """
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    if title:
        journal.title = title
    if content:
        journal.content = content
    if category:
        journal.category = category
    if archive is not None:
        journal.archive = archive
    journal.date_of_update = datetime.now(timezone.utc)
    db.commit()
    db.refresh(journal)
    return {"message": "Journal entry updated successfully"}

@app.delete("/journals/{journal_id}", response_model=dict)
def delete_journal(journal_id: int, db: Session = Depends(get_db)):
    """
    Mark a journal entry for deletion.
    Args:
    - journal_id (int): ID of the journal entry to delete.
    - db (Session): Database session.
    Returns:
    - dict: Success message.
    """
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    journal.on_delete = True
    db.commit()
    return {"message": "Journal entry marked for deletion"}

@app.get("/journals/daily", response_model=List[JournalResponse])
def get_daily_journals(db: Session = Depends(get_db)):
    """
    Fetch journal entries created today.
    Args:
    - db (Session): Database session.
    Returns:
    - List[JournalResponse]: List of today's journal entries.
    """
    today = date.today()
    journals = db.query(Journal).filter(Journal.date >= today).all()
    return journals

@app.get("/journals/weekly", response_model=List[JournalResponse])
def get_weekly_journals(db: Session = Depends(get_db)):
    """
    Fetch journal entries created this week.
    Args:
    - db (Session): Database session.
    Returns:
    - List[JournalResponse]: List of this week's journal entries.
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    journals = db.query(Journal).filter(Journal.date >= week_start).all()
    return journals

@app.get("/journals/monthly", response_model=List[JournalResponse])
def get_monthly_journals(db: Session = Depends(get_db)):
    """
    Fetch journal entries created this month.
    Args:
    - db (Session): Database session.
    Returns:
    - List[JournalResponse]: List of this month's journal entries.
    """
    today = date.today()
    journals = db.query(Journal).filter(extract('year', Journal.date) == today.year,
                                        extract('month', Journal.date) == today.month).all()
    return journals

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """
    Redirect the root endpoint to the API documentation.
    Returns:
    - RedirectResponse: Redirect to /docs.
    """
    return fastapi.responses.RedirectResponse(url="/docs")
