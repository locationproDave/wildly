"""
Test Product Sourcing Feature - Backend API Tests
Tests for /api/admin/sourcing endpoints:
- Search products
- Get categories
- Import product to store
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


class TestProductSourcingAuth:
    """Test authentication requirements for sourcing endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Login as admin and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_sourcing_search_requires_auth(self):
        """Test that sourcing search requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 100,
            "page": 1,
            "limit": 12
        })
        # Should return 401 without auth token
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Sourcing search requires authentication")
    
    def test_sourcing_categories_requires_auth(self):
        """Test that categories endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Sourcing categories requires authentication")
    
    def test_sourcing_import_requires_auth(self):
        """Test that import endpoint requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/import", json={
            "sourced_product": {"name": "Test Product"},
            "custom_name": "Test"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Sourcing import requires authentication")


class TestProductSourcingCategories:
    """Test sourcing categories endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Admin login failed")
    
    def test_categories_returns_pet_types(self):
        """Test that categories endpoint returns pet types"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "pet_types" in data, "Response should contain pet_types"
        
        pet_types = data["pet_types"]
        assert len(pet_types) >= 6, f"Expected at least 6 pet types, got {len(pet_types)}"
        
        # Check expected pet types exist
        pet_type_values = [pt["value"] for pt in pet_types]
        expected_pets = ["all", "dog", "cat", "fish", "bird", "rabbit", "small_pet"]
        for pet in expected_pets:
            assert pet in pet_type_values, f"Expected pet type '{pet}' not found"
        
        print(f"PASS: Categories returns {len(pet_types)} pet types: {pet_type_values}")
    
    def test_categories_returns_product_types(self):
        """Test that categories endpoint returns product types"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "product_types" in data, "Response should contain product_types"
        
        product_types = data["product_types"]
        assert len(product_types) >= 7, f"Expected at least 7 product types, got {len(product_types)}"
        
        product_type_values = [pt["value"] for pt in product_types]
        expected_types = ["all", "supplements", "food", "grooming", "toys", "beds", "accessories"]
        for ptype in expected_types:
            assert ptype in product_type_values, f"Expected product type '{ptype}' not found"
        
        print(f"PASS: Categories returns {len(product_types)} product types: {product_type_values}")
    
    def test_categories_returns_suppliers(self):
        """Test that categories endpoint returns suppliers"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "suppliers" in data, "Response should contain suppliers"
        
        suppliers = data["suppliers"]
        assert len(suppliers) >= 3, f"Expected at least 3 suppliers, got {len(suppliers)}"
        
        supplier_values = [s["value"] for s in suppliers]
        expected_suppliers = ["cjdropshipping", "zendrop", "spocket"]
        for supplier in expected_suppliers:
            assert supplier in supplier_values, f"Expected supplier '{supplier}' not found"
        
        print(f"PASS: Categories returns {len(suppliers)} suppliers: {supplier_values}")


class TestProductSourcingSearch:
    """Test product sourcing search endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Admin login failed")
    
    def test_search_default_returns_products(self):
        """Test that default search returns products"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 200,
            "page": 1,
            "limit": 20
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "products" in data, "Response should contain products"
        assert "total" in data, "Response should contain total"
        assert "page" in data, "Response should contain page"
        
        products = data["products"]
        assert len(products) > 0, "Should return at least some products"
        
        print(f"PASS: Default search returned {len(products)} products (total: {data['total']})")
    
    def test_search_product_has_required_fields(self):
        """Test that returned products have all required fields"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 200,
            "page": 1,
            "limit": 5
        })
        
        assert response.status_code == 200
        
        data = response.json()
        products = data["products"]
        assert len(products) > 0, "Need at least one product to test"
        
        product = products[0]
        required_fields = [
            "id", "name", "supplier", "supplier_cost", "shipping_cost",
            "landed_cost", "suggested_retail", "margin", "margin_percent",
            "pet_type", "category", "rating", "features"
        ]
        
        for field in required_fields:
            assert field in product, f"Product missing required field: {field}"
        
        # Validate margin calculation
        landed = product["landed_cost"]
        retail = product["suggested_retail"]
        expected_margin = retail - landed
        assert abs(product["margin"] - expected_margin) < 0.01, "Margin calculation incorrect"
        
        print(f"PASS: Product has all required fields. Sample: {product['name']}, Cost: ${product['supplier_cost']}, Retail: ${product['suggested_retail']}, Margin: {product['margin_percent']}%")
    
    def test_search_filter_by_pet_type(self):
        """Test search filter by pet type"""
        for pet_type in ["dog", "cat", "fish", "bird"]:
            response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
                "query": "",
                "pet_type": pet_type,
                "product_type": "all",
                "supplier": "all",
                "min_price": 0,
                "max_price": 200,
                "page": 1,
                "limit": 20
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that all returned products match the pet type
            for product in data["products"]:
                assert product["pet_type"] in [pet_type, "all"], f"Product pet_type '{product['pet_type']}' doesn't match filter '{pet_type}'"
            
            print(f"PASS: Filter by pet_type='{pet_type}' returned {len(data['products'])} products")
    
    def test_search_filter_by_supplier(self):
        """Test search filter by supplier"""
        for supplier in ["cjdropshipping", "zendrop", "spocket"]:
            response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
                "query": "",
                "pet_type": "all",
                "product_type": "all",
                "supplier": supplier,
                "min_price": 0,
                "max_price": 200,
                "page": 1,
                "limit": 20
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that all returned products are from the specified supplier
            for product in data["products"]:
                assert product["supplier"].lower() == supplier.lower(), f"Product supplier '{product['supplier']}' doesn't match filter '{supplier}'"
            
            print(f"PASS: Filter by supplier='{supplier}' returned {len(data['products'])} products")
    
    def test_search_filter_by_price_range(self):
        """Test search filter by price range"""
        min_price = 10
        max_price = 30
        
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": min_price,
            "max_price": max_price,
            "page": 1,
            "limit": 50
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all returned products are within the price range
        for product in data["products"]:
            cost = product["supplier_cost"]
            assert min_price <= cost <= max_price, f"Product cost ${cost} outside range ${min_price}-${max_price}"
        
        print(f"PASS: Price range filter ${min_price}-${max_price} returned {len(data['products'])} products")
    
    def test_search_with_query(self):
        """Test search with text query"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "calming",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 200,
            "page": 1,
            "limit": 20
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return some results for 'calming'
        print(f"PASS: Search for 'calming' returned {len(data['products'])} products")
    
    def test_search_pagination(self):
        """Test search pagination"""
        # Get first page
        response1 = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 200,
            "page": 1,
            "limit": 5
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        assert data1["page"] == 1
        assert data1["limit"] == 5
        assert "total_pages" in data1
        
        if data1["total_pages"] > 1:
            # Get second page
            response2 = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
                "query": "",
                "pet_type": "all",
                "product_type": "all",
                "supplier": "all",
                "min_price": 0,
                "max_price": 200,
                "page": 2,
                "limit": 5
            })
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["page"] == 2
            
            # Pages should have different products
            ids1 = [p["id"] for p in data1["products"]]
            ids2 = [p["id"] for p in data2["products"]]
            overlap = set(ids1) & set(ids2)
            assert len(overlap) == 0, "Pagination pages should have different products"
        
        print(f"PASS: Pagination working. Page 1: {len(data1['products'])} products, Total pages: {data1['total_pages']}")


class TestProductSourcingImport:
    """Test product import functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Admin login failed")
    
    def test_import_product_basic(self):
        """Test basic product import"""
        # First search for a product
        search_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "dog",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 100,
            "page": 1,
            "limit": 5
        })
        
        assert search_response.status_code == 200
        products = search_response.json()["products"]
        assert len(products) > 0, "Need at least one product to import"
        
        # Take the first product to import
        sourced_product = products[0]
        test_name = f"TEST_Imported_{uuid.uuid4().hex[:8]}"
        
        # Import the product
        import_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/import", json={
            "sourced_product": sourced_product,
            "custom_name": test_name,
            "custom_price": 49.99,
            "custom_description": "Test imported product description"
        })
        
        assert import_response.status_code == 200, f"Import failed: {import_response.text}"
        
        data = import_response.json()
        assert data["success"] == True, "Import should succeed"
        assert "product" in data, "Response should contain product"
        
        imported = data["product"]
        assert imported["name"] == test_name, f"Product name mismatch: expected {test_name}, got {imported['name']}"
        assert imported["price"] == 49.99, f"Price mismatch: expected 49.99, got {imported['price']}"
        assert imported["in_stock"] == True, "Imported product should be in stock"
        
        # Verify product is in catalog
        verify_response = self.session.get(f"{BASE_URL}/api/products/{imported['slug']}")
        assert verify_response.status_code == 200, f"Product not found in catalog: {imported['slug']}"
        
        print(f"PASS: Successfully imported product '{test_name}' with price ${imported['price']}")
        
        # Cleanup - delete the test product
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/products/{imported['id']}")
        if delete_response.status_code == 200:
            print(f"PASS: Cleanup - deleted test product")
    
    def test_import_preserves_sourcing_info(self):
        """Test that import preserves sourcing metadata"""
        # Search for a product
        search_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "cat",
            "product_type": "all",
            "supplier": "zendrop",
            "min_price": 0,
            "max_price": 100,
            "page": 1,
            "limit": 5
        })
        
        assert search_response.status_code == 200
        products = search_response.json()["products"]
        
        if len(products) == 0:
            pytest.skip("No cat products from Zendrop available")
        
        sourced = products[0]
        test_name = f"TEST_Sourced_{uuid.uuid4().hex[:8]}"
        
        # Import
        import_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/import", json={
            "sourced_product": sourced,
            "custom_name": test_name
        })
        
        assert import_response.status_code == 200
        imported = import_response.json()["product"]
        
        # Check sourcing metadata is preserved
        assert "sourced_from" in imported, "Imported product should have sourced_from metadata"
        sourced_from = imported["sourced_from"]
        
        assert sourced_from["supplier"] == sourced["supplier"], "Supplier mismatch in metadata"
        assert sourced_from["supplier_cost"] == sourced["supplier_cost"], "Supplier cost mismatch"
        assert sourced_from["landed_cost"] == sourced["landed_cost"], "Landed cost mismatch"
        
        print(f"PASS: Sourcing metadata preserved - Supplier: {sourced_from['supplier']}, Cost: ${sourced_from['supplier_cost']}, Landed: ${sourced_from['landed_cost']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/admin/products/{imported['id']}")


