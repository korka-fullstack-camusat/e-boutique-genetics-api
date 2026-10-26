"""Packs produits, lignes de commande « pack » et candidatures partenaires

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-26 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "packs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_packs_id", "packs", ["id"])
    op.create_index("ix_packs_created_at", "packs", ["created_at"])

    op.create_table(
        "pack_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pack_id", sa.Integer(), sa.ForeignKey("packs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_pack_items_id", "pack_items", ["id"])
    op.create_index("ix_pack_items_pack_id", "pack_items", ["pack_id"])

    # Une ligne de commande peut désormais être un pack (product_id vide, pack_id renseigné)
    op.add_column("order_items", sa.Column("pack_id", sa.Integer(), nullable=True))
    op.alter_column("order_items", "product_id", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "partner_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("zones", sa.String(), nullable=True),
        sa.Column("specialties", sa.JSON(), nullable=True),
        sa.Column("experience_years", sa.String(), nullable=True),
        sa.Column("team_size", sa.String(), nullable=True),
        sa.Column("certifications", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default="nouveau"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_partner_applications_id", "partner_applications", ["id"])
    op.create_index("ix_partner_applications_created_at", "partner_applications", ["created_at"])
    op.create_index("ix_partner_applications_status", "partner_applications", ["status"])


def downgrade() -> None:
    op.drop_table("partner_applications")
    op.execute("DELETE FROM order_items WHERE product_id IS NULL")
    op.alter_column("order_items", "product_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("order_items", "pack_id")
    op.drop_table("pack_items")
    op.drop_table("packs")
