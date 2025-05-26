import pytest
from unittest.mock import Mock

from app.services.customer import CustomerService
from app.models.schemas.customer import CustomerSchema
from app.models.domain.customer import CustomerModel


@pytest.fixture
def mock_customer_repo(mocker):
    return mocker.Mock()

@pytest.fixture
def customer_service(mock_customer_repo):
    return CustomerService(customer_repository=mock_customer_repo)

@pytest.fixture
def sample_customer_schema() -> CustomerSchema:
    return CustomerSchema(name="Test Customer", email="test@example.com", cpf="33797525095")

@pytest.fixture
def sample_customer_model() -> CustomerModel:
    return CustomerModel(id=1, name="Test Customer", email="test@example.com", cpf="33797525095")

class TestCustomerService:

    def test_get_customers(self, customer_service: CustomerService, mock_customer_repo: Mock):
        mock_customer_repo.get_customers.return_value = ["customer1", "customer2"] 
        
        result = customer_service.get_customers(order_by="name", skip=5, limit=10)

        mock_customer_repo.get_customers.assert_called_once_with("name", 5, 10)
        assert result == ["customer1", "customer2"]

    def test_get_customer_by_id(self, customer_service: CustomerService, mock_customer_repo: Mock, sample_customer_model: CustomerModel):
        mock_customer_repo.get_customer_by_id.return_value = sample_customer_model
        
        result = customer_service.get_customer_by_id(1)
        
        mock_customer_repo.get_customer_by_id.assert_called_once_with(1)
        assert result == sample_customer_model

    def test_get_customer_by_email(self, customer_service: CustomerService, mock_customer_repo: Mock, sample_customer_model: CustomerModel):
        mock_customer_repo.get_customer_by_email.return_value = sample_customer_model
        
        result = customer_service.get_customer_by_email("test@example.com")
        
        mock_customer_repo.get_customer_by_email.assert_called_once_with("test@example.com")
        assert result == sample_customer_model

    def test_get_customer_by_cpf(self, customer_service: CustomerService, mock_customer_repo: Mock, sample_customer_model: CustomerModel):
        mock_customer_repo.get_customer_by_cpf.return_value = sample_customer_model
        
        result = customer_service.get_customer_by_cpf("70537089009")
        
        mock_customer_repo.get_customer_by_cpf.assert_called_once_with("70537089009")
        assert result == sample_customer_model

    def test_create_customer(self, customer_service: CustomerService, mock_customer_repo: Mock, sample_customer_schema: CustomerSchema, sample_customer_model: CustomerModel):
        mock_customer_repo.create_customer.return_value = sample_customer_model 
        
        result = customer_service.create_customer(sample_customer_schema)
        
        call_args = mock_customer_repo.create_customer.call_args[0] 
        created_customer_arg = call_args[0] 
        
        assert isinstance(created_customer_arg, CustomerModel)
        assert created_customer_arg.name == sample_customer_schema.name
        assert created_customer_arg.email == sample_customer_schema.email
        assert created_customer_arg.cpf == sample_customer_schema.cpf
        
        assert result == sample_customer_model

    def test_update_customer(self, customer_service: CustomerService, mock_customer_repo: Mock, sample_customer_schema: CustomerSchema, sample_customer_model: CustomerModel):
        existing_customer_model = CustomerModel(id=1, name="Old Name", email="old@example.com", cpf="12345678901")
        mock_customer_repo.get_customer_by_id.return_value = existing_customer_model
        
        mock_customer_repo.update_customer.return_value = existing_customer_model 

        updated_customer = customer_service.update_customer(1, sample_customer_schema)

        mock_customer_repo.get_customer_by_id.assert_called_once_with(1)

        mock_customer_repo.update_customer.assert_called_once_with(existing_customer_model)
        assert existing_customer_model.name == sample_customer_schema.name
        assert existing_customer_model.email == sample_customer_schema.email
        assert existing_customer_model.cpf == sample_customer_schema.cpf
        
        assert updated_customer == existing_customer_model 

    def test_delete_customer(self, customer_service: CustomerService, mock_customer_repo: Mock):
        mock_customer_repo.delete_customer.return_value = None 

        customer_service.delete_customer(1)

        mock_customer_repo.delete_customer.assert_called_once_with(1)