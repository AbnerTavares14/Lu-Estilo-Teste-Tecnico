import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, selectinload
from app.models.domain.product import ProductModel, ProductImageModel
from datetime import date, timedelta

VALID_IMAGE_URL_1 = "http://example.com/image.png"
VALID_IMAGE_URL_2 = "http://example.com/image2.png"
VALID_IMAGE_URL_3 = "http://example.com/image3.png"
VALID_IMAGE_URL_4 = "http://example.com/image4.png"

@pytest.fixture
def test_product_payload():
    return {
        "description": "Test Product Alpha",
        "price": 19.99,
        "barcode": "ALPHA123456",
        "section": "TestSectionA",
        "stock": 50,
        "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
        "image_urls": [VALID_IMAGE_URL_1, VALID_IMAGE_URL_2] 
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
        "image_urls": [VALID_IMAGE_URL_3] 
    }

@pytest.fixture
def test_product_payload_gamma_section_a():
    return {
        "description": "Test Product Gamma",
        "price": 9.75,
        "barcode": "GAMMA345678",
        "section": "TestSectionA",
        "stock": 0,
        "expiry_date": (date.today() + timedelta(days=90)).isoformat(),
        "image_urls": [VALID_IMAGE_URL_4] 
    }

@pytest.fixture
def created_product(db_session: Session, test_product_payload):
    product_data = test_product_payload.copy()
    image_urls = product_data.pop("image_urls", [])

    if isinstance(product_data.get("expiry_date"), str):
        product_data["expiry_date"] = date.fromisoformat(product_data["expiry_date"])
    
    product = ProductModel(**product_data)
    db_session.add(product)
    if image_urls:
        for url in image_urls:
            product.images.append(ProductImageModel(url=url)) 

    db_session.commit()
    db_session.refresh(product)
    db_session.expire(product) 
    _ = product.images 
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
    assert "id" in data
    
    assert "images" in data
    assert isinstance(data["images"], list)
    assert len(data["images"]) == len(test_product_payload["image_urls"])
    returned_urls = sorted([img["url"] for img in data["images"]])
    expected_urls = sorted(test_product_payload["image_urls"])
    assert returned_urls == expected_urls
    assert all("id" in img for img in data["images"]) 

    product_in_db = db_session.query(ProductModel).options(selectinload(ProductModel.images)).filter(ProductModel.id == data["id"]).first()
    assert product_in_db is not None
    assert product_in_db.barcode == test_product_payload["barcode"]
    assert len(product_in_db.images) == len(test_product_payload["image_urls"])
    db_image_urls = sorted([img.url for img in product_in_db.images])
    assert db_image_urls == expected_urls

