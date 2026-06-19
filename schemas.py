from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    sous_category: Optional[str] = None
    stock: int = 0
    images: Optional[List[str]] = []
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []
    condition: Optional[str] = "neuf"
    reference: Optional[str] = None
    marque: Optional[str] = None
    disponibilite: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    sous_category: Optional[str] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    condition: Optional[str] = None
    reference: Optional[str] = None
    marque: Optional[str] = None
    disponibilite: Optional[str] = None


class ProductResponse(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    sous_category: Optional[str] = None
    stock: int = 0
    images: Optional[List[str]] = []
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []
    condition: Optional[str] = "neuf"
    reference: Optional[str] = None
    marque: Optional[str] = None
    disponibilite: Optional[str] = None
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    size: Optional[str] = None
    color: Optional[str] = None


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    size: Optional[str] = None
    color: Optional[str] = None
    id: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    payment_method: str
    total_amount: float
    delivery_method: Optional[str] = None
    delivery_fee: float = 0
    acompte_amount: Optional[float] = None
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    customer_address: Optional[str]
    payment_method: str
    total_amount: float
    delivery_method: Optional[str] = None
    delivery_fee: float = 0
    acompte_amount: Optional[float] = None
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None


# ── Admin users ───────────────────────────────────────────────────────────────

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "admin"


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Devis ─────────────────────────────────────────────────────────────────────

class DevisCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    service: str
    description: str


# ── Survey ────────────────────────────────────────────────────────────────────

class SurveyCreate(BaseModel):
    name: str
    email: str
    age: Optional[str]
    profession: Optional[str]
    style: Optional[str]
    brand: Optional[str]
    hobbies: Optional[str]
    monthly_budget: Optional[str]
    clothing_type: Optional[str]
    suggestions: Optional[str]


class SurveyResponse(BaseModel):
    name: str
    email: str
    age: Optional[str]
    profession: Optional[str]
    style: Optional[str]
    brand: Optional[str]
    hobbies: Optional[str]
    monthly_budget: Optional[str]
    clothing_type: Optional[str]
    suggestions: Optional[str]
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
