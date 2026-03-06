"""
Test Admin Product Management and Order Management APIs
Features:
- Admin Product CRUD (GET/POST/PUT/DELETE /api/admin/products)
- Admin Orders Management (GET /api/admin/orders, PATCH status update)
- Admin Order Tracking (POST /api/admin/orders/{id}/tracking)
- Admin Stats (GET /api/admin/stats)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


class TestAdminAuth:
    """Test admin authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["is_admin"] == True
        return data["token"]
    
    def test_admin_login_returns_is_admin_true(self):
        """Verify admin user has is_admin=True"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] == True
        print("PASS: Admin login returns is_admin=True")


class TestAdminStats:
    """Test admin stats endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_admin_stats_returns_all_metrics(self, admin_token):
        """GET /api/admin/stats returns all required stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "pending_orders" in data
        assert "processing_orders" in data
        assert "shipped_orders" in data
        assert "total_products" in data
        assert "total_customers" in data
        
        # All should be numbers
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["total_products"], int)
        assert isinstance(data["total_customers"], int)
        
        print(f"PASS: Admin stats - {data['total_products']} products, {data['total_orders']} orders, ${data['total_revenue']} revenue")
    
    def test_admin_stats_requires_auth(self):
        """GET /api/admin/stats requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code in [401, 403, 422]
        print("PASS: Admin stats requires authentication")


