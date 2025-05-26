"""add ENUM to role users

Revision ID: c1614b69720a
Revises: fd60eb75afd8
Create Date: 2025-05-26 12:40:29.592065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # Importar postgresql para usar postgresql.ENUM

# revision identifiers, used by Alembic.
revision: str = 'c1614b69720a'
down_revision: Union[str, None] = 'fd60eb75afd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_ROLE_ENUM_NAME = 'user_role_enum' # << MANTENHA ESTE NOME CONSISTENTE (ou user_role como você tinha)
                                     # O importante é que seja o mesmo no create e no alter_column
# Valores que serão os labels no ENUM do PostgreSQL
USER_ROLE_DB_LABELS = ('ADMIN', 'USER') # << CORRIGIDO PARA MAIÚSCULAS

# Definição do tipo ENUM para ser usado nos comandos op
user_role_pg_enum = postgresql.ENUM(*USER_ROLE_DB_LABELS, name=USER_ROLE_ENUM_NAME)


def upgrade() -> None:
    # 1. Criar o tipo ENUM no PostgreSQL com labels MAIÚSCULAS
    user_role_pg_enum.create(op.get_bind(), checkfirst=True)

    # 2. Alterar a coluna para usar o novo tipo ENUM
    # Se os valores existentes na coluna 'role' (que era VARCHAR) forem minúsculos ('admin', 'user'),
    # precisamos convertê-los para maiúsculos durante o cast para o novo tipo ENUM.
    op.alter_column('users', 'role',
               existing_type=sa.String(), # Assumindo que era String/VARCHAR antes
               type_=user_role_pg_enum,   # O tipo ENUM que acabamos de definir/criar
               nullable=False,
               # Cast para o novo tipo, convertendo para maiúsculas se necessário:
               postgresql_using=f"UPPER(role::text)::{USER_ROLE_ENUM_NAME}"
               )
    # Se você tiver um default no modelo como UserRoleEnum.USER.value, e quiser um server_default:
    # op.alter_column('users', 'role', server_default='USER') # Ou UserRoleEnum.USER.name


def downgrade() -> None:
    # 1. Alterar a coluna de volta para VARCHAR
    op.alter_column('users', 'role',
               existing_type=user_role_pg_enum, # O tipo ENUM que está sendo removido
               type_=sa.String(),
               nullable=False,
               # Se tinha um server_default, considere restaurá-lo
               postgresql_using='role::character varying' # Cast de volta para varchar
               )

    # 2. Remover o tipo ENUM do PostgreSQL
    user_role_pg_enum.drop(op.get_bind(), checkfirst=True)