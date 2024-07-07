"""
Unit tests for user and journal models and responses.
"""

from datetime import datetime
# pylint:disable = import-error
import pytest # type: ignore
from pydantic import ValidationError
from project_types import (
    UserCreate, UserUpdate, UserLogin, UserResponse,
    Token, CredentialResponse, JournalCreate,
    JournalUpdate, JournalResponse
)

def test_user_create():
    """
    Test valid and invalid user creation.
    """
    # Valid user creation
    user = UserCreate(email="test@example.com", username="testuser", password="password123")
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.password == "password123"

    # Invalid email should raise a ValidationError
    try:
        UserCreate(email="not-an-email", username="testuser", password="password123")
    except ValidationError as e:
        print("Caught ValidationError as expected: ", e)
    else:
        pytest.fail("ValidationError was not raised for invalid email")

def test_user_update():
    """
    Test valid user update and optional fields.
    """
    # Valid user update with specific values
    user = UserUpdate(username="newuser", email="new@example.com", password="newpassword")
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.password == "newpassword"

    # Optional fields set to None
    user = UserUpdate(username=None, email=None, password=None)
    assert user.username is None
    assert user.email is None
    assert user.password is None

def test_user_login():
    """
    Test user login with valid and invalid email formats.
    """
    # Valid user login
    user = UserLogin(email="test@example.com", password="password123")
    print(user)
    assert user.email == "test@example.com"
    assert user.password == "password123"

    # Invalid email should raise a ValidationError
    with pytest.raises(ValidationError):
        UserLogin(email="not-an-email", password="password123")

def test_user_response():
    """
    Test user response model.
    """
    # Create a user response object and verify attributes
    user = UserResponse(email="test@example.com", username="testuser")
    assert user.email == "test@example.com"
    assert user.username == "testuser"

def test_token():
    """
    Test token creation and attributes.
    """
    # Create a token object and verify attributes
    token = Token(access_token="someaccesstoken", token_type="bearer")
    assert token.access_token == "someaccesstoken"
    assert token.token_type == "bearer"

def test_credential_response():
    """
    Test credential response model combining user and token.
    """
    # Create a credential response object and verify attributes
    user = UserResponse(email="test@example.com", username="testuser")
    token = Token(access_token="someaccesstoken", token_type="bearer")
    cred_response = CredentialResponse(token=token, user=user)
    assert cred_response.token.access_token == "someaccesstoken"
    assert cred_response.token.token_type == "bearer"
    assert cred_response.user.email == "test@example.com"
    assert cred_response.user.username == "testuser"

def test_journal_create():
    """
    Test journal creation with default values.
    """
    # Create a journal object and verify default attributes
    journal = JournalCreate(title="Test Journal", content="Some content", category="general")
    assert journal.title == "Test Journal"
    assert journal.content == "Some content"
    assert journal.category == "general"
    assert journal.due_date is None

def test_journal_update():
    """
    Test journal update with specified values and default values.
    """
    # Update a journal object with specific values
    journal = JournalUpdate(title="Updated Title", content="Updated content", category="work")
    assert journal.title == "Updated Title"
    assert journal.content == "Updated content"
    assert journal.category == "work"
    assert journal.due_date is None

    # Update a journal object with default values (None)
    journal = JournalUpdate()
    assert journal.title is None
    assert journal.content is None
    assert journal.category is None
    assert journal.due_date is None

def test_journal_response():
    """
    Test journal response model with specified attributes.
    """
    # Create a journal response object and verify attributes
    date_created = datetime.now()
    date_of_update = datetime.now()
    journal = JournalResponse(
        id=1,
        title="Test Journal",
        content="Some content",
        category="general",
        date_created=date_created,
        due_date=None,
        date_of_update=date_of_update,
        archive=False,
        on_delete=False
    )
    assert journal.id == 1
    assert journal.title == "Test Journal"
    assert journal.content == "Some content"
    assert journal.category == "general"
    assert journal.date_created == date_created
    assert journal.due_date is None
    assert journal.date_of_update == date_of_update
    assert not journal.archive
    assert not journal.on_delete
