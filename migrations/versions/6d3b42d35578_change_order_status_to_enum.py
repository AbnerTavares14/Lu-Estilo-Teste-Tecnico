from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '6d3b42d35578'
down_revision: Union[str, None] = '5d88e09d3843'
branch_labels: Union[str, sa.Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Definir o tipo ENUM
order_status_enum = postgresql.ENUM(
    'pending', 'processing', 'completed', 'canceled',
    name='order_status',
    create_type=True
)

def upgrade() -> None:
    order_status_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        'orders',
        'status',
        existing_type=sa.String(),
        type_=order_status_enum,
        postgresql_using='status::order_status',
        nullable=False
    )

def downgrade() -> None:
    op.alter_column(
        'orders',
        'status',
        existing_type=order_status_enum,
        type_=sa.String(),
        nullable=False
    )

    order_status_enum.drop(op.get_bind(), checkfirst=True)