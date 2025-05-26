from unittest.mock import patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.models.domain.refresh_token import RefreshTokenModel
from app.models.domain.user import UserModel
from app.main import app as fastapi_app
from app.api.dependencies.auth import get_current_user
from jose import jwt
import uuid

@pytest.mark.asyncio
async def test_refresh_token_success(client: TestClient, test_refresh_token):
    payload = {"refresh_token": test_refresh_token.token}
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] > 0
    assert "refresh_token" in data
    assert data["refresh_token"] != test_refresh_token.token
    assert isinstance(data["refresh_expires_in"], int)
    assert data["refresh_expires_in"] > 0

@pytest.mark.asyncio
async def test_refresh_token_invalid(client: TestClient):
    payload = {"refresh_token": "invalid_token"}
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Invalid refresh token"]}

@pytest.mark.asyncio
async def test_refresh_token_expired(client: TestClient, db_session: Session, test_user):
    token_value = str(uuid.uuid4())
    expired_token = RefreshTokenModel(
        user_id=test_user.id,
        token=token_value,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(expired_token)
    db_session.commit()

    payload = {"refresh_token": token_value}
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Refresh token expired"]}

    token = db_session.query(RefreshTokenModel).filter_by(token=token_value).first()
    assert token is None

@pytest.mark.asyncio
async def test_register_user_success(client: TestClient, db_session: Session):
    payload = {
        "username": "newuser123",
        "email": "new123@gmail.com",
        "password": "Secure123!"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "success"}

    user = db_session.query(UserModel).filter_by(email="new123@gmail.com").first()
    assert user is not None
    assert user.username == "newuser123"

@pytest.mark.asyncio
async def test_register_user_invalid_input(client: TestClient):
    payload = {
        "username": "nu",
        "email": "invalid",
        "password": "123"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["errors"]
    print(errors)  # Manter para depuração
    assert isinstance(errors, list)
    assert any("username" in error["loc"] for error in errors)  # Verificar campo
    assert any("email" in error["loc"] for error in errors)
    assert any("password" in error["loc"] for error in errors)

@pytest.mark.asyncio
async def test_register_user_conflict(client: TestClient, test_user):
    payload = {
        "username": "testuser123",
        "email": "test123@gmail.com",
        "password": "Secure123!"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"errors": ["User already exists"]}

@pytest.mark.asyncio
async def test_login_success(client: TestClient, test_user):
    payload = {
        "username": "testuser123",
        "password": "Secure123!"
    }
    response = client.post(
        "/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] > 0
    assert "refresh_token" in data
    assert isinstance(data["refresh_expires_in"], int)
    assert data["refresh_expires_in"] > 0

    decoded = jwt.decode(data["access_token"], key=None, options={"verify_signature": False})
    assert decoded["sub"] == "testuser123"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: TestClient):
    payload = {
        "username": "testuser123",
        "password": "WrongPassword!"
    }
    response = client.post(
        "/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Invalid credentials"]}

@pytest.mark.asyncio
async def test_profile_success(client: TestClient, test_user):
    login_response = client.post(
        "/auth/login",
        data={"username": "testuser123", "password": "Secure123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testuser123"
    assert data["email"] == "test123@gmail.com"
    assert data["role"] == "user"

@pytest.mark.asyncio
async def test_profile_invalid_token(client: TestClient):
    response = client.get(
        "/auth/profile",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Invalid access token"]}