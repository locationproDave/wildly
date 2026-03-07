# shopify_service.py
# FastAPI service for Shopify Admin API integration

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/shop", tags=["shop"])

# Shopify credentials
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "wildly-ones.myshopify.com")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
SHOPIFY_API_VERSION = "2024-01"

# Token cache
_token_cache = {
    "access_token": None,
    "expires_at": None
}


async def get_access_token() -> str:
    """Get or refresh the Shopify Admin API access token"""
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            return _token_cache["access_token"]
    
    # Generate new token
    if not SHOPIFY_CLIENT_ID or not SHOPIFY_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Shopify credentials not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{SHOPIFY_STORE}/admin/oauth/access_token",
            json={
                "client_id": SHOPIFY_CLIENT_ID,
                "client_secret": SHOPIFY_CLIENT_SECRET,
                "grant_type": "client_credentials"
            },
            timeout=15.0
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to get Shopify access token")
    
    data = response.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = datetime.now() + timedelta(seconds=data.get("expires_in", 86400) - 300)
    
    return _token_cache["access_token"]


async def shopify_request(endpoint: str, method: str = "GET", json_data: dict = None) -> dict:
    """Make a request to Shopify Admin API"""
    token = await get_access_token()
    url = f"https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/{endpoint}"
    
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, timeout=15.0)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=json_data, timeout=15.0)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=json_data, timeout=15.0)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers, timeout=15.0)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
    
    if response.status_code not in [200, 201]:
        raise HTTPException(status_code=response.status_code, detail=f"Shopify API error: {response.text}")
    
    return response.json()


# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────
@router.get("/products")
async def get_products(limit: int = 50, page_info: Optional[str] = None):
    """Fetch products from Shopify"""
    endpoint = f"products.json?limit={limit}"
    if page_info:
        endpoint += f"&page_info={page_info}"
    
    data = await shopify_request(endpoint)
    return {"products": data.get("products", [])}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Fetch a single product by ID"""
    data = await shopify_request(f"products/{product_id}.json")
    if not data.get("product"):
        raise HTTPException(status_code=404, detail="Product not found")
    return data["product"]


@router.get("/products/handle/{handle}")
async def get_product_by_handle(handle: str):
    """Fetch a product by handle"""
    data = await shopify_request(f"products.json?handle={handle}")
    products = data.get("products", [])
    if not products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[0]


# ─────────────────────────────────────────────
# Collections
# ─────────────────────────────────────────────
@router.get("/collections")
async def get_collections(limit: int = 50):
    """Fetch all collections"""
    # Get custom collections
    custom = await shopify_request(f"custom_collections.json?limit={limit}")
    # Get smart collections
    smart = await shopify_request(f"smart_collections.json?limit={limit}")
    
    collections = custom.get("custom_collections", []) + smart.get("smart_collections", [])
    return {"collections": collections}


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: str):
    """Fetch a single collection"""
    try:
        data = await shopify_request(f"custom_collections/{collection_id}.json")
        return data.get("custom_collection")
    except:
        data = await shopify_request(f"smart_collections/{collection_id}.json")
        return data.get("smart_collection")


@router.get("/collections/{collection_id}/products")
async def get_collection_products(collection_id: str, limit: int = 50):
    """Fetch products in a collection"""
    data = await shopify_request(f"products.json?collection_id={collection_id}&limit={limit}")
    return {"products": data.get("products", [])}


# ─────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────
@router.get("/inventory")
async def get_inventory_levels(limit: int = 50):
    """Fetch inventory levels"""
    data = await shopify_request(f"inventory_levels.json?limit={limit}")
    return {"inventory_levels": data.get("inventory_levels", [])}


# ─────────────────────────────────────────────
# Orders (for sourcing agent)
# ─────────────────────────────────────────────
@router.get("/orders")
async def get_orders(limit: int = 50, status: str = "any"):
    """Fetch orders"""
    data = await shopify_request(f"orders.json?limit={limit}&status={status}")
    return {"orders": data.get("orders", [])}


@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Fetch a single order"""
    data = await shopify_request(f"orders/{order_id}.json")
    return data.get("order")


# ─────────────────────────────────────────────
# Product Sync (for sourcing agent to import)
# ─────────────────────────────────────────────
class ProductCreate(BaseModel):
    title: str
    body_html: Optional[str] = ""
    vendor: Optional[str] = ""
    product_type: Optional[str] = ""
    tags: Optional[List[str]] = []
    variants: Optional[List[dict]] = []
    images: Optional[List[dict]] = []


@router.post("/products")
async def create_product(product: ProductCreate):
    """Create a new product in Shopify"""
    product_data = {
        "product": {
            "title": product.title,
            "body_html": product.body_html,
            "vendor": product.vendor,
            "product_type": product.product_type,
            "tags": ",".join(product.tags) if product.tags else "",
            "variants": product.variants or [{"price": "0.00"}],
            "images": product.images or []
        }
    }
    
    data = await shopify_request("products.json", method="POST", json_data=product_data)
    return data.get("product")


@router.put("/products/{product_id}")
async def update_product(product_id: str, product: ProductCreate):
    """Update an existing product"""
    product_data = {
        "product": {
            "id": product_id,
            "title": product.title,
            "body_html": product.body_html,
            "vendor": product.vendor,
            "product_type": product.product_type,
            "tags": ",".join(product.tags) if product.tags else ""
        }
    }
    
    data = await shopify_request(f"products/{product_id}.json", method="PUT", json_data=product_data)
    return data.get("product")


@router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    await shopify_request(f"products/{product_id}.json", method="DELETE")
    return {"success": True, "deleted_id": product_id}


# ─────────────────────────────────────────────
# Store Info
# ─────────────────────────────────────────────
@router.get("/shop")
async def get_shop_info():
    """Get shop information"""
    data = await shopify_request("shop.json")
    return data.get("shop")
