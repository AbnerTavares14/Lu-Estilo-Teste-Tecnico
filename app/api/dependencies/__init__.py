from .auth import get_user_repository, get_auth_service, get_current_user, restrict_to_role
from .db import get_db_session
from .customer import get_customer_repository, get_customer_service
from .product import get_product_repository, get_product_service
from .order import get_order_repository, get_order_service, get_customer_repository
from .whatsapp import get_whatsapp_service
from .permissions import require_admin

