"""Indicateurs de bénéfice pour le tableau de bord (administration)."""
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Order, Pack, Product
from routers.admin_users import require_admin

router = APIRouter()

# Commandes prises en compte : validées par l'admin (ni en attente, ni annulées)
REALIZED_STATUSES = ("confirmed", "shipped", "delivered")


def _month_key(d: datetime) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _empty() -> dict:
    return {"orders": 0, "revenue": 0.0, "cost": 0.0, "profit": 0.0,
            "revenue_with_cost": 0.0, "revenue_without_cost": 0.0, "margin": None}


@router.get("/profit", dependencies=[Depends(require_admin)])
async def profit_stats(db: AsyncSession = Depends(get_db)):
    orders = (await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.status.in_(REALIZED_STATUSES))
    )).scalars().all()

    # Prix d'achat actuels : repli pour les commandes passées avant la saisie des prix d'achat
    product_cost = dict((await db.execute(select(Product.id, Product.cost_price))).all())
    pack_cost: dict[int, float | None] = {}
    for pack in (await db.execute(select(Pack))).scalars().all():
        costs = [product_cost.get(it.product_id) for it in pack.items]
        pack_cost[pack.id] = (
            sum(c * it.quantity for c, it in zip(costs, pack.items)) if costs and None not in costs else None
        )

    now = datetime.now(timezone.utc)
    this_month = _month_key(now)
    prev_month = "%04d-%02d" % _shift_month(now.year, now.month, -1)
    last_6 = ["%04d-%02d" % _shift_month(now.year, now.month, -k) for k in range(5, -1, -1)]

    periods = {"month": _empty(), "previous_month": _empty(), "all": _empty()}
    monthly = {m: {"month": m, "revenue": 0.0, "profit": 0.0, "orders": 0} for m in last_6}
    by_product = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "profit": 0.0, "has_cost": True})
    missing = defaultdict(float)

    for order in orders:
        month = _month_key(order.created_at.astimezone(timezone.utc))
        targets = [periods["all"]]
        if month == this_month:
            targets.append(periods["month"])
        elif month == prev_month:
            targets.append(periods["previous_month"])
        for t in targets:
            t["orders"] += 1
        if month in monthly:
            monthly[month]["orders"] += 1

        for item in order.items:
            revenue = item.price * item.quantity
            unit_cost = item.unit_cost
            if unit_cost is None:
                unit_cost = pack_cost.get(item.pack_id) if item.pack_id else product_cost.get(item.product_id)
            cost = unit_cost * item.quantity if unit_cost is not None else None
            profit = revenue - cost if cost is not None else 0.0

            for t in targets:
                t["revenue"] += revenue
                if cost is None:
                    t["revenue_without_cost"] += revenue
                else:
                    t["revenue_with_cost"] += revenue
                    t["cost"] += cost
                    t["profit"] += profit
            if month in monthly:
                monthly[month]["revenue"] += revenue
                monthly[month]["profit"] += profit

            p = by_product[item.product_name]
            p["quantity"] += item.quantity
            p["revenue"] += revenue
            p["profit"] += profit
            if cost is None:
                p["has_cost"] = False
                missing[item.product_name] += revenue

    for t in periods.values():
        if t["revenue_with_cost"] > 0:
            t["margin"] = round(t["profit"] / t["revenue_with_cost"] * 100, 1)

    top = sorted(
        ({"name": n, **v} for n, v in by_product.items() if v["has_cost"]),
        key=lambda x: x["profit"], reverse=True,
    )[:5]
    missing_cost = sorted(({"name": n, "revenue": r} for n, r in missing.items()),
                          key=lambda x: x["revenue"], reverse=True)[:10]

    return {
        "periods": periods,
        "monthly": list(monthly.values()),
        "top_products": [{k: v for k, v in p.items() if k != "has_cost"} for p in top],
        "missing_cost": missing_cost,
        "products_without_cost": sum(1 for c in product_cost.values() if c is None),
        "products_total": len(product_cost),
    }
