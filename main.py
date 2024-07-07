"""
file: main.py
"""
import os
import logging
from datetime import datetime, timedelta, timezone, date
from typing import Optional, List
import fastapi
from fastapi import FastAPI, Depends, HTTPException, status
# from sqlalchemy import desc
from sqlalchemy import create_engine, extract
from sqlalchemy.orm import sessionmaker, Session
# pylint: disable=import-error
from passlib.context import CryptContext # type: ignore
from jose import jwt, JWTError # type: ignore
from dotenv import load_dotenv
from models import User, Journal, categories
from project_types import (UserCreate, JournalCreate, JournalResponse,
    CredentialResponse, UserLogin, UserUpdate)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
if not DATABASE_URL or not SECRET_KEY:
    raise ValueError("DATABASE_URL and SECRET_KEY must be set in the environment variables")

# Create database engine and session local
engine = create_engine(DATABASE_URL)
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(fastapi.security.OAuth2PasswordBearer(tokenUrl="token"))):
    """
    Dependency to get the current user from the JWT token.
    Args:
    - db (Session): Database session.
    - token (str): JWT token from the request header.

    Returns:
    - User: Authenticated user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/users/", response_model=CredentialResponse)
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
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {'user': new_user, 'token': {'access_token': access_token, 'token_type': 'bearer'}}

@app.post("/token", response_model=CredentialResponse)
def login_for_access_token(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
    - email (str): User's email.
    - password (str): User's password.
    - db (Session): Database session.

    Returns:
    - Token: JWT token and token type.
    """
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {'user': user, 'token': {'access_token': access_token, 'token_type': 'bearer'}}

# pylint: disable=unused-argument
@app.put("/users/{email}", response_model=CredentialResponse)
def update_user_profile(
    email: str, user_update: UserUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Update user profile details.

    Args:
    - user_id (int): ID of the user to update (optional if using current_user).
    - user_update (UserUpdate): Pydantic model with updated user details.
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - CredentialResponse: Updated user information with token.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Update user details
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    db.commit()
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {'user': user, 'token': {'access_token': access_token, 'token_type': 'bearer'}}

# pylint: disable=unused-argument
@app.get("/journals/", response_model=List[JournalResponse])
def read_journals(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Fetch a list of journal entries.

    Args:
    - skip (int): Number of records to skip.
    - limit (int): Maximum number of records to return.
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - List[JournalResponse]: List of journal entries.
    """
    journals = db.query(Journal).offset(skip).limit(limit).all()
    return journals

# pylint: disable=unused-argument
@app.post("/journals/", response_model=dict)
def create_journal(journal: JournalCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Create a new journal entry.

    Args:
    - journal (JournalCreate): Pydantic model with journal entry details.
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - dict: Success message.
    """
    new_journal = Journal(**journal.dict())
    db.add(new_journal)
    db.commit()
    db.refresh(new_journal)
    return {"message": "Journal entry created successfully"}

# pylint: disable=unused-argument
@app.put("/journals/{journal_id}", response_model=dict)
def update_journal(
    journal_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    archive: Optional[bool] = None,
    due_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing journal entry.

    Args:
    - journal_id (int): ID of the journal entry to update.
    - title (Optional[str]): New title of the journal entry.
    - content (Optional[str]): New content of the journal entry.
    - category (Optional[str]): New category of the journal entry.
    - archive (Optional[bool]): Archive status of the journal entry.
    - due_date (Optional[datetime]): New due date of the journal entry.
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - dict: Success message.
    """
    logger.info("Updating journal with id: %s", journal_id)

    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        logger.error("Journal with id: %s not found", journal_id)
        raise HTTPException(status_code=404, detail="Journal not found")

    # Update fields if provided
    updated = False
    if title:
        journal.title = title
        updated = True
    if content:
        journal.content = content
        updated = True
    if category:
        journal.category = category
        updated = True
    if archive is not None:
        journal.archive = archive
        updated = True
    if due_date is not None:
        journal.due_date = due_date
        updated = True

    if updated:
        db.commit()
        logger.info("Journal with id: %s updated successfully",{journal_id})
        return {"message": "Journal entry updated successfully"}
    else:
        logger.warning("No fields provided to update for journal with id: %s",{journal_id})
        raise HTTPException(status_code=400, detail="No fields provided to update")

# pylint: disable=unused-argument
@app.delete("/journals/{journal_id}", response_model=dict)
def delete_journal(journal_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Delete a journal entry.

    Args:
    - journal_id (int): ID of the journal entry to delete.
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - dict: Success message.
    """
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    db.delete(journal)
    db.commit()
    return {"message": "Journal entry deleted successfully"}

# pylint: disable=unused-argument
@app.get("/journals/daily", response_model=List[JournalResponse])
def read_journals_daily(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Fetch journal entries created today.

    Args:
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - List[JournalResponse]: List of journal entries created today.
    """
    today = date.today()
    daily_journals = db.query(Journal).filter(
        extract('day', Journal.date_created) == today.day,
        extract('month', Journal.date_created) == today.month,
        extract('year', Journal.date_created) == today.year).all()
    return daily_journals

# pylint: disable=unused-argument
@app.get("/journals/weekly", response_model=List[JournalResponse])
def read_journals_weekly(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Fetch journal entries created this week.

    Args:
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - List[JournalResponse]: List of journal entries created this week.
    """
    start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
    end_of_week = start_of_week + timedelta(days=7)
    weekly_journals = db.query(Journal).filter(Journal.date_created >= start_of_week,
        Journal.date_created < end_of_week).all()
    return weekly_journals

# pylint: disable=unused-argument
@app.get("/journals/monthly", response_model=List[JournalResponse])
def read_journals_monthly(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Fetch journal entries created this month.

    Args:
    - db (Session): Database session.
    - current_user (User): Authenticated user.

    Returns:
    - List[JournalResponse]: List of journal entries created this month.
    """
    today = date.today()
    monthly_journals = db.query(Journal).filter(
        extract('month', Journal.date_created) == today.month,
        extract('year', Journal.date_created) == today.year).all()
    return monthly_journals

@app.get("/categories", response_model=List[dict])
def get_categories():
    """
    Fetch the list of categories.

    Returns:
    - List[dict]: List of categories.
    """
    return categories

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """
    Redirect the root endpoint to the API documentation.

    Returns:
    - RedirectResponse: Redirect to /docs.
    """
    return fastapi.responses.RedirectResponse(url="/docs")
