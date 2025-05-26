import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.domain.product import ProductModel
from datetime import date, timedelta

VALID_IMAGE_URL = "http://example.com/image.png"

@pytest.fixture
def test_product_payload():
    return {
        "description": "Test Product Alpha",
        "price": 19.99,
        "barcode": "ALPHA123456",
        "section": "TestSectionA",
        "stock": 50,
        "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
        "image_url": VALID_IMAGE_URL
    }

@pytest.fixture
def test_product_payload_beta():
    return {
        "description": "Test Product Beta",
        "price": 25.50,
        "barcode": "BETA789012",
        "section": "TestSectionB",
        "stock": 100,
        "expiry_date": (date.today() + timedelta(days=60)).isoformat(),
        "image_url": "https://example.com/beta_image.jpg"
    }

@pytest.fixture
def test_product_payload_gamma_section_a():
    return {
        "description": "Test Product Gamma",
        "price": 9.75,
        "barcode": "GAMMA345678",
        "section": "TestSectionA",
        "stock": 0, # Indisponível
        "expiry_date": (date.today() + timedelta(days=90)).isoformat(),
        "image_url": "http://example.com/gamma_image.webp"
    }

@pytest.fixture
def created_product(db_session: Session, test_product_payload):
    product_data_for_model = test_product_payload.copy()
    if isinstance(product_data_for_model.get("expiry_date"), str):
        product_data_for_model["expiry_date"] = date.fromisoformat(product_data_for_model["expiry_date"])
    
    product = ProductModel(**product_data_for_model)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.mark.asyncio
