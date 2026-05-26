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
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")


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
