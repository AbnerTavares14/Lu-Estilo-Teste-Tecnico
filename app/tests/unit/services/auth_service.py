from unittest.mock import Mock
import pytest

from jose import JWTError, jwt 
from datetime import datetime, timedelta, timezone 
from fastapi import HTTPException, status
import uuid

from app.models.schemas.user import UserCreate, UserLogin
from app.models.domain.user import UserModel
from app.models.domain.refresh_token import RefreshTokenModel
from app.services.auth import AuthService, crypt_context
from app.core.config import settings




@pytest.fixture
def mock_auth_repo(mocker):
    return mocker.Mock()

@pytest.fixture
def auth_service(mock_auth_repo):
    return AuthService(auth_repo=mock_auth_repo)

@pytest.fixture
def sample_user_password() -> str:
    return "ValidPassword123!"

@pytest.fixture
def sample_user_create(sample_user_password: str) -> UserCreate:
    return UserCreate(username="testuser", email="test@example.com", password=sample_user_password)

@pytest.fixture
def sample_user_login(sample_user_password: str) -> UserLogin:
    return UserLogin(username="testuser", password=sample_user_password)

@pytest.fixture
def sample_db_user(sample_user_password: str, mocker) -> UserModel:
    user = mocker.Mock(spec=UserModel)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = crypt_context.hash(sample_user_password)
    user.role = "user"
    user.created_at = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = None
    return user

@pytest.fixture
def sample_refresh_token_model(sample_db_user: UserModel, mocker) -> RefreshTokenModel:
    token_model = mocker.Mock(spec=RefreshTokenModel)
    token_model.id = 1
    token_model.user_id = sample_db_user.id
    token_model.token = str(uuid.uuid4())
    token_model.expires_at = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc) 
    token_model.created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return token_model


