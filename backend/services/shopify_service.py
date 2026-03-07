# shopify_service.py
# FastAPI service for Shopify Storefront API integration
# Add this to your existing FastAPI app
#
# Install deps: pip install httpx fastapi python-dotenv

import os
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/shop", tags=["shop"])

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "wildly-ones.myshopify.com")
SHOPIFY_STOREFRONT_TOKEN = os.getenv("SHOPIFY_STOREFRONT_TOKEN")
SHOPIFY_API_VERSION = "2025-01"
STOREFRONT_URL = f"https://{SHOPIFY_STORE}/api/{SHOPIFY_API_VERSION}/graphql.json"

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Storefront-Access-Token": SHOPIFY_STOREFRONT_TOKEN or "",
}


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
async def shopify_query(query: str, variables: dict = {}) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            STOREFRONT_URL,
            headers=HEADERS,
            json={"query": query, "variables": variables},
            timeout=15.0,
        )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Shopify API error")
    data = response.json()
    if "errors" in data:
        raise HTTPException(status_code=400, detail=data["errors"])
    return data["data"]


# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────
@router.get("/products")
async def get_products(limit: int = 20, cursor: Optional[str] = None):
    """Fetch paginated products."""
    after = f', after: "{cursor}"' if cursor else ""
    query = f"""
    {{
      products(first: {limit}{after}) {{
        pageInfo {{ hasNextPage endCursor }}
        edges {{
          node {{
            id
            title
            handle
            description
            priceRange {{
              minVariantPrice {{ amount currencyCode }}
            }}
            images(first: 3) {{
              edges {{ node {{ url altText }} }}
            }}
            variants(first: 10) {{
              edges {{
                node {{
                  id
                  title
                  price {{ amount currencyCode }}
                  availableForSale
                  selectedOptions {{ name value }}
                }}
              }}
            }}
            tags
            vendor
          }}
        }}
      }}
    }}
    """
    data = await shopify_query(query)
    products = [edge["node"] for edge in data["products"]["edges"]]
    page_info = data["products"]["pageInfo"]
    return {"products": products, "pageInfo": page_info}


@router.get("/products/{handle}")
async def get_product(handle: str):
    """Fetch a single product by handle."""
    query = """
    query GetProduct($handle: String!) {
      productByHandle(handle: $handle) {
        id
        title
        handle
        descriptionHtml
        priceRange {
          minVariantPrice { amount currencyCode }
          maxVariantPrice { amount currencyCode }
        }
        images(first: 10) {
          edges { node { url altText width height } }
        }
        variants(first: 20) {
          edges {
            node {
              id
              title
              price { amount currencyCode }
              compareAtPrice { amount currencyCode }
              availableForSale
              quantityAvailable
              selectedOptions { name value }
            }
          }
        }
        options { id name values }
        tags
        vendor
        productType
      }
    }
    """
    data = await shopify_query(query, {"handle": handle})
    if not data.get("productByHandle"):
        raise HTTPException(status_code=404, detail="Product not found")
    return data["productByHandle"]


