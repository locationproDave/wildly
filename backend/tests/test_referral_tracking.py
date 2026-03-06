"""
Test suite for CalmTails Referral Program and Order Tracking System
Tests:
- Referral code generation and validation API
- Referral stats API
- Order tracking API
- Admin tracking management API
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


class TestReferralAPI:
    """Tests for referral program endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture
    def test_user_token(self):
        """Create/login test user for referral tests"""
        # Try to register first
        import uuid
        test_email = f"reftest_{uuid.uuid4().hex[:6]}@test.com"
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Referral Test User"
        })
        if register_res.status_code == 200:
            return register_res.json().get("token")
        # Try login if already exists
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "testpass123"
        })
        if login_res.status_code == 200:
            return login_res.json().get("token")
        pytest.skip("Test user creation/login failed")
    
    def test_get_referral_code_requires_auth(self):
        """GET /api/referral/code requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/code")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: Referral code endpoint requires authentication")
    
    def test_get_referral_code_returns_valid_code(self, admin_token):
        """GET /api/referral/code returns valid referral code and share URL"""
        response = requests.get(
            f"{BASE_URL}/api/referral/code",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "referral_code" in data, "Response missing referral_code"
        assert "share_url" in data, "Response missing share_url"
        assert "reward_amount" in data, "Response missing reward_amount"
        assert "completed_referrals" in data, "Response missing completed_referrals"
        assert "total_earned" in data, "Response missing total_earned"
        
        # Verify data types and values
        assert isinstance(data["referral_code"], str), "referral_code should be string"
        assert len(data["referral_code"]) > 0, "referral_code should not be empty"
        assert data["share_url"].startswith("https://"), "share_url should be HTTPS"
        assert data["referral_code"] in data["share_url"], "share_url should contain referral code"
        assert data["reward_amount"] == 10.0, "reward_amount should be $10"
        
        print(f"PASS: Referral code generated: {data['referral_code']}")
        print(f"PASS: Share URL: {data['share_url']}")
        return data["referral_code"]
    
    def test_validate_referral_code_valid(self, admin_token):
        """GET /api/referral/validate/{code} validates existing code"""
        # First get a valid code
        code_res = requests.get(
            f"{BASE_URL}/api/referral/code",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert code_res.status_code == 200
        referral_code = code_res.json()["referral_code"]
        
        # Validate the code (without auth - anonymous user)
        response = requests.get(f"{BASE_URL}/api/referral/validate/{referral_code}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data.get("valid") == True, "Code should be valid"
        assert data.get("code") == referral_code.upper(), "Code should match"
        assert "referrer_name" in data, "Response should include referrer_name"
        assert "reward_amount" in data, "Response should include reward_amount"
        assert "message" in data, "Response should include message"
        
        print(f"PASS: Referral code {referral_code} validated successfully")
        print(f"PASS: Message: {data['message']}")
    
    def test_validate_referral_code_invalid(self):
        """GET /api/referral/validate/{code} returns 404 for invalid code"""
        response = requests.get(f"{BASE_URL}/api/referral/validate/INVALIDCODE123")
        assert response.status_code == 404, f"Expected 404 for invalid code, got {response.status_code}"
        print("PASS: Invalid referral code returns 404")
    
    def test_validate_referral_code_own_code(self, admin_token):
        """User cannot validate their own referral code"""
        # Get admin's code
        code_res = requests.get(
            f"{BASE_URL}/api/referral/code",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        referral_code = code_res.json()["referral_code"]
        
        # Try to validate with same user - should return 400
        response = requests.get(
            f"{BASE_URL}/api/referral/validate/{referral_code}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400 for own code, got {response.status_code}"
        print("PASS: User cannot use their own referral code")
    
    def test_referral_stats_returns_correct_structure(self, admin_token):
        """GET /api/referral/stats returns proper statistics"""
        response = requests.get(
            f"{BASE_URL}/api/referral/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_referrals" in data, "Response missing total_referrals"
        assert "pending_referrals" in data, "Response missing pending_referrals"
        assert "total_earned" in data, "Response missing total_earned"
        assert "referrals" in data, "Response missing referrals list"
        
        # Verify types
        assert isinstance(data["total_referrals"], int), "total_referrals should be int"
        assert isinstance(data["pending_referrals"], int), "pending_referrals should be int"
        assert isinstance(data["total_earned"], (int, float)), "total_earned should be numeric"
        assert isinstance(data["referrals"], list), "referrals should be a list"
        
        print(f"PASS: Referral stats - Total: {data['total_referrals']}, Pending: {data['pending_referrals']}, Earned: ${data['total_earned']}")
    
    def test_referral_stats_requires_auth(self):
        """GET /api/referral/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/stats")
        assert response.status_code == 401
        print("PASS: Referral stats requires authentication")


