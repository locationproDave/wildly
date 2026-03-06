from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from agents import AGENT_PROMPTS, AGENT_METADATA
from core.websocket import (
    manager, NotificationType, notify_new_order, notify_order_update,
    notify_low_stock, notify_new_customer, notify_revenue_update
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'calmtails_default_secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Emergent Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'sb')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # sandbox or live
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
TRACK17_API_KEY = os.environ.get('TRACK17_API_KEY', '')

# Configure Resend
import resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Create the main app
app = FastAPI(title="Wildly Ones Pet Wellness Store")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# ==================== MODELS ====================

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
    order_number: str = Field(default_factory=lambda: f"CT-{str(uuid.uuid4())[:8].upper()}")
    user_id: Optional[str] = None
    email: str
    items: List[Dict[str, Any]]
    subtotal: float
    shipping_cost: float = 0.0
    tax: float = 0.0
    total: float
    shipping_address: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, paid, processing, shipped, delivered, cancelled
    payment_status: str = "pending"  # pending, paid, failed, refunded
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
    agent_type: Literal["product_sourcing", "due_diligence", "copywriter", "seo_content", "performance_marketing", "email_marketing", "customer_service"]
    session_id: Optional[str] = None

class Promotion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: str
    discount_type: str  # percentage, fixed_amount, free_shipping
    discount_value: float  # percentage (0-100) or fixed amount
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
    tier: str = "bronze"  # bronze, silver, gold, platinum
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PointsTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    points: int  # positive for earned, negative for redeemed
    transaction_type: str  # earned, redeemed, bonus, expired
    description: str
    order_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    user_id: str
    user_name: str
    rating: int  # 1-5
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
    referrer_id: str  # User who shared the code
    referrer_code: str  # Unique referral code
    referee_id: Optional[str] = None  # User who used the code
    referee_email: Optional[str] = None
    status: str = "pending"  # pending, completed, expired
    referrer_reward: float = 10.0  # $10 for referrer
    referee_reward: float = 10.0  # $10 for referee
    order_id: Optional[str] = None  # Order that completed the referral
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class OrderTracking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    carrier: str  # ups, fedex, usps, dhl, etc.
    tracking_number: str
    status: str = "in_transit"  # pending, in_transit, out_for_delivery, delivered, exception
    status_description: str = ""
    estimated_delivery: Optional[str] = None
    last_location: Optional[str] = None
    events: List[dict] = []  # List of tracking events
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    items: List[dict] = []  # Products in subscription
    frequency: str = "monthly"  # monthly, bi-monthly, quarterly
    discount_percent: int = 10  # 10% off for subscribers
    status: str = "active"  # active, paused, cancelled
    next_delivery_date: str = Field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(days=30)).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_order_id: Optional[str] = None

class SubscriptionCreate(BaseModel):
    email: str
    items: List[dict]  # [{product_id, quantity}]
    frequency: str = "monthly"

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_discount_code() -> str:
    return f"CALM{str(uuid.uuid4())[:8].upper()}"

def generate_referral_code(user_name: str) -> str:
    """Generate a unique referral code based on user name"""
    prefix = ''.join(c for c in user_name.upper() if c.isalpha())[:4]
    if len(prefix) < 4:
        prefix = prefix.ljust(4, 'X')
    suffix = str(uuid.uuid4())[:4].upper()
    return f"{prefix}{suffix}"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        return user
    except:
        return None

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await require_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ==================== AI AGENTS ====================

async def get_agent_response(query: str, agent_type: str, session_id: str, chat_history: List[Dict[str, str]] = None) -> str:
    """Get response from specific agent with Claude"""
    system_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["product_sourcing"])
    
    models = [
        ("anthropic", "claude-opus-4-6"),
        ("anthropic", "claude-sonnet-4-5-20250929"),
        ("openai", "gpt-5.2"),
    ]
    
    last_error = None
    
    for provider, model in models:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"{agent_type}_{session_id}",
                system_message=system_prompt
            )
            chat.with_model(provider, model)
            
            context = ""
            if chat_history:
                for msg in chat_history[-6:]:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n\n"
            
            full_query = f"{context}User: {query}" if context else query
            user_message = UserMessage(text=full_query)
            
            try:
                response = await asyncio.wait_for(
                    chat.send_message(user_message),
                    timeout=90.0
                )
                logging.info(f"Agent {agent_type} response from {provider}/{model} successful")
                return response
            except asyncio.TimeoutError:
                logging.warning(f"Timeout with {provider}/{model} for agent {agent_type}")
                last_error = f"Timeout with {model}"
                continue
                
        except Exception as e:
            logging.warning(f"Error with {provider}/{model} for agent {agent_type}: {str(e)}")
            last_error = str(e)
            continue
    
    logging.error(f"All AI models failed for agent {agent_type}. Last error: {last_error}")
    
    error_msg = "AI service temporarily unavailable. Please try again in a moment."
    if "budget" in str(last_error).lower() or "cost" in str(last_error).lower():
        error_msg = "AI usage limit reached. Please go to Profile → Universal Key → Add Balance to continue."
    
    raise HTTPException(status_code=503, detail=error_msg)

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    discount_code = generate_discount_code()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "discount_code": discount_code,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_token(user_id)
    
    # Notify admin of new customer
    asyncio.create_task(notify_new_customer(user_doc))
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "is_admin": False,
            "discount_code": discount_code
        },
        "message": f"Welcome to Wildly Ones! Your exclusive discount code is: {discount_code} (15% off your first order)"
    }

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user.get("is_admin", False),
            "discount_code": user.get("discount_code")
        }
    }