class TestAuthService:

    def test_create_user(self, auth_service: AuthService, mock_auth_repo: Mock, sample_user_create: UserCreate):
        mock_auth_repo.create_user.return_value = "dummy_user_obj"
        result = auth_service.create_user(sample_user_create)
        mock_auth_repo.create_user.assert_called_once_with(
            username=sample_user_create.username,
            email=sample_user_create.email,
            password=sample_user_create.password,
            role="user"
        )
        assert result == "dummy_user_obj"

    def test_authenticate_user_success(
        self, auth_service: AuthService, mock_auth_repo: Mock,
        sample_user_login: UserLogin, sample_db_user: UserModel, mocker
    ):
        mock_auth_repo.get_user_by_username.return_value = sample_db_user
        mocker.patch.object(crypt_context, 'verify', return_value=True)
        mock_jwt_encode = mocker.patch('app.services.auth.jwt.encode', return_value="dummy_access_token")
        mock_auth_repo.create_refresh_token.return_value = None

        fixed_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        mocked_datetime_class = mocker.patch('app.services.auth.datetime')
        mocked_datetime_class.now.return_value = fixed_now

        response = auth_service.authenticate_user(sample_user_login)

        mock_auth_repo.get_user_by_username.assert_called_once_with(sample_user_login.username)
        crypt_context.verify.assert_called_once_with(sample_user_login.password, sample_db_user.password_hash)
        
        expected_access_payload = {
            "sub": sample_db_user.username,
            "exp": fixed_now + timedelta(seconds=3600), 
            "type": "access"
        }
        mock_jwt_encode.assert_called_once_with(expected_access_payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
        
        create_refresh_call_args, _ = mock_auth_repo.create_refresh_token.call_args
        assert create_refresh_call_args[0] == sample_db_user.id
        assert isinstance(create_refresh_call_args[1], str) 
        assert create_refresh_call_args[2] == fixed_now + timedelta(seconds=7 * 24 * 3600)

        assert response["access_token"] == "dummy_access_token"
        assert "refresh_token" in response

    def test_authenticate_user_not_found(self, auth_service: AuthService, mock_auth_repo: Mock, sample_user_login: UserLogin):
        mock_auth_repo.get_user_by_username.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            auth_service.authenticate_user(sample_user_login)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

    def test_authenticate_user_invalid_password(
        self, auth_service: AuthService, mock_auth_repo: Mock,
        sample_user_login: UserLogin, sample_db_user: UserModel, mocker
    ):
        mock_auth_repo.get_user_by_username.return_value = sample_db_user
        mocker.patch.object(crypt_context, 'verify', return_value=False)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.authenticate_user(sample_user_login)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"


    def test_verify_token_success(self, auth_service: AuthService, mock_auth_repo: Mock, sample_db_user: UserModel, mocker):
        valid_token = "valid_access_token"
        fixed_exp_time = datetime.now(timezone.utc) + timedelta(hours=1) 
        decoded_payload = {"sub": sample_db_user.username, "type": "access", "exp": fixed_exp_time}
        
        mock_jwt_decode = mocker.patch('app.services.auth.jwt.decode', return_value=decoded_payload)
        mock_auth_repo.get_user_by_username.return_value = sample_db_user

        user = auth_service.verify_token(valid_token)

        mock_jwt_decode.assert_called_once_with(valid_token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        mock_auth_repo.get_user_by_username.assert_called_once_with(sample_db_user.username)
        assert user == sample_db_user

    def test_verify_token_jwt_error(self, auth_service: AuthService, mocker):
        invalid_token = "invalid_token"
        mocker.patch('app.services.auth.jwt.decode', side_effect=JWTError("Token error"))
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(invalid_token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid access token"

    def test_verify_token_user_not_found(self, auth_service: AuthService, mock_auth_repo: Mock, mocker):
        token_user_nonexistent = "token_user_nonexistent"
        fixed_exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        decoded_payload = {"sub": "nonexistentuser", "type": "access", "exp": fixed_exp_time}
        
        mocker.patch('app.services.auth.jwt.decode', return_value=decoded_payload)
        mock_auth_repo.get_user_by_username.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token_user_nonexistent)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid access token"


    def test_verify_token_invalid_type(self, auth_service: AuthService, mock_auth_repo: Mock, sample_db_user: UserModel, mocker):

        token_wrong_type = "token_with_wrong_type"
        fixed_exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        decoded_payload = {"sub": sample_db_user.username, "type": "refresh", "exp": fixed_exp_time}
        mocker.patch('app.services.auth.jwt.decode', return_value=decoded_payload)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token_wrong_type)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid access token"
        mock_auth_repo.get_user_by_username.assert_not_called() 

    def test_refresh_access_token_success(
        self, auth_service: AuthService, mock_auth_repo: Mock,
        sample_refresh_token_model: RefreshTokenModel, sample_db_user: UserModel, mocker
    ):
        mock_auth_repo.get_refresh_token.return_value = sample_refresh_token_model
        mock_auth_repo.get_user_by_id.return_value = sample_db_user
        mock_jwt_encode = mocker.patch('app.services.auth.jwt.encode', return_value="new_dummy_access_token")
        mock_auth_repo.delete_refresh_token.return_value = None
        mock_auth_repo.create_refresh_token.return_value = None

        controlled_now = datetime(2025, 1, 7, 0, 0, 0, tzinfo=timezone.utc) 
        
        mocked_datetime_class = mocker.patch('app.services.auth.datetime')
        mocked_datetime_class.now.return_value = controlled_now

        response = auth_service.refresh_access_token(sample_refresh_token_model.token)

        mock_auth_repo.get_refresh_token.assert_called_once_with(sample_refresh_token_model.token)
        mock_auth_repo.get_user_by_id.assert_called_once_with(sample_refresh_token_model.user_id)
        
        expected_access_payload = {
            "sub": sample_db_user.username,
            "exp": controlled_now + timedelta(seconds=3600),
            "type": "access"
        }
        mock_jwt_encode.assert_called_once_with(expected_access_payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
        
        mock_auth_repo.delete_refresh_token.assert_called_once_with(sample_refresh_token_model.token)
        
        create_refresh_call_args, _ = mock_auth_repo.create_refresh_token.call_args
        assert create_refresh_call_args[0] == sample_db_user.id
        assert isinstance(create_refresh_call_args[1], str) 
        assert create_refresh_call_args[2] == controlled_now + timedelta(days=7)

        assert response["access_token"] == "new_dummy_access_token"
        assert response["refresh_token"] != sample_refresh_token_model.token

    def test_refresh_access_token_invalid_token(self, auth_service: AuthService, mock_auth_repo: Mock):
        mock_auth_repo.get_refresh_token.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("invalid_refresh_token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid refresh token"


    def test_refresh_access_token_expired(
        self, auth_service: AuthService, mock_auth_repo: Mock,
        sample_refresh_token_model: RefreshTokenModel, mocker
    ):
        mock_auth_repo.get_refresh_token.return_value = sample_refresh_token_model
        

        time_after_expiry = datetime(2025, 1, 9, 0, 0, 0, tzinfo=timezone.utc) 
        
        
        mocked_datetime_class = mocker.patch('app.services.auth.datetime')
        mocked_datetime_class.now.return_value = time_after_expiry


        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(sample_refresh_token_model.token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Refresh token expired"
        mock_auth_repo.delete_refresh_token.assert_called_once_with(sample_refresh_token_model.token)

    def test_refresh_access_token_user_not_found_for_token(
        self, auth_service: AuthService, mock_auth_repo: Mock,
        sample_refresh_token_model: RefreshTokenModel, mocker
    ):
        mock_auth_repo.get_refresh_token.return_value = sample_refresh_token_model
        mock_auth_repo.get_user_by_id.return_value = None 


        time_before_expiry = datetime(2025, 1, 7, 0, 0, 0, tzinfo=timezone.utc) 
        

        mocked_datetime_class = mocker.patch('app.services.auth.datetime')
        mocked_datetime_class.now.return_value = time_before_expiry
        


        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(sample_refresh_token_model.token)
            
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "User not found" 