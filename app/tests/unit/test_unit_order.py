import pytest
from unittest.mock import Mock, call
from fastapi import HTTPException, status as http_status
from datetime import date as PyDate, timedelta, datetime


from app.services.order import OrderService
from app.models.domain.order import OrderModel, OrderProduct, OrderStatus
from app.models.domain.product import ProductModel
from app.models.domain.customer import CustomerModel
from app.models.schemas.order import OrderCreate, OrderProductCreate
from app.services import WhatsappService


@pytest.fixture
def mock_order_repo(mocker):
    return mocker.Mock()

@pytest.fixture
def mock_product_service(mocker):
    service = mocker.Mock()
    service.update_product_stock = mocker.Mock(return_value=mocker.Mock(spec=ProductModel)) 
    service.get_product_by_id = mocker.Mock(return_value=mocker.Mock(spec=ProductModel))
    return service

@pytest.fixture
def mock_customer_repo(mocker):
    return mocker.Mock()

@pytest.fixture
def mock_whatsapp_service(mocker): 
    return mocker.Mock(spec=WhatsappService)

@pytest.fixture
def order_service(
    mock_order_repo: Mock, 
    mock_product_service: Mock, 
    mock_customer_repo: Mock,
    mock_whatsapp_service: Mock 
):
    return OrderService(
        order_repository=mock_order_repo,
        product_service=mock_product_service,
        customer_repository=mock_customer_repo,
        whatsapp_service=mock_whatsapp_service 
    )

@pytest.fixture
def sample_customer_model(mocker) -> Mock:
    customer = mocker.Mock(spec=CustomerModel)
    customer.id = 1
    customer.name = "Test Customer"
    return customer

@pytest.fixture
def sample_product1_model(mocker) -> Mock:
    product = mocker.Mock(spec=ProductModel)
    product.id = 101
    product.price = 20.00
    product.stock = 50
    product.section = "Eletronicos"
    return product

@pytest.fixture
def sample_product2_model(mocker) -> Mock:
    product = mocker.Mock(spec=ProductModel)
    product.id = 102
    product.price = 30.00
    product.stock = 30
    product.section = "Livros"
    return product

@pytest.fixture
def sample_order_create_schema(sample_customer_model: Mock, sample_product1_model: Mock, sample_product2_model: Mock) -> OrderCreate:
    return OrderCreate(
        customer_id=sample_customer_model.id,
        status=OrderStatus.PENDING.value,
        products=[
            OrderProductCreate(product_id=sample_product1_model.id, quantity=2),
            OrderProductCreate(product_id=sample_product2_model.id, quantity=1)
        ]
    )

@pytest.fixture
def sample_order_model(mocker, sample_order_create_schema: OrderCreate, sample_customer_model: Mock) -> Mock:
    order = mocker.Mock(spec=OrderModel)
    order.id = 1
    order.customer_id = sample_order_create_schema.customer_id
    order.customer = sample_customer_model 
    order.status = sample_order_create_schema.status
    order.total_amount = 0.0 
    order.order_products = [] 
    order.created_at = datetime.now()
    order.updated_at = None
    return order