class TestSourcingEndToEnd:
    """End-to-end sourcing flow tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Admin login failed")
    
    def test_full_sourcing_workflow(self):
        """Test complete sourcing workflow: search -> filter -> import -> verify"""
        
        # Step 1: Get categories
        cat_response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert cat_response.status_code == 200
        categories = cat_response.json()
        print(f"Step 1: Got categories - {len(categories['pet_types'])} pet types, {len(categories['suppliers'])} suppliers")
        
        # Step 2: Search with filters
        search_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "bed",
            "pet_type": "dog",
            "product_type": "beds",
            "supplier": "all",
            "min_price": 10,
            "max_price": 50,
            "page": 1,
            "limit": 10
        })
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        products = search_data["products"]
        print(f"Step 2: Searched for dog beds $10-50, found {len(products)} products")
        
        if len(products) == 0:
            # Try broader search
            search_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
                "query": "",
                "pet_type": "dog",
                "product_type": "all",
                "supplier": "all",
                "min_price": 0,
                "max_price": 100,
                "page": 1,
                "limit": 10
            })
            products = search_response.json()["products"]
            print(f"Step 2 (broader): Found {len(products)} dog products")
        
        assert len(products) > 0, "Need at least one product"
        
        # Step 3: Select a product with good margin
        selected = None
        for p in products:
            if p["margin_percent"] >= 40:
                selected = p
                break
        
        if not selected:
            selected = products[0]
        
        print(f"Step 3: Selected '{selected['name']}' - Cost: ${selected['supplier_cost']}, Margin: {selected['margin_percent']}%")
        
        # Step 4: Import the product
        test_name = f"TEST_E2E_{uuid.uuid4().hex[:8]}"
        import_response = self.session.post(f"{BASE_URL}/api/admin/sourcing/import", json={
            "sourced_product": selected,
            "custom_name": test_name,
            "custom_price": 59.99
        })
        assert import_response.status_code == 200
        imported = import_response.json()["product"]
        print(f"Step 4: Imported as '{imported['name']}' with price ${imported['price']}")
        
        # Step 5: Verify product in store catalog
        catalog_response = self.session.get(f"{BASE_URL}/api/products/{imported['slug']}")
        assert catalog_response.status_code == 200
        catalog_product = catalog_response.json()
        
        assert catalog_product["name"] == test_name
        assert catalog_product["price"] == 59.99
        assert catalog_product["in_stock"] == True
        print(f"Step 5: Verified product in catalog - slug: {imported['slug']}")
        
        # Step 6: Verify in admin products list
        admin_products_response = self.session.get(f"{BASE_URL}/api/admin/products", params={
            "search": test_name
        })
        assert admin_products_response.status_code == 200
        admin_products = admin_products_response.json()
        found = any(p["name"] == test_name for p in admin_products)
        assert found, "Imported product not found in admin products list"
        print(f"Step 6: Product found in admin products list")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/admin/products/{imported['id']}")
        print(f"Step 7: Cleanup - deleted test product")
        
        print("PASS: Full sourcing workflow completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
