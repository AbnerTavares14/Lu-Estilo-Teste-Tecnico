# app/api/routes/auth_route.py
from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse
from app.api.dependencies.auth import get_auth_service
from app.services.auth import AuthService
from app.models.schemas.user import UserCreate, UserLogin, RefreshTokenRequest
from fastapi.security import OAuth2PasswordRequestForm
from app.api.dependencies.auth import get_current_user

auth_route = APIRouter(prefix="/auth", tags=["auth"])

@auth_route.post("/register")
def user_register(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.create_user(user)
    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_201_CREATED
    )

@auth_route.post("/login")
def user_login(
    request_form_user: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = UserLogin(
        username=request_form_user.username,
        password=request_form_user.password
    )
    auth_data = auth_service.authenticate_user(user)
    return JSONResponse(
        content=auth_data,
        status_code=status.HTTP_200_OK
    )

@auth_route.post("/refresh-token")
def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    auth_data = auth_service.refresh_access_token(request.refresh_token)
    return JSONResponse(
        content=auth_data,
        status_code=status.HTTP_200_OK
    )

@auth_route.get("/profile")
def user_profile(
    user: AuthService = Depends(get_current_user)
):
    return JSONResponse(
        content={"username": user.username, "email": user.email, "role": user.role},
        status_code=status.HTTP_200_OK
    )