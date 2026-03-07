"""
Shopify Storefront API Service
Fetches products from Shopify store using the Storefront API
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/shop", tags=["shopify"])

SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")
SHOPIFY_STOREFRONT_TOKEN = os.environ.get("SHOPIFY_STOREFRONT_TOKEN")

def get_storefront_url():
    return f"https://{SHOPIFY_STORE}/api/2024-01/graphql.json"

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": SHOPIFY_STOREFRONT_TOKEN
    }

async def graphql_query(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Shopify Storefront API"""
    if not SHOPIFY_STORE or not SHOPIFY_STOREFRONT_TOKEN:
        raise HTTPException(status_code=500, detail="Shopify credentials not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            get_storefront_url(),
            json={"query": query, "variables": variables or {}},
            headers=get_headers(),
            timeout=30.0
        )
        
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Shopify authentication failed - check your Storefront Access Token")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Shopify API error: {response.text}")
        
        data = response.json()
        if "errors" in data:
            raise HTTPException(status_code=400, detail=data["errors"])
        
        return data.get("data", {})


@router.get("/products")
async def get_products(first: int = 20, after: Optional[str] = None):
    """Fetch products from Shopify store"""
    query = """
    query GetProducts($first: Int!, $after: String) {
        products(first: $first, after: $after) {
            pageInfo {
                hasNextPage
                endCursor
            }
            edges {
                node {
                    id
                    title
                    handle
                    description
                    descriptionHtml
                    productType
                    tags
                    vendor
                    createdAt
                    updatedAt
                    priceRange {
                        minVariantPrice {
                            amount
                            currencyCode
                        }
                        maxVariantPrice {
                            amount
                            currencyCode
                        }
                    }
                    compareAtPriceRange {
                        minVariantPrice {
                            amount
                            currencyCode
                        }
                        maxVariantPrice {
                            amount
                            currencyCode
                        }
                    }
                    images(first: 5) {
                        edges {
                            node {
                                id
                                url
                                altText
                                width
                                height
                            }
                        }
                    }
                    variants(first: 10) {
                        edges {
                            node {
                                id
                                title
                                sku
                                availableForSale
                                price {
                                    amount
                                    currencyCode
                                }
                                compareAtPrice {
                                    amount
                                    currencyCode
                                }
                                selectedOptions {
                                    name
                                    value
                                }
                            }
                        }
                    }
                    availableForSale
                }
            }
        }
    }
    """
    
    data = await graphql_query(query, {"first": first, "after": after})
    products_data = data.get("products", {})
    
    # Transform to simpler format
    products = []
    for edge in products_data.get("edges", []):
        node = edge["node"]
        products.append({
            "id": node["id"],
            "title": node["title"],
            "handle": node["handle"],
            "description": node["description"],
            "descriptionHtml": node["descriptionHtml"],
            "productType": node["productType"],
            "tags": node["tags"],
            "vendor": node["vendor"],
            "availableForSale": node["availableForSale"],
            "priceRange": node["priceRange"],
            "compareAtPriceRange": node["compareAtPriceRange"],
            "images": [img["node"] for img in node.get("images", {}).get("edges", [])],
            "variants": [var["node"] for var in node.get("variants", {}).get("edges", [])],
            "createdAt": node["createdAt"],
            "updatedAt": node["updatedAt"]
        })
    
    return {
        "products": products,
        "pageInfo": products_data.get("pageInfo", {})
    }


@router.get("/products/{handle}")
async def get_product_by_handle(handle: str):
    """Fetch a single product by handle"""
    query = """
    query GetProductByHandle($handle: String!) {
        productByHandle(handle: $handle) {
            id
            title
            handle
            description
            descriptionHtml
            productType
            tags
            vendor
            createdAt
            updatedAt
            priceRange {
                minVariantPrice {
                    amount
                    currencyCode
                }
                maxVariantPrice {
                    amount
                    currencyCode
                }
            }
            compareAtPriceRange {
                minVariantPrice {
                    amount
                    currencyCode
                }
            }
            images(first: 10) {
                edges {
                    node {
                        id
                        url
                        altText
                        width
                        height
                    }
                }
            }
            variants(first: 20) {
                edges {
                    node {
                        id
                        title
                        sku
                        availableForSale
                        price {
                            amount
                            currencyCode
                        }
                        compareAtPrice {
                            amount
                            currencyCode
                        }
                        selectedOptions {
                            name
                            value
                        }
                        quantityAvailable
                    }
                }
            }
            availableForSale
            options {
                id
                name
                values
            }
        }
    }
    """
    
    data = await graphql_query(query, {"handle": handle})
    product = data.get("productByHandle")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product["id"],
        "title": product["title"],
        "handle": product["handle"],
        "description": product["description"],
        "descriptionHtml": product["descriptionHtml"],
        "productType": product["productType"],
        "tags": product["tags"],
        "vendor": product["vendor"],
        "availableForSale": product["availableForSale"],
        "priceRange": product["priceRange"],
        "compareAtPriceRange": product["compareAtPriceRange"],
        "images": [img["node"] for img in product.get("images", {}).get("edges", [])],
        "variants": [var["node"] for var in product.get("variants", {}).get("edges", [])],
        "options": product.get("options", []),
        "createdAt": product["createdAt"],
        "updatedAt": product["updatedAt"]
    }


@router.get("/collections")
async def get_collections(first: int = 20):
    """Fetch collections from Shopify store"""
    query = """
    query GetCollections($first: Int!) {
        collections(first: $first) {
            edges {
                node {
                    id
                    title
                    handle
                    description
                    image {
                        url
                        altText
                    }
                }
            }
        }
    }
    """
    
    data = await graphql_query(query, {"first": first})
    collections = [edge["node"] for edge in data.get("collections", {}).get("edges", [])]
    
    return {"collections": collections}
