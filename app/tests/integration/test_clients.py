import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.domain.customer import CustomerModel
from app.main import app as fastapi_app

@pytest.fixture
def test_customer(db_session: Session):
    customer = CustomerModel(
        name="João Silva",
        email="joao.silva@example.com",
        cpf="78819522020",
        phone_number="11999999999"  
    )
    db_session.add(customer)
    db_session.commit()
    return customer

@pytest.mark.asyncio
async def test_get_customers_success(authenticated_client: TestClient, test_customer):
    response = authenticated_client.get("/clients?limit=10&skip=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "João Silva"
    assert data[0]["email"] == "joao.silva@example.com"
    assert data[0]["cpf"] == "78819522020"

@pytest.mark.asyncio
async def test_get_customers_ordered_by_name(authenticated_client: TestClient, db_session: Session):
    customer1 = CustomerModel(name="Ana Costa", email="ana@example.com", cpf="586.930.450-40")
    customer2 = CustomerModel(name="Bruno Lima", email="bruno@example.com", cpf="22222222222")
    db_session.add_all([customer1, customer2])
    db_session.commit()

    response = authenticated_client.get("/clients?order_by=name&limit=10&skip=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Ana Costa"
    assert data[1]["name"] == "Bruno Lima"

@pytest.mark.asyncio
async def test_get_customer_by_id_success(authenticated_client: TestClient, test_customer):
    response = authenticated_client.get(f"/clients/{test_customer.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_customer.id
    assert data["name"] == "João Silva"
    assert data["email"] == "joao.silva@example.com"
    assert data["cpf"] == "78819522020"

@pytest.mark.asyncio
async def test_get_customer_by_id_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/clients/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"errors": ["Customer not found"]}

@pytest.mark.asyncio
async def test_create_customer_success(authenticated_client: TestClient, db_session: Session):
    payload = {
        "name": "Maria Oliveira",
        "email": "maria.oliveira@example.com",
        "cpf": "98765432100"
    }
    response = authenticated_client.post("/clients", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "success"}

    customer = db_session.query(CustomerModel).filter_by(email="maria.oliveira@example.com").first()
    assert customer is not None
    assert customer.name == "Maria Oliveira"
    assert customer.cpf == "98765432100"

@pytest.mark.asyncio
async def test_create_customer_email_conflict(authenticated_client: TestClient, test_customer):
    payload = {
        "name": "Outro Nome",
        "email": "joao.silva@example.com",
        "cpf": "71228223033"
    }
    response = authenticated_client.post("/clients", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"errors": ["Email already registered"]}

@pytest.mark.asyncio
async def test_create_customer_cpf_conflict(authenticated_client: TestClient, test_customer):
    payload = {
        "name": "Outro Nome",
        "email": "outro@example.com",
        "cpf": "78819522020"
    }
    response = authenticated_client.post("/clients", json=payload)
    if response.status_code == 422:
        print(f"Validation error in test_create_customer_cpf_conflict: {response.json()}")
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"errors": ["CPF already registered"]}

@pytest.mark.asyncio
async def test_create_customer_invalid_input(authenticated_client: TestClient):
    payload = {
        "name": "123",  
        "email": "invalid_email",
        "cpf": "123"  
    }
    response = authenticated_client.post("/clients", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["errors"]
    assert isinstance(errors, list)
    assert any("name" in str(error).lower() for error in errors)
    assert any("email" in str(error).lower() for error in errors)
    assert any("cpf" in str(error).lower() for error in errors)

@pytest.mark.asyncio
async def test_update_customer_success(authenticated_client: TestClient, test_customer, db_session: Session):
    payload = {
        "name": "João Souza",
        "email": "joao.souza@example.com",
        "cpf": "58693045040",
        "phone_number": "11999998898"
    }
    response = authenticated_client.put(f"/clients/{test_customer.id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "João Souza"
    assert data["email"] == "joao.souza@example.com"
    assert data["cpf"] == "58693045040"
    assert data["phone_number"] == "+5511999998898"

    updated_customer_from_db = db_session.query(CustomerModel).filter(CustomerModel.id == test_customer.id).first()
    assert updated_customer_from_db is not None
    assert updated_customer_from_db.name == "João Souza"
    assert updated_customer_from_db.email == "joao.souza@example.com"
    assert updated_customer_from_db.cpf == "58693045040"
    assert updated_customer_from_db.phone_number == "+5511999998898"

@pytest.mark.asyncio
async def test_update_customer_not_found(authenticated_client: TestClient):
    payload = {
        "name": "João Souza",
        "email": "joao.souza@example.com",
        "cpf": "58693045040"
    }
    response = authenticated_client.put("/clients/999", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"errors": ["Customer not found"]}

@pytest.mark.asyncio
async def test_update_customer_email_conflict(authenticated_client: TestClient, db_session: Session):
    customer1 = CustomerModel(name="Ana Costa", email="ana@example.com", cpf="586.930.450-40")
    customer2 = CustomerModel(name="Bruno Lima", email="bruno@example.com", cpf="32945832062")
    db_session.add_all([customer1, customer2])
    db_session.commit()

    payload = {
        "name": "Bruno Lima",
        "email": "ana@example.com",
        "cpf": "32945832062"
    }
    response = authenticated_client.put(f"/clients/{customer2.id}", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"errors": ["Email already registered"]}

@pytest.mark.asyncio
async def test_update_customer_cpf_conflict(authenticated_client: TestClient, db_session: Session):
    customer1 = CustomerModel(name="Ana Costa", email="ana@example.com", cpf="58693045040")
    customer2 = CustomerModel(name="Bruno Lima", email="bruno@example.com", cpf="22222222222")
    db_session.add_all([customer1, customer2])
    db_session.commit()

    payload = {
        "name": "Bruno Lima",
        "email": "bruno@example.com",
        "cpf": "58693045040"
    }
    response = authenticated_client.put(f"/clients/{customer2.id}", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"errors": ["CPF already registered"]}

@pytest.mark.asyncio
async def test_delete_customer_success(admin_authenticated_client: TestClient, test_customer, db_session: Session):
    response = admin_authenticated_client.delete(f"/clients/{test_customer.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    customer = db_session.query(CustomerModel).filter_by(id=test_customer.id).first()
    assert customer is None

@pytest.mark.asyncio
async def test_delete_customer_not_found(admin_authenticated_client: TestClient):
    response = admin_authenticated_client.delete("/clients/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"errors": ["Customer not found"]}