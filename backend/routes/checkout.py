"""Checkout and payment routes"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import asyncio
import logging

from core.database import db
from core.config import STRIPE_API_KEY
from core.websocket import notify_new_order, notify_revenue_update, notify_low_stock
from models.schemas import CheckoutRequest
from services.auth import get_current_user
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest
)

router = APIRouter(tags=["Checkout"])


async def award_loyalty_points(user_id: str, amount: float, order_id: str):
    """Award loyalty points based on order amount"""
    points = int(amount)  # 1 point per dollar
    
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
    
    new_lifetime = loyalty.get("lifetime_points", 0) + points
    new_tier = "bronze"
    if new_lifetime >= 1000:
        new_tier = "platinum"
    elif new_lifetime >= 500:
        new_tier = "gold"
    elif new_lifetime >= 200:
        new_tier = "silver"
    
    await db.loyalty_points.update_one(
        {"user_id": user_id},
        {
            "$inc": {"points": points, "lifetime_points": points},
            "$set": {"tier": new_tier, "updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "points": points,
        "transaction_type": "earned",
        "description": f"Earned from order",
        "order_id": order_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.points_transactions.insert_one(transaction)


async def complete_referral(user_id: str, order_id: str):
    """Complete a pending referral for a user's first order"""
    referral = await db.referrals.find_one({
        "referee_id": user_id,
        "status": "pending"
    })
    
    if referral:
        await db.referrals.update_one(
            {"id": referral["id"]},
            {
                "$set": {
                    "status": "completed",
                    "order_id": order_id,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Award referrer credit
        await db.users.update_one(
            {"id": referral["referrer_id"]},
            {"$inc": {"referral_credits": referral["referrer_reward"]}}
        )


async def send_order_confirmation_email(order: dict):
    """Send order confirmation email"""
    # Placeholder - integrate with Resend when key is available
    logging.info(f"Order confirmation would be sent to {order.get('email')}")


@router.post("/checkout", response_model=dict)
async def create_checkout(
    checkout_data: CheckoutRequest, 
    request: Request, 
    user: Optional[dict] = Depends(get_current_user)
):
    cart = await db.carts.find_one({"session_id": checkout_data.cart_session_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
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
    
    order_id = str(uuid.uuid4())
    order_number = f"WO-{str(uuid.uuid4())[:8].upper()}"
    
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
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"stripe_session_id": session.session_id}}
    )
    
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


@router.get("/checkout/status/{session_id}", response_model=dict)
async def get_checkout_status(session_id: str, request: Request):
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
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
        
        order = await db.orders.find_one({"stripe_session_id": session_id})
        if order:
            await db.carts.delete_many({"user_id": order.get("user_id")})
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }


@router.post("/webhook/stripe")
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
                
                order = await db.orders.find_one({"id": order_id}, {"_id": 0})
                if order:
                    asyncio.create_task(send_order_confirmation_email(order))
                    asyncio.create_task(notify_new_order(order))
                    asyncio.create_task(notify_revenue_update(order.get("total", 0), order.get("order_number", "")))
                    
                    for item in order.get("items", []):
                        product = await db.products.find_one({"id": item.get("product_id")}, {"_id": 0})
                        if product and product.get("stock_quantity", 100) <= 10:
                            asyncio.create_task(notify_low_stock(product))
                    
                    if order.get("user_id"):
                        await award_loyalty_points(order["user_id"], order["total"], order_id)
                        await complete_referral(order["user_id"], order_id)
        
        return {"received": True}
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return {"received": True, "error": str(e)}
