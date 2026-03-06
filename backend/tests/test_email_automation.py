"""
Tests for Email Automation Admin API endpoints
Features: Abandoned cart recovery emails, post-purchase review request emails
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


class TestEmailAutomationEndpoints:
    """Email Automation Admin Endpoint Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    # === GET /api/admin/email-automation ===
    def test_get_email_automation_stats_requires_auth(self):
        """Email automation stats endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/email-automation")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Email automation stats requires authentication")
    
    def test_get_email_automation_stats_success(self):
        """Admin can fetch email automation stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email-automation",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "abandoned_carts" in data, "Missing 'abandoned_carts' in response"
        assert "review_requests" in data, "Missing 'review_requests' in response"
        assert "automation_status" in data, "Missing 'automation_status' in response"
        
        # Verify abandoned_carts structure
        abandoned = data["abandoned_carts"]
        assert "pending" in abandoned, "Missing 'pending' in abandoned_carts"
        assert "emails_sent" in abandoned, "Missing 'emails_sent' in abandoned_carts"
        assert "recovered" in abandoned, "Missing 'recovered' in abandoned_carts"
        assert "recovery_rate" in abandoned, "Missing 'recovery_rate' in abandoned_carts"
        
        # Verify review_requests structure
        reviews = data["review_requests"]
        assert "eligible_orders" in reviews, "Missing 'eligible_orders' in review_requests"
        
        # Verify automation_status structure
        status = data["automation_status"]
        assert "abandoned_cart" in status, "Missing 'abandoned_cart' in automation_status"
        assert "review_request" in status, "Missing 'review_request' in automation_status"
        assert "low_stock_alert" in status, "Missing 'low_stock_alert' in automation_status"
        
        # Verify automation states
        assert status["abandoned_cart"] == True, "Abandoned cart should be active"
        assert status["review_request"] == True, "Review request should be active"
        assert status["low_stock_alert"] == False, "Low stock alert should be inactive (coming soon)"
        
        print(f"PASS: Email automation stats returned with data: {data}")
    
    # === POST /api/admin/email-automation/send-abandoned ===
    def test_send_abandoned_emails_requires_auth(self):
        """Send abandoned cart emails requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/email-automation/send-abandoned")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Send abandoned emails requires authentication")
    
    def test_send_abandoned_emails_success(self):
        """Admin can trigger abandoned cart email sending"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email-automation/send-abandoned",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        assert "abandoned cart emails" in data["message"].lower(), f"Unexpected message: {data['message']}"
        
        print(f"PASS: Send abandoned emails returned: {data['message']}")
    
    # === POST /api/admin/email-automation/send-reviews ===
    def test_send_review_emails_requires_auth(self):
        """Send review request emails requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/email-automation/send-reviews")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Send review emails requires authentication")
    
    def test_send_review_emails_success(self):
        """Admin can trigger review request email sending"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email-automation/send-reviews",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        assert "review request emails" in data["message"].lower(), f"Unexpected message: {data['message']}"
        
        print(f"PASS: Send review emails returned: {data['message']}")


class TestBrandNameUpdate:
    """Verify brand name updated from CalmTails to Wildly Ones"""
    
    def test_health_endpoint_brand_name(self):
        """Health endpoint should return 'Wildly Ones Pet Wellness'"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("service") == "Wildly Ones Pet Wellness", \
            f"Expected 'Wildly Ones Pet Wellness', got '{data.get('service')}'"
        
        print("PASS: Health endpoint returns 'Wildly Ones Pet Wellness'")
    
    def test_root_endpoint_brand_name(self):
        """Root API endpoint should mention Wildly Ones"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "Wildly Ones" in data.get("message", ""), \
            f"Expected 'Wildly Ones' in message, got '{data.get('message')}'"
        
        print("PASS: Root endpoint returns 'Wildly Ones Pet Wellness Store API'")


class TestEmailAutomationNonAdmin:
    """Verify non-admin users cannot access email automation endpoints"""
    
    def test_non_admin_cannot_access_stats(self):
        """Regular user should get 403 when accessing email automation stats"""
        # First register a regular user
        import uuid
        test_email = f"test_regular_{uuid.uuid4().hex[:8]}@test.com"
        
        reg_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": test_email, "password": "test123", "name": "Test User"}
        )
        
        if reg_response.status_code == 200:
            token = reg_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Try to access email automation stats
            response = requests.get(
                f"{BASE_URL}/api/admin/email-automation",
                headers=headers
            )
            assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
            print("PASS: Non-admin user gets 403 when accessing email automation stats")
        else:
            print(f"SKIP: Could not create test user ({reg_response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
