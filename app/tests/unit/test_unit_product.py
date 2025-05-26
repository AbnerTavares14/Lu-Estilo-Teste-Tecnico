# app/tests/unit/services/test_product_service.py
from pydantic import HttpUrl
import pytest
from unittest.mock import Mock # Usaremos mocker.Mock()
from fastapi import HTTPException, status
from pytest_mock import mocker
from sqlalchemy.exc import IntegrityError # Para simular erros do DB
from datetime import date, timedelta
from typing import List, Optional

# Importações do seu projeto
from app.services.products import ProductService
from app.models.domain.product import ProductModel, ProductImageModel # Para type hinting e mock spec
from app.models.schemas.product import ProductSchema # Para dados de entrada

VALID_IMAGE_URL_FOR_TEST = "http://example.com/image.png"

# --- Fixtures para ProductService ---

@pytest.fixture
def mock_product_repo(mocker):
    return mocker.Mock()

@pytest.fixture
def product_service(mock_product_repo):
    return ProductService(product_repository=mock_product_repo)

@pytest.fixture
def sample_product_schema() -> ProductSchema:
    # Vamos fornecer algumas URLs de imagem aqui para que a fixture sample_product_model possa usá-las
    return ProductSchema(
        description="Test Product Schema",
        price=19.99,
        barcode="BARCODE123",
        section="TestSection",
        stock=50,
        expiry_date=date.today() + timedelta(days=30),
        image_urls=[VALID_IMAGE_URL_FOR_TEST, "https://example.com/another.jpg"] # CORRIGIDO: image_urls com valores
    )

@pytest.fixture
def sample_product_model(mocker, sample_product_schema: ProductSchema) -> Mock:
    mock_model = mocker.Mock(spec=ProductModel)
    mock_model.id = 1
    mock_model.description = sample_product_schema.description
    mock_model.price = sample_product_schema.price
    mock_model.barcode = sample_product_schema.barcode
    mock_model.section = sample_product_schema.section
    mock_model.stock = sample_product_schema.stock
    mock_model.expiry_date = sample_product_schema.expiry_date
    
    # CORRIGIDO: Configurar o atributo 'images' no mock_model
    # ProductModel tem 'images' (relação), ProductSchema tem 'image_urls' (lista de strings/HttpUrl)
    mocked_images = []
    if sample_product_schema.image_urls: # Se houver URLs no schema
        for i, pydantic_url in enumerate(sample_product_schema.image_urls):
            img_mock = mocker.Mock(spec=ProductImageModel)
            img_mock.id = i + 100 # Dummy ID para a imagem mockada
            img_mock.url = str(pydantic_url) # Converte HttpUrl para string para o mock
            img_mock.product_id = mock_model.id # Associar ao produto mockado
            mocked_images.append(img_mock)
    mock_model.images = mocked_images # O ProductModel teria uma coleção aqui

    return mock_model

# --- Testes para ProductService ---

