import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, selectinload 
from datetime import date, timedelta
import time

from app.models.domain.customer import CustomerModel
from app.models.domain.product import ProductImageModel, ProductModel
from app.models.domain.order import OrderModel, OrderProduct, OrderStatus 
from app.models.schemas.order import OrderCreate, OrderProductCreate

VALID_IMAGE_URL = "http://example.com/image1.png" 
VALID_IMAGE_URL_2 = "https://example.com/image2.jpg"
VALID_IMAGE_URL_3 = "http://example.com/image3.webp"

@pytest.fixture
def test_customer_for_order(db_session: Session) -> CustomerModel:
    customer = CustomerModel(name="Order Customer", email="ordercust@example.com", cpf="70537089009")
    existing_customer = db_session.query(CustomerModel).filter_by(email=customer.email).first()
    if existing_customer:
        return existing_customer
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer

@pytest.fixture
def product1_for_order(db_session: Session) -> ProductModel:
    barcode = "ORDERPROD001_V3"
    product = db_session.query(ProductModel).filter_by(barcode=barcode).first()
    if product:
        if product.stock != 20: product.stock = 20
        db_session.commit()
        db_session.refresh(product) 
        db_session.expire(product, ['images']) 
        _ = product.images
        return product

    product_data = {
        "description": "Order Product One", "price": 10.00, "barcode": barcode,
        "section": "SectionOrd1", "stock": 20, 
        "expiry_date": date.today() + timedelta(days=100)
    }
    image_urls_list = [VALID_IMAGE_URL] 

    new_product = ProductModel(**product_data)
    for url in image_urls_list:
        new_product.images.append(ProductImageModel(url=url))
    
    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product)
    db_session.expire(new_product, ['images'])
    _ = new_product.images
    return new_product

@pytest.fixture
def product2_for_order(db_session: Session) -> ProductModel:
    barcode = "ORDERPROD002_V3"
    product = db_session.query(ProductModel).filter_by(barcode=barcode).first()
    if product:
        if product.stock != 15: product.stock = 15
        db_session.commit()
        db_session.refresh(product)
        db_session.expire(product, ['images'])
        _ = product.images
        return product

    product_data = {
        "description": "Order Product Two", "price": 25.50, "barcode": barcode,
        "section": "SectionOrd2", "stock": 15, 
        "expiry_date": date.today() + timedelta(days=200)
    }
    image_urls_list = [VALID_IMAGE_URL_2, VALID_IMAGE_URL_3]

    new_product = ProductModel(**product_data)
    for url in image_urls_list:
        new_product.images.append(ProductImageModel(url=url))
        
    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product)
    db_session.expire(new_product, ['images'])
    _ = new_product.images
    return new_product

@pytest.fixture
def created_order_with_items(
    db_session: Session, authenticated_client: TestClient,
    test_customer_for_order: CustomerModel, product1_for_order: ProductModel, product2_for_order: ProductModel
) -> OrderModel:
    order_payload_dict = {
        "customer_id": test_customer_for_order.id,
        "products": [
            {"product_id": product1_for_order.id, "quantity": 2},
            {"product_id": product2_for_order.id, "quantity": 1}
        ]
    }
    response = authenticated_client.post("/orders/", json=order_payload_dict)
    assert response.status_code == status.HTTP_201_CREATED, f"Order creation failed: {response.json()}"
    created_order_data = response.json()
    order_in_db = db_session.query(OrderModel).options(
        selectinload(OrderModel.customer),
        selectinload(OrderModel.order_products).selectinload(OrderProduct.product).selectinload(ProductModel.images)
    ).filter(OrderModel.id == created_order_data["id"]).one()
    return order_in_db


