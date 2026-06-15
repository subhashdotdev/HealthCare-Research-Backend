"""Create tables for users, tokens, searches, sessions, and pdf_chunks

Revision ID: 3f97d3675926
Revises: 
Create Date: 2025-07-22 16:39:19.344348
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

revision = '3f97d3675926'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    

    op.create_table(
        'tbl_users',
        sa.Column('user_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'tbl_tokens',
        sa.Column('token_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('tbl_users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('jwt_access_token', sa.String(255), nullable=False),
        sa.Column('jwt_refresh_token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'tbl_searches',
        sa.Column('search_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('tbl_users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('search_term', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    op.create_table(
        'sessions',
        sa.Column('session_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('pdf_path', sa.String(512), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    op.create_table(
        'pdf_chunks',
        sa.Column('chunk_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('pdf_path', sa.String(512), nullable=False),
        sa.Column('chunk_text', sa.String, nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    op.execute("CREATE INDEX IF NOT EXISTS pdf_chunks_embedding_idx ON pdf_chunks USING hnsw (embedding vector_cosine_ops)")

def downgrade():
    op.drop_table('pdf_chunks')
    op.drop_table('sessions')
    op.drop_table('tbl_searches')
    op.drop_table('tbl_tokens')
    op.drop_table('tbl_users')
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS uuid_ossp")