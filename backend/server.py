from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'petpulse_default_secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI(title="PetPulse Sourcing Agent")

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
    discount_code: Optional[str] = None
    created_at: str

class ProductEvaluation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    product_name: str
    supplier: str
    supplier_rating: Optional[str] = None
    us_warehouse: str
    supplier_cost: str
    estimated_shipping: str
    landed_cost: str
    recommended_retail_price: str
    gross_margin: str
    emotional_angle: str
    best_ad_hook: str
    safety_check: str
    risk_flags: str
    verdict: str
    verdict_rationale: str
    raw_data: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SearchQuery(BaseModel):
    query: str
    session_id: Optional[str] = None

class SearchHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    query: str
    response: str
    products_found: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    messages: List[Dict[str, str]] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
    return f"PETPULSE{str(uuid.uuid4())[:8].upper()}"

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

# ==================== SYSTEM PROMPT ====================

SYSTEM_PROMPT = """You are a specialist product sourcing agent for PetPulse, a premium pet wellness dropshipping business. Your job is to identify winning products that meet strict sourcing quality standards.

BUSINESS CONTEXT:
- Store niche: Premium pet wellness and anxiety relief products (dogs and cats)
- Target retail price range: $28–$99 per product
- Target gross margin: 65% minimum after all costs
- Primary markets: United States, Canada, Australia
- Brand positioning: Premium, trustworthy, science-adjacent — NOT cheap or generic

APPROVED SUPPLIER PLATFORMS:
1. CJdropshipping.com — Priority. US warehouse products only. Check product rating (min 4.5 stars), processing time (under 3 days), supplier score.
2. Zendrop.com — US-based fulfillment. Strong for branded pet products and consumables with verified lab testing.
3. Spocket.co — Focus on US and EU suppliers. All suppliers are pre-vetted. Good for premium positioning.
4. Salsify-listed brands via Faire.com — For semi-wholesale drop relationships with established pet brands.

NEVER suggest products from:
- Direct AliExpress suppliers with no US warehouse
- Unknown suppliers with fewer than 50 orders or under 4.0 rating
- Products making unverified medical claims (e.g., "cures anxiety," "treats arthritis")
- Any product flagged for safety recalls (CPSC and FDA databases)
- CBD products unless supplier provides Certificate of Analysis (COA) from third-party lab

PRODUCT EVALUATION CRITERIA (score each):
1. Demand signal: Is this category trending on TikTok, Pinterest, or Google Trends?
2. Emotional hook: Does this solve a pain that makes pet owners feel guilty if they don't buy?
3. Visual appeal: Would this photograph well for social media? Is it photogenic?
4. Supplier reliability: How many orders fulfilled? On-time rate?
5. Margin math: Cost + shipping to US = landed cost. Retail price / landed cost must be 2.8x minimum.
6. Return risk: Avoid sizing items (clothes, harnesses) unless generous size guide. Avoid fragile items.
7. Repeat purchase potential: Does this lead to consumables/accessories for second purchase?

OUTPUT FORMAT — For each product recommended:

PRODUCT NAME: [exact name as listed on supplier platform]
SUPPLIER: [CJdropshipping / Zendrop / Spocket + product URL if found]
SUPPLIER RATING: [star rating and number of orders fulfilled]
US WAREHOUSE: [Yes / No / Ships from: location]
SUPPLIER COST: [$X including packaging]
ESTIMATED US SHIPPING COST: [$X via which carrier]
LANDED COST: [$X total]
RECOMMENDED RETAIL PRICE: [$X]
GROSS MARGIN: [X%]
EMOTIONAL ANGLE: [The specific fear or love that drives purchase — one sentence]
BEST AD HOOK: [Opening line for TikTok or Meta ad — max 10 words]
SAFETY/CERTIFICATION CHECK: [Any certifications found, or "No issues found"]
RISK FLAGS: [Any concerns — or "None identified"]
VERDICT: [RECOMMEND / INVESTIGATE FURTHER / SKIP] + one-sentence rationale

When asked for product ideas, generate 8–12 options ranked from highest to lowest recommendation confidence.

Be helpful, warm, and professional. Use conversational language while maintaining expertise."""

# ==================== AI CHAT ====================

import asyncio