@pytest.mark.asyncio
async def test_create_order_success(
    authenticated_client: TestClient, db_session: Session, test_customer_for_order: CustomerModel,
    product1_for_order: ProductModel, product2_for_order: ProductModel
):
    p1 = db_session.merge(product1_for_order) 
    p2 = db_session.merge(product2_for_order) 
    
    initial_stock_p1 = p1.stock
    initial_stock_p2 = p2.stock
    
    order_payload = {
        "customer_id": test_customer_for_order.id,
        "products": [
            {"product_id": p1.id, "quantity": 3},
            {"product_id": p2.id, "quantity": 2}
        ]
    }
    response = authenticated_client.post("/orders/", json=order_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["customer_id"] == test_customer_for_order.id
    assert data["customer_name"] == test_customer_for_order.name
    assert data["status"] == OrderStatus.PENDING.value
    assert data["total_amount"] == 81.00
    assert len(data["products"]) == 2
    assert any(p["product"]["id"] == p1.id and p["quantity"] == 3 for p in data["products"])
    assert any(p["product"]["id"] == p2.id and p["quantity"] == 2 for p in data["products"])

    updated_product1 = db_session.query(ProductModel).get(p1.id)
    updated_product2 = db_session.query(ProductModel).get(p2.id)
    assert updated_product1.stock == initial_stock_p1 - 3
    assert updated_product2.stock == initial_stock_p2 - 2

@pytest.mark.asyncio
async def test_create_order_customer_not_found(authenticated_client: TestClient, product1_for_order: ProductModel):
    p1 = product1_for_order 
    order_payload = {"customer_id": 99999, "products": [{"product_id": p1.id, "quantity": 1}]}
    response = authenticated_client.post("/orders/", json=order_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Customer with ID 99999 not found" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_create_order_product_not_found(authenticated_client: TestClient, test_customer_for_order: CustomerModel):
    order_payload = {"customer_id": test_customer_for_order.id, "products": [{"product_id": 99999, "quantity": 1}]}
    response = authenticated_client.post("/orders/", json=order_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Product not found" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_create_order_insufficient_stock(
    authenticated_client: TestClient, test_customer_for_order: CustomerModel, product1_for_order: ProductModel, db_session: Session
):
    p1 = db_session.merge(product1_for_order)
    order_payload = {"customer_id": test_customer_for_order.id, "products": [{"product_id": p1.id, "quantity": p1.stock + 1}]}
    response = authenticated_client.post("/orders/", json=order_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Insufficient stock for product ID {p1.id}" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_get_order_by_id_success(authenticated_client: TestClient, created_order_with_items: OrderModel):
    response = authenticated_client.get(f"/orders/{created_order_with_items.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == created_order_with_items.id
    assert data["customer_name"] == created_order_with_items.customer.name
    assert data["status"] == created_order_with_items.status 


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/orders/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Order not found"

@pytest.mark.asyncio
async def test_list_orders_filter_by_customer_id(
    authenticated_client: TestClient, db_session: Session,
    created_order_with_items: OrderModel, 
    test_customer_for_order: CustomerModel,
    
    product1_for_order: ProductModel
):

    main_order_id = created_order_with_items.id
    main_customer_id = test_customer_for_order.id 

    other_customer_cpf = "33797525095"
    other_customer_email = f"otherfilter_{other_customer_cpf}@example.com"
    
    other_customer = db_session.query(CustomerModel).filter_by(email=other_customer_email).first()
    if not other_customer:
        other_customer = CustomerModel(name="Other Filter Cust", email=other_customer_email, cpf=other_customer_cpf)
        db_session.add(other_customer)
        db_session.commit()
        db_session.refresh(other_customer)
    
    p1_live = db_session.merge(product1_for_order) 

    other_order_payload = OrderCreate(
        customer_id=other_customer.id,
        products=[OrderProductCreate(product_id=p1_live.id, quantity=1)]
    )
    res_other_order = authenticated_client.post("/orders/", json=other_order_payload.model_dump(mode='json'))
    assert res_other_order.status_code == status.HTTP_201_CREATED, f"Falha ao criar o segundo pedido: {res_other_order.json()}"
    other_order_id = res_other_order.json()["id"]

    response = authenticated_client.get(f"/orders/?customer_id={main_customer_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data) >= 1
    
    assert all(order["customer_id"] == main_customer_id for order in data)
    
    assert any(order["id"] == main_order_id for order in data)
    

    assert not any(order["id"] == other_order_id for order in data)

@pytest.mark.asyncio
async def test_update_order_status_success_and_cancel_restores_stock(
    authenticated_client: TestClient, created_order_with_items: OrderModel,
    product1_for_order: ProductModel, product2_for_order: ProductModel, db_session: Session
):
    order_id = created_order_with_items.id
    
    p1_live = db_session.query(ProductModel).get(product1_for_order.id)
    p2_live = db_session.query(ProductModel).get(product2_for_order.id)
    stock_p1_after_creation = p1_live.stock
    stock_p2_after_creation = p2_live.stock

    status_payload_processing = {"status": OrderStatus.PROCESSING.value}
    response_processing = authenticated_client.patch(f"/orders/{order_id}/status", json=status_payload_processing)
    assert response_processing.status_code == status.HTTP_200_OK

    status_payload_canceled = {"status": OrderStatus.CANCELED.value}
    response_canceled = authenticated_client.patch(f"/orders/{order_id}/status", json=status_payload_canceled)
    assert response_canceled.status_code == status.HTTP_200_OK
    
    p1_reloaded = db_session.query(ProductModel).get(product1_for_order.id)
    p2_reloaded = db_session.query(ProductModel).get(product2_for_order.id)
    assert p1_reloaded.stock == stock_p1_after_creation + 2
    assert p2_reloaded.stock == stock_p2_after_creation + 1


@pytest.mark.asyncio
async def test_update_order_status_order_not_found(authenticated_client: TestClient):
    status_payload = {"status": OrderStatus.COMPLETED.value}
    response = authenticated_client.patch("/orders/99999/status", json=status_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Order not found"

@pytest.mark.asyncio
async def test_update_order_status_invalid_status_value(authenticated_client: TestClient, created_order_with_items: OrderModel):
    status_payload = {"status": "invalid_status_value"}
    response = authenticated_client.patch(f"/orders/{created_order_with_items.id}/status", json=status_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    errors = response.json()["errors"]
    assert len(errors) > 0 

    status_error = None
    for err in errors:
        if err.get("loc") == ["body", "status"]:
            status_error = err
            break
    
    assert status_error is not None, "Não foi encontrado erro de validação para o campo 'status'"
    
    expected_message_part = "Status must be one of ['pending', 'processing', 'completed', 'canceled']"
    assert expected_message_part in status_error["msg"]
    

    assert status_error["type"] == "value_error"


@pytest.mark.asyncio
async def test_update_order_success_change_items(
    authenticated_client: TestClient, created_order_with_items: OrderModel,
    test_customer_for_order: CustomerModel, product1_for_order: ProductModel,
    product2_for_order: ProductModel, db_session: Session
):
    order_id = created_order_with_items.id
    
    p1_live = db_session.query(ProductModel).get(product1_for_order.id)
    p2_live = db_session.query(ProductModel).get(product2_for_order.id)
    initial_stock_p1 = p1_live.stock 
    initial_stock_p2 = p2_live.stock 

    updated_order_payload = {
        "customer_id": test_customer_for_order.id,
        "status": OrderStatus.PROCESSING.value,
        "products": [
            {"product_id": p1_live.id, "quantity": 1}, 
            {"product_id": p2_live.id, "quantity": 3}  
        ]
    }
    response = authenticated_client.put(f"/orders/{order_id}", json=updated_order_payload)
    assert response.status_code == status.HTTP_200_OK
    
    p1_reloaded = db_session.query(ProductModel).get(p1_live.id)
    p2_reloaded = db_session.query(ProductModel).get(p2_live.id)
    assert p1_reloaded.stock == initial_stock_p1 + (2 - 1) 
    assert p2_reloaded.stock == initial_stock_p2 + (1 - 3)


@pytest.mark.asyncio
async def test_delete_order_success_restores_stock(
    admin_authenticated_client: TestClient, created_order_with_items: OrderModel,
    product1_for_order: ProductModel, product2_for_order: ProductModel, db_session: Session
):
    order_id_to_delete = created_order_with_items.id
    

    product1_id = product1_for_order.id
    product2_id = product2_for_order.id

    p1_before_delete = db_session.get(ProductModel, product1_id)
    assert p1_before_delete is not None, "Product 1 not found before delete"
    stock_p1_before_delete = p1_before_delete.stock

    p2_before_delete = db_session.get(ProductModel, product2_id)
    assert p2_before_delete is not None, "Product 2 not found before delete"
    stock_p2_before_delete = p2_before_delete.stock

    live_order_before_delete = db_session.query(OrderModel).options(
        selectinload(OrderModel.order_products)
    ).filter(OrderModel.id == order_id_to_delete).one()

    qty_p1_in_order = next(
        op.quantity for op in live_order_before_delete.order_products if op.product_id == product1_id
    )
    qty_p2_in_order = next(
        op.quantity for op in live_order_before_delete.order_products if op.product_id == product2_id
    )

    response = admin_authenticated_client.delete(f"/orders/{order_id_to_delete}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    order_in_db_after_delete = db_session.get(OrderModel, order_id_to_delete)
    assert order_in_db_after_delete is None

    p1_after_delete = db_session.get(ProductModel, product1_id)
    assert p1_after_delete is not None, "Product 1 not found after delete"
    assert p1_after_delete.stock == stock_p1_before_delete + qty_p1_in_order

    p2_after_delete = db_session.get(ProductModel, product2_id)
    assert p2_after_delete is not None, "Product 2 not found after delete"
    assert p2_after_delete.stock == stock_p2_before_delete + qty_p2_in_order


@pytest.mark.asyncio
async def test_delete_order_not_found(admin_authenticated_client: TestClient):
    response = admin_authenticated_client.delete("/orders/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["errors"][0] == "Order not found"


@pytest.fixture
def product_section_A_for_filter(db_session: Session) -> ProductModel:
    barcode = "FILTER_SEC_A_PROD_V3"
    product = db_session.query(ProductModel).filter_by(barcode=barcode).first()
    if product:
        if product.stock != 50: product.stock = 50
        db_session.commit()
        db_session.refresh(product)
        db_session.expire(product, ['images'])
        _ = product.images
        return product
        
    product_data = {"description": "Filter Sec A Prod", "price": 5.0, "barcode": barcode, "section": "FilterSectionA", "stock": 50}
    image_urls_list = [VALID_IMAGE_URL]

    new_product = ProductModel(**product_data)
    for url in image_urls_list:
        new_product.images.append(ProductImageModel(url=url))

    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product)
    db_session.expire(new_product, ['images'])
    _ = new_product.images
    return new_product

@pytest.fixture
def product_section_B_for_filter(db_session: Session) -> ProductModel:
    barcode = "FILTER_SEC_B_PROD_V3"
    product = db_session.query(ProductModel).filter_by(barcode=barcode).first()
    if product:
        if product.stock != 50: product.stock = 50
        db_session.commit()
        db_session.refresh(product)
        db_session.expire(product, ['images'])
        _ = product.images
        return product

    product_data = {"description": "Filter Sec B Prod", "price": 7.50, "barcode": barcode, "section": "FilterSectionB", "stock": 50}
    image_urls_list = [VALID_IMAGE_URL_2]

    new_product = ProductModel(**product_data)
    for url in image_urls_list:
        new_product.images.append(ProductImageModel(url=url))
        
    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product)
    db_session.expire(new_product, ['images'])
    _ = new_product.images
    return new_product


@pytest.mark.asyncio
async def test_list_orders_filter_by_product_section(
    authenticated_client: TestClient, db_session: Session, test_customer_for_order: CustomerModel,
    product_section_A_for_filter: ProductModel, product_section_B_for_filter: ProductModel
):
    db_session.query(OrderProduct).delete()
    db_session.query(OrderModel).delete()
    db_session.commit()
    
    p_A_id = product_section_A_for_filter.id
    p_B_id = product_section_B_for_filter.id

    res_A = authenticated_client.post("/orders/", json=OrderCreate(customer_id=test_customer_for_order.id, products=[OrderProductCreate(product_id=p_A_id, quantity=1)]).model_dump(mode='json'))
    assert res_A.status_code == status.HTTP_201_CREATED
    order_A_id = res_A.json()["id"]

    res_B = authenticated_client.post("/orders/", json=OrderCreate(customer_id=test_customer_for_order.id, products=[OrderProductCreate(product_id=p_B_id, quantity=1)]).model_dump(mode='json'))
    assert res_B.status_code == status.HTTP_201_CREATED

    response_sec_A = authenticated_client.get("/orders/?section=FilterSectionA")
    assert response_sec_A.status_code == status.HTTP_200_OK
    data_sec_A = response_sec_A.json()
    assert len(data_sec_A) >= 1 
    assert any(o["id"] == order_A_id for o in data_sec_A)
    assert all(any(p["product"]["section"] == "FilterSectionA" for p in o["products"]) for o in data_sec_A)

@pytest.mark.asyncio
async def test_list_orders_sorting(
    authenticated_client: TestClient, db_session: Session, test_customer_for_order: CustomerModel, product1_for_order: ProductModel
):
    
    p1 = db_session.merge(product1_for_order)

    res1 = authenticated_client.post("/orders/", json=OrderCreate(customer_id=test_customer_for_order.id, products=[OrderProductCreate(product_id=p1.id, quantity=1)]).model_dump(mode='json')) 
    time.sleep(0.2) 
    res2 = authenticated_client.post("/orders/", json=OrderCreate(customer_id=test_customer_for_order.id, products=[OrderProductCreate(product_id=p1.id, quantity=3)]).model_dump(mode='json')) 
    time.sleep(0.2)
    res3 = authenticated_client.post("/orders/", json=OrderCreate(customer_id=test_customer_for_order.id, products=[OrderProductCreate(product_id=p1.id, quantity=2)]).model_dump(mode='json')) 

    assert res1.status_code == 201 and res2.status_code == 201 and res3.status_code == 201
    id1, id2, id3 = res1.json()["id"], res2.json()["id"], res3.json()["id"]

    response_created_desc = authenticated_client.get("/orders/?order_by=created_at&order_direction=desc")
    data_created_desc = response_created_desc.json()
    assert [o["id"] for o in data_created_desc if o["id"] in [id1,id2,id3]] == [id3, id2, id1] 

    response_total_asc = authenticated_client.get("/orders/?order_by=total_amount&order_direction=asc")
    data_total_asc = response_total_asc.json()
    relevant_orders_asc = sorted([o for o in data_total_asc if o["id"] in [id1, id2, id3]], key=lambda x: x["total_amount"])
    assert [o["total_amount"] for o in relevant_orders_asc] == [10.0, 20.0, 30.0]


@pytest.mark.asyncio
async def test_update_order_customer_not_found(
    authenticated_client: TestClient, created_order_with_items: OrderModel, product1_for_order: ProductModel
):
    order_id = created_order_with_items.id
    update_payload = {"customer_id": 99999, "status": OrderStatus.PROCESSING.value, "products": [{"product_id": product1_for_order.id, "quantity": 1}]}
    response = authenticated_client.put(f"/orders/{order_id}", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Customer with ID 99999 not found" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_update_order_product_not_found_in_new_items(
    authenticated_client: TestClient, created_order_with_items: OrderModel, test_customer_for_order: CustomerModel
):
    order_id = created_order_with_items.id
    update_payload = {"customer_id": test_customer_for_order.id, "status": OrderStatus.PROCESSING.value, "products": [{"product_id": 99999, "quantity": 1}]}
    response = authenticated_client.put(f"/orders/{order_id}", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Product not found" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_update_order_insufficient_stock_for_updated_item(
    authenticated_client: TestClient, created_order_with_items: OrderModel,
    test_customer_for_order: CustomerModel, product1_for_order: ProductModel, db_session: Session
):
    order_id = created_order_with_items.id
    p1_live = db_session.query(ProductModel).get(product1_for_order.id)
    
    requested_qty = p1_live.stock + 2 + 1 

    update_payload = {
        "customer_id": test_customer_for_order.id,
        "status": OrderStatus.PROCESSING.value,
        "products": [
            {"product_id": p1_live.id, "quantity": requested_qty },
            {"product_id": created_order_with_items.order_products[1].product_id, 
             "quantity": created_order_with_items.order_products[1].quantity}
        ]
    }
    response = authenticated_client.put(f"/orders/{order_id}", json=update_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Insufficient stock for product ID {p1_live.id}" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_list_orders_invalid_status_filter(authenticated_client: TestClient):
    response = authenticated_client.get("/orders/?status=invalid_status")
    assert response.status_code == status.HTTP_400_BAD_REQUEST 
    assert "Invalid order status filter" in response.json()["errors"][0]

@pytest.mark.asyncio
async def test_list_orders_invalid_date_format_filter(authenticated_client: TestClient):
    response_start = authenticated_client.get("/orders/?start_date=invalid-date-format")
    assert response_start.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid start_date format" in response_start.json()["errors"][0]

    response_end = authenticated_client.get("/orders/?end_date=2023/12/31")
    assert response_end.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid end_date format" in response_end.json()["errors"][0]