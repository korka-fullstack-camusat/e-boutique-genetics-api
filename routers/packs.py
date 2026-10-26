from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Pack, PackItem, Product
from routers.admin_users import require_admin
from schemas import PackCreate, PackUpdate, PackResponse, PackItemIn

router = APIRouter()


def _serialize(pack: Pack) -> PackResponse:
    items = []
    regular_price = 0.0
    stock = None
    for it in pack.items:
        p = it.product
        if p is None:
            continue
        regular_price += p.price * it.quantity
        possible = (p.stock or 0) // it.quantity
        stock = possible if stock is None else min(stock, possible)
        items.append({
            "product_id":    p.id,
            "quantity":      it.quantity,
            "product_name":  p.name,
            "product_price": p.price,
            "product_image": (p.images or [None])[0],
            "product_stock": p.stock or 0,
        })
    return PackResponse(
        id=pack.id,
        name=pack.name,
        description=pack.description,
        price=pack.price,
        images=pack.images or [],
        is_active=bool(pack.is_active),
        created_at=pack.created_at,
        items=items,
        regular_price=regular_price,
        savings=max(0.0, regular_price - pack.price),
        stock=stock or 0,
    )


async def _get_pack(db: AsyncSession, pack_id: int) -> Pack:
    pack = (await db.execute(select(Pack).where(Pack.id == pack_id))).scalar_one_or_none()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack introuvable")
    return pack


async def _build_items(db: AsyncSession, items: List[PackItemIn]) -> List[PackItem]:
    """Vérifie que les produits existent et regroupe les doublons."""
    quantities: dict[int, int] = {}
    for it in items:
        quantities[it.product_id] = quantities.get(it.product_id, 0) + it.quantity
    found = (await db.execute(select(Product.id).where(Product.id.in_(quantities)))).scalars().all()
    missing = set(quantities) - set(found)
    if missing:
        raise HTTPException(status_code=400, detail=f"Produit(s) introuvable(s) : {sorted(missing)}")
    return [PackItem(product_id=pid, quantity=qty) for pid, qty in quantities.items()]


@router.get("/", response_model=List[PackResponse])
async def list_packs(response: Response, db: AsyncSession = Depends(get_db)):
    """Packs visibles sur la boutique."""
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
    packs = (await db.execute(
        select(Pack).where(Pack.is_active == True).order_by(Pack.created_at.desc())  # noqa: E712
    )).scalars().all()
    return [_serialize(p) for p in packs if p.items]


@router.get("/admin/all", response_model=List[PackResponse], dependencies=[Depends(require_admin)])
async def list_all_packs(db: AsyncSession = Depends(get_db)):
    """Tous les packs, y compris masqués (administration)."""
    packs = (await db.execute(select(Pack).order_by(Pack.created_at.desc()))).scalars().all()
    return [_serialize(p) for p in packs]


@router.get("/{pack_id}", response_model=PackResponse)
async def get_pack(pack_id: int, db: AsyncSession = Depends(get_db)):
    pack = await _get_pack(db, pack_id)
    if not pack.is_active:
        raise HTTPException(status_code=404, detail="Pack introuvable")
    return _serialize(pack)


@router.post("/", response_model=PackResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def create_pack(data: PackCreate, db: AsyncSession = Depends(get_db)):
    pack = Pack(
        name=data.name.strip(),
        description=data.description,
        price=data.price,
        images=data.images or [],
        is_active=data.is_active,
    )
    pack.items = await _build_items(db, data.items)
    db.add(pack)
    await db.commit()
    pack_id = pack.id
    db.expire_all()  # recharge les produits des lignes (évite un chargement paresseux en async)
    return _serialize(await _get_pack(db, pack_id))


@router.put("/{pack_id}", response_model=PackResponse, dependencies=[Depends(require_admin)])
async def update_pack(pack_id: int, data: PackUpdate, db: AsyncSession = Depends(get_db)):
    pack = await _get_pack(db, pack_id)
    fields = data.model_dump(exclude_unset=True)
    items = fields.pop("items", None)
    for field, value in fields.items():
        setattr(pack, field, value.strip() if field == "name" and value else value)
    if items is not None:
        pack.items = await _build_items(db, data.items)
    await db.commit()
    db.expire_all()
    return _serialize(await _get_pack(db, pack_id))


@router.delete("/{pack_id}", dependencies=[Depends(require_admin)])
async def delete_pack(pack_id: int, db: AsyncSession = Depends(get_db)):
    pack = await _get_pack(db, pack_id)
    await db.delete(pack)
    await db.commit()
    return {"message": "Pack supprimé"}
