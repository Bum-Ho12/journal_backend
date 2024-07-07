# Journal API

This is a FastAPI-based backend for managing user accounts and journal entries. The backend uses SQLite as the database and JWT for authentication.

## Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
  - [User Management](#user-management)
  - [Authentication](#authentication)
  - [Journal Management](#journal-management)
- [License](#license)

## Requirements

- Python 3.8+
- SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Bum-Ho12/journal_backend.git
   cd journal_backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Create a `.env` file in the root directory and add the following environment variables:

```
DATABASE_URL=sqlite:///./test.db  # Change this to your database URL
SECRET_KEY=your_secret_key  # Change this to a random secret key
```

## Running the Application

1. Start the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### User Management

- **POST** `/users/` - Create a new user.
  - Request body:
    ```json
    {
      "email": "user@example.com",
      "username": "user",
      "password": "password"
    }
    ```
  - Response:
    ```json
    {
      "id": 1,
      "email": "user@example.com",
      "username": "user"
    }
    ```

- **PUT** `/users/{email}` - Update user profile details.
  - Request body:
    ```json
    {
      "email":"email_address",
      "username": "new_username",
      "password": "new_password"
    }
    ```
  - Response:
    ```json
    {
      "id": 1,
      "email": "user@example.com",
      "username": "new_username"
    }
    ```

### Authentication

- **POST** `/token` - Obtain a JWT token.
  - Request body:
    ```json
    {
      "username": "user",
      "password": "password"
    }
    ```
  - Response:
    ```json
    {
      "access_token": "your_jwt_token",
      "token_type": "bearer"
    }
    ```

### Journal Management

- **GET** `/journals/` - Fetch a list of journal entries.
  - Response:
    ```json
    [
      {
        "id": 1,
        "title": "First Entry",
        "content": "This is my first journal entry.",
        "category": "Personal",
        "created_date": "2023-07-02",
        "due_date":null,
        "date_of_update": "2023-07-01",
        "archive": false
      }
    ]
    ```

- **POST** `/journals/` - Create a new journal entry.
  - Request body:
    ```json
    {
      "title": "First Entry",
      "content": "This is my first journal entry.",
      "category": "Personal",
      "created_date": "2023-07-02",
      "due_date":null,
      "date_of_update": "2023-07-01",
      "archive": false
    }
    ```
  - Response:
    ```json
    {
      "id": 1,
      "title": "First Entry",
      "content": "This is my first journal entry.",
      "category": "Personal",
      "created_date": "2023-07-02",
      "due_date":null,
      "date_of_update": "2023-07-01",
      "archive": false
    }
    ```

- **PUT** `/journals/{journal_id}` - Update a journal entry.
  - Request body:
    ```json
    {
      "title": "Updated Entry",
      "content": "This is my updated journal entry.",
      "category": "Work",
      "created_date": "2023-07-02",
      "due_date":null,
      "date_of_update": "2023-07-02",
      "archive": false
    }
    ```
  - Response:
    ```json
    {
      "id": 1,
      "title": "Updated Entry",
      "content": "This is my updated journal entry.",
      "category": "Work",
      "created_date": "2023-07-02",
      "due_date":"2023-07-02",
      "date_of_update": "2023-07-02",
      "archive": false
    }
    ```

- **DELETE** `/journals/{journal_id}` - Delete a journal entry.
  - Response:
    ```json
    {
      "detail": "Journal entry deleted"
    }
    ```

## License

This project is licensed under the MIT License.
