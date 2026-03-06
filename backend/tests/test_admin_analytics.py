"""
Test Admin Analytics Dashboard API
- GET /api/admin/analytics returns comprehensive analytics data
- Requires admin authentication
- Validates summary, sales_trend, top_products, category_breakdown, pet_type_breakdown, recent_customers
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Return headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAdminAnalyticsEndpoint:
    """Test /api/admin/analytics endpoint"""
    
    def test_analytics_requires_auth(self):
        """Analytics endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403, got {response.status_code}"
        print("✓ Analytics endpoint requires authentication (401)")
    
    def test_analytics_requires_admin(self, admin_headers):
        """Test that non-admin users get 403"""
        # First create a regular user
        import uuid
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "test123",
            "name": "Test User"
        })
        if reg_response.status_code == 200:
            user_token = reg_response.json().get("token")
            user_headers = {"Authorization": f"Bearer {user_token}"}
            response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=user_headers)
            assert response.status_code == 403, \
                f"Expected 403 for non-admin, got {response.status_code}"
            print("✓ Analytics endpoint requires admin role (403 for regular user)")
        else:
            # If registration failed, skip this test
            pytest.skip("Could not create test user")
    
    def test_analytics_returns_summary(self, admin_headers):
        """Analytics should return summary with total_revenue, total_orders, total_customers, avg_order_value"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "summary" in data, "Missing 'summary' in response"
        
        summary = data["summary"]
        assert "total_revenue" in summary, "Missing 'total_revenue' in summary"
        assert "total_orders" in summary, "Missing 'total_orders' in summary"
        assert "total_customers" in summary, "Missing 'total_customers' in summary"
        assert "avg_order_value" in summary, "Missing 'avg_order_value' in summary"
        
        # Validate types
        assert isinstance(summary["total_revenue"], (int, float)), "total_revenue should be numeric"
        assert isinstance(summary["total_orders"], int), "total_orders should be integer"
        assert isinstance(summary["total_customers"], int), "total_customers should be integer"
        assert isinstance(summary["avg_order_value"], (int, float)), "avg_order_value should be numeric"
        
        print(f"✓ Summary: Revenue=${summary['total_revenue']}, Orders={summary['total_orders']}, Customers={summary['total_customers']}, AOV=${summary['avg_order_value']}")
    
    def test_analytics_returns_sales_trend(self, admin_headers):
        """Analytics should return sales_trend array with date, revenue, orders for last 30 days"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "sales_trend" in data, "Missing 'sales_trend' in response"
        
        sales_trend = data["sales_trend"]
        assert isinstance(sales_trend, list), "sales_trend should be a list"
        assert len(sales_trend) == 30, f"Expected 30 days of data, got {len(sales_trend)}"
        
        # Check structure of trend data
        for day in sales_trend:
            assert "date" in day, "Each trend item should have 'date'"
            assert "revenue" in day, "Each trend item should have 'revenue'"
            assert "orders" in day, "Each trend item should have 'orders'"
        
        print(f"✓ Sales trend: {len(sales_trend)} days of data")
    
    def test_analytics_returns_top_products(self, admin_headers):
        """Analytics should return top_products with id, name, image, quantity, revenue"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "top_products" in data, "Missing 'top_products' in response"
        
        top_products = data["top_products"]
        assert isinstance(top_products, list), "top_products should be a list"
        
        # If there are products, validate structure
        if len(top_products) > 0:
            product = top_products[0]
            assert "id" in product, "Product should have 'id'"
            assert "name" in product, "Product should have 'name'"
            assert "quantity" in product, "Product should have 'quantity'"
            assert "revenue" in product, "Product should have 'revenue'"
            print(f"✓ Top products: {len(top_products)} products, top is '{product['name']}' with ${product['revenue']} revenue")
        else:
            print("✓ Top products: empty list (no sales yet)")
    
    def test_analytics_returns_category_breakdown(self, admin_headers):
        """Analytics should return category_breakdown with category, revenue, orders"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "category_breakdown" in data, "Missing 'category_breakdown' in response"
        
        category_breakdown = data["category_breakdown"]
        assert isinstance(category_breakdown, list), "category_breakdown should be a list"
        
        # Validate structure if data exists
        if len(category_breakdown) > 0:
            cat = category_breakdown[0]
            assert "category" in cat, "Category item should have 'category'"
            assert "revenue" in cat, "Category item should have 'revenue'"
            assert "orders" in cat, "Category item should have 'orders'"
            print(f"✓ Category breakdown: {len(category_breakdown)} categories, top is '{cat['category']}' with ${cat['revenue']} revenue")
        else:
            print("✓ Category breakdown: empty list (no sales yet)")
    
    def test_analytics_returns_pet_type_breakdown(self, admin_headers):
        """Analytics should return pet_type_breakdown with pet_type, revenue, orders"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "pet_type_breakdown" in data, "Missing 'pet_type_breakdown' in response"
        
        pet_type_breakdown = data["pet_type_breakdown"]
        assert isinstance(pet_type_breakdown, list), "pet_type_breakdown should be a list"
        
        # Validate structure if data exists
        if len(pet_type_breakdown) > 0:
            pt = pet_type_breakdown[0]
            assert "pet_type" in pt, "Pet type item should have 'pet_type'"
            assert "revenue" in pt, "Pet type item should have 'revenue'"
            assert "orders" in pt, "Pet type item should have 'orders'"
            print(f"✓ Pet type breakdown: {len(pet_type_breakdown)} types, top is '{pt['pet_type']}' with ${pt['revenue']} revenue")
        else:
            print("✓ Pet type breakdown: empty list (no sales yet)")
    
    def test_analytics_returns_recent_customers(self, admin_headers):
        """Analytics should return recent_customers with id, name, email, created_at"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "recent_customers" in data, "Missing 'recent_customers' in response"
        
        recent_customers = data["recent_customers"]
        assert isinstance(recent_customers, list), "recent_customers should be a list"
        
        # Validate structure if data exists
        if len(recent_customers) > 0:
            customer = recent_customers[0]
            assert "id" in customer, "Customer should have 'id'"
            assert "name" in customer, "Customer should have 'name'"
            assert "email" in customer, "Customer should have 'email'"
            print(f"✓ Recent customers: {len(recent_customers)} customers, most recent is '{customer['name']}'")
        else:
            print("✓ Recent customers: empty list (no customers yet)")
    
    def test_analytics_returns_order_status_breakdown(self, admin_headers):
        """Analytics should return order_status_breakdown"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "order_status_breakdown" in data, "Missing 'order_status_breakdown' in response"
        
        order_status = data["order_status_breakdown"]
        assert isinstance(order_status, list), "order_status_breakdown should be a list"
        
        if len(order_status) > 0:
            status = order_status[0]
            assert "status" in status, "Status item should have 'status'"
            assert "count" in status, "Status item should have 'count'"
            print(f"✓ Order status breakdown: {len(order_status)} statuses")
        else:
            print("✓ Order status breakdown: empty list")
    
    def test_analytics_returns_acquisition_trend(self, admin_headers):
        """Analytics should return acquisition_trend with signups per day"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "acquisition_trend" in data, "Missing 'acquisition_trend' in response"
        
        acquisition_trend = data["acquisition_trend"]
        assert isinstance(acquisition_trend, list), "acquisition_trend should be a list"
        assert len(acquisition_trend) == 30, f"Expected 30 days of data, got {len(acquisition_trend)}"
        
        for day in acquisition_trend:
            assert "date" in day, "Each acquisition item should have 'date'"
            assert "signups" in day, "Each acquisition item should have 'signups'"
        
        print(f"✓ Acquisition trend: {len(acquisition_trend)} days of signup data")
    
    def test_analytics_data_accuracy(self, admin_headers):
        """Verify analytics data is accurate by comparing with raw data"""
        # Get analytics
        analytics_response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        
        # Get stats for comparison
        stats_response = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Compare total orders - should match exactly
        assert analytics["summary"]["total_orders"] == stats["total_orders"], \
            f"Analytics total_orders ({analytics['summary']['total_orders']}) != stats total_orders ({stats['total_orders']})"
        
        # Note: Analytics excludes admin users from customer count (correct behavior)
        # Stats includes all users - so we just verify analytics customer count is reasonable
        assert analytics["summary"]["total_customers"] >= 0, "total_customers should be non-negative"
        assert analytics["summary"]["total_customers"] <= stats["total_customers"], \
            "Analytics customers should be <= stats (analytics excludes admins)"
        
        print(f"✓ Analytics data validated: {analytics['summary']['total_orders']} orders, {analytics['summary']['total_customers']} customers (excludes admins)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
