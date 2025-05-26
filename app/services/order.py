from typing import List, Optional
from fastapi import HTTPException, status as http_status
from app.services.whatsapp_service import logger
from datetime import date as PyDate

from app.db.repositories.orders import OrderRepository
from app.services.products import ProductService 
from app.db.repositories.customers import CustomerRepository
from app.models.domain.order import OrderModel, OrderProduct, OrderStatus 
from app.models.schemas.order import OrderCreate, OrderStatusUpdate 
from app.services.whatsapp_service import WhatsappService

class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_service: ProductService, 
        customer_repository: CustomerRepository,
        whatsapp_service: WhatsappService
    ):
        self.order_repository = order_repository
        self.product_service = product_service 
        self.customer_repository = customer_repository
        self.whatsapp_service = whatsapp_service

    def _validate_customer_exists(self, customer_id: int):
        customer = self.customer_repository.get_customer_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        return customer

    def _prepare_order_items_and_calc_total(
        self,
        order_product_inputs: List[dict], 
        is_update: bool = False,
        existing_order_products: Optional[List[OrderProduct]] = None
    ) -> tuple[List[OrderProduct], float]:

        if is_update and existing_order_products:
            for old_op in existing_order_products:
                self.product_service.update_product_stock(
                    product_id=old_op.product_id,
                    quantity_change=old_op.quantity,
                    increase=True
                )
        
        new_order_product_models = []
        current_total_amount = 0.0

        for item_input in order_product_inputs:
            product_model = self.product_service.get_product_by_id(item_input.product_id)

            if product_model.stock < item_input.quantity: 
                 raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product ID {item_input.product_id}. Available: {product_model.stock}, Requested: {item_input.quantity}"
                )

            self.product_service.update_product_stock(
                product_id=product_model.id,
                quantity_change=item_input.quantity,
                increase=False 
            )

            new_op_model = OrderProduct(
                product_id=product_model.id,
                quantity=item_input.quantity,
                unit_price=product_model.price
            )
            new_order_product_models.append(new_op_model)
            current_total_amount += product_model.price * item_input.quantity
        
        return new_order_product_models, current_total_amount


    async def create_order(self, order_data: OrderCreate) -> OrderModel:
        customer = self._validate_customer_exists(order_data.customer_id) 

        try:
            OrderStatus(order_data.status) 
        except ValueError:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid order status: {order_data.status}")

        order_product_models, total_amount = self._prepare_order_items_and_calc_total(
            order_data.products
        )
        
        order_model_to_create = OrderModel(
            customer_id=order_data.customer_id,
            status=OrderStatus(order_data.status),
            total_amount=total_amount
        )
        
        created_order_model = self.order_repository.create_order(
            order_model_to_create, 
            order_product_models
        )
        if created_order_model: 
            if customer and customer.phone_number: 
                customer_name_first_part = customer.name.split(" ")[0]
                message = (
                    f"Olá {customer_name_first_part}, seu pedido Lu Estilo #{created_order_model.id} "
                    f"foi recebido e está sendo processado! Total: R${created_order_model.total_amount:.2f}. "
                    f"Obrigado!"
                )
                try:
                    success = await self.whatsapp_service.send_message(customer.phone_number, message)
                    if success:
                        logger.info(f"Notificação de WhatsApp para o pedido {created_order_model.id} enviada/simulada com sucesso.")
                    else:
                        logger.warning(f"Falha ao enviar/simular notificação de WhatsApp para o pedido {created_order_model.id}.")
                except Exception as e:
                    logger.error(f"Erro inesperado ao tentar enviar notificação de WhatsApp para pedido {created_order_model.id}: {str(e)}")
            elif customer:
                logger.info(f"Cliente {customer.name} (ID: {customer.id}) não possui número de telefone. Notificação WhatsApp não enviada para pedido {created_order_model.id}.")

        return created_order_model

    def get_order_by_id(self, order_id: int) -> OrderModel:
        order = self.order_repository.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
    
    def get_orders(
        self,
        limit: int = 100,
        skip: int = 0,
        customer_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        start_date_str: Optional[str] = None, 
        end_date_str: Optional[str] = None,   
        order_by_field: str = "created_at",
        order_direction: str = "desc",
        product_section: Optional[str] = None
    ) -> List[OrderModel]:
        if status_filter is not None:
            try:
                OrderStatus(status_filter) 
            except ValueError:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid order status filter: {status_filter}")

        parsed_start_date: Optional[PyDate] = None
        if start_date_str:
            try:
                parsed_start_date = PyDate.fromisoformat(start_date_str)
            except ValueError:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid start_date format. Use YYYY-MM-DD.")
        
        parsed_end_date: Optional[PyDate] = None
        if end_date_str:
            try:
                parsed_end_date = PyDate.fromisoformat(end_date_str)
            except ValueError:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid end_date format. Use YYYY-MM-DD.")

        return self.order_repository.get_orders(
            limit=limit, skip=skip, customer_id=customer_id, status_filter=status_filter,
            start_date=parsed_start_date, end_date=parsed_end_date,
            order_by_field=order_by_field, order_direction=order_direction, product_section=product_section
        )
    
    async def update_order_status(self, order_id: int, status_update_data: OrderStatusUpdate) -> OrderModel:
        order_to_update = self.get_order_by_id(order_id) 
        if not order_to_update: 
             raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")


        new_status_str = status_update_data.status
        try:
            new_status_enum = OrderStatus(new_status_str)
        except ValueError:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid order status: {new_status_str}")

        current_status_str = order_to_update.status.value if isinstance(order_to_update.status, OrderStatus) else order_to_update.status
        
        if new_status_enum == OrderStatus.CANCELED and current_status_str != OrderStatus.CANCELED.value:
            if not order_to_update.order_products: 
                 reloaded_order_for_stock = self.order_repository.get_order_by_id_internal(order_id, load_relations=True)
                 if not reloaded_order_for_stock: 
                     raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found for stock update.")
                 items_to_restore = reloaded_order_for_stock.order_products
            else:
                 items_to_restore = order_to_update.order_products

            for op in items_to_restore:
                self.product_service.update_product_stock(op.product_id, op.quantity, increase=True)

        updated_order_model = self.order_repository.update_order_status(order_to_update, new_status_enum)

        if updated_order_model:
            customer = updated_order_model.customer 
            if customer and customer.phone_number:
                customer_name_first_part = customer.name.split(" ")[0]
                
                message_map = {
                    OrderStatus.PROCESSING.value: f"Seu pedido Lu Estilo #{updated_order_model.id} está sendo preparado para envio!",
                    OrderStatus.COMPLETED.value: f"Oba! Seu pedido Lu Estilo #{updated_order_model.id} foi concluído e enviado. Código de rastreio: XYZ123BR.",
                    OrderStatus.CANCELED.value: f"Seu pedido Lu Estilo #{updated_order_model.id} foi cancelado conforme solicitado."
                }
                
                message_body = message_map.get(new_status_str) 
                
                if message_body: 
                    full_message = f"Olá {customer_name_first_part}, {message_body}"
                    try:
                        success = await self.whatsapp_service.send_message(customer.phone_number, full_message)
                        if success:
                            logger.info(f"Notificação de status '{new_status_str}' para o pedido {updated_order_model.id} enviada/simulada.")
                        else:
                            logger.warning(f"Falha ao enviar/simular notificação de status '{new_status_str}' para o pedido {updated_order_model.id}.")
                    except Exception as e:
                        logger.error(f"Erro inesperado ao tentar enviar notificação de status (WhatsApp) para pedido {updated_order_model.id}: {str(e)}")
                else:
                    logger.info(f"Nenhuma mensagem de WhatsApp configurada para o status '{new_status_str}' do pedido {updated_order_model.id}.")
            elif customer:
                logger.info(f"Cliente {customer.name} não possui número de telefone. Notificação de status (WhatsApp) não enviada para pedido {updated_order_model.id}.")

        return updated_order_model


    def delete_order(self, order_id: int) -> None:
        order_to_delete = self.get_order_by_id(order_id)

        if order_to_delete.status != OrderStatus.CANCELED.value: 
            for op in order_to_delete.order_products:
                self.product_service.update_product_stock(op.product_id, op.quantity, increase=True)
        
        self.order_repository.delete_order(order_to_delete)

    
    def update_order(self, order_id: int, order_update_data: OrderCreate) -> OrderModel:
        order_to_update = self.order_repository.get_order_by_id_internal(order_id, load_relations=True) 
        if not order_to_update:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")

        self._validate_customer_exists(order_update_data.customer_id)
        try:
            OrderStatus(order_update_data.status)
        except ValueError:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid order status: {order_update_data.status}")


        new_order_product_models, new_total_amount = self._prepare_order_items_and_calc_total(
            order_update_data.products,
            is_update=True,
            existing_order_products=list(order_to_update.order_products) 
        )

        return self.order_repository.update_order(
            order_to_update,
            new_customer_id=order_update_data.customer_id,
            new_status=order_update_data.status,
            new_total_amount=new_total_amount,
            new_order_products=new_order_product_models
        )

    def delete_order(self, order_id: int) -> None:
        order_to_delete = self.get_order_by_id(order_id) 

        if order_to_delete.status != OrderStatus.CANCELED.value:
            for op in order_to_delete.order_products:
                try:
                    self.product_service.update_product_stock(op.product_id, op.quantity, increase=True)
                except HTTPException as e:
                    print(f"Warning: Could not restore stock for product {op.product_id} during order deletion: {e.detail}")
        
        self.order_repository.delete_order(order_to_delete)