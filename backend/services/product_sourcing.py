"""
Product Sourcing Service - Supplier data aggregation
Supports: Rokt, Zendrop
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Pet category mappings for supplier searches
PET_CATEGORIES = {
    "dog": ["dog", "puppy", "canine", "pet dog"],
    "cat": ["cat", "kitten", "feline", "pet cat"],
    "fish": ["fish", "aquarium", "aquatic", "tropical fish", "goldfish", "betta"],
    "bird": ["bird", "parrot", "parakeet", "cockatiel", "budgie", "avian"],
    "rabbit": ["rabbit", "bunny", "small animal"],
    "small_pet": ["hamster", "guinea pig", "gerbil", "ferret", "chinchilla", "small pet"]
}

PRODUCT_TYPES = {
    "supplements": ["supplement", "vitamin", "health", "calming", "anxiety", "joint"],
    "food": ["food", "treat", "snack", "chew", "nutrition"],
    "grooming": ["grooming", "brush", "shampoo", "nail", "bath", "cleaning"],
    "toys": ["toy", "play", "interactive", "puzzle", "ball", "chew toy"],
    "beds": ["bed", "sleeping", "cushion", "mat", "blanket", "cozy"],
    "accessories": ["collar", "leash", "harness", "bowl", "feeder", "carrier"],
    "health": ["health", "wellness", "care", "medicine", "first aid"]
}

class ProductSourcingService:
    def __init__(self):
        pass
        
    async def search_products(
        self,
        query: str = "",
        pet_type: str = "all",
        product_type: str = "all",
        min_price: float = 0,
        max_price: float = 1000,
        supplier: str = "all",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for products across Rokt and Zendrop
        """
        all_products = []
        errors = []
        
        # Build search keywords
        keywords = self._build_search_keywords(query, pet_type, product_type)
        
        # Fetch from all suppliers or specific one
        suppliers_to_search = ["rokt", "zendrop"] if supplier == "all" else [supplier]
        
        tasks = []
        for sup in suppliers_to_search:
            if sup == "rokt":
                tasks.append(self._search_rokt(keywords, min_price, max_price))
            elif sup == "zendrop":
                tasks.append(self._search_zendrop(keywords, min_price, max_price))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"{suppliers_to_search[i]}: {str(result)}")
            elif isinstance(result, list):
                all_products.extend(result)
        
        # Filter by price range
        filtered_products = [
            p for p in all_products 
            if min_price <= p.get("supplier_cost", 0) <= max_price
        ]
        
        # Filter by pet type if specified
        if pet_type != "all":
            filtered_products = [
                p for p in filtered_products
                if p.get("pet_type", "").lower() == pet_type.lower() or p.get("pet_type", "").lower() == "all"
            ]
        
        # Sort by margin (highest first)
        filtered_products.sort(key=lambda x: x.get("margin_percent", 0), reverse=True)
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_products = filtered_products[start_idx:end_idx]
        
        return {
            "products": paginated_products,
            "total": len(filtered_products),
            "page": page,
            "limit": limit,
            "total_pages": (len(filtered_products) + limit - 1) // limit,
            "errors": errors if errors else None
        }
    
    def _build_search_keywords(self, query: str, pet_type: str, product_type: str) -> str:
        """Build optimized search keywords"""
        keywords = []
        
        if query:
            keywords.append(query)
        
        if pet_type != "all" and pet_type in PET_CATEGORIES:
            keywords.append(PET_CATEGORIES[pet_type][0])
        
        if product_type != "all" and product_type in PRODUCT_TYPES:
            keywords.append(PRODUCT_TYPES[product_type][0])
        
        if not keywords:
            keywords = ["pet wellness", "pet supplies"]
        
        return " ".join(keywords)
    
    async def _search_rokt(self, keywords: str, min_price: float, max_price: float) -> List[Dict]:
        """Search Rokt - Connect your Rokt API for live products"""
        products = self._get_rokt_pet_catalog(keywords)
        return [p for p in products if min_price <= p.get("supplier_cost", 0) <= max_price][:20]
    
    async def _search_zendrop(self, keywords: str, min_price: float, max_price: float) -> List[Dict]:
        """Search Zendrop - Connect your Zendrop API for live products"""
        products = self._get_zendrop_pet_catalog(keywords)
        return [p for p in products if min_price <= p.get("supplier_cost", 0) <= max_price][:20]
    
    def _get_rokt_pet_catalog(self, keywords: str) -> List[Dict]:
        """Rokt pet product catalog - Empty until API integration"""
        # TODO: Integrate with Rokt API for live products
        return []
    
    def _get_zendrop_pet_catalog(self, keywords: str) -> List[Dict]:
        """Zendrop pet product catalog - Empty until API integration"""
        # TODO: Integrate with Zendrop API for live products
        return []
    
    def calculate_profit_metrics(self, product: Dict) -> Dict:
        """Calculate detailed profit metrics for a product"""
        supplier_cost = product.get("supplier_cost", 0)
        shipping_cost = product.get("shipping_cost", 0)
        suggested_retail = product.get("suggested_retail", 0)
        
        landed_cost = supplier_cost + shipping_cost
        gross_margin = suggested_retail - landed_cost
        margin_percent = (gross_margin / suggested_retail * 100) if suggested_retail > 0 else 0
        
        # Estimate additional costs
        payment_processing = suggested_retail * 0.029 + 0.30  # Stripe fees
        marketing_cost = suggested_retail * 0.20  # 20% marketing budget estimate
        
        net_profit = gross_margin - payment_processing - marketing_cost
        net_margin = (net_profit / suggested_retail * 100) if suggested_retail > 0 else 0
        
        return {
            "landed_cost": round(landed_cost, 2),
            "gross_margin": round(gross_margin, 2),
            "gross_margin_percent": round(margin_percent, 1),
            "payment_processing": round(payment_processing, 2),
            "estimated_marketing": round(marketing_cost, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_percent": round(net_margin, 1),
            "break_even_units": 0,
            "recommended_ad_spend": round(gross_margin * 0.3, 2)
        }


# Singleton instance
product_sourcing_service = ProductSourcingService()
