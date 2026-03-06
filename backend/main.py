"""
Wildly Ones Pet Wellness Store - Main Application Entry Point
Refactored modular architecture
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from core.database import client
from core.websocket import manager

# Import route modules
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.checkout import router as checkout_router
from routes.orders import router as orders_router
from routes.admin import router as admin_router
from routes.agents import router as agents_router
from routes.promotions import router as promotions_router
from routes.reviews import router as reviews_router
from routes.referrals import router as referrals_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="Wildly Ones Pet Wellness Store")

# Include all routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(checkout_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(promotions_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(referrals_router, prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/api/")
async def root():
    return {"message": "Wildly Ones Pet Wellness Store API", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Wildly Ones Pet Wellness"}

# WebSocket endpoint
@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time admin dashboard notifications"""
    await manager.connect(websocket, "admin")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "admin")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