class TestAdminProductsCRUD:
    """Test Admin Product CRUD Operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def test_product_id(self, admin_token):
        """Create a test product and return its ID for cleanup"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"TEST_Product_{unique_id}",
            "slug": f"test-product-{unique_id}",
            "description": "Test product for API testing",
            "short_description": "Test product",
            "price": 29.99,
            "cost": 10.00,
            "category": "supplements",
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/products",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("id")
        return None
    
    def test_get_admin_products_list(self, admin_token):
        """GET /api/admin/products returns list of products"""
        response = requests.get(
            f"{BASE_URL}/api/admin/products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/admin/products returns {len(data)} products")
    
    def test_get_admin_products_with_search_filter(self, admin_token):
        """GET /api/admin/products supports search parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/products?search=calm",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/admin/products?search=calm returns {len(data)} products")
    
    def test_get_admin_products_with_pet_type_filter(self, admin_token):
        """GET /api/admin/products supports pet_type filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/products?pet_type=dog",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All products should have pet_type=dog or both
        for product in data:
            assert product["pet_type"] in ["dog", "both"], f"Unexpected pet_type: {product['pet_type']}"
        print(f"PASS: GET /api/admin/products?pet_type=dog returns {len(data)} products")
    
    def test_get_admin_products_with_category_filter(self, admin_token):
        """GET /api/admin/products supports category filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/products?category=supplements",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for product in data:
            assert product["category"] == "supplements"
        print(f"PASS: GET /api/admin/products?category=supplements returns {len(data)} products")
    
    def test_create_product(self, admin_token):
        """POST /api/admin/products creates a new product"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"TEST_New_Product_{unique_id}",
            "slug": f"test-new-product-{unique_id}",
            "description": "A new test product for admin testing",
            "short_description": "New test product",
            "price": 39.99,
            "compare_at_price": 49.99,
            "cost": 15.00,
            "category": "calming",
            "pet_type": "cat",
            "in_stock": True,
            "stock_quantity": 100,
            "tags": ["calming", "test"],
            "features": ["Feature 1", "Feature 2"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/products",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        assert "id" in data or "product" in data
        
        # Verify the product was created by fetching it
        product_id = data.get("id") or data.get("product", {}).get("id")
        if product_id:
            get_response = requests.get(
                f"{BASE_URL}/api/admin/products/{product_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert get_response.status_code == 200
            created_product = get_response.json()
            assert created_product["name"] == product_data["name"]
            assert created_product["price"] == product_data["price"]
            
            # Cleanup - delete the test product
            requests.delete(
                f"{BASE_URL}/api/admin/products/{product_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        print(f"PASS: POST /api/admin/products creates product - ID: {product_id}")
    
    def test_update_product(self, admin_token):
        """PUT /api/admin/products/{id} updates a product"""
        # First create a product to update
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "name": f"TEST_Update_Product_{unique_id}",
            "slug": f"test-update-product-{unique_id}",
            "description": "Product to update",
            "short_description": "To update",
            "price": 19.99,
            "cost": 8.00,
            "category": "toys",
            "pet_type": "dog",
            "in_stock": True,
            "stock_quantity": 25
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/products",
            json=create_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        product_id = create_response.json().get("id") or create_response.json().get("product", {}).get("id")
        
        # Update the product
        update_data = {
            **create_data,
            "name": f"TEST_Updated_Product_{unique_id}",
            "price": 24.99,
            "stock_quantity": 50
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/admin/products/{product_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        
        # Verify update by GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        updated_product = get_response.json()
        assert updated_product["price"] == 24.99
        assert updated_product["stock_quantity"] == 50
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"PASS: PUT /api/admin/products/{product_id} updates product price to $24.99")
    
    def test_delete_product(self, admin_token):
        """DELETE /api/admin/products/{id} deletes a product"""
        # First create a product to delete
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "name": f"TEST_Delete_Product_{unique_id}",
            "slug": f"test-delete-product-{unique_id}",
            "description": "Product to delete",
            "short_description": "To delete",
            "price": 9.99,
            "cost": 3.00,
            "category": "grooming",
            "pet_type": "cat",
            "in_stock": True,
            "stock_quantity": 10
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/products",
            json=create_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        product_id = create_response.json().get("id") or create_response.json().get("product", {}).get("id")
        
        # Delete the product
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify deletion - should return 404
        get_response = requests.get(
            f"{BASE_URL}/api/admin/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404
        
        print(f"PASS: DELETE /api/admin/products/{product_id} removes product (now 404)")
    
    def test_admin_products_requires_auth(self):
        """GET /api/admin/products requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/products")
        assert response.status_code in [401, 403, 422]
        print("PASS: Admin products endpoints require authentication")


class TestAdminOrdersManagement:
    """Test Admin Order Management"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_all_orders(self, admin_token):
        """GET /api/admin/orders returns all orders"""
        response = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify order structure
        if len(data) > 0:
            order = data[0]
            assert "id" in order
            assert "order_number" in order
            assert "email" in order
            assert "total" in order
            assert "status" in order
            assert "items" in order
        
        print(f"PASS: GET /api/admin/orders returns {len(data)} orders")
    
    def test_get_orders_with_status_filter(self, admin_token):
        """GET /api/admin/orders?status=pending filters by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/orders?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All orders should have pending status
        for order in data:
            assert order["status"] == "pending"
        
        print(f"PASS: GET /api/admin/orders?status=pending returns {len(data)} pending orders")
    
    def test_update_order_status(self, admin_token):
        """PATCH /api/admin/orders/{id}?status=processing updates order status"""
        # First get an order
        orders_response = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        orders = orders_response.json()
        
        if len(orders) == 0:
            pytest.skip("No orders available for testing")
        
        order_id = orders[0]["id"]
        original_status = orders[0]["status"]
        
        # Try to update to processing
        new_status = "processing" if original_status != "processing" else "pending"
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/orders/{order_id}?status={new_status}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Revert back to original status
        requests.patch(
            f"{BASE_URL}/api/admin/orders/{order_id}?status={original_status}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"PASS: PATCH /api/admin/orders/{order_id}?status={new_status} updates order status")
    
    def test_admin_orders_requires_auth(self):
        """GET /api/admin/orders requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/orders")
        assert response.status_code in [401, 403, 422]
        print("PASS: Admin orders endpoint requires authentication")


class TestAdminOrderTracking:
    """Test Admin Order Tracking Endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_add_tracking_to_order(self, admin_token):
        """POST /api/admin/orders/{id}/tracking adds tracking info"""
        # Get an order without tracking
        orders_response = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        orders = orders_response.json()
        
        # Find an order without tracking
        order_without_tracking = None
        for order in orders:
            if not order.get("tracking"):
                order_without_tracking = order
                break
        
        if not order_without_tracking:
            pytest.skip("No orders without tracking available for testing")
        
        order_id = order_without_tracking["id"]
        
        # Add tracking
        response = requests.post(
            f"{BASE_URL}/api/admin/orders/{order_id}/tracking?carrier=usps&tracking_number=TEST123456789",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tracking" in data
        assert data["tracking"]["carrier"] == "usps"
        assert data["tracking"]["tracking_number"] == "TEST123456789"
        assert "tracking_url" in data
        
        print(f"PASS: POST /api/admin/orders/{order_id}/tracking adds tracking with USPS")
    
    def test_add_tracking_requires_admin(self):
        """POST /api/admin/orders/{id}/tracking requires admin auth"""
        response = requests.post(
            f"{BASE_URL}/api/admin/orders/fake-order-id/tracking?carrier=usps&tracking_number=TEST",
        )
        assert response.status_code in [401, 403, 422]
        print("PASS: Add tracking requires admin authentication")


class TestAdminDashboardNavigation:
    """Test that admin dashboard has correct navigation links"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_all_admin_endpoints_accessible(self, admin_token):
        """Verify all admin endpoints are accessible"""
        endpoints = [
            "/api/admin/stats",
            "/api/admin/orders",
            "/api/admin/products",
            "/api/admin/promotions"
        ]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200, f"{endpoint} failed with {response.status_code}"
            print(f"PASS: {endpoint} accessible (200)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