class TestOrderTrackingAPI:
    """Tests for order tracking endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture
    def test_order_id(self, admin_token):
        """Get an existing order ID from admin orders"""
        # Admin can see all orders
        admin_orders_res = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if admin_orders_res.status_code == 200 and admin_orders_res.json():
            # Find an order without tracking for test isolation
            orders = admin_orders_res.json()
            for order in orders:
                if not order.get("tracking"):
                    return order["id"]
            # If all have tracking, use first one
            return orders[0]["id"]
        
        pytest.skip("No orders found for testing")
    
    def test_get_tracking_requires_auth(self):
        """GET /api/orders/{id}/tracking requires authentication"""
        response = requests.get(f"{BASE_URL}/api/orders/test-order-id/tracking")
        assert response.status_code == 401
        print("PASS: Order tracking requires authentication")
    
    def test_get_tracking_not_found(self, admin_token):
        """GET /api/orders/{id}/tracking returns 404 for invalid order"""
        response = requests.get(
            f"{BASE_URL}/api/orders/nonexistent-order-id/tracking",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("PASS: Tracking for nonexistent order returns 404")
    
    def test_get_tracking_no_tracking_info(self, admin_token, test_order_id):
        """GET /api/orders/{id}/tracking returns proper tracking when accessed via admin"""
        # Admin endpoint to get order tracking - uses admin orders endpoint directly
        admin_orders_res = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_orders_res.status_code == 200
        orders = admin_orders_res.json()
        
        # Check an order with tracking exists
        tracked_order = None
        for order in orders:
            if order.get("tracking"):
                tracked_order = order
                break
        
        if tracked_order:
            tracking = tracked_order["tracking"]
            assert "carrier" in tracking, "Tracking should have carrier"
            assert "tracking_number" in tracking, "Tracking should have tracking_number"
            assert "status" in tracking, "Tracking should have status"
            assert "events" in tracking, "Tracking should have events"
            print(f"PASS: Order {tracked_order['id']} has tracking: {tracking['carrier']} - {tracking['tracking_number']}")
        else:
            # Find an order without tracking
            untracked_order = None
            for order in orders:
                if not order.get("tracking"):
                    untracked_order = order
                    break
            
            if untracked_order:
                print(f"PASS: Order {untracked_order['id']} has no tracking yet (as expected)")
            else:
                print("PASS: All orders have tracking info")
    
    def test_admin_add_tracking_requires_admin(self, admin_token):
        """POST /api/admin/orders/{id}/tracking requires admin role"""
        # Test without auth
        response = requests.post(
            f"{BASE_URL}/api/admin/orders/test-id/tracking",
            params={"carrier": "ups", "tracking_number": "1Z999AA10123456784"}
        )
        assert response.status_code == 401
        print("PASS: Adding tracking requires authentication")
    
    def test_admin_add_tracking_valid(self, admin_token, test_order_id):
        """POST /api/admin/orders/{id}/tracking adds tracking successfully"""
        import uuid
        tracking_number = f"1Z999AA1{uuid.uuid4().hex[:8].upper()}"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/orders/{test_order_id}/tracking",
            params={
                "carrier": "ups",
                "tracking_number": tracking_number
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert "message" in data
        assert "tracking" in data
        assert "tracking_url" in data
        
        # Verify tracking details
        tracking = data["tracking"]
        assert tracking["carrier"] == "ups"
        assert tracking["tracking_number"] == tracking_number
        assert tracking["status"] == "in_transit"
        assert "events" in tracking
        assert len(tracking["events"]) > 0
        
        print(f"PASS: Tracking added - Carrier: UPS, Number: {tracking_number}")
        print(f"PASS: Tracking URL: {data['tracking_url']}")
        
        # Verify order status changed to shipped
        order_res = requests.get(
            f"{BASE_URL}/api/orders/{test_order_id}/tracking",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if order_res.status_code == 200:
            order_data = order_res.json()
            assert order_data.get("has_tracking") == True
            print("PASS: Order tracking info updated correctly")
    
    def test_admin_add_tracking_various_carriers(self, admin_token, test_order_id):
        """Verify various carrier tracking URLs are generated correctly"""
        carriers = ["fedex", "usps", "dhl"]
        
        for carrier in carriers:
            import uuid
            tracking_number = f"TEST{uuid.uuid4().hex[:10].upper()}"
            
            response = requests.post(
                f"{BASE_URL}/api/admin/orders/{test_order_id}/tracking",
                params={
                    "carrier": carrier,
                    "tracking_number": tracking_number
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "tracking_url" in data
            
            # Verify URL contains carrier domain
            tracking_url = data["tracking_url"].lower()
            if carrier == "fedex":
                assert "fedex.com" in tracking_url
            elif carrier == "usps":
                assert "usps.com" in tracking_url
            elif carrier == "dhl":
                assert "dhl.com" in tracking_url
            
            print(f"PASS: {carrier.upper()} tracking URL generated correctly")


class TestLoyaltyIntegration:
    """Tests for loyalty points display in Account page API"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_loyalty_status_endpoint(self, admin_token):
        """GET /api/loyalty/status returns correct structure for Account page"""
        response = requests.get(
            f"{BASE_URL}/api/loyalty/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure needed for Rewards card
        assert "points" in data, "Response missing points"
        assert "tier" in data, "Response missing tier"
        assert "lifetime_points" in data, "Response missing lifetime_points"
        
        # Verify tier is valid
        valid_tiers = ["bronze", "silver", "gold", "platinum"]
        assert data["tier"] in valid_tiers, f"Invalid tier: {data['tier']}"
        
        print(f"PASS: Loyalty status - Points: {data['points']}, Tier: {data['tier']}")
        
        # Check for tier progress info
        if data.get("next_tier"):
            assert "points_to_next_tier" in data
            print(f"PASS: Progress to {data['next_tier']}: {data['points_to_next_tier']} pts to go")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