# ─────────────────────────────────────────────
# Collections
# ─────────────────────────────────────────────
@router.get("/collections")
async def get_collections(limit: int = 10):
    """Fetch all collections."""
    query = f"""
    {{
      collections(first: {limit}) {{
        edges {{
          node {{
            id
            title
            handle
            description
            image {{ url altText }}
            products(first: 4) {{
              edges {{
                node {{
                  id title handle
                  priceRange {{ minVariantPrice {{ amount currencyCode }} }}
                  images(first: 1) {{ edges {{ node {{ url altText }} }} }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    data = await shopify_query(query)
    return [edge["node"] for edge in data["collections"]["edges"]]


@router.get("/collections/{handle}/products")
async def get_collection_products(handle: str, limit: int = 20):
    """Fetch products in a specific collection."""
    query = """
    query CollectionProducts($handle: String!, $limit: Int!) {
      collectionByHandle(handle: $handle) {
        title
        products(first: $limit) {
          edges {
            node {
              id title handle
              priceRange { minVariantPrice { amount currencyCode } }
              images(first: 2) { edges { node { url altText } } }
              variants(first: 5) {
                edges {
                  node {
                    id title
                    price { amount currencyCode }
                    availableForSale
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    data = await shopify_query(query, {"handle": handle, "limit": limit})
    if not data.get("collectionByHandle"):
        raise HTTPException(status_code=404, detail="Collection not found")
    collection = data["collectionByHandle"]
    products = [edge["node"] for edge in collection["products"]["edges"]]
    return {"collection": collection["title"], "products": products}


# ─────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────
class CartCreateInput(BaseModel):
    variantId: str
    quantity: int = 1


class CartAddInput(BaseModel):
    cartId: str
    variantId: str
    quantity: int = 1


class CartUpdateInput(BaseModel):
    cartId: str
    lineId: str
    quantity: int


class CartRemoveInput(BaseModel):
    cartId: str
    lineIds: list[str]


@router.post("/cart/create")
async def create_cart(item: CartCreateInput):
    """Create a new cart with one item."""
    query = """
    mutation CartCreate($variantId: ID!, $quantity: Int!) {
      cartCreate(input: {
        lines: [{ quantity: $quantity merchandiseId: $variantId }]
      }) {
        cart {
          id
          checkoutUrl
          totalQuantity
          cost {
            totalAmount { amount currencyCode }
            subtotalAmount { amount currencyCode }
          }
          lines(first: 20) {
            edges {
              node {
                id quantity
                merchandise {
                  ... on ProductVariant {
                    id title price { amount currencyCode }
                    product { title handle images(first:1) { edges { node { url } } } }
                  }
                }
              }
            }
          }
        }
        userErrors { field message }
      }
    }
    """
    data = await shopify_query(query, {"variantId": item.variantId, "quantity": item.quantity})
    errors = data["cartCreate"].get("userErrors", [])
    if errors:
        raise HTTPException(status_code=400, detail=errors)
    return data["cartCreate"]["cart"]


@router.post("/cart/add")
async def add_to_cart(item: CartAddInput):
    """Add a product to an existing cart."""
    query = """
    mutation CartLinesAdd($cartId: ID!, $variantId: ID!, $quantity: Int!) {
      cartLinesAdd(cartId: $cartId, lines: [{ quantity: $quantity merchandiseId: $variantId }]) {
        cart {
          id checkoutUrl totalQuantity
          cost { totalAmount { amount currencyCode } }
          lines(first: 20) {
            edges {
              node {
                id quantity
                merchandise {
                  ... on ProductVariant {
                    id title price { amount currencyCode }
                    product { title handle images(first:1) { edges { node { url } } } }
                  }
                }
              }
            }
          }
        }
        userErrors { field message }
      }
    }
    """
    data = await shopify_query(query, {
        "cartId": item.cartId,
        "variantId": item.variantId,
        "quantity": item.quantity
    })
    errors = data["cartLinesAdd"].get("userErrors", [])
    if errors:
        raise HTTPException(status_code=400, detail=errors)
    return data["cartLinesAdd"]["cart"]


@router.put("/cart/update")
async def update_cart_item(item: CartUpdateInput):
    """Update quantity of a cart line."""
    query = """
    mutation CartLinesUpdate($cartId: ID!, $lineId: ID!, $quantity: Int!) {
      cartLinesUpdate(cartId: $cartId, lines: [{ id: $lineId quantity: $quantity }]) {
        cart {
          id checkoutUrl totalQuantity
          cost { totalAmount { amount currencyCode } }
          lines(first: 20) {
            edges {
              node {
                id quantity
                merchandise {
                  ... on ProductVariant {
                    id title price { amount currencyCode }
                    product { title handle }
                  }
                }
              }
            }
          }
        }
        userErrors { field message }
      }
    }
    """
    data = await shopify_query(query, {
        "cartId": item.cartId,
        "lineId": item.lineId,
        "quantity": item.quantity
    })
    errors = data["cartLinesUpdate"].get("userErrors", [])
    if errors:
        raise HTTPException(status_code=400, detail=errors)
    return data["cartLinesUpdate"]["cart"]


@router.post("/cart/remove")
async def remove_from_cart(item: CartRemoveInput):
    """Remove items from cart."""
    query = """
    mutation CartLinesRemove($cartId: ID!, $lineIds: [ID!]!) {
      cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
        cart {
          id checkoutUrl totalQuantity
          cost { totalAmount { amount currencyCode } }
          lines(first: 20) {
            edges {
              node {
                id quantity
                merchandise {
                  ... on ProductVariant {
                    id title price { amount currencyCode }
                    product { title handle }
                  }
                }
              }
            }
          }
        }
        userErrors { field message }
      }
    }
    """
    data = await shopify_query(query, {"cartId": item.cartId, "lineIds": item.lineIds})
    errors = data["cartLinesRemove"].get("userErrors", [])
    if errors:
        raise HTTPException(status_code=400, detail=errors)
    return data["cartLinesRemove"]["cart"]


@router.get("/cart/{cart_id}")
async def get_cart(cart_id: str):
    """Fetch current cart state."""
    query = """
    query GetCart($cartId: ID!) {
      cart(id: $cartId) {
        id checkoutUrl totalQuantity
        cost {
          totalAmount { amount currencyCode }
          subtotalAmount { amount currencyCode }
          totalTaxAmount { amount currencyCode }
        }
        lines(first: 20) {
          edges {
            node {
              id quantity
              cost { totalAmount { amount currencyCode } }
              merchandise {
                ... on ProductVariant {
                  id title price { amount currencyCode }
                  product {
                    title handle
                    images(first: 1) { edges { node { url altText } } }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    data = await shopify_query(query, {"cartId": cart_id})
    if not data.get("cart"):
        raise HTTPException(status_code=404, detail="Cart not found")
    return data["cart"]
