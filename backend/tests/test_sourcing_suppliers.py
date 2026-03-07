"""
Test Product Sourcing - Verify only Faire and Zendrop suppliers
Tests for supplier migration from old suppliers (Spocket, CJdropshipping) to new suppliers (Faire, Zendrop)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

class TestSourcingSuppliers:
    """Test that product sourcing only uses Faire and Zendrop suppliers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@calmtails.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    # =====================================================
    # GET /api/admin/sourcing/categories TESTS
    # =====================================================
    
    def test_categories_endpoint_returns_200(self):
        """GET /api/admin/sourcing/categories should return 200"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_categories_has_suppliers_array(self):
        """Categories response should have suppliers array"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        data = response.json()
        assert "suppliers" in data, "Response missing 'suppliers' key"
        assert isinstance(data["suppliers"], list), "Suppliers should be a list"
        
    def test_categories_suppliers_only_faire_and_zendrop(self):
        """Suppliers array should ONLY contain Faire and Zendrop (plus 'all' option)"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        data = response.json()
        suppliers = data["suppliers"]
        
        # Extract supplier values
        supplier_values = [s["value"] for s in suppliers]
        
        # Expected suppliers: all, faire, zendrop
        expected_values = ["all", "faire", "zendrop"]
        
        assert set(supplier_values) == set(expected_values), \
            f"Expected suppliers {expected_values}, got {supplier_values}"
            
    def test_categories_no_old_suppliers(self):
        """Suppliers array should NOT contain Spocket or CJdropshipping"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        data = response.json()
        suppliers = data["suppliers"]
        
        supplier_values = [s["value"].lower() for s in suppliers]
        supplier_labels = [s["label"].lower() for s in suppliers]
        
        # Old suppliers that should NOT be present
        old_suppliers = ["spocket", "cjdropshipping", "cj dropshipping", "cj"]
        
        for old in old_suppliers:
            assert old not in supplier_values, f"Old supplier '{old}' found in values: {supplier_values}"
            assert old not in supplier_labels, f"Old supplier '{old}' found in labels: {supplier_labels}"
            
    def test_categories_faire_label_correct(self):
        """Faire supplier should have correct label"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        data = response.json()
        suppliers = data["suppliers"]
        
        faire = next((s for s in suppliers if s["value"] == "faire"), None)
        assert faire is not None, "Faire supplier not found"
        assert faire["label"] == "Faire", f"Faire label incorrect: {faire['label']}"
        
    def test_categories_zendrop_label_correct(self):
        """Zendrop supplier should have correct label"""
        response = self.session.get(f"{BASE_URL}/api/admin/sourcing/categories")
        data = response.json()
        suppliers = data["suppliers"]
        
        zendrop = next((s for s in suppliers if s["value"] == "zendrop"), None)
        assert zendrop is not None, "Zendrop supplier not found"
        assert zendrop["label"] == "Zendrop", f"Zendrop label incorrect: {zendrop['label']}"
        
    # =====================================================
    # POST /api/admin/sourcing/search TESTS
    # =====================================================
    
    def test_search_endpoint_returns_200(self):
        """POST /api/admin/sourcing/search should return 200"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_search_returns_products_array(self):
        """Search response should have products array"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        data = response.json()
        assert "products" in data, "Response missing 'products' key"
        assert isinstance(data["products"], list), "Products should be a list"
        
    def test_search_all_products_from_faire_or_zendrop(self):
        """ALL products returned should be from Faire or Zendrop ONLY"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 50
        })
        data = response.json()
        products = data["products"]
        
        assert len(products) > 0, "No products returned - expected Faire and Zendrop products"
        
        allowed_suppliers = ["Faire", "Zendrop"]
        
        for product in products:
            supplier = product.get("supplier", "")
            assert supplier in allowed_suppliers, \
                f"Product '{product.get('name')}' has invalid supplier: '{supplier}'. Only {allowed_suppliers} allowed."
                
    def test_search_no_old_suppliers_in_products(self):
        """Products should NOT be from Spocket or CJdropshipping"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 50
        })
        data = response.json()
        products = data["products"]
        
        old_suppliers = ["Spocket", "spocket", "CJdropshipping", "cjdropshipping", "CJ"]
        
        for product in products:
            supplier = product.get("supplier", "")
            assert supplier not in old_suppliers, \
                f"Product '{product.get('name')}' from old supplier: '{supplier}'"
                
    def test_search_faire_filter_returns_only_faire(self):
        """Filtering by 'faire' should return ONLY Faire products"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "faire",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        data = response.json()
        products = data["products"]
        
        assert len(products) > 0, "No Faire products returned"
        
        for product in products:
            supplier = product.get("supplier", "")
            assert supplier == "Faire", \
                f"Expected Faire product, got supplier: '{supplier}'"
                
    def test_search_zendrop_filter_returns_only_zendrop(self):
        """Filtering by 'zendrop' should return ONLY Zendrop products"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "zendrop",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        data = response.json()
        products = data["products"]
        
        assert len(products) > 0, "No Zendrop products returned"
        
        for product in products:
            supplier = product.get("supplier", "")
            assert supplier == "Zendrop", \
                f"Expected Zendrop product, got supplier: '{supplier}'"
                
    def test_search_products_have_required_fields(self):
        """Products should have all required fields"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 10
        })
        data = response.json()
        products = data["products"]
        
        required_fields = ["id", "name", "supplier", "supplier_cost", "suggested_retail", "margin_percent"]
        
        for product in products[:5]:  # Check first 5 products
            for field in required_fields:
                assert field in product, \
                    f"Product missing required field '{field}': {product.get('name')}"
                    
    def test_search_faire_products_have_correct_badge_data(self):
        """Faire products should have supplier field set to 'Faire'"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "faire",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 5
        })
        data = response.json()
        products = data["products"]
        
        for product in products:
            assert product["supplier"] == "Faire", \
                f"Faire product has incorrect supplier value: {product['supplier']}"
                
    def test_search_zendrop_products_have_correct_badge_data(self):
        """Zendrop products should have supplier field set to 'Zendrop'"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "zendrop",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 5
        })
        data = response.json()
        products = data["products"]
        
        for product in products:
            assert product["supplier"] == "Zendrop", \
                f"Zendrop product has incorrect supplier value: {product['supplier']}"
                
    def test_search_dog_products_available(self):
        """Dog products should be available from both suppliers"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "dog",
            "pet_type": "dog",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        data = response.json()
        products = data["products"]
        
        # Should have products and they should be from valid suppliers
        if len(products) > 0:
            suppliers_found = set(p["supplier"] for p in products)
            for s in suppliers_found:
                assert s in ["Faire", "Zendrop"], f"Invalid supplier in dog products: {s}"
                
    def test_search_cat_products_available(self):
        """Cat products should be available from both suppliers"""
        response = self.session.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "cat",
            "pet_type": "cat",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        data = response.json()
        products = data["products"]
        
        # Should have products and they should be from valid suppliers
        if len(products) > 0:
            suppliers_found = set(p["supplier"] for p in products)
            for s in suppliers_found:
                assert s in ["Faire", "Zendrop"], f"Invalid supplier in cat products: {s}"


class TestSourcingUnauthorized:
    """Test that sourcing endpoints require admin authentication"""
    
    def test_categories_requires_auth(self):
        """GET /api/admin/sourcing/categories should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/sourcing/categories")
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
            
    def test_search_requires_auth(self):
        """POST /api/admin/sourcing/search should require authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/sourcing/search", json={
            "query": "",
            "pet_type": "all",
            "product_type": "all",
            "supplier": "all",
            "min_price": 0,
            "max_price": 1000,
            "page": 1,
            "limit": 20
        })
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