class TestOrderService:

    def test_validate_customer_exists_found(
        self, order_service: OrderService, mock_customer_repo: Mock, sample_customer_model: Mock
    ):
        mock_customer_repo.get_customer_by_id.return_value = sample_customer_model
        customer = order_service._validate_customer_exists(1)
        mock_customer_repo.get_customer_by_id.assert_called_once_with(1)
        assert customer == sample_customer_model

    def test_validate_customer_exists_not_found(self, order_service: OrderService, mock_customer_repo: Mock):
        mock_customer_repo.get_customer_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            order_service._validate_customer_exists(999)
        assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND
        assert "Customer with ID 999 not found" in exc_info.value.detail

    def test_prepare_order_items_create_mode_success(
        self, order_service: OrderService, mock_product_service: Mock,
        sample_product1_model: Mock, sample_product2_model: Mock
    ):
        order_product_inputs = [
            OrderProductCreate(product_id=sample_product1_model.id, quantity=2),
            OrderProductCreate(product_id=sample_product2_model.id, quantity=1)
        ]
        
        mock_product_service.get_product_by_id.side_effect = [sample_product1_model, sample_product2_model]

        prepared_items, total_amount = order_service._prepare_order_items_and_calc_total(order_product_inputs)

        assert len(prepared_items) == 2
        assert isinstance(prepared_items[0], OrderProduct)
        assert prepared_items[0].product_id == sample_product1_model.id
        assert prepared_items[0].quantity == 2
        assert prepared_items[0].unit_price == sample_product1_model.price
        
        assert isinstance(prepared_items[1], OrderProduct)
        assert prepared_items[1].product_id == sample_product2_model.id
        assert prepared_items[1].quantity == 1
        assert prepared_items[1].unit_price == sample_product2_model.price
        
        expected_total = (sample_product1_model.price * 2) + (sample_product2_model.price * 1)
        assert total_amount == expected_total

        mock_product_service.get_product_by_id.assert_has_calls([
            call(sample_product1_model.id),
            call(sample_product2_model.id)
        ])
        mock_product_service.update_product_stock.assert_has_calls([
            call(product_id=sample_product1_model.id, quantity_change=2, increase=False),
            call(product_id=sample_product2_model.id, quantity_change=1, increase=False)
        ])

    def test_prepare_order_items_product_not_found(self, order_service: OrderService, mock_product_service: Mock):
        order_product_inputs = [OrderProductCreate(product_id=999, quantity=1)]
        mock_product_service.get_product_by_id.side_effect = HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            order_service._prepare_order_items_and_calc_total(order_product_inputs)
        assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND

    def test_prepare_order_items_insufficient_stock(
        self, order_service: OrderService, mock_product_service: Mock, sample_product1_model: Mock
    ):
        sample_product1_model.stock = 1 
        order_product_inputs = [OrderProductCreate(product_id=sample_product1_model.id, quantity=2)]
        mock_product_service.get_product_by_id.return_value = sample_product1_model
        
        with pytest.raises(HTTPException) as exc_info:
            order_service._prepare_order_items_and_calc_total(order_product_inputs)
        assert exc_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert f"Insufficient stock for product ID {sample_product1_model.id}" in exc_info.value.detail



    async def test_create_order_success(
        self, order_service: OrderService, mock_order_repo: Mock, mock_customer_repo: Mock, 
        mock_product_service: Mock, sample_order_create_schema: OrderCreate, 
        sample_customer_model: Mock, sample_product1_model: Mock, sample_product2_model: Mock,
        sample_order_model: Mock, mocker
    ):
        mock_customer_repo.get_customer_by_id.return_value = sample_customer_model
        
        mock_prepared_items = [mocker.Mock(spec=OrderProduct), mocker.Mock(spec=OrderProduct)]
        mock_total_amount = 70.0 

        mock_prepare_method = mocker.patch.object(
            order_service, 
            '_prepare_order_items_and_calc_total', 
            return_value=(mock_prepared_items, mock_total_amount)
        )
        
        mock_order_repo.create_order.return_value = sample_order_model

        created_order = await order_service.create_order(sample_order_create_schema)

        mock_customer_repo.get_customer_by_id.assert_called_once_with(sample_order_create_schema.customer_id)
        mock_prepare_method.assert_called_once_with(sample_order_create_schema.products)
        
        args_repo_create, _ = mock_order_repo.create_order.call_args
        order_model_arg = args_repo_create[0]
        order_product_models_arg = args_repo_create[1]

        assert isinstance(order_model_arg, OrderModel)
        assert order_model_arg.customer_id == sample_order_create_schema.customer_id
        assert order_model_arg.status.value == sample_order_create_schema.status
        assert order_model_arg.total_amount == mock_total_amount
        assert order_product_models_arg == mock_prepared_items
        
        assert created_order == sample_order_model

    def test_get_order_by_id_found(
        self, order_service: OrderService, mock_order_repo: Mock, sample_order_model: Mock
    ):
        mock_order_repo.get_order_by_id.return_value = sample_order_model
        order = order_service.get_order_by_id(1)
        mock_order_repo.get_order_by_id.assert_called_once_with(1)
        assert order == sample_order_model

    def test_get_order_by_id_not_found(self, order_service: OrderService, mock_order_repo: Mock):
        mock_order_repo.get_order_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            order_service.get_order_by_id(999)
        assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Order not found"

    def test_get_orders_invalid_status_filter(self, order_service: OrderService):
        with pytest.raises(HTTPException) as exc_info:
            order_service.get_orders(status_filter="wrong_status")
        assert exc_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "Invalid order status filter: wrong_status" in exc_info.value.detail

    def test_get_orders_invalid_date_format(self, order_service: OrderService):
        with pytest.raises(HTTPException) as exc_info_start:
            order_service.get_orders(start_date_str="invalid-date")
        assert exc_info_start.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "Invalid start_date format" in exc_info_start.value.detail

        with pytest.raises(HTTPException) as exc_info_end:
            order_service.get_orders(end_date_str="another-invalid-date")
        assert exc_info_end.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "Invalid end_date format" in exc_info_end.value.detail

    def test_get_orders_calls_repo_correctly(self, order_service: OrderService, mock_order_repo: Mock):
        mock_order_repo.get_orders.return_value = [] 
        order_service.get_orders(
            limit=50, skip=10, customer_id=1, status_filter="pending",
            start_date_str="2023-01-01", end_date_str="2023-01-31",
            order_by_field="total_amount", order_direction="asc", product_section="Eletronicos"
        )
        mock_order_repo.get_orders.assert_called_once_with(
            limit=50, skip=10, customer_id=1, status_filter="pending",
            start_date=PyDate(2023,1,1), end_date=PyDate(2023,1,31),
            order_by_field="total_amount", order_direction="asc", product_section="Eletronicos"
        )

    def test_update_order_status_success(
        self, order_service: OrderService, mock_order_repo: Mock, sample_order_model: Mock, mocker
    ):
        sample_order_model.status = OrderStatus.PENDING.value 
        mock_get_by_id = mocker.patch.object(order_service, 'get_order_by_id', return_value=sample_order_model)
        mock_order_repo.update_order_status.return_value = sample_order_model

    async def test_create_order_service_handles_invalid_status_string(
        self, order_service: OrderService, mock_customer_repo: Mock, 
        sample_customer_model: Mock, mocker
    ):
        mock_customer_repo.get_customer_by_id.return_value = sample_customer_model

        order_data_mock = mocker.Mock(spec=OrderCreate)
        order_data_mock.customer_id = sample_customer_model.id
        order_data_mock.status = "shipped_illegally" 
        order_data_mock.products = [mocker.Mock(spec=OrderProductCreate, product_id=1, quantity=1)]

        mocker.patch.object(order_service, '_prepare_order_items_and_calc_total', 
                            return_value=([], 0.0)) 

        with pytest.raises(HTTPException) as exc_info:
            await order_service.create_order(order_data_mock)

        assert exc_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "Invalid order status: shipped_illegally" in exc_info.value.detail
        mock_customer_repo.get_customer_by_id.assert_called_once_with(sample_customer_model.id)
    

    async def test_create_order_service_internal_invalid_status_check(
        self, order_service: OrderService, mock_customer_repo: Mock, 
        sample_customer_model: Mock, mocker
    ):
        mock_customer_repo.get_customer_by_id.return_value = sample_customer_model
        
        order_data_mock = mocker.Mock(spec=OrderCreate)
        order_data_mock.customer_id = sample_customer_model.id
        order_data_mock.status = "este_status_nao_existe" 
        order_data_mock.products = [mocker.Mock(spec=OrderProductCreate, product_id=1, quantity=1)]

        mocker.patch.object(order_service, '_prepare_order_items_and_calc_total', return_value=([], 0.0))

        with pytest.raises(HTTPException) as exc_info:
            await order_service.create_order(order_data_mock)
        
        assert exc_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
        assert f"Invalid order status: {order_data_mock.status}" in exc_info.value.detail
        mock_customer_repo.get_customer_by_id.assert_called_once_with(sample_customer_model.id)
        order_service._prepare_order_items_and_calc_total.assert_not_called()