async def get_ai_response(query: str, session_id: str, chat_history: List[Dict[str, str]] = None) -> str:
    """Get response from Claude Opus 4.6 with fallback"""
    
    # List of models to try in order
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
                session_id=session_id,
                system_message=SYSTEM_PROMPT
            )
            chat.with_model(provider, model)
            
            # Build context from history
            context = ""
            if chat_history:
                for msg in chat_history[-6:]:  # Last 6 messages for context (reduced for speed)
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n\n"
            
            full_query = f"{context}User: {query}" if context else query
            
            user_message = UserMessage(text=full_query)
            
            # Add timeout of 60 seconds
            try:
                response = await asyncio.wait_for(
                    chat.send_message(user_message),
                    timeout=60.0
                )
                logging.info(f"AI response from {provider}/{model} successful")
                return response
            except asyncio.TimeoutError:
                logging.warning(f"Timeout with {provider}/{model}, trying next...")
                last_error = f"Timeout with {model}"
                continue
                
        except Exception as e:
            logging.warning(f"Error with {provider}/{model}: {str(e)}")
            last_error = str(e)
            continue
    
    # If all models fail, raise error with helpful message
    logging.error(f"All AI models failed. Last error: {last_error}")
    
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
            "discount_code": discount_code
        },
        "message": f"Welcome! Your exclusive discount code is: {discount_code} (15% off your first month)"
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
            "discount_code": user.get("discount_code")
        }
    }

@api_router.get("/auth/me", response_model=dict)
async def get_me(user: dict = Depends(require_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "discount_code": user.get("discount_code")
    }

# ==================== CHAT ROUTES ====================

@api_router.post("/chat/send", response_model=dict)
async def send_chat_message(query: SearchQuery, user: Optional[dict] = Depends(get_current_user)):
    session_id = query.session_id or str(uuid.uuid4())
    user_id = user["id"] if user else None
    
    # Get or create session
    session = await db.chat_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        session = {
            "id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_sessions.insert_one(session)
    
    # Add user message
    user_message = {
        "role": "user",
        "content": query.query,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Get AI response
    response = await get_ai_response(query.query, session_id, session.get("messages", []))
    
    # Add assistant message
    assistant_message = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Update session
    await db.chat_sessions.update_one(
        {"id": session_id},
        {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Save to search history
    history_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "query": query.query,
        "response": response[:500] + "..." if len(response) > 500 else response,
        "products_found": response.lower().count("product name:"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.search_history.insert_one(history_doc)
    
    return {
        "session_id": session_id,
        "response": response,
        "message": assistant_message
    }

@api_router.get("/chat/sessions", response_model=List[dict])
async def get_chat_sessions(user: dict = Depends(require_user)):
    sessions = await db.chat_sessions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(50)
    return sessions

@api_router.get("/chat/session/{session_id}", response_model=dict)
async def get_chat_session(session_id: str, user: Optional[dict] = Depends(get_current_user)):
    session = await db.chat_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@api_router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str, user: dict = Depends(require_user)):
    result = await db.chat_sessions.delete_one({"id": session_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}

# ==================== PRODUCT ROUTES ====================

@api_router.post("/products/save", response_model=dict)
async def save_product(product: ProductEvaluation, user: dict = Depends(require_user)):
    product_dict = product.model_dump()
    product_dict["user_id"] = user["id"]
    product_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.saved_products.insert_one(product_dict)
    return {"message": "Product saved", "product_id": product_dict["id"]}

@api_router.get("/products/saved", response_model=List[dict])
async def get_saved_products(user: dict = Depends(require_user)):
    products = await db.saved_products.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return products

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(require_user)):
    result = await db.saved_products.delete_one({"id": product_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

@api_router.patch("/products/{product_id}/verdict")
async def update_verdict(product_id: str, verdict: str, user: dict = Depends(require_user)):
    if verdict not in ["RECOMMEND", "INVESTIGATE FURTHER", "SKIP"]:
        raise HTTPException(status_code=400, detail="Invalid verdict")
    
    result = await db.saved_products.update_one(
        {"id": product_id, "user_id": user["id"]},
        {"$set": {"verdict": verdict}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Verdict updated"}

# ==================== HISTORY ROUTES ====================

@api_router.get("/history", response_model=List[dict])
async def get_search_history(user: dict = Depends(require_user)):
    history = await db.search_history.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return history

@api_router.delete("/history/{history_id}")
async def delete_history_item(history_id: str, user: dict = Depends(require_user)):
    result = await db.search_history.delete_one({"id": history_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="History item not found")
    return {"message": "History item deleted"}

# ==================== STATS ROUTES ====================

@api_router.get("/stats", response_model=dict)
async def get_user_stats(user: dict = Depends(require_user)):
    saved_count = await db.saved_products.count_documents({"user_id": user["id"]})
    searches_count = await db.search_history.count_documents({"user_id": user["id"]})
    recommend_count = await db.saved_products.count_documents({"user_id": user["id"], "verdict": "RECOMMEND"})
    
    return {
        "saved_products": saved_count,
        "total_searches": searches_count,
        "recommended_products": recommend_count
    }

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "PetPulse Sourcing Agent API", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PetPulse Sourcing Agent"}

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