@api_router.get("/auth/me", response_model=dict)
async def get_me(user: dict = Depends(require_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "is_admin": user.get("is_admin", False),
        "discount_code": user.get("discount_code")
    }

# ==================== PRODUCT ROUTES ====================

@api_router.get("/products", response_model=List[dict])
async def get_products(
    category: Optional[str] = None,
    pet_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    query_filter = {"in_stock": True}
    
    if category:
        query_filter["category"] = category
    if pet_type:
        # "both" means dogs and cats only, other pet types are standalone
        if pet_type in ["reptile", "bird", "rabbit", "fish", "small_pet", "chicken"]:
            query_filter["pet_type"] = pet_type
        else:
            query_filter["pet_type"] = {"$in": [pet_type, "both"]}
    if min_price is not None:
        query_filter["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query_filter:
            query_filter["price"]["$lte"] = max_price
        else:
            query_filter["price"] = {"$lte": max_price}
    if search:
        query_filter["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.products.find(query_filter, {"_id": 0}).limit(limit).to_list(limit)
    return products

@api_router.get("/products/featured", response_model=List[dict])
async def get_featured_products():
    products = await db.products.find(
        {"in_stock": True},
        {"_id": 0}
    ).sort("rating", -1).limit(8).to_list(8)
    return products

@api_router.get("/products/bestsellers", response_model=List[dict])
async def get_bestsellers():
    """Get best-selling products sorted by review count and rating"""
    products = await db.products.find(
        {"in_stock": True},
        {"_id": 0}
    ).sort([("review_count", -1), ("rating", -1)]).limit(8).to_list(8)
    return products

@api_router.get("/products/categories", response_model=List[str])
async def get_categories():
    categories = await db.products.distinct("category")
    return categories

@api_router.get("/products/{slug}", response_model=dict)
async def get_product(slug: str):
    product = await db.products.find_one({"slug": slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ==================== CART ROUTES ====================

@api_router.get("/cart/{session_id}", response_model=dict)
async def get_cart(session_id: str):
    cart = await db.carts.find_one({"session_id": session_id}, {"_id": 0})
    if not cart:
        cart = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "items": [],
            "subtotal": 0.0,
            "item_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.carts.insert_one({**cart})
        return cart
    
    # Populate product details
    populated_items = []
    for item in cart.get("items", []):
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            populated_items.append({
                **item,
                "product": product
            })
    
    cart["items"] = populated_items
    cart["subtotal"] = sum(item["product"]["price"] * item["quantity"] for item in populated_items) if populated_items else 0.0
    cart["item_count"] = sum(item["quantity"] for item in populated_items) if populated_items else 0
    
    return cart

@api_router.post("/cart/{session_id}/add", response_model=dict)
async def add_to_cart(session_id: str, item: CartItem):
    cart = await db.carts.find_one({"session_id": session_id})
    
    if not cart:
        cart = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "items": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.carts.insert_one(cart)
    
    # Check if product exists
    product = await db.products.find_one({"id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update cart items
    items = cart.get("items", [])
    existing_item = next((i for i in items if i["product_id"] == item.product_id), None)
    
    if existing_item:
        existing_item["quantity"] += item.quantity
    else:
        items.append({"product_id": item.product_id, "quantity": item.quantity})
    
    await db.carts.update_one(
        {"session_id": session_id},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return await get_cart(session_id)

@api_router.post("/cart/{session_id}/update", response_model=dict)
async def update_cart_item(session_id: str, item: CartItem):
    cart = await db.carts.find_one({"session_id": session_id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = cart.get("items", [])
    
    if item.quantity <= 0:
        items = [i for i in items if i["product_id"] != item.product_id]
    else:
        existing_item = next((i for i in items if i["product_id"] == item.product_id), None)
        if existing_item:
            existing_item["quantity"] = item.quantity
    
    await db.carts.update_one(
        {"session_id": session_id},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return await get_cart(session_id)

@api_router.delete("/cart/{session_id}/item/{product_id}", response_model=dict)
async def remove_from_cart(session_id: str, product_id: str):
    cart = await db.carts.find_one({"session_id": session_id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = [i for i in cart.get("items", []) if i["product_id"] != product_id]
    
    await db.carts.update_one(
        {"session_id": session_id},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return await get_cart(session_id)

@api_router.delete("/cart/{session_id}", response_model=dict)
async def clear_cart(session_id: str):
    await db.carts.update_one(
        {"session_id": session_id},
        {"$set": {"items": [], "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Cart cleared"}

# ==================== CHECKOUT & PAYMENT ROUTES ====================

@api_router.post("/checkout", response_model=dict)
async def create_checkout(checkout_data: CheckoutRequest, request: Request, user: Optional[dict] = Depends(get_current_user)):
    # Get cart
    cart = await db.carts.find_one({"session_id": checkout_data.cart_session_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate totals
    items = []
    subtotal = 0.0
    
    for cart_item in cart["items"]:
        product = await db.products.find_one({"id": cart_item["product_id"]}, {"_id": 0})
        if product:
            item_total = product["price"] * cart_item["quantity"]
            subtotal += item_total
            items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": cart_item["quantity"],
                "price": product["price"],
                "image": product["images"][0] if product.get("images") else None
            })
    
    # Apply promo code discount
    promo_discount = 0.0
    applied_promo = None
    if checkout_data.promo_code:
        now = datetime.now(timezone.utc).isoformat()
        promo = await db.promotions.find_one({
            "code": checkout_data.promo_code.upper(),
            "is_active": True,
            "valid_from": {"$lte": now}
        })
        if promo:
            # Check validity
            valid = True
            if promo.get("valid_until") and promo["valid_until"] < now:
                valid = False
            if promo.get("max_uses") and promo["uses_count"] >= promo["max_uses"]:
                valid = False
            if subtotal < promo.get("min_purchase", 0):
                valid = False
            if promo.get("is_first_order_only") and user:
                order_count = await db.orders.count_documents({"user_id": user["id"], "payment_status": "paid"})
                if order_count > 0:
                    valid = False
            
            if valid:
                if promo["discount_type"] == "percentage":
                    promo_discount = subtotal * (promo["discount_value"] / 100)
                elif promo["discount_type"] == "fixed_amount":
                    promo_discount = min(promo["discount_value"], subtotal)
                applied_promo = promo
    
    discounted_subtotal = max(0, subtotal - promo_discount)
    shipping_cost = 0.0 if subtotal >= 50 else 5.99
    tax = round(discounted_subtotal * 0.08, 2)  # 8% tax
    total = round(discounted_subtotal + shipping_cost + tax, 2)
    
    # Create order
    order_id = str(uuid.uuid4())
    order_number = f"CT-{str(uuid.uuid4())[:8].upper()}"
    
    order_doc = {
        "id": order_id,
        "order_number": order_number,
        "user_id": user["id"] if user else None,
        "email": checkout_data.email,
        "items": items,
        "subtotal": subtotal,
        "promo_code": applied_promo["code"] if applied_promo else None,
        "promo_discount": promo_discount,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total,
        "shipping_address": checkout_data.shipping_address.model_dump() if checkout_data.shipping_address else None,
        "status": "pending",
        "payment_status": "pending",
        "payment_method": "stripe",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.insert_one(order_doc)
    
    # Create Stripe checkout session
    host_url = checkout_data.origin_url
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{host_url}/order-confirmation?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/cart"
    
    checkout_request = CheckoutSessionRequest(
        amount=total,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "order_id": order_id,
            "order_number": order_number,
            "email": checkout_data.email
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Update order with stripe session id
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"stripe_session_id": session.session_id}}
    )
    
    # Create payment transaction record
    payment_doc = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "session_id": session.session_id,
        "amount": total,
        "currency": "usd",
        "email": checkout_data.email,
        "user_id": user["id"] if user else None,
        "payment_status": "pending",
        "metadata": {"order_number": order_number},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(payment_doc)
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id,
        "order_id": order_id,
        "order_number": order_number
    }

@api_router.get("/checkout/status/{session_id}", response_model=dict)
async def get_checkout_status(session_id: str, request: Request):
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update order and payment status
    if status.payment_status == "paid":
        await db.orders.update_one(
            {"stripe_session_id": session_id},
            {"$set": {
                "payment_status": "paid",
                "status": "processing",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid"}}
        )
        
        # Clear the cart
        order = await db.orders.find_one({"stripe_session_id": session_id})
        if order:
            await db.carts.delete_many({"user_id": order.get("user_id")})
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            order_id = webhook_response.metadata.get("order_id")
            if order_id:
                await db.orders.update_one(
                    {"id": order_id},
                    {"$set": {
                        "payment_status": "paid",
                        "status": "processing",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Send order confirmation email
                order = await db.orders.find_one({"id": order_id}, {"_id": 0})
                if order:
                    asyncio.create_task(send_order_confirmation_email(order))
                    
                    # Send real-time notification to admin
                    asyncio.create_task(notify_new_order(order))
                    asyncio.create_task(notify_revenue_update(order.get("total", 0), order.get("order_number", "")))
                    
                    # Check for low stock items and notify
                    for item in order.get("items", []):
                        product = await db.products.find_one({"id": item.get("product_id")}, {"_id": 0})
                        if product and product.get("stock_quantity", 100) <= 10:
                            asyncio.create_task(notify_low_stock(product))
                    
                    # Award loyalty points
                    if order.get("user_id"):
                        await award_loyalty_points(order["user_id"], order["total"], order_id)
                        # Complete any pending referral
                        await complete_referral(order["user_id"], order_id)
        
        return {"received": True}
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return {"received": True, "error": str(e)}

# ==================== PAYPAL ROUTES ====================

import paypalrestsdk

# Configure PayPal
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

@api_router.post("/paypal/create-order", response_model=dict)
async def create_paypal_order(order_data: PayPalOrderRequest, user: Optional[dict] = Depends(get_current_user)):
    """Create a PayPal order for checkout"""
    # Get cart
    cart = await db.carts.find_one({"session_id": order_data.cart_session_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate totals
    items = []
    subtotal = 0.0
    
    for cart_item in cart["items"]:
        product = await db.products.find_one({"id": cart_item["product_id"]}, {"_id": 0})
        if product:
            item_total = product["price"] * cart_item["quantity"]
            subtotal += item_total
            items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": cart_item["quantity"],
                "price": product["price"],
                "image": product["images"][0] if product.get("images") else None
            })
    
    # Apply promo code discount
    promo_discount = 0.0
    applied_promo = None
    if order_data.promo_code:
        now = datetime.now(timezone.utc).isoformat()
        promo = await db.promotions.find_one({
            "code": order_data.promo_code.upper(),
            "is_active": True,
            "valid_from": {"$lte": now}
        })
        if promo:
            valid = True
            if promo.get("valid_until") and promo["valid_until"] < now:
                valid = False
            if promo.get("max_uses") and promo["uses_count"] >= promo["max_uses"]:
                valid = False
            if subtotal < promo.get("min_purchase", 0):
                valid = False
            if promo.get("is_first_order_only") and user:
                order_count = await db.orders.count_documents({"user_id": user["id"], "payment_status": "paid"})
                if order_count > 0:
                    valid = False
            
            if valid:
                if promo["discount_type"] == "percentage":
                    promo_discount = subtotal * (promo["discount_value"] / 100)
                elif promo["discount_type"] == "fixed_amount":
                    promo_discount = min(promo["discount_value"], subtotal)
                applied_promo = promo
    
    discounted_subtotal = max(0, subtotal - promo_discount)
    shipping_cost = 0.0 if subtotal >= 50 else 5.99
    tax = round(discounted_subtotal * 0.08, 2)
    total = round(discounted_subtotal + shipping_cost + tax, 2)
    
    # Create internal order
    order_id = str(uuid.uuid4())
    order_number = f"CT-{str(uuid.uuid4())[:8].upper()}"
    
    order_doc = {
        "id": order_id,
        "order_number": order_number,
        "user_id": user["id"] if user else None,
        "email": order_data.email,
        "items": items,
        "subtotal": subtotal,
        "promo_code": applied_promo["code"] if applied_promo else None,
        "promo_discount": promo_discount,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total,
        "status": "pending",
        "payment_status": "pending",
        "payment_method": "paypal",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.orders.insert_one(order_doc)
    
    # Create PayPal payment
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "transactions": [{
            "amount": {
                "total": f"{total:.2f}",
                "currency": "USD",
                "details": {
                    "subtotal": f"{discounted_subtotal:.2f}",
                    "shipping": f"{shipping_cost:.2f}",
                    "tax": f"{tax:.2f}"
                }
            },
            "description": f"Wildly Ones Order {order_number}",
            "custom": order_id,
            "item_list": {
                "items": [
                    {
                        "name": item["product_name"][:127],
                        "price": f"{item['price']:.2f}",
                        "currency": "USD",
                        "quantity": item["quantity"]
                    }
                    for item in items[:10]  # PayPal limits items
                ]
            }
        }],
        "redirect_urls": {
            "return_url": "https://wildlyones.com/paypal/success",
            "cancel_url": "https://wildlyones.com/cart"
        }
    })
    
    if payment.create():
        # Update order with PayPal payment ID
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {"paypal_payment_id": payment.id}}
        )
        
        return {
            "order_id": payment.id,
            "internal_order_id": order_id,
            "order_number": order_number,
            "total": total
        }
    else:
        logging.error(f"PayPal payment creation failed: {payment.error}")
        raise HTTPException(status_code=500, detail="Failed to create PayPal order")

@api_router.post("/paypal/capture-order/{paypal_order_id}", response_model=dict)
async def capture_paypal_order(paypal_order_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Capture/execute a PayPal payment after user approval"""
    # Find our order by PayPal payment ID
    order = await db.orders.find_one({"paypal_payment_id": paypal_order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Execute the payment
    payment = paypalrestsdk.Payment.find(paypal_order_id)
    
    if payment.execute({"payer_id": payment.payer.payer_info.payer_id}):
        # Payment successful - update order
        await db.orders.update_one(
            {"id": order["id"]},
            {"$set": {
                "payment_status": "paid",
                "status": "processing",
                "paypal_payer_id": payment.payer.payer_info.payer_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update promo code usage if applicable
        if order.get("promo_code"):
            await db.promotions.update_one(
                {"code": order["promo_code"]},
                {"$inc": {"uses_count": 1}}
            )
        
        # Award loyalty points if user is logged in
        if order.get("user_id"):
            await award_loyalty_points(order["user_id"], order["total"], order["id"])
            # Complete any pending referral
            await complete_referral(order["user_id"], order["id"])
        
        # Clear the cart
        if order.get("user_id"):
            await db.carts.delete_many({"user_id": order["user_id"]})
        
        # Send order confirmation email
        updated_order = await db.orders.find_one({"id": order["id"]}, {"_id": 0})
        if updated_order:
            asyncio.create_task(send_order_confirmation_email(updated_order))
        
        return {
            "success": True,
            "order_id": order["id"],
            "order_number": order["order_number"],
            "total": order["total"],
            "payment_status": "paid"
        }
    else:
        logging.error(f"PayPal execution failed: {payment.error}")
        raise HTTPException(status_code=400, detail="Payment execution failed")

# ==================== ORDER ROUTES ====================

@api_router.get("/orders", response_model=List[dict])
async def get_user_orders(user: dict = Depends(require_user)):
    orders = await db.orders.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return orders

@api_router.get("/orders/{order_id}", response_model=dict)
async def get_order(order_id: str, user: Optional[dict] = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        # Try by order number
        order = await db.orders.find_one({"order_number": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/orders", response_model=List[dict])
async def get_all_orders(status: Optional[str] = None, user: dict = Depends(require_admin)):
    query_filter = {}
    if status:
        query_filter["status"] = status
    
    orders = await db.orders.find(query_filter, {"_id": 0}).sort("created_at", -1).to_list(100)
    return orders

@api_router.patch("/admin/orders/{order_id}", response_model=dict)
async def update_order_status(order_id: str, status: str, tracking_number: Optional[str] = None, user: dict = Depends(require_admin)):
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if tracking_number:
        update_data["tracking_number"] = tracking_number
    
    result = await db.orders.update_one({"id": order_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order updated"}

@api_router.get("/admin/stats", response_model=dict)
async def get_admin_stats(user: dict = Depends(require_admin)):
    total_orders = await db.orders.count_documents({})
    total_revenue = 0
    paid_orders = await db.orders.find({"payment_status": "paid"}, {"total": 1}).to_list(1000)
    for order in paid_orders:
        total_revenue += order.get("total", 0)
    
    pending_orders = await db.orders.count_documents({"status": "pending"})
    processing_orders = await db.orders.count_documents({"status": "processing"})
    shipped_orders = await db.orders.count_documents({"status": "shipped"})
    
    total_products = await db.products.count_documents({})
    total_customers = await db.users.count_documents({})
    
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "shipped_orders": shipped_orders,
        "total_products": total_products,
        "total_customers": total_customers
    }

@api_router.get("/admin/analytics", response_model=dict)
async def get_analytics(user: dict = Depends(require_admin)):
    """Get comprehensive analytics data for admin dashboard"""
    
    # Get all orders for analysis
    all_orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Calculate total metrics
    total_revenue = sum(o.get("total", 0) for o in all_orders if o.get("payment_status") == "paid")
    total_orders = len(all_orders)
    total_customers = await db.users.count_documents({"is_admin": {"$ne": True}})
    
    # Calculate average order value
    paid_orders = [o for o in all_orders if o.get("payment_status") == "paid"]
    avg_order_value = total_revenue / len(paid_orders) if paid_orders else 0
    
    # Sales by day (last 30 days)
    from collections import defaultdict
    daily_sales = defaultdict(lambda: {"revenue": 0, "orders": 0})
    for order in all_orders:
        if order.get("payment_status") == "paid":
            date_str = order.get("created_at", "")[:10]  # YYYY-MM-DD
            if date_str:
                daily_sales[date_str]["revenue"] += order.get("total", 0)
                daily_sales[date_str]["orders"] += 1
    
    # Convert to sorted list (last 30 days)
    sales_trend = []
    today = datetime.now(timezone.utc)
    for i in range(30):
        date = (today - timedelta(days=29-i)).strftime("%Y-%m-%d")
        day_data = daily_sales.get(date, {"revenue": 0, "orders": 0})
        sales_trend.append({
            "date": date,
            "revenue": round(day_data["revenue"], 2),
            "orders": day_data["orders"]
        })
    
    # Top selling products
    product_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0, "name": "", "image": ""})
    for order in all_orders:
        if order.get("payment_status") == "paid":
            for item in order.get("items", []):
                pid = item.get("product_id", "")
                product_sales[pid]["quantity"] += item.get("quantity", 0)
                product_sales[pid]["revenue"] += item.get("price", 0) * item.get("quantity", 0)
                product_sales[pid]["name"] = item.get("product_name", "Unknown")
                product_sales[pid]["image"] = item.get("image", "")
    
    top_products = sorted(
        [{"id": k, **v} for k, v in product_sales.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:10]
    
    # Sales by category
    category_sales = defaultdict(lambda: {"revenue": 0, "orders": 0})
    products = await db.products.find({}, {"_id": 0, "id": 1, "category": 1}).to_list(500)
    product_categories = {p["id"]: p.get("category", "other") for p in products}
    
    for order in all_orders:
        if order.get("payment_status") == "paid":
            for item in order.get("items", []):
                pid = item.get("product_id", "")
                cat = product_categories.get(pid, "other")
                category_sales[cat]["revenue"] += item.get("price", 0) * item.get("quantity", 0)
                category_sales[cat]["orders"] += 1
    
    category_breakdown = [
        {"category": k, "revenue": round(v["revenue"], 2), "orders": v["orders"]}
        for k, v in category_sales.items()
    ]
    category_breakdown.sort(key=lambda x: x["revenue"], reverse=True)
    
    # Sales by pet type
    pet_type_sales = defaultdict(lambda: {"revenue": 0, "orders": 0})
    product_pet_types = {p["id"]: p.get("pet_type", "other") for p in await db.products.find({}, {"_id": 0, "id": 1, "pet_type": 1}).to_list(500)}
    
    for order in all_orders:
        if order.get("payment_status") == "paid":
            for item in order.get("items", []):
                pid = item.get("product_id", "")
                pt = product_pet_types.get(pid, "other")
                pet_type_sales[pt]["revenue"] += item.get("price", 0) * item.get("quantity", 0)
                pet_type_sales[pt]["orders"] += 1
    
    pet_type_breakdown = [
        {"pet_type": k, "revenue": round(v["revenue"], 2), "orders": v["orders"]}
        for k, v in pet_type_sales.items()
    ]
    pet_type_breakdown.sort(key=lambda x: x["revenue"], reverse=True)
    
    # Order status distribution
    status_counts = defaultdict(int)
    for order in all_orders:
        status_counts[order.get("status", "unknown")] += 1
    
    order_status_breakdown = [
        {"status": k, "count": v}
        for k, v in status_counts.items()
    ]
    
    # Recent customers (last 10 signups)
    recent_customers = await db.users.find(
        {"is_admin": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Customer acquisition (signups per day, last 30 days)
    customer_signups = defaultdict(int)
    all_users = await db.users.find({"is_admin": {"$ne": True}}, {"_id": 0, "created_at": 1}).to_list(1000)
    for user in all_users:
        date_str = user.get("created_at", "")[:10]
        if date_str:
            customer_signups[date_str] += 1
    
    acquisition_trend = []
    for i in range(30):
        date = (today - timedelta(days=29-i)).strftime("%Y-%m-%d")
        acquisition_trend.append({
            "date": date,
            "signups": customer_signups.get(date, 0)
        })
    
    return {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "avg_order_value": round(avg_order_value, 2)
        },
        "sales_trend": sales_trend,
        "top_products": top_products,
        "category_breakdown": category_breakdown,
        "pet_type_breakdown": pet_type_breakdown,
        "order_status_breakdown": order_status_breakdown,
        "recent_customers": recent_customers,
        "acquisition_trend": acquisition_trend
    }

@api_router.get("/admin/products", response_model=List[dict])
async def get_all_products_admin(
    search: Optional[str] = None,
    pet_type: Optional[str] = None,
    category: Optional[str] = None,
    user: dict = Depends(require_admin)
):
    """Get all products for admin (including out of stock)"""
    query_filter = {}
    
    if search:
        query_filter["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"slug": {"$regex": search, "$options": "i"}}
        ]
    if pet_type:
        query_filter["pet_type"] = pet_type
    if category:
        query_filter["category"] = category
    
    products = await db.products.find(query_filter, {"_id": 0}).sort("created_at", -1).to_list(500)
    return products

@api_router.get("/admin/products/{product_id}", response_model=dict)
async def get_product_admin(product_id: str, user: dict = Depends(require_admin)):
    """Get single product by ID for admin"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/admin/products", response_model=dict)
async def create_product(product: Product, user: dict = Depends(require_admin)):
    product_dict = product.model_dump()
    await db.products.insert_one(product_dict)
    # Exclude MongoDB _id from response
    product_dict.pop("_id", None)
    return {"message": "Product created", "id": product_dict["id"], "product": product_dict}

@api_router.put("/admin/products/{product_id}", response_model=dict)
async def update_product(product_id: str, product: Product, user: dict = Depends(require_admin)):
    product_dict = product.model_dump()
    # Preserve the original product ID - don't let the model generate a new one
    product_dict["id"] = product_id
    product_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.products.update_one({"id": product_id}, {"$set": product_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    # Exclude MongoDB _id from response
    product_dict.pop("_id", None)
    return {"message": "Product updated", "product": product_dict}

@api_router.delete("/admin/products/{product_id}", response_model=dict)
async def delete_product(product_id: str, user: dict = Depends(require_admin)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

# ==================== PROMOTIONS & LOYALTY ROUTES ====================

LOYALTY_TIERS = {
    "bronze": {"min_points": 0, "discount_percent": 0, "points_multiplier": 1.0},
    "silver": {"min_points": 500, "discount_percent": 5, "points_multiplier": 1.25},
    "gold": {"min_points": 1500, "discount_percent": 10, "points_multiplier": 1.5},
    "platinum": {"min_points": 3000, "discount_percent": 15, "points_multiplier": 2.0}
}

def calculate_tier(lifetime_points: int) -> str:
    """Calculate user's loyalty tier based on lifetime points"""
    if lifetime_points >= 3000:
        return "platinum"
    elif lifetime_points >= 1500:
        return "gold"
    elif lifetime_points >= 500:
        return "silver"
    return "bronze"

@api_router.get("/promotions", response_model=List[dict])
async def get_active_promotions():
    """Get all active promotions"""
    now = datetime.now(timezone.utc).isoformat()
    promotions = await db.promotions.find({
        "is_active": True,
        "valid_from": {"$lte": now},
        "$or": [
            {"valid_until": None},
            {"valid_until": {"$gte": now}}
        ],
        "is_loyalty_reward": False
    }, {"_id": 0}).to_list(100)
    return promotions

@api_router.get("/promotions/validate/{code}", response_model=dict)
async def validate_promotion(code: str, subtotal: float = 0, user: Optional[dict] = Depends(get_current_user)):
    """Validate a promotion code and return discount details"""
    now = datetime.now(timezone.utc).isoformat()
    promotion = await db.promotions.find_one({
        "code": code.upper(),
        "is_active": True,
        "valid_from": {"$lte": now},
        "$or": [
            {"valid_until": None},
            {"valid_until": {"$gte": now}}
        ]
    }, {"_id": 0})
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Invalid or expired promotion code")
    
    # Check max uses
    if promotion.get("max_uses") and promotion["uses_count"] >= promotion["max_uses"]:
        raise HTTPException(status_code=400, detail="Promotion code has reached maximum uses")
    
    # Check minimum purchase
    if subtotal < promotion.get("min_purchase", 0):
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum purchase of ${promotion['min_purchase']:.2f} required"
        )
    
    # Check first order only
    if promotion.get("is_first_order_only"):
        if user:
            order_count = await db.orders.count_documents({"user_id": user["id"], "payment_status": "paid"})
            if order_count > 0:
                raise HTTPException(status_code=400, detail="This promotion is for first orders only")
    
    # Calculate discount
    discount_amount = 0
    if promotion["discount_type"] == "percentage":
        discount_amount = subtotal * (promotion["discount_value"] / 100)
    elif promotion["discount_type"] == "fixed_amount":
        discount_amount = min(promotion["discount_value"], subtotal)
    
    return {
        "valid": True,
        "promotion": promotion,
        "discount_amount": round(discount_amount, 2)
    }

@api_router.get("/loyalty/status", response_model=dict)
async def get_loyalty_status(user: dict = Depends(require_user)):
    """Get user's loyalty program status"""
    loyalty = await db.loyalty_points.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not loyalty:
        # Create new loyalty account
        loyalty = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "points": 0,
            "lifetime_points": 0,
            "tier": "bronze",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.loyalty_points.insert_one(loyalty)
        loyalty.pop("_id", None)
    
    tier_info = LOYALTY_TIERS[loyalty["tier"]]
    next_tier = None
    points_to_next = None
    
    if loyalty["tier"] == "bronze":
        next_tier = "silver"
        points_to_next = 500 - loyalty["lifetime_points"]
    elif loyalty["tier"] == "silver":
        next_tier = "gold"
        points_to_next = 1500 - loyalty["lifetime_points"]
    elif loyalty["tier"] == "gold":
        next_tier = "platinum"
        points_to_next = 3000 - loyalty["lifetime_points"]
    
    # Get recent transactions
    transactions = await db.points_transactions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "points": loyalty["points"],
        "lifetime_points": loyalty["lifetime_points"],
        "tier": loyalty["tier"],
        "tier_benefits": tier_info,
        "next_tier": next_tier,
        "points_to_next_tier": max(0, points_to_next) if points_to_next else None,
        "recent_transactions": transactions
    }

@api_router.post("/loyalty/redeem", response_model=dict)
async def redeem_points(points_to_redeem: int, user: dict = Depends(require_user)):
    """Redeem loyalty points for a discount code"""
    if points_to_redeem < 100:
        raise HTTPException(status_code=400, detail="Minimum 100 points required to redeem")
    
    loyalty = await db.loyalty_points.find_one({"user_id": user["id"]})
    if not loyalty:
        raise HTTPException(status_code=404, detail="Loyalty account not found")
    
    if loyalty["points"] < points_to_redeem:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    # Calculate discount value (100 points = $5)
    discount_value = (points_to_redeem // 100) * 5
    actual_points = (points_to_redeem // 100) * 100
    
    # Create promotion code
    promo_code = f"LOYAL{str(uuid.uuid4())[:6].upper()}"
    promotion = {
        "id": str(uuid.uuid4()),
        "code": promo_code,
        "name": f"Loyalty Reward - ${discount_value} Off",
        "description": f"Redeemed {actual_points} loyalty points",
        "discount_type": "fixed_amount",
        "discount_value": discount_value,
        "min_purchase": 0,
        "max_uses": 1,
        "uses_count": 0,
        "is_active": True,
        "is_first_order_only": False,
        "is_loyalty_reward": True,
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promotions.insert_one(promotion)
    
    # Deduct points
    new_points = loyalty["points"] - actual_points
    await db.loyalty_points.update_one(
        {"user_id": user["id"]},
        {"$set": {"points": new_points, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "points": -actual_points,
        "transaction_type": "redeemed",
        "description": f"Redeemed for ${discount_value} discount code",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.points_transactions.insert_one(transaction)
    
    return {
        "message": f"Successfully redeemed {actual_points} points",
        "discount_code": promo_code,
        "discount_value": discount_value,
        "remaining_points": new_points
    }

async def award_loyalty_points(user_id: str, order_total: float, order_id: str):
    """Award loyalty points after a successful order"""
    # Get or create loyalty account
    loyalty = await db.loyalty_points.find_one({"user_id": user_id})
    if not loyalty:
        loyalty = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "points": 0,
            "lifetime_points": 0,
            "tier": "bronze",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.loyalty_points.insert_one(loyalty)
    
    tier_info = LOYALTY_TIERS[loyalty.get("tier", "bronze")]
    
    # Calculate points (1 point per dollar spent, with tier multiplier)
    base_points = int(order_total)
    earned_points = int(base_points * tier_info["points_multiplier"])
    
    # Update points
    new_points = loyalty["points"] + earned_points
    new_lifetime = loyalty["lifetime_points"] + earned_points
    new_tier = calculate_tier(new_lifetime)
    
    await db.loyalty_points.update_one(
        {"user_id": user_id},
        {"$set": {
            "points": new_points,
            "lifetime_points": new_lifetime,
            "tier": new_tier,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "points": earned_points,
        "transaction_type": "earned",
        "description": f"Earned from order (${order_total:.2f})",
        "order_id": order_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.points_transactions.insert_one(transaction)
    
    return earned_points, new_tier

@api_router.post("/admin/promotions", response_model=dict)
async def create_promotion(
    code: str,
    name: str,
    description: str,
    discount_type: str,
    discount_value: float,
    min_purchase: float = 0,
    max_uses: Optional[int] = None,
    is_first_order_only: bool = False,
    valid_days: int = 30,
    user: dict = Depends(require_admin)
):
    """Create a new promotion code"""
    existing = await db.promotions.find_one({"code": code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Promotion code already exists")
    
    promotion = {
        "id": str(uuid.uuid4()),
        "code": code.upper(),
        "name": name,
        "description": description,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "min_purchase": min_purchase,
        "max_uses": max_uses,
        "uses_count": 0,
        "is_active": True,
        "is_first_order_only": is_first_order_only,
        "is_loyalty_reward": False,
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=valid_days)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promotions.insert_one(promotion)
    
    return {"message": "Promotion created", "promotion": {k: v for k, v in promotion.items() if k != "_id"}}

@api_router.get("/admin/promotions", response_model=List[dict])
async def get_all_promotions(user: dict = Depends(require_admin)):
    """Get all promotions (admin only)"""
    promotions = await db.promotions.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return promotions

# ==================== EMAIL ROUTES ====================

async def send_order_confirmation_email(order: dict):
    """Send order confirmation email to customer"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured - skipping email")
        return None
    
    # Generate order items HTML
    items_html = ""
    for item in order.get("items", []):
        items_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #E8DFD5;">
                <img src="{item.get('image', '')}" alt="{item.get('product_name', '')}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;">
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #E8DFD5;">
                <strong>{item.get('product_name', '')}</strong><br>
                <span style="color: #5C6D5E;">Qty: {item.get('quantity', 1)}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #E8DFD5; text-align: right;">
                ${item.get('price', 0) * item.get('quantity', 1):.2f}
            </td>
        </tr>
        """
    
    promo_html = ""
    if order.get("promo_discount", 0) > 0:
        promo_html = f"""
        <tr>
            <td colspan="2" style="padding: 8px 0; text-align: right; color: #6B8F71;">Promo Discount ({order.get('promo_code', '')})</td>
            <td style="padding: 8px 0; text-align: right; color: #6B8F71;">-${order.get('promo_discount', 0):.2f}</td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <!-- Header -->
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                </td>
            </tr>
            
            <!-- Order Confirmation -->
            <tr>
                <td style="padding: 32px 24px;">
                    <h2 style="color: #2D4A3E; margin: 0 0 8px 0;">Thank you for your order!</h2>
                    <p style="color: #5C6D5E; margin: 0 0 24px 0;">
                        Your order <strong style="color: #2D4A3E;">{order.get('order_number', '')}</strong> has been confirmed.
                    </p>
                    
                    <!-- Order Items -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                        <tr>
                            <td colspan="3" style="padding-bottom: 12px; border-bottom: 2px solid #2D4A3E;">
                                <strong style="color: #2D4A3E;">Order Summary</strong>
                            </td>
                        </tr>
                        {items_html}
                    </table>
                    
                    <!-- Totals -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                        <tr>
                            <td colspan="2" style="padding: 8px 0; text-align: right;">Subtotal</td>
                            <td style="padding: 8px 0; text-align: right;">${order.get('subtotal', 0):.2f}</td>
                        </tr>
                        {promo_html}
                        <tr>
                            <td colspan="2" style="padding: 8px 0; text-align: right;">Shipping</td>
                            <td style="padding: 8px 0; text-align: right;">{f"${order.get('shipping_cost', 0):.2f}" if order.get('shipping_cost', 0) > 0 else "Free"}</td>
                        </tr>
                        <tr>
                            <td colspan="2" style="padding: 8px 0; text-align: right;">Tax</td>
                            <td style="padding: 8px 0; text-align: right;">${order.get('tax', 0):.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="2" style="padding: 12px 0; text-align: right; border-top: 2px solid #2D4A3E;">
                                <strong style="color: #2D4A3E; font-size: 18px;">Total</strong>
                            </td>
                            <td style="padding: 12px 0; text-align: right; border-top: 2px solid #2D4A3E;">
                                <strong style="color: #2D4A3E; font-size: 18px;">${order.get('total', 0):.2f}</strong>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- CTA -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center; padding: 24px 0;">
                                <a href="https://wildlyones.com/account" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    View Order Details
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            
            <!-- Loyalty Points -->
            <tr>
                <td style="background-color: #E8DFD5; padding: 24px; text-align: center;">
                    <p style="color: #2D4A3E; margin: 0;">
                        🎉 You earned <strong>{int(order.get('total', 0))} loyalty points</strong> with this order!
                    </p>
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <p style="color: #FFFFFF; margin: 0 0 8px 0; font-size: 14px;">
                        Questions? Contact us at support@wildlyones.com
                    </p>
                    <p style="color: #D4A574; margin: 0; font-size: 12px;">
                        © 2026 Wildly Ones Pet Wellness. All rights reserved.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [order.get("email")],
            "subject": f"Order Confirmed - {order.get('order_number', '')} 🐾",
            "html": html_content
        }
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Order confirmation email sent to {order.get('email')}")
        return email_result
    except Exception as e:
        logging.error(f"Failed to send order confirmation email: {str(e)}")
        return None

# ==================== REVIEW ROUTES ====================

@api_router.get("/products/{product_slug}/reviews", response_model=List[dict])
async def get_product_reviews(product_slug: str, limit: int = 20, skip: int = 0):
    """Get reviews for a product"""
    product = await db.products.find_one({"slug": product_slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = await db.reviews.find(
        {"product_id": product["id"]},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return reviews

@api_router.get("/products/{product_slug}/reviews/summary", response_model=dict)
async def get_product_reviews_summary(product_slug: str):
    """Get review summary stats for a product"""
    product = await db.products.find_one({"slug": product_slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = await db.reviews.find(
        {"product_id": product["id"]},
        {"_id": 0, "rating": 1}
    ).to_list(1000)
    
    total_reviews = len(reviews)
    if total_reviews == 0:
        return {
            "average_rating": 0,
            "total_reviews": 0,
            "rating_breakdown": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }
    
    ratings = [r["rating"] for r in reviews]
    average = sum(ratings) / total_reviews
    
    breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for rating in ratings:
        breakdown[rating] = breakdown.get(rating, 0) + 1
    
    return {
        "average_rating": round(average, 1),
        "total_reviews": total_reviews,
        "rating_breakdown": breakdown
    }

@api_router.post("/products/{product_slug}/reviews", response_model=dict)
async def create_review(product_slug: str, review_data: ReviewCreate, user: dict = Depends(require_user)):
    """Create a review for a product"""
    product = await db.products.find_one({"slug": product_slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user already reviewed this product
    existing = await db.reviews.find_one({
        "product_id": product["id"],
        "user_id": user["id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")
    
    # Validate rating
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if user has purchased this product (verified purchase)
    orders = await db.orders.find({
        "user_id": user["id"],
        "payment_status": "paid"
    }).to_list(100)
    
    verified_purchase = False
    for order in orders:
        for item in order.get("items", []):
            if item.get("product_id") == product["id"]:
                verified_purchase = True
                break
        if verified_purchase:
            break
    
    review = {
        "id": str(uuid.uuid4()),
        "product_id": product["id"],
        "user_id": user["id"],
        "user_name": user.get("name", user.get("email", "").split("@")[0]),
        "rating": review_data.rating,
        "title": review_data.title,
        "content": review_data.content,
        "verified_purchase": verified_purchase,
        "helpful_count": 0,
        "images": review_data.images,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reviews.insert_one(review)
    
    # Update product rating
    all_reviews = await db.reviews.find({"product_id": product["id"]}, {"rating": 1}).to_list(1000)
    new_avg = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    await db.products.update_one(
        {"id": product["id"]},
        {"$set": {"rating": round(new_avg, 1), "review_count": len(all_reviews)}}
    )
    
    # Award bonus points for review
    if user.get("id"):
        bonus_points = 25 if verified_purchase else 10
        loyalty = await db.loyalty_points.find_one({"user_id": user["id"]})
        if loyalty:
            await db.loyalty_points.update_one(
                {"user_id": user["id"]},
                {"$inc": {"points": bonus_points, "lifetime_points": bonus_points}}
            )
            transaction = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "points": bonus_points,
                "transaction_type": "bonus",
                "description": f"Bonus for writing a {'verified ' if verified_purchase else ''}review",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(transaction)
    
    review.pop("_id", None)
    return {"message": "Review submitted successfully", "review": review, "bonus_points": bonus_points if user.get("id") else 0}

@api_router.post("/reviews/{review_id}/helpful", response_model=dict)
async def mark_review_helpful(review_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Mark a review as helpful"""
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    await db.reviews.update_one(
        {"id": review_id},
        {"$inc": {"helpful_count": 1}}
    )
    
    return {"message": "Marked as helpful", "helpful_count": review.get("helpful_count", 0) + 1}

# ==================== REFERRAL ROUTES ====================

@api_router.get("/referral/code", response_model=dict)
async def get_referral_code(user: dict = Depends(require_user)):
    """Get or create user's referral code"""
    # Check if user already has a referral code
    existing = await db.referrals.find_one({"referrer_id": user["id"], "referee_id": None}, {"_id": 0})
    
    if existing:
        referral_code = existing["referrer_code"]
    else:
        # Generate new referral code
        user_name = user.get("name", user.get("email", "").split("@")[0])
        referral_code = generate_referral_code(user_name)
        
        # Make sure code is unique
        while await db.referrals.find_one({"referrer_code": referral_code}):
            referral_code = generate_referral_code(user_name)
        
        # Create referral entry
        referral = {
            "id": str(uuid.uuid4()),
            "referrer_id": user["id"],
            "referrer_code": referral_code,
            "referee_id": None,
            "referee_email": None,
            "status": "pending",
            "referrer_reward": 10.0,
            "referee_reward": 10.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.referrals.insert_one(referral)
    
    # Get referral stats
    completed_referrals = await db.referrals.count_documents({
        "referrer_id": user["id"],
        "status": "completed"
    })
    total_earned = completed_referrals * 10.0
    
    return {
        "referral_code": referral_code,
        "share_url": f"https://wildlyones.com/ref/{referral_code}",
        "reward_amount": 10.0,
        "completed_referrals": completed_referrals,
        "total_earned": total_earned
    }

@api_router.get("/referral/validate/{code}", response_model=dict)
async def validate_referral_code(code: str, user: Optional[dict] = Depends(get_current_user)):
    """Validate a referral code and check if it can be used"""
    referral = await db.referrals.find_one({"referrer_code": code.upper()}, {"_id": 0})
    
    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Check if user is trying to use their own code
    if user and referral["referrer_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot use your own referral code")
    
    # Check if user has already used a referral code
    if user:
        existing_use = await db.referrals.find_one({
            "referee_id": user["id"],
            "status": "completed"
        })
        if existing_use:
            raise HTTPException(status_code=400, detail="You have already used a referral code")
    
    # Get referrer info
    referrer = await db.users.find_one({"id": referral["referrer_id"]}, {"_id": 0, "name": 1, "email": 1})
    referrer_name = referrer.get("name", referrer.get("email", "").split("@")[0]) if referrer else "A friend"
    
    return {
        "valid": True,
        "code": code.upper(),
        "referrer_name": referrer_name,
        "reward_amount": referral["referee_reward"],
        "message": f"{referrer_name} wants to give you ${referral['referee_reward']:.0f} off your first order!"
    }

@api_router.post("/referral/apply/{code}", response_model=dict)
async def apply_referral_code(code: str, user: dict = Depends(require_user)):
    """Apply a referral code and create discount for user"""
    referral = await db.referrals.find_one({"referrer_code": code.upper()})
    
    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referral["referrer_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot use your own referral code")
    
    # Check if user already has a pending referral
    existing = await db.referrals.find_one({
        "referee_id": user["id"],
        "status": {"$in": ["pending", "completed"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have already used a referral code")
    
    # Create a promo code for the referee
    promo_code = f"REF{str(uuid.uuid4())[:6].upper()}"
    promotion = {
        "id": str(uuid.uuid4()),
        "code": promo_code,
        "name": f"Referral Reward - ${referral['referee_reward']:.0f} Off",
        "description": "Referral discount for new customer",
        "discount_type": "fixed_amount",
        "discount_value": referral["referee_reward"],
        "min_purchase": 0,
        "max_uses": 1,
        "uses_count": 0,
        "is_active": True,
        "is_first_order_only": True,
        "is_loyalty_reward": False,
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promotions.insert_one(promotion)
    
    # Update the referral with referee info
    await db.referrals.update_one(
        {"id": referral["id"]},
        {"$set": {
            "referee_id": user["id"],
            "referee_email": user.get("email"),
            "status": "pending"
        }}
    )
    
    return {
        "message": f"You got ${referral['referee_reward']:.0f} off! Use code {promo_code} at checkout.",
        "promo_code": promo_code,
        "discount_amount": referral["referee_reward"]
    }

async def complete_referral(user_id: str, order_id: str):
    """Complete a referral after successful first order"""
    # Find pending referral for this user
    referral = await db.referrals.find_one({
        "referee_id": user_id,
        "status": "pending"
    })
    
    if not referral:
        return
    
    # Mark referral as completed
    await db.referrals.update_one(
        {"id": referral["id"]},
        {"$set": {
            "status": "completed",
            "order_id": order_id,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create promo code reward for referrer
    promo_code = f"THANKYOU{str(uuid.uuid4())[:4].upper()}"
    promotion = {
        "id": str(uuid.uuid4()),
        "code": promo_code,
        "name": f"Referral Reward - ${referral['referrer_reward']:.0f} Off",
        "description": "Thank you for referring a friend!",
        "discount_type": "fixed_amount",
        "discount_value": referral["referrer_reward"],
        "min_purchase": 0,
        "max_uses": 1,
        "uses_count": 0,
        "is_active": True,
        "is_first_order_only": False,
        "is_loyalty_reward": False,
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promotions.insert_one(promotion)
    
    # Award bonus loyalty points to referrer
    referrer_loyalty = await db.loyalty_points.find_one({"user_id": referral["referrer_id"]})
    if referrer_loyalty:
        bonus_points = 100  # Bonus points for successful referral
        await db.loyalty_points.update_one(
            {"user_id": referral["referrer_id"]},
            {"$inc": {"points": bonus_points, "lifetime_points": bonus_points}}
        )
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": referral["referrer_id"],
            "points": bonus_points,
            "transaction_type": "bonus",
            "description": "Referral bonus - friend completed their first order!",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.points_transactions.insert_one(transaction)
    
    logging.info(f"Referral completed: {referral['id']}, referrer gets code {promo_code}")

@api_router.get("/referral/stats", response_model=dict)
async def get_referral_stats(user: dict = Depends(require_user)):
    """Get user's referral statistics"""
    referrals = await db.referrals.find({
        "referrer_id": user["id"]
    }, {"_id": 0}).to_list(100)
    
    completed = [r for r in referrals if r.get("status") == "completed"]
    pending = [r for r in referrals if r.get("status") == "pending" and r.get("referee_id")]
    
    return {
        "total_referrals": len(completed),
        "pending_referrals": len(pending),
        "total_earned": len(completed) * 10.0,
        "referrals": [
            {
                "referee_email": r.get("referee_email", "")[:3] + "***",
                "status": r.get("status"),
                "completed_at": r.get("completed_at"),
                "reward": r.get("referrer_reward", 10.0)
            }
            for r in referrals if r.get("referee_id")
        ]
    }

# ==================== ORDER TRACKING ROUTES ====================

CARRIER_NAMES = {
    "ups": "UPS",
    "fedex": "FedEx",
    "usps": "USPS",
    "dhl": "DHL",
    "amazon": "Amazon Logistics",
    "ontrac": "OnTrac",
    "lasership": "LaserShip"
}

@api_router.get("/orders/{order_id}/tracking", response_model=dict)
async def get_order_tracking(order_id: str, user: dict = Depends(require_user)):
    """Get tracking info for an order"""
    order = await db.orders.find_one({
        "id": order_id,
        "$or": [{"user_id": user["id"]}, {"email": user.get("email")}]
    }, {"_id": 0})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    tracking = order.get("tracking")
    if not tracking:
        return {
            "has_tracking": False,
            "message": "Tracking information not yet available. You'll receive an email when your order ships."
        }
    
    return {
        "has_tracking": True,
        "carrier": CARRIER_NAMES.get(tracking.get("carrier", "").lower(), tracking.get("carrier", "")),
        "tracking_number": tracking.get("tracking_number"),
        "status": tracking.get("status"),
        "status_description": tracking.get("status_description"),
        "estimated_delivery": tracking.get("estimated_delivery"),
        "last_location": tracking.get("last_location"),
        "events": tracking.get("events", []),
        "last_updated": tracking.get("last_updated"),
        "tracking_url": get_carrier_tracking_url(tracking.get("carrier"), tracking.get("tracking_number"))
    }

def get_carrier_tracking_url(carrier: str, tracking_number: str) -> str:
    """Generate tracking URL for various carriers"""
    carrier = carrier.lower() if carrier else ""
    urls = {
        "ups": f"https://www.ups.com/track?tracknum={tracking_number}",
        "fedex": f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        "usps": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        "dhl": f"https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
        "amazon": f"https://track.amazon.com/tracking/{tracking_number}"
    }
    return urls.get(carrier, f"https://www.17track.net/en/track?nums={tracking_number}")

@api_router.post("/admin/orders/{order_id}/tracking", response_model=dict)
async def add_order_tracking(
    order_id: str,
    carrier: str,
    tracking_number: str,
    user: dict = Depends(require_admin)
):
    """Add tracking information to an order (admin only)"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    tracking = {
        "carrier": carrier.lower(),
        "tracking_number": tracking_number,
        "status": "in_transit",
        "status_description": "Package is on its way",
        "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "last_location": None,
        "events": [
            {
                "status": "shipped",
                "description": f"Shipped via {CARRIER_NAMES.get(carrier.lower(), carrier)}",
                "location": "Warehouse",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "tracking": tracking,
            "status": "shipped",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send shipping notification email
    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if updated_order and updated_order.get("email"):
        asyncio.create_task(send_shipping_notification_email(updated_order, tracking))
    
    return {
        "message": "Tracking added successfully",
        "tracking": tracking,
        "tracking_url": get_carrier_tracking_url(carrier, tracking_number)
    }

@api_router.put("/admin/orders/{order_id}/tracking", response_model=dict)
async def update_order_tracking(
    order_id: str,
    status: str,
    status_description: str,
    location: Optional[str] = None,
    user: dict = Depends(require_admin)
):
    """Update tracking status for an order (admin only)"""
    order = await db.orders.find_one({"id": order_id})
    if not order or not order.get("tracking"):
        raise HTTPException(status_code=404, detail="Order or tracking not found")
    
    tracking = order["tracking"]
    
    # Add new event
    event = {
        "status": status,
        "description": status_description,
        "location": location,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    tracking["events"].append(event)
    tracking["status"] = status
    tracking["status_description"] = status_description
    if location:
        tracking["last_location"] = location
    tracking["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # Update order status if delivered
    order_status = "shipped"
    if status == "delivered":
        order_status = "delivered"
    elif status == "out_for_delivery":
        order_status = "shipped"
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "tracking": tracking,
            "status": order_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Tracking updated", "tracking": tracking}

async def send_shipping_notification_email(order: dict, tracking: dict):
    """Send shipping notification email to customer"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured - skipping shipping email")
        return None
    
    carrier_name = CARRIER_NAMES.get(tracking.get("carrier", "").lower(), tracking.get("carrier", ""))
    tracking_url = get_carrier_tracking_url(tracking.get("carrier"), tracking.get("tracking_number"))
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 24px;">
                    <h2 style="color: #2D4A3E; margin: 0 0 8px 0;">Your order is on its way! 📦</h2>
                    <p style="color: #5C6D5E; margin: 0 0 24px 0;">
                        Great news! Your order <strong>{order.get('order_number', '')}</strong> has shipped.
                    </p>
                    
                    <div style="background-color: #E8DFD5; padding: 20px; border-radius: 12px; margin-bottom: 24px;">
                        <p style="margin: 0 0 8px 0; color: #2D4A3E;"><strong>Carrier:</strong> {carrier_name}</p>
                        <p style="margin: 0 0 8px 0; color: #2D4A3E;"><strong>Tracking Number:</strong> {tracking.get('tracking_number', '')}</p>
                        <p style="margin: 0; color: #5C6D5E;">Estimated delivery: 3-5 business days</p>
                    </div>
                    
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center;">
                                <a href="{tracking_url}" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    Track Your Package
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <p style="color: #D4A574; margin: 0; font-size: 12px;">© 2026 Wildly Ones Pet Wellness</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [order.get("email")],
            "subject": f"Your Wildly Ones order is on its way! 📦",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Shipping notification email sent to {order.get('email')}")
    except Exception as e:
        logging.error(f"Failed to send shipping email: {str(e)}")

# ==================== SUBSCRIPTION SYSTEM ====================

SUBSCRIPTION_DISCOUNT = 10  # 10% discount for subscription orders

@api_router.post("/subscriptions", response_model=dict)
async def create_subscription(sub_data: SubscriptionCreate, user: dict = Depends(require_user)):
    """Create a new monthly subscription for products"""
    # Validate products exist
    product_ids = [item.get("product_id") for item in sub_data.items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(None)
    
    if len(products) != len(product_ids):
        raise HTTPException(status_code=400, detail="One or more products not found")
    
    # Calculate next delivery date based on frequency
    freq_days = {"monthly": 30, "bi-monthly": 60, "quarterly": 90}
    next_delivery = datetime.now(timezone.utc) + timedelta(days=freq_days.get(sub_data.frequency, 30))
    
    # Build subscription items with product details
    subscription_items = []
    for item in sub_data.items:
        product = next((p for p in products if p["id"] == item.get("product_id")), None)
        if product:
            subscription_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "product_image": product.get("images", ["/placeholder.jpg"])[0],
                "quantity": item.get("quantity", 1),
                "price": product["price"],
                "discounted_price": round(product["price"] * (1 - SUBSCRIPTION_DISCOUNT / 100), 2)
            })
    
    subscription = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "email": sub_data.email or user.get("email"),
        "items": subscription_items,
        "frequency": sub_data.frequency,
        "discount_percent": SUBSCRIPTION_DISCOUNT,
        "status": "active",
        "next_delivery_date": next_delivery.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_order_id": None
    }
    
    await db.subscriptions.insert_one(subscription)
    subscription.pop("_id", None)
    
    return {
        "message": f"Subscription created! You'll save {SUBSCRIPTION_DISCOUNT}% on every delivery.",
        "subscription": subscription
    }

@api_router.get("/subscriptions", response_model=List[dict])
async def get_user_subscriptions(user: dict = Depends(require_user)):
    """Get all subscriptions for the current user"""
    subscriptions = await db.subscriptions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(None)
    return subscriptions

@api_router.get("/subscriptions/{subscription_id}", response_model=dict)
async def get_subscription(subscription_id: str, user: dict = Depends(require_user)):
    """Get a specific subscription"""
    subscription = await db.subscriptions.find_one(
        {"id": subscription_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@api_router.put("/subscriptions/{subscription_id}/pause", response_model=dict)
async def pause_subscription(subscription_id: str, user: dict = Depends(require_user)):
    """Pause a subscription"""
    result = await db.subscriptions.update_one(
        {"id": subscription_id, "user_id": user["id"]},
        {"$set": {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Subscription paused"}

@api_router.put("/subscriptions/{subscription_id}/resume", response_model=dict)
async def resume_subscription(subscription_id: str, user: dict = Depends(require_user)):
    """Resume a paused subscription"""
    freq_days = {"monthly": 30, "bi-monthly": 60, "quarterly": 90}
    subscription = await db.subscriptions.find_one({"id": subscription_id, "user_id": user["id"]})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    next_delivery = datetime.now(timezone.utc) + timedelta(days=freq_days.get(subscription.get("frequency", "monthly"), 30))
    
    await db.subscriptions.update_one(
        {"id": subscription_id},
        {"$set": {
            "status": "active",
            "next_delivery_date": next_delivery.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Subscription resumed", "next_delivery_date": next_delivery.isoformat()}

@api_router.delete("/subscriptions/{subscription_id}", response_model=dict)
async def cancel_subscription(subscription_id: str, user: dict = Depends(require_user)):
    """Cancel a subscription"""
    result = await db.subscriptions.update_one(
        {"id": subscription_id, "user_id": user["id"]},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Subscription cancelled"}

@api_router.post("/checkout/subscription", response_model=dict)
async def create_subscription_checkout(checkout_data: CheckoutRequest, request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Create checkout with subscription discount applied"""
    cart = await db.carts.find_one({"session_id": checkout_data.cart_session_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate totals with subscription discount
    items = cart.get("items", [])
    original_subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
    subscription_discount = original_subtotal * (SUBSCRIPTION_DISCOUNT / 100)
    discounted_subtotal = original_subtotal - subscription_discount
    
    # Create order with subscription flag
    order_id = str(uuid.uuid4())
    order_number = f"SUB-{str(uuid.uuid4())[:8].upper()}"
    
    order_doc = {
        "id": order_id,
        "order_number": order_number,
        "user_id": user["id"] if user else None,
        "email": checkout_data.email,
        "items": items,
        "original_subtotal": original_subtotal,
        "subscription_discount": subscription_discount,
        "subtotal": discounted_subtotal,
        "shipping_address": checkout_data.shipping_address.model_dump() if checkout_data.shipping_address else None,
        "status": "pending",
        "payment_status": "pending",
        "is_subscription": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.insert_one(order_doc)
    
    # Create Stripe checkout session
    host_url = checkout_data.origin_url
    webhook_url = f"{host_url}/api/stripe/webhook"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{host_url}/order-confirmation?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/cart"
    
    checkout_request = CheckoutSessionRequest(
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"name": f"Subscription Order (Save {SUBSCRIPTION_DISCOUNT}%)", "quantity": 1, "unit_amount": int(discounted_subtotal * 100)}],
        metadata={
            "order_id": order_id,
            "order_number": order_number,
            "email": checkout_data.email,
            "is_subscription": "true"
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"stripe_session_id": session.session_id}}
    )
    
    # Create subscription record if user is logged in
    if user:
        subscription_items = [{
            "product_id": item.get("product_id"),
            "product_name": item.get("name"),
            "product_image": item.get("image"),
            "quantity": item.get("quantity", 1),
            "price": item.get("price"),
            "discounted_price": round(item.get("price", 0) * (1 - SUBSCRIPTION_DISCOUNT / 100), 2)
        } for item in items]
        
        subscription = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "email": checkout_data.email,
            "items": subscription_items,
            "frequency": "monthly",
            "discount_percent": SUBSCRIPTION_DISCOUNT,
            "status": "pending",  # Will be activated after payment
            "next_delivery_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_order_id": order_id
        }
        await db.subscriptions.insert_one(subscription)
    
    return {
        "checkout_url": session.url,
        "order_id": order_id,
        "order_number": order_number,
        "original_subtotal": original_subtotal,
        "subscription_discount": subscription_discount,
        "discounted_subtotal": discounted_subtotal
    }

# ==================== EMAIL AUTOMATION ====================

class EmailAutomationConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    automation_type: str  # abandoned_cart, review_request, low_stock_alert, welcome_series
    is_active: bool = True
    delay_hours: int = 24  # Hours to wait before sending
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AbandonedCart(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    email: Optional[str] = None
    items: List[Dict[str, Any]] = []
    subtotal: float = 0.0
    reminder_sent: bool = False
    recovered: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_activity: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

async def send_abandoned_cart_email(cart_data: dict):
    """Send abandoned cart recovery email"""
    if not RESEND_API_KEY or not cart_data.get("email"):
        logging.warning("Abandoned cart email skipped - no API key or email")
        return
    
    items_html = ""
    for item in cart_data.get("items", [])[:5]:
        items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #E8DFD5;">
                <table width="100%">
                    <tr>
                        <td width="80">
                            <img src="{item.get('image', '')}" alt="" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;">
                        </td>
                        <td>
                            <p style="margin: 0; color: #2D4A3E; font-weight: bold;">{item.get('name', '')}</p>
                            <p style="margin: 4px 0 0 0; color: #5C6D5E;">Qty: {item.get('quantity', 1)}</p>
                        </td>
                        <td style="text-align: right;">
                            <p style="margin: 0; color: #2D4A3E; font-weight: bold;">${item.get('price', 0):.2f}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 24px;">
                    <h2 style="color: #2D4A3E; margin: 0 0 8px 0;">Forget something? 🛒</h2>
                    <p style="color: #5C6D5E; margin: 0 0 24px 0;">
                        You left some amazing items in your cart. Don't let them slip away!
                    </p>
                    
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                        {items_html}
                    </table>
                    
                    <div style="background-color: #E8DFD5; padding: 16px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
                        <p style="margin: 0; color: #2D4A3E; font-size: 18px;">
                            <strong>Cart Total: ${cart_data.get('subtotal', 0):.2f}</strong>
                        </p>
                        <p style="margin: 8px 0 0 0; color: #6B8F71; font-size: 14px;">
                            ✨ Use code <strong>COMEBACK10</strong> for 10% off!
                        </p>
                    </div>
                    
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center;">
                                <a href="https://wildlyones.com/cart" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    Complete Your Order
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <p style="color: #D4A574; margin: 0; font-size: 12px;">© 2026 Wildly Ones Pet Wellness</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [cart_data.get("email")],
            "subject": "You left something behind! 🛒",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Abandoned cart email sent to {cart_data.get('email')}")
    except Exception as e:
        logging.error(f"Failed to send abandoned cart email: {str(e)}")

async def send_review_request_email(order: dict):
    """Send post-purchase review request email"""
    if not RESEND_API_KEY or not order.get("email"):
        return
    
    # Get first item for review focus
    first_item = order.get("items", [{}])[0] if order.get("items") else {}
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 24px; text-align: center;">
                    <h2 style="color: #2D4A3E; margin: 0 0 8px 0;">How's your fur baby loving it? ⭐</h2>
                    <p style="color: #5C6D5E; margin: 0 0 24px 0;">
                        We hope your pet is enjoying their new {first_item.get('product_name', 'products')}!
                    </p>
                    
                    <div style="background-color: #FDF8F3; padding: 24px; border-radius: 16px; margin-bottom: 24px;">
                        <p style="color: #2D4A3E; margin: 0 0 16px 0; font-size: 18px;">
                            <strong>Share your experience!</strong>
                        </p>
                        <p style="color: #5C6D5E; margin: 0 0 16px 0;">
                            Your review helps other pet parents make great choices for their furry friends.
                        </p>
                        <p style="color: #6B8F71; margin: 0; font-size: 14px;">
                            🎁 <strong>Earn 25 bonus points</strong> for leaving a review!
                        </p>
                    </div>
                    
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center;">
                                <a href="https://wildlyones.com/account" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    Write a Review
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <p style="color: #D4A574; margin: 0; font-size: 12px;">© 2026 Wildly Ones Pet Wellness</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [order.get("email")],
            "subject": "How's your pet loving their new goodies? ⭐",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Review request email sent to {order.get('email')}")
    except Exception as e:
        logging.error(f"Failed to send review request email: {str(e)}")

@api_router.get("/admin/email-automation", response_model=dict)
async def get_email_automation_stats(user: dict = Depends(require_admin)):
    """Get email automation statistics"""
    # Count abandoned carts
    abandoned_carts = await db.abandoned_carts.count_documents({"reminder_sent": False})
    recovered_carts = await db.abandoned_carts.count_documents({"recovered": True})
    
    # Count emails sent
    total_abandoned_emails = await db.abandoned_carts.count_documents({"reminder_sent": True})
    
    # Orders eligible for review requests (delivered in last 7 days)
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    review_eligible = await db.orders.count_documents({
        "status": "delivered",
        "updated_at": {"$gte": seven_days_ago}
    })
    
    return {
        "abandoned_carts": {
            "pending": abandoned_carts,
            "emails_sent": total_abandoned_emails,
            "recovered": recovered_carts,
            "recovery_rate": round((recovered_carts / total_abandoned_emails * 100) if total_abandoned_emails > 0 else 0, 1)
        },
        "review_requests": {
            "eligible_orders": review_eligible
        },
        "low_stock": await get_low_stock_count(),
        "automation_status": {
            "abandoned_cart": True,
            "review_request": True,
            "low_stock_alert": True
        }
    }

async def get_low_stock_count():
    """Get count of low stock products"""
    low_stock_threshold = 10
    return await db.products.count_documents({"stock_quantity": {"$lte": low_stock_threshold}, "in_stock": True})

@api_router.get("/admin/low-stock-products", response_model=dict)
async def get_low_stock_products(user: dict = Depends(require_admin)):
    """Get all products with low stock"""
    low_stock_threshold = 10
    products = await db.products.find(
        {"stock_quantity": {"$lte": low_stock_threshold}, "in_stock": True},
        {"_id": 0}
    ).sort("stock_quantity", 1).to_list(100)
    
    return {
        "products": products,
        "count": len(products),
        "threshold": low_stock_threshold
    }

async def send_low_stock_alert_email(products: list):
    """Send low stock alert email to admin"""
    if not RESEND_API_KEY or not products:
        return
    
    products_html = ""
    for product in products[:10]:
        products_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #E8DFD5;">
                <strong>{product.get('name', 'Unknown')}</strong><br>
                <span style="color: #5C6D5E; font-size: 12px;">SKU: {product.get('slug', 'N/A')}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #E8DFD5; text-align: center;">
                <span style="color: #E74C3C; font-weight: bold;">{product.get('stock_quantity', 0)}</span>
            </td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 24px;">
                    <div style="background-color: #FEE2E2; border-left: 4px solid #E74C3C; padding: 16px; margin-bottom: 24px;">
                        <h2 style="color: #E74C3C; margin: 0 0 8px 0;">⚠️ Low Stock Alert</h2>
                        <p style="color: #5C6D5E; margin: 0;">{len(products)} products are running low on inventory.</p>
                    </div>
                    
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                        <thead>
                            <tr>
                                <th style="padding: 12px; background-color: #E8DFD5; text-align: left;">Product</th>
                                <th style="padding: 12px; background-color: #E8DFD5; text-align: center;">Stock</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products_html}
                        </tbody>
                    </table>
                    
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center;">
                                <a href="https://wildlyones.com/admin/products" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    Manage Inventory
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                    <p style="color: #D4A574; margin: 0; font-size: 12px;">© 2026 Wildly Ones Pet Wellness</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        # Get admin email
        admin = await db.users.find_one({"is_admin": True}, {"email": 1})
        if admin:
            params = {
                "from": SENDER_EMAIL,
                "to": [admin.get("email")],
                "subject": f"⚠️ Low Stock Alert: {len(products)} products need restocking",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            logging.info(f"Low stock alert email sent")
    except Exception as e:
        logging.error(f"Failed to send low stock alert email: {str(e)}")

@api_router.post("/admin/email-automation/send-low-stock", response_model=dict)
async def trigger_low_stock_alerts(user: dict = Depends(require_admin)):
    """Manually trigger low stock alert emails"""
    low_stock_threshold = 10
    products = await db.products.find(
        {"stock_quantity": {"$lte": low_stock_threshold}, "in_stock": True},
        {"_id": 0}
    ).to_list(100)
    
    if products:
        await send_low_stock_alert_email(products)
        # Also send real-time notifications
        for product in products:
            await notify_low_stock(product)
        return {"message": f"Low stock alert sent for {len(products)} products"}
    
    return {"message": "No low stock products found"}

@api_router.post("/admin/email-automation/send-abandoned", response_model=dict)
async def trigger_abandoned_cart_emails(user: dict = Depends(require_admin)):
    """Manually trigger abandoned cart emails"""
    # Find carts older than 1 hour that haven't received reminders
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    
    abandoned = await db.abandoned_carts.find({
        "reminder_sent": False,
        "email": {"$ne": None},
        "last_activity": {"$lt": one_hour_ago}
    }).to_list(50)
    
    sent_count = 0
    for cart in abandoned:
        await send_abandoned_cart_email(cart)
        await db.abandoned_carts.update_one(
            {"id": cart["id"]},
            {"$set": {"reminder_sent": True}}
        )
        sent_count += 1
    
    return {"message": f"Sent {sent_count} abandoned cart emails"}

@api_router.post("/admin/email-automation/send-reviews", response_model=dict)
async def trigger_review_request_emails(user: dict = Depends(require_admin)):
    """Manually trigger review request emails for delivered orders"""
    # Find delivered orders from 3-7 days ago that haven't received review requests
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    orders = await db.orders.find({
        "status": "delivered",
        "updated_at": {"$gte": seven_days_ago, "$lte": three_days_ago},
        "review_request_sent": {"$ne": True}
    }, {"_id": 0}).to_list(50)
    
    sent_count = 0
    for order in orders:
        await send_review_request_email(order)
        await db.orders.update_one(
            {"id": order["id"]},
            {"$set": {"review_request_sent": True}}
        )
        sent_count += 1
    
    return {"message": f"Sent {sent_count} review request emails"}

# ==================== CUSTOMER SEGMENTATION ====================

class CustomerSegment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    segment: str  # vip, loyal, at_risk, new, dormant
    label: str
    description: str
    criteria: Dict[str, Any]
    customer_count: int = 0

SEGMENT_DEFINITIONS = {
    "vip": {
        "label": "VIP Customers",
        "description": "High-value customers with 5+ orders or $500+ total spend",
        "color": "#FFD700"
    },
    "loyal": {
        "label": "Loyal Customers",
        "description": "Regular customers with 3-4 orders in the last 6 months",
        "color": "#6B8F71"
    },
    "at_risk": {
        "label": "At-Risk Customers",
        "description": "Previously active customers with no orders in 60+ days",
        "color": "#E74C3C"
    },
    "new": {
        "label": "New Customers",
        "description": "Customers who signed up in the last 30 days",
        "color": "#3498DB"
    },
    "dormant": {
        "label": "Dormant Customers",
        "description": "Customers with no orders in 90+ days",
        "color": "#95A5A6"
    }
}

async def calculate_customer_segments():
    """Calculate customer segments based on purchase behavior"""
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    sixty_days_ago = (now - timedelta(days=60)).isoformat()
    ninety_days_ago = (now - timedelta(days=90)).isoformat()
    six_months_ago = (now - timedelta(days=180)).isoformat()
    
    segments = {}
    
    # Get all non-admin users
    users = await db.users.find({"is_admin": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    for user in users:
        user_id = user.get("id")
        
        # Get user's orders
        orders = await db.orders.find(
            {"user_id": user_id, "payment_status": "paid"},
            {"_id": 0, "total": 1, "created_at": 1}
        ).to_list(100)
        
        total_orders = len(orders)
        total_spend = sum(o.get("total", 0) for o in orders)
        
        # Get most recent order date
        recent_order = None
        if orders:
            recent_order = max(o.get("created_at", "") for o in orders)
        
        # Determine segment
        segment = "new"  # Default
        
        if total_orders >= 5 or total_spend >= 500:
            segment = "vip"
        elif total_orders >= 3 and recent_order and recent_order >= six_months_ago:
            segment = "loyal"
        elif total_orders > 0 and recent_order and recent_order < sixty_days_ago:
            if recent_order < ninety_days_ago:
                segment = "dormant"
            else:
                segment = "at_risk"
        elif user.get("created_at", "") >= thirty_days_ago:
            segment = "new"
        elif total_orders == 0 and user.get("created_at", "") < thirty_days_ago:
            segment = "dormant"
        
        # Store segment
        if segment not in segments:
            segments[segment] = []
        segments[segment].append({
            "id": user_id,
            "email": user.get("email"),
            "name": user.get("name", ""),
            "total_orders": total_orders,
            "total_spend": round(total_spend, 2),
            "last_order": recent_order,
            "created_at": user.get("created_at")
        })
        
        # Update user's segment in database
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"segment": segment, "segment_updated_at": now.isoformat()}}
        )
    
    return segments

@api_router.get("/admin/customer-segments", response_model=dict)
async def get_customer_segments(user: dict = Depends(require_admin)):
    """Get customer segments with counts and details"""
    segments = await calculate_customer_segments()
    
    result = []
    for segment_key, customers in segments.items():
        segment_def = SEGMENT_DEFINITIONS.get(segment_key, {})
        result.append({
            "segment": segment_key,
            "label": segment_def.get("label", segment_key.title()),
            "description": segment_def.get("description", ""),
            "color": segment_def.get("color", "#888888"),
            "customer_count": len(customers),
            "total_revenue": round(sum(c.get("total_spend", 0) for c in customers), 2),
            "customers": customers[:20]  # Limit to 20 for preview
        })
    
    # Sort by priority: VIP > Loyal > At-Risk > New > Dormant
    priority_order = ["vip", "loyal", "at_risk", "new", "dormant"]
    result.sort(key=lambda x: priority_order.index(x["segment"]) if x["segment"] in priority_order else 99)
    
    # Calculate overall stats
    total_customers = sum(s["customer_count"] for s in result)
    total_revenue = sum(s["total_revenue"] for s in result)
    
    return {
        "segments": result,
        "summary": {
            "total_customers": total_customers,
            "total_revenue": round(total_revenue, 2),
            "segment_count": len(result)
        }
    }

@api_router.get("/admin/customer-segments/{segment}", response_model=dict)
async def get_segment_customers(segment: str, user: dict = Depends(require_admin)):
    """Get all customers in a specific segment"""
    if segment not in SEGMENT_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Invalid segment")
    
    customers = await db.users.find(
        {"segment": segment, "is_admin": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(500)
    
    # Enrich with order data
    enriched = []
    for customer in customers:
        orders = await db.orders.find(
            {"user_id": customer.get("id"), "payment_status": "paid"},
            {"_id": 0, "total": 1, "created_at": 1}
        ).to_list(100)
        
        enriched.append({
            **customer,
            "total_orders": len(orders),
            "total_spend": round(sum(o.get("total", 0) for o in orders), 2),
            "last_order": max((o.get("created_at") for o in orders), default=None) if orders else None
        })
    
    segment_def = SEGMENT_DEFINITIONS.get(segment, {})
    return {
        "segment": segment,
        "label": segment_def.get("label", segment.title()),
        "description": segment_def.get("description", ""),
        "color": segment_def.get("color", "#888888"),
        "customers": enriched,
        "customer_count": len(enriched)
    }

@api_router.post("/admin/customer-segments/{segment}/campaign", response_model=dict)
async def create_segment_campaign(
    segment: str,
    campaign_type: str = "promotional",  # promotional, win_back, loyalty, welcome
    user: dict = Depends(require_admin)
):
    """Generate AI-powered email campaign for a customer segment"""
    if segment not in SEGMENT_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Invalid segment")
    
    segment_def = SEGMENT_DEFINITIONS.get(segment, {})
    
    # Get customer count for context
    customer_count = await db.users.count_documents({"segment": segment, "is_admin": {"$ne": True}})
    
    # Campaign templates based on segment
    campaign_templates = {
        "vip": {
            "subject": "Exclusive VIP Offer Just for You! 🌟",
            "discount": "20% off + Free Shipping",
            "code": "VIP20",
            "message": "As one of our most valued customers, enjoy this exclusive offer as a thank you for your loyalty."
        },
        "loyal": {
            "subject": "A Special Thank You from Wildly Ones 💚",
            "discount": "15% off your next order",
            "code": "LOYAL15",
            "message": "We appreciate your continued support! Here's a special discount just for you."
        },
        "at_risk": {
            "subject": "We Miss You! Come Back for 25% Off 🐾",
            "discount": "25% off + Free Gift",
            "code": "COMEBACK25",
            "message": "It's been a while since your last visit. We'd love to see you again!"
        },
        "new": {
            "subject": "Welcome to the Wildly Ones Family! 🎉",
            "discount": "10% off your first purchase",
            "code": "WELCOME10",
            "message": "Thanks for joining us! Here's a special welcome gift to get you started."
        },
        "dormant": {
            "subject": "We've Missed You! Here's 30% Off 💝",
            "discount": "30% off + Free Shipping",
            "code": "WINBACK30",
            "message": "It's been too long! Come back and discover what's new for your furry friend."
        }
    }
    
    template = campaign_templates.get(segment, campaign_templates["new"])
    
    return {
        "segment": segment,
        "label": segment_def.get("label"),
        "customer_count": customer_count,
        "campaign": {
            "type": campaign_type,
            "subject": template["subject"],
            "discount": template["discount"],
            "promo_code": template["code"],
            "message": template["message"],
            "preview_html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #2D4A3E; color: white; padding: 20px; text-align: center;">
                        <h1>🐾 Wildly Ones</h1>
                    </div>
                    <div style="padding: 30px; background: #FDF8F3;">
                        <h2 style="color: #2D4A3E;">{template['subject']}</h2>
                        <p style="color: #5C6D5E;">{template['message']}</p>
                        <div style="background: #E8DFD5; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;">
                            <p style="font-size: 24px; color: #2D4A3E; margin: 0;"><strong>{template['discount']}</strong></p>
                            <p style="color: #6B8F71; margin-top: 8px;">Use code: <strong>{template['code']}</strong></p>
                        </div>
                        <a href="https://wildlyones.com" style="display: inline-block; background: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">Shop Now</a>
                    </div>
                </div>
            """
        },
        "ready_to_send": True
    }

@api_router.post("/admin/customer-segments/{segment}/send-campaign", response_model=dict)
async def send_segment_campaign(
    segment: str,
    subject: str,
    message: str,
    promo_code: str,
    discount: str,
    user: dict = Depends(require_admin)
):
    """Send email campaign to all customers in a segment"""
    if segment not in SEGMENT_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Invalid segment")
    
    if not RESEND_API_KEY:
        return {"message": "Email API not configured", "sent_count": 0}
    
    customers = await db.users.find(
        {"segment": segment, "is_admin": {"$ne": True}},
        {"_id": 0, "email": 1, "name": 1}
    ).to_list(500)
    
    sent_count = 0
    for customer in customers:
        if not customer.get("email"):
            continue
            
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #FDF8F3;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
                <tr>
                    <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                        <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 Wildly Ones</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 32px 24px;">
                        <h2 style="color: #2D4A3E; margin: 0 0 16px 0;">{subject}</h2>
                        <p style="color: #5C6D5E; margin: 0 0 24px 0;">{message}</p>
                        
                        <div style="background-color: #E8DFD5; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
                            <p style="font-size: 20px; color: #2D4A3E; margin: 0;"><strong>{discount}</strong></p>
                            <p style="color: #6B8F71; margin-top: 8px;">Use code: <strong>{promo_code}</strong></p>
                        </div>
                        
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="text-align: center;">
                                    <a href="https://wildlyones.com" style="display: inline-block; background-color: #D4A574; color: #2D4A3E; padding: 14px 32px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                        Shop Now
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="background-color: #2D4A3E; padding: 24px; text-align: center;">
                        <p style="color: #D4A574; margin: 0; font-size: 12px;">© 2026 Wildly Ones Pet Wellness</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [customer.get("email")],
                "subject": subject,
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            sent_count += 1
        except Exception as e:
            logging.error(f"Failed to send campaign email to {customer.get('email')}: {str(e)}")
    
    # Log the campaign
    await db.campaigns.insert_one({
        "id": str(uuid.uuid4()),
        "segment": segment,
        "subject": subject,
        "promo_code": promo_code,
        "sent_count": sent_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    })
    
    return {"message": f"Campaign sent to {sent_count} customers", "sent_count": sent_count}

# ==================== AGENT ROUTES ====================

@api_router.get("/agents", response_model=dict)
async def get_agents():
    return {"agents": AGENT_METADATA}

@api_router.post("/agents/chat", response_model=dict)
async def agent_chat(query: AgentQuery, user: Optional[dict] = Depends(get_current_user)):
    session_id = query.session_id or str(uuid.uuid4())
    user_id = user["id"] if user else None
    agent_type = query.agent_type
    
    agent_session_id = f"{agent_type}_{session_id}"
    session = await db.agent_sessions.find_one({"id": agent_session_id}, {"_id": 0})
    
    if not session:
        session = {
            "id": agent_session_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.agent_sessions.insert_one(session)
    
    user_message = {
        "role": "user",
        "content": query.query,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = await get_agent_response(query.query, agent_type, session_id, session.get("messages", []))
    
    assistant_message = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.agent_sessions.update_one(
        {"id": agent_session_id},
        {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "session_id": session_id,
        "agent_type": agent_type,
        "response": response,
        "message": assistant_message
    }

@api_router.get("/agents/sessions", response_model=List[dict])
async def get_agent_sessions(agent_type: Optional[str] = None, user: dict = Depends(require_user)):
    query_filter = {"user_id": user["id"]}
    if agent_type:
        query_filter["agent_type"] = agent_type
    
    sessions = await db.agent_sessions.find(query_filter, {"_id": 0}).sort("updated_at", -1).to_list(50)
    return sessions

# ==================== SEED DATA ====================

@api_router.post("/seed-products")
async def seed_products():
    """Seed the database with initial pet wellness products"""
    existing = await db.products.count_documents({})
    if existing > 0:
        return {"message": f"Products already seeded ({existing} products)"}
    
    products = [
        # DOG PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Calming Dog Bed - Deep Pressure Comfort",
            "slug": "calming-dog-bed",
            "description": "Your dog deserves a sanctuary. The Calming Dog Bed uses deep pressure stimulation technology — the same principle behind weighted blankets — to help promote relaxation during stressful moments. The raised rim provides head and neck support while creating a sense of security. Many pet parents report their dogs settle faster and sleep more soundly, especially during thunderstorms or when left alone.",
            "short_description": "Deep pressure comfort bed designed to support relaxation for anxious dogs",
            "price": 49.99,
            "compare_at_price": 69.99,
            "cost": 15.00,
            "category": "home_goods",
            "subcategory": "Dog Beds",
            "images": ["https://images.unsplash.com/photo-1646195164326-124b72fb9d34?w=600"],
            "tags": ["calming", "anxiety", "dog bed", "sleep", "comfort"],
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 150,
            "supplier": "CJdropshipping",
            "features": ["Deep pressure stimulation", "Raised rim for security", "Machine washable cover", "Non-slip bottom"],
            "dimensions": "Medium: 24\" diameter, Large: 32\" diameter",
            "rating": 4.8,
            "review_count": 234
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Calming Soft Chews for Dogs",
            "slug": "calming-soft-chews-dogs",
            "description": "For those moments when your dog needs a little extra support. Our Calming Soft Chews are formulated with L-Theanine, Chamomile, and Valerian Root — ingredients known to support relaxation without drowsiness. Many pet parents give them before car rides, vet visits, or during fireworks season. Bacon-flavored so dogs actually look forward to them.",
            "short_description": "Natural calming chews with L-Theanine and Chamomile",
            "price": 29.99,
            "compare_at_price": None,
            "cost": 8.50,
            "category": "Supplements",
            "subcategory": "Calming",
            "images": ["https://images.unsplash.com/photo-1763668331599-487470fb85b2?w=600"],
            "tags": ["calming", "treats", "anxiety", "supplements", "natural"],
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 300,
            "supplier": "Zendrop",
            "features": ["L-Theanine formula", "Chamomile & Valerian Root", "Bacon flavored", "90 chews per jar"],
            "ingredients": "L-Theanine, Chamomile Extract, Valerian Root, Passionflower, Ginger Root",
            "rating": 4.6,
            "review_count": 189
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Orthopedic Memory Foam Pet Bed",
            "slug": "orthopedic-memory-foam-bed",
            "description": "Senior pets and those with joint concerns deserve extra support. Our Orthopedic Memory Foam Bed features 4 inches of medical-grade memory foam that contours to your pet's body, relieving pressure points and supporting healthy joints. The waterproof liner protects against accidents, and the removable cover is machine washable.",
            "short_description": "4\" memory foam bed with orthopedic support for joints",
            "price": 79.99,
            "compare_at_price": 99.99,
            "cost": 25.00,
            "category": "home_goods",
            "subcategory": "Orthopedic",
            "images": ["https://images.unsplash.com/photo-1765604554147-0cecc68aa60e?w=600"],
            "tags": ["orthopedic", "memory foam", "senior", "joints", "comfort"],
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 75,
            "supplier": "Spocket",
            "features": ["4\" memory foam", "Waterproof liner", "Removable washable cover", "Non-slip bottom", "Bolstered edges"],
            "dimensions": "Large: 36\" x 28\" x 6\"",
            "rating": 4.8,
            "review_count": 198
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Calming Collar for Dogs",
            "slug": "calming-collar-dogs",
            "description": "A convenient, always-on solution for dogs who need consistent calming support. The Calming Collar releases a blend of lavender and chamomile essential oils through body heat activation. Adjustable to fit most breeds, water-resistant, and lasts up to 30 days.",
            "short_description": "30-day lavender & chamomile calming collar",
            "price": 24.99,
            "compare_at_price": None,
            "cost": 6.00,
            "category": "home_goods",
            "subcategory": "Collars",
            "images": ["https://images.unsplash.com/photo-1629130622663-02fa6b459bd7?w=600"],
            "tags": ["collar", "calming", "lavender", "aromatherapy", "anxiety"],
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 250,
            "supplier": "CJdropshipping",
            "features": ["Lavender & chamomile blend", "30-day effectiveness", "Adjustable fit", "Water-resistant", "Breakaway safety"],
            "rating": 4.4,
            "review_count": 423
        },
        # CAT PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Cat Calming Diffuser Kit",
            "slug": "cat-calming-diffuser",
            "description": "Cats are sensitive creatures, and sometimes the home environment can trigger stress behaviors like scratching, hiding, or inappropriate marking. Our Calming Diffuser releases a synthetic version of the feline facial pheromone — the same pheromone cats deposit when they rub their face on objects they feel comfortable with. Covers up to 700 sq ft for 30 days.",
            "short_description": "Pheromone diffuser designed to help cats feel calm and secure",
            "price": 34.99,
            "compare_at_price": None,
            "cost": 10.00,
            "category": "home_goods",
            "subcategory": "Diffusers",
            "images": ["https://images.unsplash.com/photo-1770810416702-59eefaeab7a5?w=600"],
            "tags": ["cat", "diffuser", "pheromone", "calming", "stress"],
            "pet_type": "cat",
            "in_stock": True,
            "stock_quantity": 200,
            "supplier": "CJdropshipping",
            "features": ["Synthetic pheromone formula", "Covers 700 sq ft", "30-day supply", "Plug-in design"],
            "rating": 4.5,
            "review_count": 312
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Anxiety Relief Chews for Cats",
            "slug": "anxiety-relief-chews-cats",
            "description": "Cats can be finicky, which is why we spent months perfecting the taste of these Anxiety Relief Chews. Formulated with L-Tryptophan and Thiamine (B1), these soft chews support relaxation during stressful events like vet visits, travel, or when introducing a new pet to the household. Chicken-liver flavored for maximum appeal.",
            "short_description": "L-Tryptophan formula chews for cat relaxation support",
            "price": 32.99,
            "compare_at_price": None,
            "cost": 9.00,
            "category": "Supplements",
            "subcategory": "Calming",
            "images": ["https://images.unsplash.com/photo-1771100515722-468bb8d3a17d?w=600"],
            "tags": ["cat", "chews", "anxiety", "calming", "supplements"],
            "pet_type": "cat",
            "in_stock": True,
            "stock_quantity": 180,
            "supplier": "Zendrop",
            "features": ["L-Tryptophan formula", "Thiamine B1 added", "Chicken-liver flavor", "60 chews per bag"],
            "ingredients": "L-Tryptophan, Thiamine (Vitamin B1), Chamomile, Ginger, Brewer's Yeast",
            "rating": 4.5,
            "review_count": 145
        },
        # DOG-SPECIFIC (weighted blankets not safe for cats)
        {
            "id": str(uuid.uuid4()),
            "name": "Weighted Calming Blanket for Dogs",
            "slug": "weighted-calming-blanket",
            "description": "The gentle, even pressure of our Weighted Calming Blanket mimics the feeling of being held, which many dogs find naturally comforting. At 3 lbs, it's ideal for medium to large dogs (20+ lbs). The ultra-soft minky fabric on one side and breathable cotton on the other means comfort in any season. Note: Not recommended for cats or small dogs under 20 lbs due to weight safety concerns.",
            "short_description": "3lb weighted blanket with deep pressure comfort for medium to large dogs",
            "price": 59.99,
            "compare_at_price": 79.99,
            "cost": 18.00,
            "category": "home_goods",
            "subcategory": "Blankets",
            "images": ["https://images.unsplash.com/photo-1769068874492-a848eae2e5fa?w=600"],
            "tags": ["weighted", "blanket", "calming", "anxiety", "comfort", "large dogs"],
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 100,
            "supplier": "Spocket",
            "features": ["3lb weighted design", "Dual-sided fabric", "Machine washable", "Even weight distribution", "For dogs 20+ lbs"],
            "dimensions": "36\" x 48\"",
            "weight": "3 lbs",
            "rating": 4.7,
            "review_count": 156
        },
        # BOTH DOGS & CATS (CBD is safe for both in proper doses)
        {
            "id": str(uuid.uuid4()),
            "name": "Premium CBD Oil for Pets",
            "slug": "premium-cbd-oil-pets",
            "description": "Our Premium CBD Oil is made from organically grown hemp and third-party tested for purity and potency. Each batch comes with a Certificate of Analysis. The natural bacon flavor makes it easy to administer directly or mixed with food. Many pet parents use it as part of their pet's daily wellness routine.",
            "short_description": "Organic hemp-derived CBD oil with third-party COA",
            "price": 44.99,
            "compare_at_price": 54.99,
            "cost": 14.00,
            "category": "Supplements",
            "subcategory": "CBD",
            "images": ["https://images.unsplash.com/photo-1635943051866-3271c28168f8?w=600"],
            "tags": ["cbd", "hemp", "oil", "wellness", "organic"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 80,
            "supplier": "Zendrop",
            "features": ["500mg CBD per bottle", "Organic hemp", "Third-party tested", "COA included", "Bacon flavor"],
            "ingredients": "Organic Hemp Extract, MCT Oil, Natural Bacon Flavor",
            "rating": 4.9,
            "review_count": 267
        },
        # REPTILE PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Bearded Dragon Calcium + D3 Supplement",
            "slug": "bearded-dragon-calcium-d3",
            "description": "Essential calcium supplementation for bearded dragons to support strong bones and prevent metabolic bone disease (MBD). Our ultra-fine powder adheres perfectly to feeder insects and vegetables. Contains optimal D3 levels for bearded dragons under UVB lighting.",
            "short_description": "Essential calcium + D3 for bearded dragon bone health",
            "price": 18.99,
            "compare_at_price": None,
            "cost": 5.50,
            "category": "Reptile",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1619816128374-a6b4766ca92c?w=600"],
            "tags": ["reptile", "bearded dragon", "calcium", "d3", "supplements", "mbd prevention"],
            "pet_type": "reptile",
            "in_stock": True,
            "stock_quantity": 200,
            "supplier": "Zendrop",
            "features": ["Ultra-fine powder", "Optimal D3 ratio", "MBD prevention", "Vet-formulated", "100g jar"],
            "ingredients": "Calcium Carbonate, Vitamin D3, Phosphorus-free formula",
            "rating": 4.8,
            "review_count": 234
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Leopard Gecko Multivitamin Powder",
            "slug": "leopard-gecko-multivitamin",
            "description": "Complete multivitamin formula designed specifically for leopard geckos and other insectivorous reptiles. Contains essential vitamins A, E, and B-complex without excessive D3 (since leos don't require UVB). Dust on feeders 2-3 times per week for optimal health.",
            "short_description": "Complete vitamin supplement for leopard geckos",
            "price": 16.99,
            "compare_at_price": None,
            "cost": 4.80,
            "category": "Reptile",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1758445046837-a840a8cbc701?w=600"],
            "tags": ["reptile", "leopard gecko", "multivitamin", "supplements", "shedding"],
            "pet_type": "reptile",
            "in_stock": True,
            "stock_quantity": 180,
            "supplier": "CJdropshipping",
            "features": ["Low D3 formula", "Supports shedding", "Beta-carotene vitamin A", "No artificial colors", "60g jar"],
            "ingredients": "Vitamin A (Beta-carotene), Vitamin E, B-Complex, Calcium, Trace minerals",
            "rating": 4.7,
            "review_count": 156
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Reptile Stress Relief Drops",
            "slug": "reptile-stress-relief-drops",
            "description": "Gentle, herbal-based stress support for reptiles during handling, transport, relocation, or environmental changes. Our liquid formula can be added to drinking water or applied to food. Safe for bearded dragons, leopard geckos, ball pythons, and other common pet reptiles.",
            "short_description": "Herbal calming drops for stressed reptiles",
            "price": 22.99,
            "compare_at_price": 27.99,
            "cost": 7.00,
            "category": "Reptile",
            "subcategory": "Calming",
            "images": ["https://images.unsplash.com/photo-1759167844894-b06c85312fbc?w=600"],
            "tags": ["reptile", "stress relief", "calming", "herbal", "natural"],
            "pet_type": "reptile",
            "in_stock": True,
            "stock_quantity": 120,
            "supplier": "Spocket",
            "features": ["Herbal formula", "Add to water or food", "Multi-species safe", "No harsh chemicals", "2oz dropper bottle"],
            "ingredients": "Chamomile Extract, Passionflower, Vegetable Glycerin, Purified Water",
            "rating": 4.5,
            "review_count": 89
        },
        # BIRD PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Avian Calm Supplement Drops",
            "slug": "avian-calm-supplement-drops",
            "description": "Gentle calming support for pet birds experiencing stress from travel, new environments, or seasonal changes. Our liquid formula is designed specifically for avian species and can be added to drinking water. Made with natural chamomile and valerian extracts, safe for parakeets, cockatiels, finches, and parrots.",
            "short_description": "Natural stress relief drops for pet birds",
            "price": 19.99,
            "compare_at_price": None,
            "cost": 5.50,
            "category": "Bird",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1695260699146-6ab3d4e45d8f?w=600"],
            "tags": ["bird", "parakeet", "cockatiel", "calming", "supplements", "avian"],
            "pet_type": "bird",
            "in_stock": True,
            "stock_quantity": 200,
            "supplier": "Zendrop",
            "features": ["Avian-safe formula", "Add to water", "Natural ingredients", "Multi-species safe", "1oz dropper bottle"],
            "ingredients": "Chamomile Extract, Valerian Root, Vegetable Glycerin, Purified Water",
            "rating": 4.6,
            "review_count": 127
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Premium Bird Vitamin Blend",
            "slug": "premium-bird-vitamin-blend",
            "description": "Complete daily vitamin supplement to support your bird's overall health and vibrant plumage. Our formula includes essential vitamins A, D3, E, and B-complex along with calcium and trace minerals. Simply sprinkle on food or add to water. Ideal for parakeets, canaries, finches, and small parrots.",
            "short_description": "Complete vitamin supplement for healthy feathers and vitality",
            "price": 24.99,
            "compare_at_price": 29.99,
            "cost": 7.00,
            "category": "Bird",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1698666047105-9a26fc245347?w=600"],
            "tags": ["bird", "vitamins", "feathers", "health", "supplements"],
            "pet_type": "bird",
            "in_stock": True,
            "stock_quantity": 180,
            "supplier": "CJdropshipping",
            "features": ["Complete vitamin blend", "Supports feather health", "Easy-to-use powder", "Multi-species safe", "60g jar"],
            "ingredients": "Vitamin A, D3, E, B-Complex, Calcium, Iodine, Zinc",
            "rating": 4.7,
            "review_count": 98
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bird Digestive Health Probiotic",
            "slug": "bird-digestive-probiotic",
            "description": "Support your bird's digestive system with our specialized probiotic formula. Contains beneficial bacteria strains specifically selected for avian species. Helps maintain healthy gut flora, improves nutrient absorption, and supports immune function. Perfect for birds recovering from illness or on antibiotics.",
            "short_description": "Avian probiotic for optimal digestive health",
            "price": 21.99,
            "compare_at_price": None,
            "cost": 6.50,
            "category": "Bird",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1761724337314-747c172a492c?w=600"],
            "tags": ["bird", "probiotic", "digestive", "health", "gut flora"],
            "pet_type": "bird",
            "in_stock": True,
            "stock_quantity": 150,
            "supplier": "Spocket",
            "features": ["Avian-specific strains", "Improves digestion", "Supports immunity", "Easy dosing", "30-day supply"],
            "ingredients": "Lactobacillus acidophilus, Bifidobacterium, Enterococcus faecium",
            "rating": 4.5,
            "review_count": 76
        },
        # RABBIT PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Rabbit Calming Hay Blend",
            "slug": "rabbit-calming-hay-blend",
            "description": "Premium timothy hay infused with chamomile and lavender for natural calming support. Perfect for anxious bunnies during travel, vet visits, or bonding periods. The familiar hay format encourages natural foraging behavior while delivering gentle calming benefits. Made with 100% organic, pesticide-free ingredients.",
            "short_description": "Chamomile-infused timothy hay for anxious rabbits",
            "price": 18.99,
            "compare_at_price": None,
            "cost": 5.00,
            "category": "Rabbit",
            "subcategory": "Calming",
            "images": ["https://images.unsplash.com/photo-1636096034623-1d3254303038?w=600"],
            "tags": ["rabbit", "bunny", "hay", "calming", "timothy", "chamomile"],
            "pet_type": "rabbit",
            "in_stock": True,
            "stock_quantity": 220,
            "supplier": "Zendrop",
            "features": ["Timothy hay base", "Chamomile & lavender", "Organic ingredients", "Encourages foraging", "8oz bag"],
            "ingredients": "Organic Timothy Hay, Chamomile Flowers, Lavender Buds",
            "rating": 4.8,
            "review_count": 156
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Rabbit Joint & Mobility Supplement",
            "slug": "rabbit-joint-mobility-supplement",
            "description": "Support your rabbit's mobility and joint health with our specially formulated supplement. Contains glucosamine, chondroitin, and MSM in rabbit-safe doses. Ideal for senior rabbits or those recovering from injury. Tasty hay-flavored tablets that most bunnies accept readily.",
            "short_description": "Joint support supplement for senior and active rabbits",
            "price": 26.99,
            "compare_at_price": 32.99,
            "cost": 8.00,
            "category": "Rabbit",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1626242078533-e1242089eae2?w=600"],
            "tags": ["rabbit", "joint", "mobility", "senior", "supplements"],
            "pet_type": "rabbit",
            "in_stock": True,
            "stock_quantity": 140,
            "supplier": "CJdropshipping",
            "features": ["Glucosamine formula", "Hay-flavored tablets", "Senior-friendly", "Easy to administer", "60 tablets"],
            "ingredients": "Glucosamine, Chondroitin, MSM, Vitamin C, Timothy Hay Powder",
            "rating": 4.6,
            "review_count": 89
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bunny Digestive Health Papaya Tablets",
            "slug": "bunny-digestive-papaya-tablets",
            "description": "Natural papaya enzyme tablets to support healthy digestion and help prevent wool block in rabbits. Papain enzymes assist in breaking down ingested fur and promoting gut motility. Many rabbit owners give these as a treat — bunnies love the sweet papaya flavor!",
            "short_description": "Papaya enzyme treats for digestive wellness",
            "price": 14.99,
            "compare_at_price": None,
            "cost": 4.00,
            "category": "Rabbit",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1715159668261-323380b89fd3?w=600"],
            "tags": ["rabbit", "papaya", "digestive", "wool block", "treats"],
            "pet_type": "rabbit",
            "in_stock": True,
            "stock_quantity": 280,
            "supplier": "Spocket",
            "features": ["Natural papain enzyme", "Prevents wool block", "Tasty treat format", "No artificial colors", "90 tablets"],
            "ingredients": "Dried Papaya, Papain Enzyme, Natural Flavors",
            "rating": 4.9,
            "review_count": 234
        },
        # FISH PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Aquarium Stress Coat Water Conditioner",
            "slug": "aquarium-stress-coat",
            "description": "Reduce fish stress and promote healing with our advanced water conditioner. Contains aloe vera extract that helps replace the natural slime coat on fish skin, protecting them from disease and infection. Also neutralizes chlorine and heavy metals. Essential for water changes and new tank setups.",
            "short_description": "Aloe-based stress reducer and slime coat protector",
            "price": 15.99,
            "compare_at_price": None,
            "cost": 4.50,
            "category": "Fish",
            "subcategory": "Water Care",
            "images": ["https://images.unsplash.com/photo-1666996547874-0dc4eb17ccc1?w=600"],
            "tags": ["fish", "aquarium", "stress coat", "water conditioner", "tank"],
            "pet_type": "fish",
            "in_stock": True,
            "stock_quantity": 300,
            "supplier": "Zendrop",
            "features": ["Aloe vera formula", "Replaces slime coat", "Neutralizes chlorine", "Safe for all fish", "8oz bottle"],
            "ingredients": "Aloe Vera Extract, Water Conditioner, Chlorine Neutralizer",
            "rating": 4.7,
            "review_count": 312
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Premium Fish Immune Support Food",
            "slug": "fish-immune-support-food",
            "description": "Boost your fish's natural defenses with our vitamin-enriched premium food. Contains beta-glucan and vitamin C to support immune function, plus natural color enhancers for vibrant scales. Slow-sinking pellets ideal for community tanks with mid-dwelling species.",
            "short_description": "Immune-boosting fish food with color enhancers",
            "price": 12.99,
            "compare_at_price": None,
            "cost": 3.50,
            "category": "Fish",
            "subcategory": "Food",
            "images": ["https://images.unsplash.com/photo-1758854486625-2ef3d73853fc?w=600"],
            "tags": ["fish", "food", "immune", "vitamins", "color enhancer"],
            "pet_type": "fish",
            "in_stock": True,
            "stock_quantity": 400,
            "supplier": "CJdropshipping",
            "features": ["Beta-glucan added", "Natural color enhancers", "Slow-sinking pellets", "High protein content", "4oz jar"],
            "ingredients": "Fish Meal, Spirulina, Beta-Glucan, Vitamin C, Astaxanthin",
            "rating": 4.6,
            "review_count": 178
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Betta Fish Wellness Drops",
            "slug": "betta-wellness-drops",
            "description": "Specially formulated for betta fish health and longevity. Our concentrated drops support fin health, improve coloration, and help prevent common betta ailments. Contains natural tea tree and aloe extracts with antibacterial properties. Simply add to tank water weekly.",
            "short_description": "Weekly wellness treatment for healthy bettas",
            "price": 11.99,
            "compare_at_price": 14.99,
            "cost": 3.00,
            "category": "Fish",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1763770448943-11a878b4e1a2?w=600"],
            "tags": ["betta", "fish", "wellness", "fin health", "drops"],
            "pet_type": "fish",
            "in_stock": True,
            "stock_quantity": 250,
            "supplier": "Spocket",
            "features": ["Betta-specific formula", "Supports fin health", "Natural antibacterial", "Easy weekly dosing", "2oz dropper bottle"],
            "ingredients": "Tea Tree Extract, Aloe Vera, Vitamin E, Purified Water",
            "rating": 4.8,
            "review_count": 203
        },
        # SMALL PET PRODUCTS (Guinea Pigs, Hamsters, Gerbils, etc.)
        {
            "id": str(uuid.uuid4()),
            "name": "Small Pet Calming Herbal Blend",
            "slug": "small-pet-calming-blend",
            "description": "Gentle herbal mix to support calm and reduce stress in guinea pigs, hamsters, gerbils, and chinchillas. Contains chamomile, dandelion, and rose petals that small pets naturally enjoy foraging. Perfect for introducing to new environments or during social introductions.",
            "short_description": "Natural calming herbs for guinea pigs, hamsters & more",
            "price": 13.99,
            "compare_at_price": None,
            "cost": 3.80,
            "category": "Small Pet",
            "subcategory": "Calming",
            "images": ["https://images.unsplash.com/photo-1619961279595-d9440fbf93a7?w=600"],
            "tags": ["guinea pig", "hamster", "gerbil", "calming", "herbs", "small pet"],
            "pet_type": "small_pet",
            "in_stock": True,
            "stock_quantity": 260,
            "supplier": "Zendrop",
            "features": ["Natural herb blend", "Foraging enrichment", "Multi-species safe", "No artificial additives", "4oz bag"],
            "ingredients": "Chamomile Flowers, Dandelion Leaves, Rose Petals, Calendula",
            "rating": 4.7,
            "review_count": 145
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Guinea Pig Vitamin C Drops",
            "slug": "guinea-pig-vitamin-c-drops",
            "description": "Essential vitamin C supplementation for guinea pigs who cannot produce their own. Our stabilized liquid formula ensures your guinea pig gets the vitamin C they need to prevent scurvy and support overall health. Tasteless formula can be added to water bottle without changing the flavor.",
            "short_description": "Essential vitamin C for guinea pig health",
            "price": 16.99,
            "compare_at_price": None,
            "cost": 4.80,
            "category": "Small Pet",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1619961534986-5064211a7227?w=600"],
            "tags": ["guinea pig", "vitamin c", "supplements", "scurvy prevention"],
            "pet_type": "small_pet",
            "in_stock": True,
            "stock_quantity": 220,
            "supplier": "CJdropshipping",
            "features": ["Stabilized vitamin C", "Tasteless formula", "Add to water", "Prevents scurvy", "2oz dropper bottle"],
            "ingredients": "Ascorbic Acid (Vitamin C), Purified Water, Natural Stabilizers",
            "rating": 4.9,
            "review_count": 289
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hamster Health & Coat Supplement",
            "slug": "hamster-health-coat-supplement",
            "description": "Support your hamster's shiny coat and overall vitality with our specially formulated supplement. Contains omega fatty acids, biotin, and vitamins to promote healthy fur and skin. Easy-to-feed powder that can be sprinkled on food. Also suitable for gerbils and mice.",
            "short_description": "Coat health supplement for hamsters and small rodents",
            "price": 14.99,
            "compare_at_price": 17.99,
            "cost": 4.20,
            "category": "Small Pet",
            "subcategory": "Supplements",
            "images": ["https://images.unsplash.com/photo-1630173207885-c903abb963f6?w=600"],
            "tags": ["hamster", "gerbil", "coat", "fur health", "supplements"],
            "pet_type": "small_pet",
            "in_stock": True,
            "stock_quantity": 190,
            "supplier": "Spocket",
            "features": ["Omega fatty acids", "Biotin for coat health", "Easy powder format", "Multi-species safe", "60g jar"],
            "ingredients": "Flaxseed Oil Powder, Biotin, Vitamin E, Zinc",
            "rating": 4.6,
            "review_count": 112
        },
        # HOME GOODS - NEW PRODUCTS
        {
            "id": str(uuid.uuid4()),
            "name": "Smart Automatic Pet Feeder",
            "slug": "smart-automatic-feeder",
            "description": "Never miss a feeding with our WiFi-enabled automatic pet feeder. Schedule up to 6 meals per day via smartphone app, control portions precisely, and get notifications when food is dispensed. The twist-lock lid keeps food fresh, and the slow-feed option helps prevent gulping. Works with dry kibble up to 15mm diameter.",
            "short_description": "WiFi smart feeder with app control and portion management",
            "price": 89.99,
            "compare_at_price": 119.99,
            "cost": 35.00,
            "category": "home_goods",
            "subcategory": "Feeders",
            "images": ["https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=600"],
            "tags": ["automatic feeder", "smart", "wifi", "portion control", "schedule"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 75,
            "supplier": "CJdropshipping",
            "features": ["WiFi app control", "6 meals per day", "Portion control", "Twist-lock freshness lid", "4L capacity"],
            "rating": 4.7,
            "review_count": 342
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Stainless Steel Pet Water Fountain",
            "slug": "pet-water-fountain",
            "description": "Encourage healthy hydration with our ultra-quiet stainless steel water fountain. The triple filtration system (foam, carbon, ion exchange) ensures clean, fresh water that entices pets to drink more. Stainless steel is naturally antibacterial and easy to clean. LED water level indicator prevents dry running.",
            "short_description": "3L stainless steel fountain with triple filtration",
            "price": 54.99,
            "compare_at_price": 69.99,
            "cost": 18.00,
            "category": "home_goods",
            "subcategory": "Water Fountains",
            "images": ["https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=600"],
            "tags": ["water fountain", "stainless steel", "filtration", "hydration", "quiet"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 120,
            "supplier": "Spocket",
            "features": ["Triple filtration", "Ultra-quiet pump", "LED water indicator", "3L capacity", "Dishwasher safe"],
            "rating": 4.8,
            "review_count": 456
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Collapsible Travel Pet Crate",
            "slug": "collapsible-travel-crate",
            "description": "The perfect solution for travel, vet visits, or training. Our collapsible crate sets up in seconds with no tools required. The heavy-duty 600D fabric is scratch-resistant and easy to clean, while mesh windows provide ventilation and visibility. Includes removable fleece mat and carrying handles.",
            "short_description": "Portable soft crate with easy setup and fleece mat",
            "price": 64.99,
            "compare_at_price": 84.99,
            "cost": 22.00,
            "category": "home_goods",
            "subcategory": "Crates",
            "images": ["https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=600"],
            "tags": ["crate", "travel", "collapsible", "portable", "training"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 90,
            "supplier": "Zendrop",
            "features": ["Instant setup", "600D scratch-resistant fabric", "Mesh ventilation", "Removable fleece mat", "Carrying handles"],
            "dimensions": "Medium: 30\"L x 21\"W x 23\"H",
            "rating": 4.5,
            "review_count": 287
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Elevated Bamboo Pet Bowl Stand",
            "slug": "elevated-bamboo-bowls",
            "description": "Promote better digestion and reduce neck strain with our elevated bamboo feeding station. The natural bamboo stand is eco-friendly and moisture-resistant. Includes two removable stainless steel bowls (for food and water) that are dishwasher safe. Adjustable height suits pets of different sizes.",
            "short_description": "Eco-friendly bamboo stand with stainless steel bowls",
            "price": 39.99,
            "compare_at_price": 49.99,
            "cost": 12.00,
            "category": "home_goods",
            "subcategory": "Bowls",
            "images": ["https://images.unsplash.com/photo-1567225477277-c8162eb4991d?w=600"],
            "tags": ["bowls", "elevated", "bamboo", "stainless steel", "eco-friendly"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 150,
            "supplier": "CJdropshipping",
            "features": ["Eco-friendly bamboo", "Adjustable height", "Removable SS bowls", "Non-slip feet", "Easy cleaning"],
            "rating": 4.6,
            "review_count": 198
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Self-Warming Pet Mat",
            "slug": "self-warming-pet-mat",
            "description": "Keep your pet cozy without electricity. Our self-warming mat uses a special thermal layer that reflects your pet's body heat, creating a warm resting spot naturally. The non-slip bottom stays in place, and the soft fleece top is machine washable. Perfect for beds, crates, or car travel.",
            "short_description": "No-electricity warming mat with thermal reflection",
            "price": 29.99,
            "compare_at_price": 39.99,
            "cost": 9.00,
            "category": "home_goods",
            "subcategory": "Mats",
            "images": ["https://images.unsplash.com/photo-1574158622682-e40e69881006?w=600"],
            "tags": ["warming mat", "self-heating", "thermal", "cozy", "no electricity"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 200,
            "supplier": "Spocket",
            "features": ["Self-warming technology", "No electricity needed", "Non-slip bottom", "Machine washable", "Portable"],
            "dimensions": "24\" x 18\"",
            "rating": 4.7,
            "review_count": 321
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Interactive Slow Feeder Bowl",
            "slug": "interactive-slow-feeder",
            "description": "Turn mealtime into enrichment time. Our slow feeder bowl features a maze pattern that challenges your pet to work for their food, slowing eating by up to 10x. This helps prevent bloat, improves digestion, and provides mental stimulation. BPA-free and dishwasher safe.",
            "short_description": "Maze bowl that slows eating and provides enrichment",
            "price": 19.99,
            "compare_at_price": 24.99,
            "cost": 5.50,
            "category": "home_goods",
            "subcategory": "Bowls",
            "images": ["https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=600"],
            "tags": ["slow feeder", "anti-gulp", "enrichment", "bloat prevention", "puzzle"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 300,
            "supplier": "CJdropshipping",
            "features": ["Slows eating 10x", "Prevents bloat", "Mental stimulation", "BPA-free", "Dishwasher safe"],
            "rating": 4.5,
            "review_count": 534
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Plush Pet Blanket - Ultra Soft",
            "slug": "plush-pet-blanket",
            "description": "The ultimate in comfort for your furry friend. Our ultra-plush blanket features double-sided softness with fluffy faux fur on one side and cozy sherpa on the other. Machine washable and tumble dry safe. Perfect for couches, beds, or keeping furniture protected.",
            "short_description": "Double-sided luxury blanket with faux fur & sherpa",
            "price": 34.99,
            "compare_at_price": 44.99,
            "cost": 10.00,
            "category": "home_goods",
            "subcategory": "Blankets",
            "images": ["https://images.unsplash.com/photo-1587116861219-230ac19df971?w=600"],
            "tags": ["blanket", "plush", "soft", "sherpa", "cozy"],
            "pet_type": "both",
            "in_stock": True,
            "stock_quantity": 180,
            "supplier": "Zendrop",
            "features": ["Double-sided softness", "Faux fur & sherpa", "Machine washable", "Furniture protector", "Multiple sizes"],
            "dimensions": "Large: 50\" x 60\"",
            "rating": 4.9,
            "review_count": 412
        }
    ]
    
    for product in products:
        product["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.insert_many(products)
    
    # Create admin user
    admin_exists = await db.users.find_one({"email": "admin@calmtails.com"})
    if not admin_exists:
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@calmtails.com",
            "name": "Wildly Ones Admin",
            "password_hash": hash_password("admin123"),
            "is_admin": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_user)
    
    return {"message": f"Seeded {len(products)} products and admin user"}

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Wildly Ones Pet Wellness Store API", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Wildly Ones Pet Wellness"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== WEBSOCKET ROUTES ====================

@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time admin dashboard notifications"""
    await manager.connect(websocket, "admin")
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Can handle client messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "admin")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
