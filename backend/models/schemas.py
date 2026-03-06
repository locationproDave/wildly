"""Pydantic models for the Wildly Ones API"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
import uuid


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    is_admin: bool = False
    discount_code: Optional[str] = None
    created_at: str


class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: str
    short_description: str
    price: float
    compare_at_price: Optional[float] = None
    cost: float
    category: str
    subcategory: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []
    pet_type: str  # dog, cat, both, reptile, bird, rabbit, fish, small_pet
    in_stock: bool = True
    stock_quantity: int = 100
    supplier: Optional[str] = None
    supplier_sku: Optional[str] = None
    features: List[str] = []
    ingredients: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    rating: float = 4.5
    review_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


class Cart(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: str
    items: List[Dict[str, Any]] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    image: Optional[str] = None


class ShippingAddress(BaseModel):
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "US"
    phone: Optional[str] = None


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"WO-{str(uuid.uuid4())[:8].upper()}")
    user_id: Optional[str] = None
    email: str
    items: List[Dict[str, Any]]
    subtotal: float
    shipping_cost: float = 0.0
    tax: float = 0.0
    total: float
    shipping_address: Optional[Dict[str, Any]] = None
    status: str = "pending"
    payment_status: str = "pending"
    stripe_session_id: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CheckoutRequest(BaseModel):
    cart_session_id: str
    email: str
    origin_url: str
    shipping_address: Optional[ShippingAddress] = None
    promo_code: Optional[str] = None


class PayPalOrderRequest(BaseModel):
    cart_session_id: str
    email: str
    promo_code: Optional[str] = None


class AgentQuery(BaseModel):
    query: str
    agent_type: Literal[
        "product_sourcing", "due_diligence", "copywriter", 
        "seo_content", "performance_marketing", "email_marketing", "customer_service"
    ]
    session_id: Optional[str] = None


class Promotion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: str
    discount_type: str  # percentage, fixed_amount, free_shipping
    discount_value: float
    min_purchase: float = 0.0
    max_uses: Optional[int] = None
    uses_count: int = 0
    is_active: bool = True
    is_first_order_only: bool = False
    is_loyalty_reward: bool = False
    valid_from: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LoyaltyPoints(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    points: int = 0
    lifetime_points: int = 0
    tier: str = "bronze"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PointsTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    points: int
    transaction_type: str
    description: str
    order_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    user_id: str
    user_name: str
    rating: int
    title: str
    content: str
    verified_purchase: bool = False
    helpful_count: int = 0
    images: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    title: str
    content: str
    images: List[str] = []


class Referral(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_id: str
    referrer_code: str
    referee_id: Optional[str] = None
    referee_email: Optional[str] = None
    status: str = "pending"
    referrer_reward: float = 10.0
    referee_reward: float = 10.0
    order_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class OrderTracking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    carrier: str
    tracking_number: str
    status: str = "in_transit"
    status_description: str = ""
    estimated_delivery: Optional[str] = None
    last_location: Optional[str] = None
    events: List[dict] = []
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Admin-specific models
class ProductCreate(BaseModel):
    name: str
    slug: str
    description: str
    short_description: str
    price: float
    compare_at_price: Optional[float] = None
    cost: float
    category: str
    subcategory: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []
    pet_type: str = "both"
    stock_quantity: int = 100
    features: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    cost: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    pet_type: Optional[str] = None
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    features: Optional[List[str]] = None


class OrderStatusUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class EmailCampaign(BaseModel):
    subject: str
    content: str
    segment_ids: List[str] = []
