from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session, token_verifier
from app.api.dependencies.auth import UserManager
from app.models.schemas.user import UserCreate, UserLogin
from fastapi.security import OAuth2PasswordRequestForm
from app.models.schemas.user import RefreshTokenRequest

auth_route = APIRouter(prefix="/auth", tags=["auth"])


@auth_route.post("/register")
def user_register(
    user: UserCreate,
    db_session: Session = Depends(get_db_session)
):
    um = UserManager(db_session)
    um.create_user(user)
    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_201_CREATED)

@auth_route.post("/login")
def user_login(
    request_form_user: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(get_db_session)
):
    um = UserManager(db_session)
    user = UserLogin(
        username=request_form_user.username,
        password=request_form_user.password
    )  
    auth_data = um.authenticate_user(user=user)
    return JSONResponse(
        content=auth_data,
        status_code=status.HTTP_200_OK
    )


@auth_route.post("/refresh-token")
def refresh_token(
    request: RefreshTokenRequest,
    db_session: Session = Depends(get_db_session)
):
    um = UserManager(db_session)
    auth_data = um.refresh_access_token(refresh_token=request.refresh_token)
    return JSONResponse(
        content=auth_data,
        status_code=status.HTTP_200_OK
    )


@auth_route.get("/profile")
def user_profile(
    token_verify = Depends(token_verifier),
):
    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_200_OK
    )