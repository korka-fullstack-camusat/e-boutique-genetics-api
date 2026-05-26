from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from database import get_db
from models import Product
from schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    sous_category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all products with optional filtering by category, sous-category and search"""
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    if sous_category:
        stmt = stmt.where(Product.sous_category == sous_category)
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Product.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single product by ID"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, updates: ProductUpdate, db: AsyncSession = Depends(get_db)):
    """Update a product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted"}
