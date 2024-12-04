import pytest
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from main import app, get_db, authenticate_user, create_access_token, get_current_user
from db_models import User
from jose import jwt
from datetime import timedelta

# Mock database session
@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    yield db

# Test client
@pytest.fixture
def client():
    return TestClient(app)

# Override `get_db` dependency
@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.pop(get_db)

# Mock current user dependency
@pytest.fixture
def override_get_current_user():
    def mock_get_current_user():
        return User(username="testuser", hashed_password="hashedpassword")
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user)

# Helper to hash passwords for tests
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Test authenticate_user
def test_authenticate_user_success(mock_db):
    user = User(username="testuser", hashed_password=hash_password("testpassword"))
    mock_db.query.return_value.filter.return_value.first.return_value = user
    
    authenticated_user = authenticate_user("testuser", "testpassword", mock_db)
    assert authenticated_user is not False
    assert authenticated_user.username == "testuser"

def test_authenticate_user_invalid_username(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    authenticated_user = authenticate_user("wronguser", "testpassword", mock_db)
    assert authenticated_user is False

def test_authenticate_user_invalid_password(mock_db):
    user = User(username="testuser", hashed_password=hash_password("testpassword"))
    mock_db.query.return_value.filter.return_value.first.return_value = user
    
    authenticated_user = authenticate_user("testuser", "wrongpassword", mock_db)
    assert authenticated_user is False


# Test create_access_token
def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
    assert payload.get("sub") == "testuser"


# Test get_current_user
def test_get_current_user_valid_token(mock_db, client, override_get_db):
    user = User(username="testuser", hashed_password="hashedpassword")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    token = create_access_token({"sub": "testuser"}, timedelta(minutes=30))
    headers = {"Cookie": f"access_token={token}"}

    response = client.get("/some-protected-route", headers=headers)  # Replace with an actual route
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": "testuser"}  # Adjust based on route response


def test_get_current_user_invalid_token(mock_db, client, override_get_db):
    token = "invalidtoken"
    headers = {"Cookie": f"access_token={token}"}

    response = client.get("/some-protected-route", headers=headers)  # Replace with an actual route
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_no_token(client):
    response = client.get("/some-protected-route")  # Replace with an actual route
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


pytest.main(["-v", "test_auth.py"])