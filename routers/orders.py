from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from database import get_db
from models import Order, OrderItem, Product
from schemas import OrderCreate, OrderUpdate, OrderResponse
from email_service import send_order_confirmation

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def get_orders(db: AsyncSession = Depends(get_db)):
    """Get all orders with their items"""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new order and send email notification"""
    order = Order(
        customer_name    = order_data.customer_name,
        customer_email   = order_data.customer_email,
        customer_phone   = order_data.customer_phone,
        customer_address = order_data.customer_address,
        payment_method   = order_data.payment_method,
        total_amount     = order_data.total_amount,
        delivery_method  = order_data.delivery_method,
        delivery_fee     = order_data.delivery_fee or 0,
        acompte_amount   = order_data.acompte_amount,
        status           = "pending",
    )
    db.add(order)
    await db.flush()  # get order.id before committing

    items = [
        OrderItem(
            order_id     = order.id,
            product_id   = i.product_id,
            product_name = i.product_name,
            quantity     = i.quantity,
            price        = i.price,
            size         = i.size,
            color        = i.color,
        )
        for i in order_data.items
    ]
    db.add_all(items)

    # Décrémenter le stock de chaque produit commandé
    for i in order_data.items:
        prod_result = await db.execute(select(Product).where(Product.id == i.product_id))
        product = prod_result.scalar_one_or_none()
        if product:
            product.stock = max(0, product.stock - i.quantity)

    await db.commit()

    # Serialize to plain dict before session closes — avoids DetachedInstanceError
    email_data = {
        "id":               order.id,
        "customer_name":    order.customer_name,
        "customer_email":   order.customer_email,
        "customer_phone":   order.customer_phone,
        "customer_address": order.customer_address,
        "payment_method":   order.payment_method,
        "total_amount":     order.total_amount,
        "delivery_method":  order.delivery_method,
        "delivery_fee":     order.delivery_fee,
        "acompte_amount":   order.acompte_amount,
        "created_at":       order.created_at,
        "items": [
            {
                "product_name": i.product_name,
                "quantity":     i.quantity,
                "price":        i.price,
                "size":         i.size,
                "color":        i.color,
            }
            for i in items
        ],
    }
    background_tasks.add_task(send_order_confirmation, email_data)

    return {"message": "Order created successfully", "order_id": order.id}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single order by ID with its items"""
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order_status(order_id: int, updates: OrderUpdate, db: AsyncSession = Depends(get_db)):
    """Update order status"""
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if updates.status:
        order.status = updates.status
    await db.commit()
    await db.refresh(order)
    return order
