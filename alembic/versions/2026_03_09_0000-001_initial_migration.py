"""Initial migration - create users and links tables

Revision ID: 001
Revises: 
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table (FastAPI Users compatible)
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create links table
    op.create_table(
        'links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_url', sa.String(length=2048), nullable=False),
        sa.Column('short_code', sa.String(length=50), nullable=False),
        sa.Column('custom_alias', sa.String(length=100), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=True),
        sa.Column('project', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_links_custom_alias'), 'links', ['custom_alias'], unique=True)
    op.create_index(op.f('ix_links_id'), 'links', ['id'], unique=False)
    op.create_index(op.f('ix_links_original_url'), 'links', ['original_url'], unique=False)
    op.create_index(op.f('ix_links_project'), 'links', ['project'], unique=False)
    op.create_index(op.f('ix_links_short_code'), 'links', ['short_code'], unique=True)


def downgrade() -> None:
    # Drop links table
    op.drop_index(op.f('ix_links_short_code'), table_name='links')
    op.drop_index(op.f('ix_links_project'), table_name='links')
    op.drop_index(op.f('ix_links_original_url'), table_name='links')
    op.drop_index(op.f('ix_links_id'), table_name='links')
    op.drop_index(op.f('ix_links_custom_alias'), table_name='links')
    op.drop_table('links')

    # Drop users table
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
