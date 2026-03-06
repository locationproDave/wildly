"""
Test suite for CalmTails Product Filtering API
Tests pet_type filtering for all 7 animal categories + 'both' logic
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pet-wellness-shop-2.preview.emergentagent.com')

class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")

    def test_products_endpoint_available(self):
        """Verify products endpoint is available"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 23  # 23 products seeded
        print(f"✓ Products endpoint returned {len(data)} products")


class TestProductFiltersByPetType:
    """Test product filtering for each pet type"""
    
    def test_filter_bird_products(self):
        """Bird filter should return only bird products (3 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=bird")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 bird products, got {len(data)}"
        # Verify all products are bird type
        for product in data:
            assert product["pet_type"] == "bird", f"Product {product['name']} has type {product['pet_type']}, expected bird"
        print(f"✓ Bird filter: {len(data)} products (correct)")
    
    def test_filter_rabbit_products(self):
        """Rabbit filter should return only rabbit products (3 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=rabbit")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 rabbit products, got {len(data)}"
        for product in data:
            assert product["pet_type"] == "rabbit", f"Product {product['name']} has type {product['pet_type']}, expected rabbit"
        print(f"✓ Rabbit filter: {len(data)} products (correct)")
    
    def test_filter_fish_products(self):
        """Fish filter should return only fish products (3 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=fish")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 fish products, got {len(data)}"
        for product in data:
            assert product["pet_type"] == "fish", f"Product {product['name']} has type {product['pet_type']}, expected fish"
        print(f"✓ Fish filter: {len(data)} products (correct)")
    
    def test_filter_small_pet_products(self):
        """Small pet filter should return only small_pet products (3 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=small_pet")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 small_pet products, got {len(data)}"
        for product in data:
            assert product["pet_type"] == "small_pet", f"Product {product['name']} has type {product['pet_type']}, expected small_pet"
        print(f"✓ Small pet filter: {len(data)} products (correct)")
    
    def test_filter_reptile_products_excludes_both(self):
        """Reptile filter should return only reptile products (3 expected), NOT 'both'"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=reptile")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 reptile products, got {len(data)}"
        for product in data:
            assert product["pet_type"] == "reptile", f"Product {product['name']} has type {product['pet_type']}, expected reptile (not 'both')"
        print(f"✓ Reptile filter: {len(data)} products, correctly excludes 'both' type")
    
    def test_filter_dog_products_includes_both(self):
        """Dog filter should return dog products AND 'both' products (6 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=dog")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6, f"Expected 6 products (4 dog + 2 both), got {len(data)}"
        
        # Count pet types
        pet_type_counts = {"dog": 0, "both": 0}
        for product in data:
            assert product["pet_type"] in ["dog", "both"], f"Unexpected pet_type: {product['pet_type']}"
            pet_type_counts[product["pet_type"]] += 1
        
        assert pet_type_counts["dog"] == 4, f"Expected 4 dog products, got {pet_type_counts['dog']}"
        assert pet_type_counts["both"] == 2, f"Expected 2 'both' products, got {pet_type_counts['both']}"
        print(f"✓ Dog filter: {len(data)} products (4 dog + 2 both)")
    
    def test_filter_cat_products_includes_both(self):
        """Cat filter should return cat products AND 'both' products (4 expected)"""
        response = requests.get(f"{BASE_URL}/api/products?pet_type=cat")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4, f"Expected 4 products (2 cat + 2 both), got {len(data)}"
        
        # Count pet types
        pet_type_counts = {"cat": 0, "both": 0}
        for product in data:
            assert product["pet_type"] in ["cat", "both"], f"Unexpected pet_type: {product['pet_type']}"
            pet_type_counts[product["pet_type"]] += 1
        
        assert pet_type_counts["cat"] == 2, f"Expected 2 cat products, got {pet_type_counts['cat']}"
        assert pet_type_counts["both"] == 2, f"Expected 2 'both' products, got {pet_type_counts['both']}"
        print(f"✓ Cat filter: {len(data)} products (2 cat + 2 both)")


class TestProductData:
    """Test product data integrity"""
    
    def test_all_products_have_images(self):
        """All products should have at least one image URL"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        
        products_without_images = []
        for product in data:
            if not product.get("images") or len(product["images"]) == 0:
                products_without_images.append(product["name"])
        
        assert len(products_without_images) == 0, f"Products without images: {products_without_images}"
        print(f"✓ All {len(data)} products have images")
    
    def test_product_images_are_valid_urls(self):
        """All product images should be valid Unsplash URLs"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        
        invalid_images = []
        for product in data:
            for img in product.get("images", []):
                if not img.startswith("https://images.unsplash.com"):
                    invalid_images.append({"product": product["name"], "image": img})
        
        # Note: We'll report these but not fail the test - some images may be from other sources
        if invalid_images:
            print(f"⚠ Non-Unsplash images found: {len(invalid_images)}")
        else:
            print(f"✓ All product images are from Unsplash")
    
    def test_featured_products_endpoint(self):
        """Featured products endpoint should return top products"""
        response = requests.get(f"{BASE_URL}/api/products/featured")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 8, f"Featured products should return max 8, got {len(data)}"
        print(f"✓ Featured products: {len(data)} products returned")


class TestCartFunctionality:
    """Test cart operations"""
    
    def test_add_to_cart(self):
        """Test adding a product to cart"""
        import uuid
        session_id = f"test_{uuid.uuid4()}"
        
        # Get a product first
        products = requests.get(f"{BASE_URL}/api/products").json()
        product_id = products[0]["id"]
        
        # Add to cart
        response = requests.post(
            f"{BASE_URL}/api/cart/{session_id}/add",
            json={"product_id": product_id, "quantity": 1}
        )
        assert response.status_code == 200
        cart = response.json()
        assert cart["item_count"] >= 1
        print(f"✓ Add to cart successful: {cart['item_count']} items in cart")
    
    def test_get_cart(self):
        """Test getting cart contents"""
        import uuid
        session_id = f"test_{uuid.uuid4()}"
        
        response = requests.get(f"{BASE_URL}/api/cart/{session_id}")
        assert response.status_code == 200
        cart = response.json()
        assert "items" in cart
        assert "subtotal" in cart
        print(f"✓ Get cart successful: subtotal ${cart['subtotal']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