class TestProductService:

    def test_get_product_by_id_found(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock
    ):
        mock_product_repo.get_product_by_id.return_value = sample_product_model
        
        product = product_service.get_product_by_id(1)
        
        mock_product_repo.get_product_by_id.assert_called_once_with(1)
        assert product == sample_product_model

    def test_get_product_by_id_not_found(self, product_service: ProductService, mock_product_repo: Mock):
        mock_product_repo.get_product_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            product_service.get_product_by_id(999)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Product not found"
        mock_product_repo.get_product_by_id.assert_called_once_with(999)

    def test_get_products(self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock, mocker):
        mock_products_list = [sample_product_model, mocker.Mock(spec=ProductModel)]
        mock_product_repo.get_products.return_value = mock_products_list
        
        result = product_service.get_products(skip=5, limit=10, section="Test", min_price=5.0, max_price=20.0, available=True)
        
        mock_product_repo.get_products.assert_called_once_with(
            skip=5, limit=10, section="Test", min_price=5.0, max_price=20.0, available=True
        )
        assert result == mock_products_list

    def test_create_product_success(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock
    ):
        mock_product_repo.get_product_by_barcode.return_value = None # Barcode não existe
        mock_product_repo.create_product.return_value = sample_product_model # Repo retorna o modelo criado
        
        created_product = product_service.create_product(sample_product_schema)
        
        mock_product_repo.get_product_by_barcode.assert_called_once_with(sample_product_schema.barcode)
        mock_product_repo.create_product.assert_called_once_with(sample_product_schema)
        assert created_product == sample_product_model

    def test_create_product_barcode_already_registered(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock
    ):
        mock_product_repo.get_product_by_barcode.return_value = sample_product_model # Simula barcode existente
        
        with pytest.raises(HTTPException) as exc_info:
            product_service.create_product(sample_product_schema)
            
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Barcode already registered"
        mock_product_repo.get_product_by_barcode.assert_called_once_with(sample_product_schema.barcode)
        mock_product_repo.create_product.assert_not_called()

    def test_create_product_db_integrity_error_on_create(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_schema: ProductSchema
    ):
        mock_product_repo.get_product_by_barcode.return_value = None # Barcode passou na checagem inicial
        mock_product_repo.create_product.side_effect = IntegrityError("mocked db error", params={}, orig=None) # Falha no DB
        
        with pytest.raises(HTTPException) as exc_info:
            product_service.create_product(sample_product_schema)
            
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Barcode already registered (DB integrity)"

    def test_update_product_success_barcode_not_changed(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock # sample_product_model é o produto existente
    ):
        product_id = sample_product_model.id
        # O schema de atualização tem o mesmo barcode que o produto existente
        update_data_same_barcode = sample_product_schema 

        # get_product_by_id (chamado por self.get_product_by_id)
        mock_product_repo.get_product_by_id.return_value = sample_product_model 
        # update_product do repo
        mock_product_repo.update_product.return_value = sample_product_model # Simula o produto atualizado retornado

        updated_product = product_service.update_product(product_id, update_data_same_barcode)

        mock_product_repo.get_product_by_id.assert_called_once_with(product_id)
        mock_product_repo.get_product_by_barcode.assert_not_called() # Não deve ser chamado se o barcode não mudou
        mock_product_repo.update_product.assert_called_once_with(sample_product_model, update_data_same_barcode)
        assert updated_product == sample_product_model

    def test_update_product_success_barcode_changed_and_unique(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock, mocker
    ):
        product_id = sample_product_model.id
        existing_product_mock = mocker.Mock(spec=ProductModel)
        existing_product_mock.id = product_id
        existing_product_mock.barcode = "OLD_BARCODE" # Barcode antigo
        # ... (outros atributos de existing_product_mock)

        update_data_new_barcode = sample_product_schema # Usa o barcode de sample_product_schema ("BARCODE123")
        assert update_data_new_barcode.barcode != existing_product_mock.barcode

        mock_product_repo.get_product_by_id.return_value = existing_product_mock
        mock_product_repo.get_product_by_barcode.return_value = None # Novo barcode é único
        mock_product_repo.update_product.return_value = existing_product_mock # Simula atualização
        
        updated_product = product_service.update_product(product_id, update_data_new_barcode)

        mock_product_repo.get_product_by_id.assert_called_once_with(product_id)
        mock_product_repo.get_product_by_barcode.assert_called_once_with(update_data_new_barcode.barcode)
        mock_product_repo.update_product.assert_called_once_with(existing_product_mock, update_data_new_barcode)
        assert updated_product == existing_product_mock

    def test_update_product_barcode_changed_to_conflicting(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock, mocker
    ):
        product_id_to_update = 1
        product_to_update_mock = mocker.Mock(spec=ProductModel)
        product_to_update_mock.id = product_id_to_update
        product_to_update_mock.barcode = "OLD_BARCODE"

        conflicting_barcode = sample_product_schema.barcode # Ex: "BARCODE123"
        update_data_conflicting_barcode = ProductSchema(
            description="Update with conflict", price=10.0, barcode=conflicting_barcode,
            section="Sect", stock=10, image_urls=[VALID_IMAGE_URL_FOR_TEST]
        )

        # Outro produto já existe com este barcode
        other_product_with_barcode = mocker.Mock(spec=ProductModel)
        other_product_with_barcode.id = 2 # ID diferente
        other_product_with_barcode.barcode = conflicting_barcode

        mock_product_repo.get_product_by_id.return_value = product_to_update_mock
        mock_product_repo.get_product_by_barcode.return_value = other_product_with_barcode # Conflito encontrado

        with pytest.raises(HTTPException) as exc_info:
            product_service.update_product(product_id_to_update, update_data_conflicting_barcode)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Barcode already registered for another product"
        mock_product_repo.get_product_by_id.assert_called_once_with(product_id_to_update)
        mock_product_repo.get_product_by_barcode.assert_called_once_with(conflicting_barcode)
        mock_product_repo.update_product.assert_not_called()

    def test_update_product_db_integrity_error_on_update(
        self, product_service: ProductService, mock_product_repo: Mock,
        sample_product_schema: ProductSchema, sample_product_model: Mock 
    ):
        product_id = sample_product_model.id
        update_data = sample_product_schema

        mock_product_repo.get_product_by_id.return_value = sample_product_model
        if update_data.barcode != sample_product_model.barcode:
            mock_product_repo.get_product_by_barcode.return_value = None
            
        mock_product_repo.update_product.side_effect = IntegrityError("mocked db error", params={}, orig=None)

        with pytest.raises(HTTPException) as exc_info:
            product_service.update_product(product_id, update_data)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        # CORREÇÃO AQUI:
        assert exc_info.value.detail == "Update failed due to data conflict (e.g., barcode already exists for another product - DB integrity)"


    def test_update_product_stock_decrease_success(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock, mocker
    ):
        product_id = sample_product_model.id
        initial_stock = sample_product_model.stock # 50
        quantity_change = 10
        expected_new_stock = initial_stock - quantity_change # 40

        # Mock get_product_by_id para retornar o produto com estoque inicial
        # sample_product_model já tem o estoque inicial configurado
        mock_product_repo.get_product_by_id.return_value = sample_product_model
        
        # Mock update_stock para retornar o produto com o estoque atualizado
        updated_product_mock = mocker.Mock(spec=ProductModel) # Pode ser o mesmo sample_product_model modificado
        # Copiar atributos e atualizar o estoque
        for attr in ['id', 'description', 'price', 'barcode', 'section', 'expiry_date', 'images']:
            setattr(updated_product_mock, attr, getattr(sample_product_model, attr))
        updated_product_mock.stock = expected_new_stock
        mock_product_repo.update_stock.return_value = updated_product_mock


        result = product_service.update_product_stock(product_id, quantity_change, increase=False)

        mock_product_repo.get_product_by_id.assert_called_once_with(product_id)
        mock_product_repo.update_stock.assert_called_once_with(sample_product_model, expected_new_stock)
        assert result.stock == expected_new_stock

    def test_update_product_stock_decrease_insufficient_stock(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock
    ):
        product_id = sample_product_model.id
        initial_stock = sample_product_model.stock # 50
        quantity_change = initial_stock + 1 # Tenta tirar mais do que tem

        mock_product_repo.get_product_by_id.return_value = sample_product_model

        with pytest.raises(HTTPException) as exc_info:
            product_service.update_product_stock(product_id, quantity_change, increase=False)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Insufficient stock"

    def test_update_product_stock_decrease_negative_quantity(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock
    ):
        mock_product_repo.get_product_by_id.return_value = sample_product_model # get_product_by_id é chamado primeiro
        with pytest.raises(HTTPException) as exc_info:
            product_service.update_product_stock(sample_product_model.id, -5, increase=False)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Quantity to decrease must be non-negative"

    def test_update_product_stock_increase_success(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock, mocker
    ):
        product_id = sample_product_model.id
        initial_stock = sample_product_model.stock # 50
        quantity_change = 10
        expected_new_stock = initial_stock + quantity_change # 60

        mock_product_repo.get_product_by_id.return_value = sample_product_model
        
        updated_product_mock = mocker.Mock(spec=ProductModel)
        for attr in ['id', 'description', 'price', 'barcode', 'section', 'expiry_date', 'images']:
            setattr(updated_product_mock, attr, getattr(sample_product_model, attr))
        updated_product_mock.stock = expected_new_stock
        mock_product_repo.update_stock.return_value = updated_product_mock

        result = product_service.update_product_stock(product_id, quantity_change, increase=True)

        mock_product_repo.get_product_by_id.assert_called_once_with(product_id)
        mock_product_repo.update_stock.assert_called_once_with(sample_product_model, expected_new_stock)
        assert result.stock == expected_new_stock

    def test_update_product_stock_increase_negative_quantity(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock
    ):
        mock_product_repo.get_product_by_id.return_value = sample_product_model
        with pytest.raises(HTTPException) as exc_info:
            product_service.update_product_stock(sample_product_model.id, -5, increase=True)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Quantity to increase must be non-negative"


    def test_delete_product_success(
        self, product_service: ProductService, mock_product_repo: Mock, sample_product_model: Mock
    ):
        product_id = sample_product_model.id
        mock_product_repo.get_product_by_id.return_value = sample_product_model # Produto existe
        mock_product_repo.delete_product.return_value = None # delete não retorna nada

        product_service.delete_product(product_id)

        mock_product_repo.get_product_by_id.assert_called_once_with(product_id)
        mock_product_repo.delete_product.assert_called_once_with(sample_product_model)

    def test_delete_product_not_found(self, product_service: ProductService, mock_product_repo: Mock):
        mock_product_repo.get_product_by_id.return_value = None # Produto não existe
        
        with pytest.raises(HTTPException) as exc_info:
            product_service.delete_product(999)
            
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Product not found"
        mock_product_repo.delete_product.assert_not_called()