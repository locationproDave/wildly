"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid
import asyncio

from core.database import db
from core.websocket import notify_new_customer
from models.schemas import UserCreate, UserLogin
from services.auth import (
    hash_password, verify_password, create_token, 
    generate_discount_code, require_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
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


@router.post("/login", response_model=dict)
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


@router.get("/me", response_model=dict)
async def get_me(user: dict = Depends(require_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "is_admin": user.get("is_admin", False),
        "discount_code": user.get("discount_code")
    }
