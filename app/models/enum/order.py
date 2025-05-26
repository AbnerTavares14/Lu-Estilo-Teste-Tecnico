from enum import Enum as PyEnum

class OrderStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELED = "canceled"

