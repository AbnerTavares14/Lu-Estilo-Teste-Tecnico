"""add ENUM to role users

Revision ID: c1614b69720a
Revises: fd60eb75afd8
Create Date: 2025-05-26 12:40:29.592065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c1614b69720a'
down_revision: Union[str, None] = 'fd60eb75afd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_ROLE_ENUM_NAME = 'user_role_enum'
USER_ROLE_DB_LABELS = ('ADMIN', 'USER') 

user_role_pg_enum = postgresql.ENUM(*USER_ROLE_DB_LABELS, name=USER_ROLE_ENUM_NAME)


def upgrade() -> None:
    user_role_pg_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column('users', 'role',
               existing_type=sa.String(),
               type_=user_role_pg_enum,   
               nullable=False,
               postgresql_using=f"UPPER(role::text)::{USER_ROLE_ENUM_NAME}"
               )


def downgrade() -> None:
    op.alter_column('users', 'role',
               existing_type=user_role_pg_enum, 
               type_=sa.String(),
               nullable=False,
               postgresql_using='role::character varying' 
               )

    user_role_pg_enum.drop(op.get_bind(), checkfirst=True)