"""Core module exports"""
from .database import db, client
from .config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    EMERGENT_LLM_KEY, STRIPE_API_KEY, PAYPAL_CLIENT_ID,
    PAYPAL_CLIENT_SECRET, PAYPAL_MODE, RESEND_API_KEY,
    SENDER_EMAIL, TRACK17_API_KEY
)
from .websocket import (
    manager, ConnectionManager, NotificationType,
    notify_new_order, notify_order_update, notify_low_stock,
    notify_new_customer, notify_revenue_update
)

__all__ = [
    'db', 'client',
    'JWT_SECRET', 'JWT_ALGORITHM', 'JWT_EXPIRATION_HOURS',
    'EMERGENT_LLM_KEY', 'STRIPE_API_KEY', 'PAYPAL_CLIENT_ID',
    'PAYPAL_CLIENT_SECRET', 'PAYPAL_MODE', 'RESEND_API_KEY',
    'SENDER_EMAIL', 'TRACK17_API_KEY',
    'manager', 'ConnectionManager', 'NotificationType',
    'notify_new_order', 'notify_order_update', 'notify_low_stock',
    'notify_new_customer', 'notify_revenue_update'
]
