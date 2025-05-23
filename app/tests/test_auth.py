from unittest.mock import patch
import pytest
from fastapi import HTTPException, status
from app.models.domain.refresh_token import RefreshTokenModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.models.domain.user import UserModel
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.api.dependencies.db import token_verifier

@pytest.mark.asyncio
async def test_refresh_token_success(client: TestClient, test_refresh_token):
    payload = {
        "refresh_token": test_refresh_token.token
    }
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != test_refresh_token.token  
    assert "refresh_expires_in" in data

@pytest.mark.asyncio
async def test_refresh_token_invalid(client: TestClient):
    payload = {
        "refresh_token": "invalid_token"
    }
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Invalid refresh token"]}

@pytest.mark.asyncio
async def test_refresh_token_expired(client: TestClient, db_session: Session, test_user):
    expired_token = RefreshTokenModel(
        user_id=test_user.id,
        token="expired-123e4567-e89b-12d3-a456-426614174000",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(expired_token)
    db_session.commit()

    payload = {
        "refresh_token": expired_token.token
    }
    response = client.post("/auth/refresh-token", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Refresh token expired"]}

    token = db_session.query(RefreshTokenModel).filter_by(token=expired_token.token).first()
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
    assert "expires_in" in data
    assert "refresh_token" in data
    assert "refresh_expires_in" in data

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
async def test_profile_success(client: TestClient, test_user: UserModel):
    fastapi_app.dependency_overrides[token_verifier] = lambda: test_user
    try:
        response = client.get(
            "/auth/profile",
            headers={"Authorization": "Bearer some_valid_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "success"}
    finally:
        fastapi_app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_profile_invalid_token(client: TestClient):
    with patch("app.api.dependencies.db.token_verifier", side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")):
        response = client.get(
            "/auth/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"errors": ["Invalid access token"]}