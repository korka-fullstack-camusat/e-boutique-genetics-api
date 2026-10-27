from pydantic import BaseModel, Field, model_validator
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
    cost_price: Optional[float] = Field(None, ge=0)


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
    cost_price: Optional[float] = Field(None, ge=0)


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


# ── Packs ─────────────────────────────────────────────────────────────────────

class PackItemIn(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)


class PackCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    images: Optional[List[str]] = []
    is_active: bool = True
    items: List[PackItemIn] = Field(..., min_length=1)


class PackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None
    items: Optional[List[PackItemIn]] = Field(None, min_length=1)


class PackItemResponse(BaseModel):
    product_id: int
    quantity: int
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    product_stock: int = 0


class PackResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    images: List[str] = []
    is_active: bool
    created_at: datetime
    items: List[PackItemResponse] = []
    regular_price: float          # somme des prix unitaires × quantités
    savings: float                # regular_price - price (≥ 0)
    stock: int                    # nombre de packs réalisables avec le stock actuel


# ── Partenaires installateurs ─────────────────────────────────────────────────

class PartnerApplicationCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    company: Optional[str] = None
    phone: str = Field(..., min_length=6)
    email: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2)
    zones: Optional[str] = None
    specialties: List[str] = Field(..., min_length=1)
    experience_years: str
    team_size: Optional[str] = None
    certifications: Optional[str] = None
    message: Optional[str] = None


class PartnerApplicationUpdate(BaseModel):
    status: str = Field(..., pattern="^(nouveau|contacte|valide|refuse)$")


class PartnerApplicationResponse(BaseModel):
    id: int
    full_name: str
    company: Optional[str] = None
    phone: str
    email: str
    city: str
    zones: Optional[str] = None
    specialties: List[str] = []
    experience_years: Optional[str] = None
    team_size: Optional[str] = None
    certifications: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: Optional[int] = None
    pack_id: Optional[int] = None
    product_name: str
    quantity: int
    price: float
    size: Optional[str] = None
    color: Optional[str] = None

    @model_validator(mode="after")
    def _product_or_pack(self):
        if (self.product_id is None) == (self.pack_id is None):
            raise ValueError("Chaque ligne doit référencer soit un produit, soit un pack")
        return self


class OrderItemResponse(BaseModel):
    product_id: Optional[int] = None
    pack_id: Optional[int] = None
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
    invoice_number: Optional[int] = None
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class ProductCost(BaseModel):
    id: int
    cost_price: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Réglages : mode maintenance ───────────────────────────────────────────────

DEFAULT_MAINTENANCE_MESSAGE = (
    "Notre boutique est en cours de maintenance. Nous revenons très vite — merci de votre patience !"
)


class MaintenanceSetting(BaseModel):
    enabled: bool = False
    message: str = DEFAULT_MAINTENANCE_MESSAGE
    updated_at: Optional[datetime] = None


class MaintenanceUpdate(BaseModel):
    enabled: bool
    message: Optional[str] = Field(None, max_length=500)


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
