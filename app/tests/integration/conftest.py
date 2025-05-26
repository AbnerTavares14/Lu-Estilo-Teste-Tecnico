from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app as fastapi_app
from app.api.dependencies.db import get_db_session
from app.api.dependencies.auth import get_current_user
from app.models.domain.product import ProductModel
from sqlalchemy.orm import Session

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    if transaction.is_active: 
        transaction.rollback()
    connection.close()


@pytest.fixture
def authenticated_client(client: TestClient, test_user):
    payload = {"username": "testuser123", "password": "Secure123!"}
    response = client.post(
        "/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    fastapi_app.dependency_overrides[get_db_session] = _override_get_db
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def override_get_current_user(test_user):
    def _override_get_current_user_func():
        pass 
    
    fastapi_app.dependency_overrides[get_current_user] = _override_get_current_user_func
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db):
    with TestClient(fastapi_app) as client:
        yield client

@pytest.fixture(scope="function")
def test_user(db_session):
    from app.models.domain.user import UserModel
    from passlib.context import CryptContext
    crypt_context = CryptContext(schemes=["sha256_crypt"])
    user = UserModel(
        username="testuser123",
        email="test123@gmail.com",
        password_hash=crypt_context.hash("Secure123!"),
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_refresh_token(db_session, test_user):
    from app.models.domain.refresh_token import RefreshTokenModel
    from datetime import datetime, timedelta, timezone
    refresh_token = RefreshTokenModel(
        user_id=test_user.id,
        token="123e4567-e89b-12d3-a456-426614174000",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(refresh_token)
    db_session.commit()
    return refresh_token

@pytest.fixture
def product_section_A_barcode() -> str:
    return "FILTER_SEC_A_PROD_UNIQUE" # Garanta unicidade

@pytest.fixture
def product_section_A_for_filter(db_session: Session, product_section_A_barcode: str) -> ProductModel:
    prod = db_session.query(ProductModel).filter_by(barcode=product_section_A_barcode).first()
    if prod:
        prod.stock = 50 # Reset
        db_session.commit()
        return prod
    prod = ProductModel(description="Filter Sec A Prod", price=5.0, barcode=product_section_A_barcode, section="FilterSectionA", stock=50, image_url="https://images.kabum.com.br/produtos/fotos/sync_mirakl/649731/xlarge/Smartphone-Samsung-Galaxy-A06-128GB-Azul-Escuro-4g-Ram-4gb-C-mera-50mp-Selfie-8mp-Tela-6-7-_1742413229.jpg")
    db_session.add(prod)
    db_session.commit(); db_session.refresh(prod)
    return prod

@pytest.fixture(autouse=True)
def disable_sentry(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "")
    yield
