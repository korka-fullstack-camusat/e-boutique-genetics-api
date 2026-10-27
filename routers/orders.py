from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from database import get_db
from models import Order, OrderItem, Pack, Product
from schemas import OrderCreate, OrderUpdate, OrderResponse
from email_service import send_order_confirmation, send_invoice_email
from routers.admin_users import require_admin
from routers.settings import get_maintenance

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
    if (await get_maintenance(db)).enabled:
        raise HTTPException(status_code=503, detail="La boutique est en maintenance, les commandes sont suspendues")
    max_invoice_number = (await db.execute(select(func.max(Order.invoice_number)))).scalar() or 0

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
        invoice_number   = max_invoice_number + 1,
        status           = "pending",
    )
    db.add(order)
    await db.flush()  # get order.id before committing

    async def decrement_stock(product_id: int, qty: int) -> Product | None:
        product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
        if product:
            product.stock = max(0, product.stock - qty)
        return product

    items = []
    for i in order_data.items:
        name = i.product_name
        unit_cost = None  # prix d'achat unitaire figé au moment de la vente (calcul du bénéfice)
        if i.pack_id is not None:
            pack = (await db.execute(select(Pack).where(Pack.id == i.pack_id))).scalar_one_or_none()
            if not pack or not pack.is_active:
                raise HTTPException(status_code=400, detail=f"Pack {i.pack_id} indisponible")
            # Le nom de la ligne (repris dans les emails et la facture) détaille le contenu du pack
            contents = ", ".join(f"{it.quantity}× {it.product.name}" for it in pack.items if it.product)
            name = f"Pack {pack.name} ({contents})" if contents else f"Pack {pack.name}"
            costs = [it.product.cost_price * it.quantity if it.product and it.product.cost_price is not None else None
                     for it in pack.items]
            unit_cost = sum(costs) if costs and None not in costs else None
            for it in pack.items:
                await decrement_stock(it.product_id, it.quantity * i.quantity)
        else:
            product = await decrement_stock(i.product_id, i.quantity)
            unit_cost = product.cost_price if product else None

        items.append(OrderItem(
            order_id     = order.id,
            product_id   = i.product_id,
            pack_id      = i.pack_id,
            product_name = name,
            quantity     = i.quantity,
            price        = i.price,
            unit_cost    = unit_cost,
            size         = i.size,
            color        = i.color,
        ))
    db.add_all(items)

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
        "invoice_number":   order.invoice_number,
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

    return {"message": "Order created successfully", "order_id": order.id, "invoice_number": order.invoice_number}


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


@router.post("/{order_id}/send-invoice")
async def send_order_invoice(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Send the invoice PDF for a confirmed order to the customer by email"""
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order.status != "confirmed":
        raise HTTPException(status_code=400, detail="La commande n'est pas confirmée")

    invoice_data = {
        "id":               order.id,
        "customer_name":    order.customer_name,
        "customer_email":   order.customer_email,
        "customer_phone":   order.customer_phone,
        "customer_address": order.customer_address,
        "payment_method":   order.payment_method,
        "total_amount":     order.total_amount,
        "acompte_amount":   order.acompte_amount,
        "invoice_number":   order.invoice_number,
        "created_at":       order.created_at,
        "items": [
            {"product_name": i.product_name, "quantity": i.quantity, "price": i.price}
            for i in order.items
        ],
    }
    try:
        await send_invoice_email(invoice_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur envoi facture : {exc}")
    return {"message": "Facture envoyée avec succès"}


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


@router.delete("/{order_id}", dependencies=[Depends(require_admin)])
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Supprime une commande déjà traitée (validée, expédiée, livrée ou annulée)."""
    order = (await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order.status == "pending":
        raise HTTPException(status_code=400, detail="Une commande en attente doit d'abord être validée ou rejetée")
    await db.delete(order)  # les lignes sont supprimées en cascade
    await db.commit()
    return {"message": "Commande supprimée"}
