"""
Test suite for CalmTails Best Sellers and Promotions APIs
Tests: /api/products/bestsellers, /api/promotions, /api/promotions/validate
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://calm-tails-staging.preview.emergentagent.com')


class TestBestsellersEndpoint:
    """Tests for /api/products/bestsellers endpoint"""
    
    def test_bestsellers_returns_8_products(self):
        """Bestsellers endpoint should return 8 products"""
        response = requests.get(f"{BASE_URL}/api/products/bestsellers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 8, f"Expected 8 bestsellers, got {len(data)}"
        print(f"✓ Bestsellers endpoint: {len(data)} products returned")
    
    def test_bestsellers_sorted_by_review_count(self):
        """Bestsellers should be sorted by review_count (descending)"""
        response = requests.get(f"{BASE_URL}/api/products/bestsellers")
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorting by review_count
        review_counts = [p.get("review_count", 0) for p in data]
        for i in range(len(review_counts) - 1):
            assert review_counts[i] >= review_counts[i + 1], \
                f"Products not sorted correctly: {review_counts[i]} < {review_counts[i + 1]}"
        
        print(f"✓ Bestsellers sorted by review_count: {review_counts}")
    
    def test_bestsellers_have_required_fields(self):
        """All bestsellers should have required fields"""
        response = requests.get(f"{BASE_URL}/api/products/bestsellers")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "name", "slug", "price", "rating", "review_count", "images", "pet_type"]
        
        for product in data:
            for field in required_fields:
                assert field in product, f"Missing field '{field}' in product {product.get('name', 'Unknown')}"
        
        print(f"✓ All bestsellers have required fields")
    
    def test_bestsellers_products_in_stock(self):
        """All bestsellers should be in stock"""
        response = requests.get(f"{BASE_URL}/api/products/bestsellers")
        assert response.status_code == 200
        data = response.json()
        
        for product in data:
            assert product.get("in_stock", False) == True, \
                f"Product {product['name']} is not in stock"
        
        print(f"✓ All bestsellers are in stock")


class TestPromotionsEndpoint:
    """Tests for /api/promotions endpoint"""
    
    def test_promotions_returns_active_promotions(self):
        """Promotions endpoint should return active promotions"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4, f"Expected at least 4 promotions, got {len(data)}"
        print(f"✓ Promotions endpoint: {len(data)} active promotions")
    
    def test_promotions_have_expected_codes(self):
        """Verify expected promotion codes exist"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        expected_codes = ["WELCOME15", "FREESHIP50", "PAWS10", "SPRING25"]
        actual_codes = [p["code"] for p in data]
        
        for code in expected_codes:
            assert code in actual_codes, f"Expected promotion code '{code}' not found"
        
        print(f"✓ All expected promotion codes found: {expected_codes}")
    
    def test_promotions_have_required_fields(self):
        """All promotions should have required fields"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "code", "name", "description", "discount_type", "discount_value", "is_active"]
        
        for promo in data:
            for field in required_fields:
                assert field in promo, f"Missing field '{field}' in promotion {promo.get('code', 'Unknown')}"
            assert promo["is_active"] == True, f"Promotion {promo['code']} is not active"
        
        print(f"✓ All promotions have required fields and are active")
    
    def test_welcome15_promotion_details(self):
        """Verify WELCOME15 promotion details"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        welcome15 = next((p for p in data if p["code"] == "WELCOME15"), None)
        assert welcome15 is not None, "WELCOME15 promotion not found"
        assert welcome15["discount_type"] == "percentage"
        assert welcome15["discount_value"] == 15
        assert welcome15["is_first_order_only"] == True
        
        print(f"✓ WELCOME15 promotion: 15% off first order")
    
    def test_freeship50_promotion_details(self):
        """Verify FREESHIP50 promotion details"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        freeship = next((p for p in data if p["code"] == "FREESHIP50"), None)
        assert freeship is not None, "FREESHIP50 promotion not found"
        assert freeship["discount_type"] == "free_shipping"
        assert freeship["min_purchase"] == 50
        
        print(f"✓ FREESHIP50 promotion: free shipping on $50+")
    
    def test_paws10_promotion_details(self):
        """Verify PAWS10 promotion details"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        paws10 = next((p for p in data if p["code"] == "PAWS10"), None)
        assert paws10 is not None, "PAWS10 promotion not found"
        assert paws10["discount_type"] == "fixed_amount"
        assert paws10["discount_value"] == 10
        assert paws10["min_purchase"] == 75
        
        print(f"✓ PAWS10 promotion: $10 off $75+")
    
    def test_spring25_promotion_details(self):
        """Verify SPRING25 promotion details"""
        response = requests.get(f"{BASE_URL}/api/promotions")
        assert response.status_code == 200
        data = response.json()
        
        spring25 = next((p for p in data if p["code"] == "SPRING25"), None)
        assert spring25 is not None, "SPRING25 promotion not found"
        assert spring25["discount_type"] == "percentage"
        assert spring25["discount_value"] == 25
        assert spring25["min_purchase"] == 100
        
        print(f"✓ SPRING25 promotion: 25% off $100+")


class TestPromotionValidation:
    """Tests for /api/promotions/validate/{code} endpoint"""
    
    def test_validate_welcome15_with_subtotal(self):
        """Validate WELCOME15 code returns correct discount"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/WELCOME15?subtotal=50")
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == True
        assert data["promotion"]["code"] == "WELCOME15"
        assert data["discount_amount"] == 7.5  # 15% of $50
        
        print(f"✓ WELCOME15 validated: $7.50 discount on $50 subtotal")
    
    def test_validate_welcome15_case_insensitive(self):
        """Validate promotion code is case-insensitive"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/welcome15?subtotal=100")
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == True
        assert data["discount_amount"] == 15  # 15% of $100
        
        print(f"✓ Promotion validation is case-insensitive")
    
    def test_validate_paws10_below_minimum(self):
        """PAWS10 should fail below $75 minimum purchase"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/PAWS10?subtotal=50")
        assert response.status_code == 400
        data = response.json()
        assert "minimum" in data.get("detail", "").lower() or "75" in data.get("detail", "")
        
        print(f"✓ PAWS10 rejected for subtotal below $75")
    
    def test_validate_paws10_above_minimum(self):
        """PAWS10 should work above $75 minimum purchase"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/PAWS10?subtotal=80")
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == True
        assert data["discount_amount"] == 10  # $10 fixed amount
        
        print(f"✓ PAWS10 validated: $10 discount on $80 subtotal")
    
    def test_validate_spring25_above_minimum(self):
        """SPRING25 should work above $100 minimum purchase"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/SPRING25?subtotal=120")
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == True
        assert data["discount_amount"] == 30  # 25% of $120
        
        print(f"✓ SPRING25 validated: $30 discount on $120 subtotal")
    
    def test_validate_invalid_code(self):
        """Invalid promotion code should return 404"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/INVALID_CODE?subtotal=50")
        assert response.status_code == 404
        
        print(f"✓ Invalid promotion code returns 404")
    
    def test_validate_freeship50_returns_zero_discount(self):
        """FREESHIP50 discount type is free_shipping, should return 0 discount amount"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/FREESHIP50?subtotal=100")
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == True
        # Free shipping discount type returns 0 as discount_amount (shipping is handled separately)
        assert data["discount_amount"] == 0
        
        print(f"✓ FREESHIP50 validated: free shipping (0 direct discount)")


class TestLoyaltyEndpoints:
    """Tests for loyalty program endpoints (requires auth)"""
    
    def test_loyalty_status_requires_auth(self):
        """Loyalty status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/loyalty/status")
        assert response.status_code == 401
        
        print(f"✓ Loyalty status endpoint requires authentication")
    
    def test_loyalty_redeem_requires_auth(self):
        """Loyalty redeem endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/loyalty/redeem",
            json={"points_to_redeem": 100}
        )
        assert response.status_code == 401
        
        print(f"✓ Loyalty redeem endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
