"""Product routes"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from core.database import db

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[dict])
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


@router.get("/featured", response_model=List[dict])
async def get_featured_products():
    products = await db.products.find(
        {"in_stock": True},
        {"_id": 0}
    ).sort("rating", -1).limit(8).to_list(8)
    return products


@router.get("/bestsellers", response_model=List[dict])
async def get_bestsellers():
    """Get best-selling products sorted by review count and rating"""
    products = await db.products.find(
        {"in_stock": True},
        {"_id": 0}
    ).sort([("review_count", -1), ("rating", -1)]).limit(8).to_list(8)
    return products


@router.get("/categories", response_model=List[str])
async def get_categories():
    categories = await db.products.distinct("category")
    return categories


@router.get("/{slug}", response_model=dict)
async def get_product(slug: str):
    product = await db.products.find_one({"slug": slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
