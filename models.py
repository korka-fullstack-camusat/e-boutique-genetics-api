from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON,
    ForeignKey, Text, Index, Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category", "category"),
        Index("ix_products_sous_category", "sous_category"),
        Index("ix_products_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    sous_category = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    images = Column(JSON, default=list)
    sizes = Column(JSON, default=list)
    colors = Column(JSON, default=list)
    condition      = Column(String, default="neuf")  # "neuf" | "reconditionne"
    reference      = Column(String, nullable=True)
    marque         = Column(String, nullable=True)
    disponibilite  = Column(String, nullable=True)   # "24h" | "48h" | "72h"
    cost_price     = Column(Float, nullable=True)    # prix d'achat — jamais exposé sur l'API publique
    created_at     = Column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_customer_email", "customer_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)
    customer_address = Column(Text, nullable=True)
    payment_method = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    delivery_method = Column(String, nullable=True)   # domicile | retrait | personnel
    delivery_fee    = Column(Float,  default=0)
    acompte_amount  = Column(Float,  nullable=True)   # montant de l'acompte Wave si applicable
    invoice_number  = Column(Integer, nullable=True, unique=True)  # numéro séquentiel de facture (01, 02, ...)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, nullable=True)   # null pour une ligne « pack »
    pack_id    = Column(Integer, nullable=True)   # renseigné quand la ligne est un pack
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=True)      # prix d'achat unitaire au moment de la vente
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")


class Pack(Base):
    """Lot de plusieurs produits vendu à un prix groupé."""
    __tablename__ = "packs"
    __table_args__ = (
        Index("ix_packs_created_at", "created_at"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price       = Column(Float, nullable=False)          # prix du pack
    images      = Column(JSON, default=list)
    is_active   = Column(Boolean, default=True)          # visible sur la boutique
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "PackItem", back_populates="pack",
        cascade="all, delete-orphan", order_by="PackItem.id", lazy="selectin",
    )


class PackItem(Base):
    __tablename__ = "pack_items"
    __table_args__ = (
        Index("ix_pack_items_pack_id", "pack_id"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    pack_id    = Column(Integer, ForeignKey("packs.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity   = Column(Integer, nullable=False, default=1)

    pack    = relationship("Pack", back_populates="items")
    product = relationship("Product", lazy="selectin")


class PartnerApplication(Base):
    """Candidature d'un installateur souhaitant devenir partenaire."""
    __tablename__ = "partner_applications"
    __table_args__ = (
        Index("ix_partner_applications_created_at", "created_at"),
        Index("ix_partner_applications_status", "status"),
    )

    id               = Column(Integer, primary_key=True, index=True)
    full_name        = Column(String, nullable=False)
    company          = Column(String, nullable=True)
    phone            = Column(String, nullable=False)
    email            = Column(String, nullable=False)
    city             = Column(String, nullable=False)
    zones            = Column(String, nullable=True)      # zones d'intervention
    specialties      = Column(JSON, default=list)         # domaines d'installation
    experience_years = Column(String, nullable=True)
    team_size        = Column(String, nullable=True)
    certifications   = Column(Text, nullable=True)
    message          = Column(Text, nullable=True)
    status           = Column(String, default="nouveau")  # nouveau | contacte | valide | refuse
    created_at       = Column(DateTime(timezone=True), server_default=func.now())


class AppSetting(Base):
    """Réglages globaux de la boutique (ex. mode maintenance), stockés en JSON par clé."""
    __tablename__ = "app_settings"

    key        = Column(String, primary_key=True)
    value      = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        Index("ix_admin_users_email", "email", unique=True),
    )

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    email      = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role       = Column(String, default="admin")   # "superadmin" | "admin"
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Survey(Base):
    __tablename__ = "surveys"
    __table_args__ = (
        Index("ix_surveys_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    age = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    style = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    hobbies = Column(String, nullable=True)
    monthly_budget = Column(String, nullable=True)
    clothing_type = Column(String, nullable=True)
    suggestions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