async def test_create_product_success(authenticated_client: TestClient, test_product_payload, db_session: Session):
    response = authenticated_client.post("/products/", json=test_product_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert data["description"] == test_product_payload["description"]
    assert data["price"] == test_product_payload["price"]
    assert data["barcode"] == test_product_payload["barcode"]
    assert data["section"] == test_product_payload["section"]
    assert data["stock"] == test_product_payload["stock"]
    assert data["expiry_date"] == test_product_payload["expiry_date"]
    assert data["image_url"] == test_product_payload["image_url"]
    assert "id" in data

    product_in_db = db_session.query(ProductModel).filter(ProductModel.id == data["id"]).first()
    assert product_in_db is not None
    assert product_in_db.barcode == test_product_payload["barcode"]

@pytest.mark.asyncio
async def test_create_product_barcode_conflict(authenticated_client: TestClient, created_product):
    conflict_payload = {
        "description": "Another Product Same Barcode",
        "price": 10.0,
        "barcode": created_product.barcode, # Barcode já existente
        "section": "ConflictSection",
        "stock": 1,
        "image_url": VALID_IMAGE_URL
    }
    response = authenticated_client.post("/products/", json=conflict_payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["errors"][0] == "Barcode already registered" # Ajustado para detail conforme HTTPException comum

@pytest.mark.asyncio
async def test_create_product_invalid_input_schema(authenticated_client: TestClient):
    invalid_payload = {
        "description": "", "price": -10.0, "barcode": "INVALID BARCODE", 
        "section": "!@#$", "stock": 0, "expiry_date": "not-a-date",
        "image_url": "ftp://example.com/image.png"
    }
    response = authenticated_client.post("/products/", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["errors"] # FastAPI default error structure
    
    locs = [tuple(err["loc"]) for err in errors]
    assert ("body", "description") in locs
    assert ("body", "price") in locs
    assert ("body", "barcode") in locs
    assert ("body", "section") in locs
    assert ("body", "stock") in locs
    assert ("body", "expiry_date") in locs
    assert ("body", "image_url") in locs

@pytest.mark.asyncio
async def test_get_product_by_id_success(authenticated_client: TestClient, created_product):
    response = authenticated_client.get(f"/products/{created_product.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["id"] == created_product.id
    assert data["description"] == created_product.description
    assert data["price"] == created_product.price
    assert data["barcode"] == created_product.barcode
    assert data["expiry_date"] == created_product.expiry_date.isoformat() if created_product.expiry_date else None

@pytest.mark.asyncio
async def test_get_product_by_id_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_update_product_success(authenticated_client: TestClient, created_product, db_session: Session):
    update_payload = {
        "description": "Updated Test Product Alpha",
        "price": 25.99,
        "barcode": created_product.barcode, # Mesmo barcode
        "section": "UpdatedSection",
        "stock": 75,
        "expiry_date": (date.today() + timedelta(days=15)).isoformat(),
        "image_url": "http://example.com/updated_image.png"
    }
    response = authenticated_client.put(f"/products/{created_product.id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == update_payload["description"]
    assert data["price"] == update_payload["price"]
    assert data["stock"] == update_payload["stock"]

    db_product = db_session.query(ProductModel).filter(ProductModel.id == created_product.id).first()
    assert db_product.description == update_payload["description"]

@pytest.mark.asyncio
async def test_update_product_not_found(authenticated_client: TestClient, test_product_payload):
    response = authenticated_client.put("/products/99999", json=test_product_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_update_product_barcode_conflict(authenticated_client: TestClient, created_product, test_product_payload_beta, db_session: Session):
    payload_beta_for_model = test_product_payload_beta.copy()
    if isinstance(payload_beta_for_model.get("expiry_date"), str):
        payload_beta_for_model["expiry_date"] = date.fromisoformat(payload_beta_for_model["expiry_date"])
    product_beta = ProductModel(**payload_beta_for_model)
    db_session.add(product_beta)
    db_session.commit()
    db_session.refresh(product_beta)

    update_conflict_payload = {
        "description": "Conflict Update", "price": 10.0,
        "barcode": product_beta.barcode, # Barcode que já existe em product_beta
        "section": "ConflictSection", "stock": 10, "image_url": VALID_IMAGE_URL
    }
    response = authenticated_client.put(f"/products/{created_product.id}", json=update_conflict_payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["errors"][0] == "Barcode already registered for another product"

@pytest.mark.asyncio
async def test_delete_product_success(authenticated_client: TestClient, created_product, db_session: Session):
    response = authenticated_client.delete(f"/products/{created_product.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not response.content # Sem conteúdo para 204

    db_product = db_session.query(ProductModel).filter(ProductModel.id == created_product.id).first()
    assert db_product is None

@pytest.mark.asyncio
async def test_delete_product_not_found(authenticated_client: TestClient):
    response = authenticated_client.delete("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_get_products_list_success_and_pagination(authenticated_client: TestClient, db_session: Session, test_product_payload, test_product_payload_beta):
    p1_data = test_product_payload.copy()
    if isinstance(p1_data.get("expiry_date"), str): p1_data["expiry_date"] = date.fromisoformat(p1_data["expiry_date"])
    db_session.add(ProductModel(**p1_data))

    p2_data = test_product_payload_beta.copy()
    if isinstance(p2_data.get("expiry_date"), str): p2_data["expiry_date"] = date.fromisoformat(p2_data["expiry_date"])
    db_session.add(ProductModel(**p2_data))
    db_session.commit()

    response_all = authenticated_client.get("/products/")
    assert response_all.status_code == status.HTTP_200_OK
    data_all = response_all.json()
    assert isinstance(data_all, list)
    assert len(data_all) >= 2 
    
    barcodes_in_response = [p["barcode"] for p in data_all]
    assert p1_data["barcode"] in barcodes_in_response
    assert p2_data["barcode"] in barcodes_in_response

    # Teste com limit=1
    response_limit1 = authenticated_client.get("/products/?limit=1")
    assert response_limit1.status_code == status.HTTP_200_OK
    data_limit1 = response_limit1.json()
    assert len(data_limit1) == 1

    response_skip1_limit1 = authenticated_client.get("/products/?skip=1&limit=1")
    assert response_skip1_limit1.status_code == status.HTTP_200_OK
    data_skip1_limit1 = response_skip1_limit1.json()
    assert len(data_skip1_limit1) == 1

    if len(data_all) > 1:
         assert data_skip1_limit1[0]["barcode"] == data_all[1]["barcode"]


@pytest.mark.asyncio
async def test_get_products_with_filters(
    authenticated_client: TestClient, db_session: Session,
    test_product_payload, test_product_payload_beta, test_product_payload_gamma_section_a
):
    db_session.query(ProductModel).delete()
    db_session.commit()

    p1_data = test_product_payload.copy() 
    if isinstance(p1_data.get("expiry_date"), str): p1_data["expiry_date"] = date.fromisoformat(p1_data["expiry_date"])
    db_session.add(ProductModel(**p1_data))

    p2_data = test_product_payload_beta.copy() 
    if isinstance(p2_data.get("expiry_date"), str): p2_data["expiry_date"] = date.fromisoformat(p2_data["expiry_date"])
    db_session.add(ProductModel(**p2_data))

    p3_data = test_product_payload_gamma_section_a.copy() 
    if isinstance(p3_data.get("expiry_date"), str): p3_data["expiry_date"] = date.fromisoformat(p3_data["expiry_date"])
    db_session.add(ProductModel(**p3_data))
    db_session.commit()

    response_section_a = authenticated_client.get("/products/?section=TestSectionA")
    assert response_section_a.status_code == status.HTTP_200_OK
    data_section_a = response_section_a.json()
    assert len(data_section_a) == 2
    assert all(p["section"] == "TestSectionA" for p in data_section_a)
    barcodes_section_a = {p["barcode"] for p in data_section_a}
    assert p1_data["barcode"] in barcodes_section_a
    assert p3_data["barcode"] in barcodes_section_a

    response_min_price = authenticated_client.get("/products/?min_price=20.0")
    assert response_min_price.status_code == status.HTTP_200_OK
    data_min_price = response_min_price.json()
    assert len(data_min_price) == 1
    assert data_min_price[0]["barcode"] == p2_data["barcode"]

    response_max_price = authenticated_client.get("/products/?max_price=10.0")
    assert response_max_price.status_code == status.HTTP_200_OK
    data_max_price = response_max_price.json()
    assert len(data_max_price) == 1
    assert data_max_price[0]["barcode"] == p3_data["barcode"]

    response_available_true = authenticated_client.get("/products/?available=true")
    assert response_available_true.status_code == status.HTTP_200_OK
    data_available_true = response_available_true.json()
    assert len(data_available_true) == 2
    barcodes_available_true = {p["barcode"] for p in data_available_true}
    assert p1_data["barcode"] in barcodes_available_true
    assert p2_data["barcode"] in barcodes_available_true

    response_available_false = authenticated_client.get("/products/?available=false")
    assert response_available_false.status_code == status.HTTP_200_OK
    data_available_false = response_available_false.json()
    assert len(data_available_false) == 1
    assert data_available_false[0]["barcode"] == p3_data["barcode"]

    response_combined = authenticated_client.get("/products/?section=TestSectionA&available=true")
    assert response_combined.status_code == status.HTTP_200_OK
    data_combined = response_combined.json()
    assert len(data_combined) == 1
    assert data_combined[0]["barcode"] == p1_data["barcode"]