from .auth_route import auth_route
from .customer_route import customer_route
from .product_route import product_route
from fastapi import APIRouter

router = APIRouter()

router.include_router(auth_route)
router.include_router(customer_route)
router.include_router(product_route)