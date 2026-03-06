from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
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

# Create the main app
app = FastAPI(title="CalmTails Pet Wellness Store")

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

class AgentQuery(BaseModel):
    query: str
    agent_type: Literal["product_sourcing", "due_diligence", "copywriter", "seo_content", "performance_marketing", "email_marketing", "customer_service"]
    session_id: Optional[str] = None

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
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "is_admin": False,
            "discount_code": discount_code
        },
        "message": f"Welcome to CalmTails! Your exclusive discount code is: {discount_code} (15% off your first order)"
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
        if pet_type in ["reptile", "bird", "rabbit", "fish", "small_pet"]:
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
    
    shipping_cost = 0.0 if subtotal >= 50 else 5.99
    tax = round(subtotal * 0.08, 2)  # 8% tax
    total = round(subtotal + shipping_cost + tax, 2)
    
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
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total,
        "shipping_address": checkout_data.shipping_address.model_dump() if checkout_data.shipping_address else None,
        "status": "pending",
        "payment_status": "pending",
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
        
        return {"received": True}
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return {"received": True, "error": str(e)}

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

@api_router.post("/admin/products", response_model=dict)
async def create_product(product: Product, user: dict = Depends(require_admin)):
    product_dict = product.model_dump()
    await db.products.insert_one(product_dict)
    return {"message": "Product created", "id": product_dict["id"]}

@api_router.put("/admin/products/{product_id}", response_model=dict)
async def update_product(product_id: str, product: Product, user: dict = Depends(require_admin)):
    product_dict = product.model_dump()
    result = await db.products.update_one({"id": product_id}, {"$set": product_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated"}

@api_router.delete("/admin/products/{product_id}", response_model=dict)
async def delete_product(product_id: str, user: dict = Depends(require_admin)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

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
            "category": "Beds & Blankets",
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
            "category": "Beds & Blankets",
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
            "category": "Calming Aids",
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
            "category": "Calming Aids",
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
            "category": "Beds & Blankets",
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
            "name": "CalmTails Admin",
            "password_hash": hash_password("admin123"),
            "is_admin": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_user)
    
    return {"message": f"Seeded {len(products)} products and admin user"}

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "CalmTails Pet Wellness Store API", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CalmTails Pet Wellness"}

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