@pytest.mark.asyncio
async def test_create_product_barcode_conflict(authenticated_client: TestClient, created_product):
    conflict_payload = {
        "description": "Another Product Same Barcode",
        "price": 10.0,
        "barcode": created_product.barcode, 
        "section": "ConflictSection",
        "stock": 1,
        "image_urls": [VALID_IMAGE_URL_3] 
    }
    response = authenticated_client.post("/products/", json=conflict_payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["errors"][0] == "Barcode already registered"

@pytest.mark.asyncio
async def test_create_product_invalid_input_schema(authenticated_client: TestClient):
    invalid_payload = {
        "description": "", 
        "price": -10.0, 
        "barcode": "INVALID BARCODE", 
        "section": "!@#$", 
        "stock": -1, 
        "expiry_date": "not-a-date",
        "image_urls": ["ftp://example.com/image.png", "not_a_valid_url"] 
    }
    response = authenticated_client.post("/products/", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["errors"]
    
    locs = [tuple(err["loc"]) for err in errors]
    assert ("body", "description") in locs
    assert ("body", "price") in locs
    # ... (outras validações de schema)
    assert ("body", "stock") in locs
    assert ("body", "image_urls", 0) in locs or ("body", "image_urls", 1) in locs 


@pytest.mark.asyncio
async def test_get_product_by_id_success(authenticated_client: TestClient, created_product: ProductModel, db_session: Session):
    live_product_from_fixture = db_session.query(ProductModel).options(selectinload(ProductModel.images)).get(created_product.id)

    response = authenticated_client.get(f"/products/{live_product_from_fixture.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["id"] == live_product_from_fixture.id
    assert data["description"] == live_product_from_fixture.description
    assert "images" in data
    assert isinstance(data["images"], list)
    assert len(data["images"]) == len(live_product_from_fixture.images)
    
    expected_image_urls = sorted([img.url for img in live_product_from_fixture.images])
    returned_image_urls = sorted([img_data["url"] for img_data in data["images"]])
    assert returned_image_urls == expected_image_urls


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_update_product_success(authenticated_client: TestClient, created_product: ProductModel, db_session: Session):
    product_id_to_update = created_product.id
    new_image_list = [VALID_IMAGE_URL_3, "https://newdomain.com/new_image.jpeg"]
    
    update_payload = {
        "description": "Updated Product Alpha New Images",
        "price": 29.99,
        "barcode": created_product.barcode,
        "section": "UpdatedSectionAlpha",
        "stock": 75,
        "expiry_date": (date.today() + timedelta(days=45)).isoformat(),
        "image_urls": new_image_list
    }
    response = authenticated_client.put(f"/products/{product_id_to_update}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["description"] == update_payload["description"]
    assert data["price"] == update_payload["price"]
    assert len(data["images"]) == len(new_image_list)
    assert sorted([img["url"] for img in data["images"]]) == sorted(new_image_list)

    db_product = db_session.query(ProductModel).options(selectinload(ProductModel.images)).filter(ProductModel.id == product_id_to_update).first()
    assert db_product is not None
    assert db_product.description == update_payload["description"]
    assert len(db_product.images) == len(new_image_list)
    assert sorted([img.url for img in db_product.images]) == sorted(new_image_list)

@pytest.mark.asyncio
async def test_update_product_remove_all_images(authenticated_client: TestClient, created_product: ProductModel, db_session: Session):
    product_id_to_update = created_product.id 
    
    update_payload = { 
        "description": created_product.description,
        "price": created_product.price,
        "barcode": created_product.barcode,
        "section": created_product.section,
        "stock": created_product.stock,
        "image_urls": []
    }
    response = authenticated_client.put(f"/products/{product_id_to_update}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "images" in data
    assert len(data["images"]) == 0

    db_product = db_session.query(ProductModel).options(selectinload(ProductModel.images)).filter(ProductModel.id == product_id_to_update).first()
    assert db_product is not None
    assert len(db_product.images) == 0

@pytest.mark.asyncio
async def test_update_product_not_found(authenticated_client: TestClient, test_product_payload):
    response = authenticated_client.put("/products/99999", json=test_product_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_update_product_barcode_conflict(authenticated_client: TestClient, created_product: ProductModel, test_product_payload_beta, db_session: Session):
    product_to_update_id = created_product.id 

    payload_beta_api = test_product_payload_beta.copy()
    res_beta = authenticated_client.post("/products/", json=payload_beta_api)
    assert res_beta.status_code == status.HTTP_201_CREATED
    product_beta_data = res_beta.json()
    product_beta_barcode = product_beta_data["barcode"]

    update_conflict_payload = {
        "description": "Conflict Update", "price": 10.0,
        "barcode": product_beta_barcode, 
        "section": "ConflictSection", "stock": 10,
        "image_urls": [VALID_IMAGE_URL_1] 
    }
    response = authenticated_client.put(f"/products/{product_to_update_id}", json=update_conflict_payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["errors"][0] == "Barcode already registered for another product"

@pytest.mark.asyncio
async def test_get_products_list_includes_images(authenticated_client: TestClient, created_product: ProductModel, db_session: Session):
    live_created_product = db_session.query(ProductModel).options(selectinload(ProductModel.images)).get(created_product.id)


    response = authenticated_client.get("/products/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    found_product_data = None
    for p_data in data:
        if p_data["id"] == live_created_product.id:
            found_product_data = p_data
            break
    
    assert found_product_data is not None, "Produto criado pela fixture não encontrado na lista"
    assert "images" in found_product_data
    assert isinstance(found_product_data["images"], list)
    assert len(found_product_data["images"]) == len(live_created_product.images)
    if live_created_product.images: 
        assert found_product_data["images"][0]["url"] == live_created_product.images[0].url


@pytest.mark.asyncio
async def test_delete_product_success(authenticated_client: TestClient, created_product, db_session: Session):
    response = authenticated_client.delete(f"/products/{created_product.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not response.content 

    db_product = db_session.query(ProductModel).filter(ProductModel.id == created_product.id).first()
    assert db_product is None

@pytest.mark.asyncio
async def test_delete_product_not_found(authenticated_client: TestClient):
    response = authenticated_client.delete("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Product not found"

@pytest.mark.asyncio
async def test_get_products_list_success_and_pagination(authenticated_client: TestClient, db_session: Session, test_product_payload, test_product_payload_beta):
    db_session.query(ProductImageModel).delete()
    db_session.query(ProductModel).delete()
    db_session.commit()

    p1_dict_payload = test_product_payload.copy()
    p1_image_urls = p1_dict_payload.pop("image_urls", [])
    if isinstance(p1_dict_payload.get("expiry_date"), str):
         p1_dict_payload["expiry_date"] = date.fromisoformat(p1_dict_payload["expiry_date"])
    product1 = ProductModel(**p1_dict_payload)
    for url in p1_image_urls:
        product1.images.append(ProductImageModel(url=url))
    db_session.add(product1)

    p2_dict_payload = test_product_payload_beta.copy()
    p2_image_urls = p2_dict_payload.pop("image_urls", [])
    if isinstance(p2_dict_payload.get("expiry_date"), str):
         p2_dict_payload["expiry_date"] = date.fromisoformat(p2_dict_payload["expiry_date"])
    product2 = ProductModel(**p2_dict_payload)
    for url in p2_image_urls:
        product2.images.append(ProductImageModel(url=url))
    db_session.add(product2)

    db_session.commit()
    p1_barcode = product1.barcode
    p2_barcode = product2.barcode


    response_all = authenticated_client.get("/products/")
    assert response_all.status_code == status.HTTP_200_OK
    data_all = response_all.json()
    assert isinstance(data_all, list)
    assert len(data_all) >= 2 

    barcodes_in_response = {p["barcode"] for p in data_all}
    assert p1_barcode in barcodes_in_response
    assert p2_barcode in barcodes_in_response

    response_limit1 = authenticated_client.get("/products/?limit=1")
    assert response_limit1.status_code == status.HTTP_200_OK
    data_limit1 = response_limit1.json()
    assert len(data_limit1) == 1

    response_skip1_limit1 = authenticated_client.get("/products/?skip=1&limit=1")
    assert response_skip1_limit1.status_code == status.HTTP_200_OK
    data_skip1_limit1 = response_skip1_limit1.json()
    assert len(data_skip1_limit1) == 1

    all_ids_ordered = sorted([p["id"] for p in data_all])
    if len(all_ids_ordered) > 1:
        second_product_id_in_list = all_ids_ordered[1]
        expected_second_product_barcode = next(p["barcode"] for p in data_all if p["id"] == second_product_id_in_list)
        assert data_skip1_limit1[0]["barcode"] == expected_second_product_barcode


@pytest.mark.asyncio
async def test_get_products_with_filters(
    authenticated_client: TestClient, db_session: Session,
    test_product_payload, 
    test_product_payload_beta, 
    test_product_payload_gamma_section_a 
):
    db_session.query(ProductImageModel).delete()
    db_session.query(ProductModel).delete()
    db_session.commit()

    res_p1 = authenticated_client.post("/products/", json=test_product_payload)
    assert res_p1.status_code == status.HTTP_201_CREATED, f"P1 creation failed: {res_p1.json()}"
    p1_data_from_api = res_p1.json()

    res_p2 = authenticated_client.post("/products/", json=test_product_payload_beta)
    assert res_p2.status_code == status.HTTP_201_CREATED, f"P2 creation failed: {res_p2.json()}"
    p2_data_from_api = res_p2.json()

    res_p3 = authenticated_client.post("/products/", json=test_product_payload_gamma_section_a)
    assert res_p3.status_code == status.HTTP_201_CREATED, f"P3 creation failed: {res_p3.json()}"
    p3_data_from_api = res_p3.json()

    target_section = p1_data_from_api['section']
    response_section_a = authenticated_client.get(f"/products/?section={target_section}")
    assert response_section_a.status_code == status.HTTP_200_OK
    data_section_a = response_section_a.json()
    
    assert len(data_section_a) == 2 
    returned_barcodes_section_a = {p["barcode"] for p in data_section_a}
    assert p1_data_from_api["barcode"] in returned_barcodes_section_a
    assert p3_data_from_api["barcode"] in returned_barcodes_section_a
    for p in data_section_a:
        assert "images" in p 
        assert isinstance(p["images"], list)

    response_min_price = authenticated_client.get("/products/?min_price=20.0")
    assert response_min_price.status_code == status.HTTP_200_OK
    data_min_price = response_min_price.json()
    assert len(data_min_price) == 1
    assert data_min_price[0]["barcode"] == p2_data_from_api["barcode"]

    response_max_price = authenticated_client.get("/products/?max_price=10.0")
    assert response_max_price.status_code == status.HTTP_200_OK
    data_max_price = response_max_price.json()
    assert len(data_max_price) == 1
    assert data_max_price[0]["barcode"] == p3_data_from_api["barcode"]

    response_available_true = authenticated_client.get("/products/?available=true")
    assert response_available_true.status_code == status.HTTP_200_OK
    data_available_true = response_available_true.json()
    assert len(data_available_true) == 2
    barcodes_available_true = {p["barcode"] for p in data_available_true}
    assert p1_data_from_api["barcode"] in barcodes_available_true
    assert p2_data_from_api["barcode"] in barcodes_available_true

    response_available_false = authenticated_client.get("/products/?available=false")
    assert response_available_false.status_code == status.HTTP_200_OK
    data_available_false = response_available_false.json()
    assert len(data_available_false) == 1
    assert data_available_false[0]["barcode"] == p3_data_from_api["barcode"]

    response_combined = authenticated_client.get(f"/products/?section={target_section}&available=true")
    assert response_combined.status_code == status.HTTP_200_OK
    data_combined = response_combined.json()
    assert len(data_combined) == 1
    assert data_combined[0]["barcode"] == p1_data_from_api["barcode"]

    response_combined_price = authenticated_client.get(f"/products/?section={target_section}&max_price=10.0")
    assert response_combined_price.status_code == status.HTTP_200_OK
    data_combined_price = response_combined_price.json()
    assert len(data_combined_price) == 1
    assert data_combined_price[0]["barcode"] == p3_data_from_api["barcode"]