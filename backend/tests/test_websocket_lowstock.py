"""
Backend API tests for WebSocket, Low Stock, and Email Automation features
Tests WebSocket endpoint availability, low stock products API, and email automation endpoints
"""
import pytest
import requests
import os
import websocket
import json
import threading
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed - skipping admin tests")


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_is_available(self, api_client):
        """Verify API is responding"""
        response = api_client.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"API not available: {response.status_code}"
        print("✓ API is available and responding")


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login(self, api_client):
        """Verify admin can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print("✓ Admin login successful")


class TestLowStockProducts:
    """Low stock products API tests"""
    
    def test_low_stock_requires_auth(self, api_client):
        """GET /api/admin/low-stock-products requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/admin/low-stock-products")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Low stock endpoint requires authentication")
    
    def test_get_low_stock_products(self, api_client, admin_token):
        """GET /api/admin/low-stock-products returns products with stock <= 10"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/low-stock-products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "products" in data
        assert "count" in data
        assert "threshold" in data
        assert data["threshold"] == 10
        
        # Verify all returned products have low stock
        for product in data["products"]:
            assert product.get("stock_quantity", 999) <= 10, f"Product {product.get('name')} has stock > 10"
            assert product.get("in_stock") == True
        
        print(f"✓ Low stock products API returned {data['count']} products with threshold={data['threshold']}")
        return data


class TestEmailAutomation:
    """Email automation API tests"""
    
    def test_email_automation_requires_auth(self, api_client):
        """GET /api/admin/email-automation requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/admin/email-automation")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Email automation endpoint requires authentication")
    
    def test_get_email_automation_stats(self, api_client, admin_token):
        """GET /api/admin/email-automation returns automation stats with low_stock count"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/email-automation",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "abandoned_carts" in data
        assert "review_requests" in data
        assert "low_stock" in data
        assert "automation_status" in data
        
        # Verify automation_status contains low_stock_alert
        assert "low_stock_alert" in data["automation_status"]
        assert data["automation_status"]["low_stock_alert"] == True
        
        print(f"✓ Email automation stats: low_stock={data['low_stock']}, low_stock_alert={data['automation_status']['low_stock_alert']}")
        return data
    
    def test_send_low_stock_alerts_requires_auth(self, api_client):
        """POST /api/admin/email-automation/send-low-stock requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/admin/email-automation/send-low-stock")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Send low stock alerts endpoint requires authentication")
    
    def test_send_low_stock_alerts(self, api_client, admin_token):
        """POST /api/admin/email-automation/send-low-stock sends low stock alert emails"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/email-automation/send-low-stock",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        print(f"✓ Send low stock alerts response: {data['message']}")
        return data


class TestWebSocketEndpoint:
    """WebSocket endpoint availability tests"""
    
    def test_websocket_endpoint_available(self):
        """Verify WebSocket endpoint /ws/admin is available and accepts connections"""
        import asyncio
        import websockets
        
        # Use internal URL since WebSocket needs direct connection
        # External WSS proxy may have routing issues
        ws_endpoint = "ws://0.0.0.0:8001/ws/admin"
        
        async def test_connection():
            try:
                async with websockets.connect(ws_endpoint, ping_interval=5, ping_timeout=10) as ws:
                    return True, None
            except Exception as e:
                return False, str(e)
        
        connected, error_msg = asyncio.get_event_loop().run_until_complete(test_connection())
        
        assert connected, f"Failed to connect to WebSocket: {error_msg}"
        print(f"✓ WebSocket endpoint /ws/admin is available and accepts connections (internal)")


class TestLowStockDataVerification:
    """Verify low stock data consistency"""
    
    def test_low_stock_count_matches_products(self, api_client, admin_token):
        """Verify low_stock count in email-automation matches actual low stock products count"""
        # Get email automation stats
        email_response = api_client.get(
            f"{BASE_URL}/api/admin/email-automation",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert email_response.status_code == 200
        email_data = email_response.json()
        
        # Get low stock products
        products_response = api_client.get(
            f"{BASE_URL}/api/admin/low-stock-products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert products_response.status_code == 200
        products_data = products_response.json()
        
        # Verify counts match
        assert email_data["low_stock"] == products_data["count"], \
            f"Low stock count mismatch: email-automation={email_data['low_stock']}, low-stock-products={products_data['count']}"
        
        print(f"✓ Low stock count consistent: {email_data['low_stock']} products")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
