"""WebSocket manager for real-time notifications"""
from fastapi import WebSocket
from typing import List, Dict
import json
import logging

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "admin": [],  # Admin dashboard connections
            "orders": [],  # Order update subscriptions
        }
    
    async def connect(self, websocket: WebSocket, channel: str = "admin"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logging.info(f"WebSocket connected to {channel}. Total: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "admin"):
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            logging.info(f"WebSocket disconnected from {channel}. Total: {len(self.active_connections[channel])}")
    
    async def broadcast(self, message: dict, channel: str = "admin"):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, channel)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logging.error(f"Failed to send personal message: {e}")

# Global connection manager instance
manager = ConnectionManager()

# Notification types
class NotificationType:
    NEW_ORDER = "new_order"
    ORDER_UPDATE = "order_update"
    LOW_STOCK = "low_stock"
    NEW_CUSTOMER = "new_customer"
    NEW_REVIEW = "new_review"
    REVENUE_UPDATE = "revenue_update"

async def notify_new_order(order_data: dict):
    """Notify admins of new order"""
    await manager.broadcast({
        "type": NotificationType.NEW_ORDER,
        "data": {
            "order_number": order_data.get("order_number"),
            "total": order_data.get("total"),
            "items_count": len(order_data.get("items", [])),
            "customer_email": order_data.get("email"),
            "timestamp": order_data.get("created_at")
        }
    }, "admin")

async def notify_order_update(order_id: str, status: str, order_number: str):
    """Notify of order status change"""
    await manager.broadcast({
        "type": NotificationType.ORDER_UPDATE,
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "status": status
        }
    }, "admin")

async def notify_low_stock(product_data: dict):
    """Notify admins of low stock"""
    await manager.broadcast({
        "type": NotificationType.LOW_STOCK,
        "data": {
            "product_id": product_data.get("id"),
            "product_name": product_data.get("name"),
            "stock_quantity": product_data.get("stock_quantity")
        }
    }, "admin")

async def notify_new_customer(customer_data: dict):
    """Notify admins of new customer signup"""
    await manager.broadcast({
        "type": NotificationType.NEW_CUSTOMER,
        "data": {
            "customer_id": customer_data.get("id"),
            "email": customer_data.get("email"),
            "name": customer_data.get("name"),
            "timestamp": customer_data.get("created_at")
        }
    }, "admin")

async def notify_revenue_update(amount: float, order_number: str):
    """Notify of revenue update"""
    await manager.broadcast({
        "type": NotificationType.REVENUE_UPDATE,
        "data": {
            "amount": amount,
            "order_number": order_number
        }
    }, "admin")
