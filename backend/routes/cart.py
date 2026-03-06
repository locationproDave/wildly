"""Cart routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import uuid

from core.database import db
from models.schemas import CartItem

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/{session_id}", response_model=dict)
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


@router.post("/{session_id}/add", response_model=dict)
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
    
    product = await db.products.find_one({"id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
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


@router.post("/{session_id}/update", response_model=dict)
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


@router.delete("/{session_id}/item/{product_id}", response_model=dict)
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


@router.delete("/{session_id}", response_model=dict)
async def clear_cart(session_id: str):
    await db.carts.update_one(
        {"session_id": session_id},
        {"$set": {"items": [], "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Cart cleared"}
