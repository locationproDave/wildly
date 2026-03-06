"""Order routes"""
from fastapi import APIRouter, Depends
from typing import List

from core.database import db
from services.auth import require_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[dict])
async def get_user_orders(user: dict = Depends(require_user)):
    orders = await db.orders.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return orders


@router.get("/{order_number}", response_model=dict)
async def get_order_by_number(order_number: str, user: dict = Depends(require_user)):
    order = await db.orders.find_one(
        {"order_number": order_number, "user_id": user["id"]},
        {"_id": 0}
    )
    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    return order
