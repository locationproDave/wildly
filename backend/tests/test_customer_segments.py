"""
Test Customer Segmentation API Endpoints
- GET /api/admin/customer-segments - returns segment data with customers
- GET /api/admin/customer-segments/{segment} - returns detailed segment info
- POST /api/admin/customer-segments/{segment}/campaign - generates campaign template
- POST /api/admin/customer-segments/{segment}/send-campaign - sends emails
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@calmtails.com"
ADMIN_PASSWORD = "admin123"


class TestCustomerSegmentsAuth:
    """Test authentication requirements for customer segments endpoints"""
    
    def test_get_segments_requires_auth(self):
        """GET /api/admin/customer-segments requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/customer-segments")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ GET /api/admin/customer-segments requires authentication")
    
    def test_get_segment_detail_requires_auth(self):
        """GET /api/admin/customer-segments/{segment} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/customer-segments/new")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ GET /api/admin/customer-segments/new requires authentication")
    
    def test_create_campaign_requires_auth(self):
        """POST /api/admin/customer-segments/{segment}/campaign requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/customer-segments/new/campaign")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ POST /api/admin/customer-segments/new/campaign requires authentication")
    
    def test_send_campaign_requires_auth(self):
        """POST /api/admin/customer-segments/{segment}/send-campaign requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/new/send-campaign",
            params={
                "subject": "Test",
                "message": "Test",
                "promo_code": "TEST",
                "discount": "10%"
            }
        )
        assert response.status_code == 401 or response.status_code == 403
        print("✓ POST /api/admin/customer-segments/new/send-campaign requires authentication")


class TestCustomerSegmentsAdminRequired:
    """Test that non-admin users cannot access customer segments"""
    
    @pytest.fixture(scope="class")
    def regular_user_token(self):
        """Create a regular (non-admin) user for testing"""
        import uuid
        # Create a unique test user
        test_email = f"test_nonadmin_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register user
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "testpass123",
                "name": "Test Non-Admin"
            }
        )
        
        if register_response.status_code == 200:
            return register_response.json().get("token")
        
        # If user exists, login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "testpass123"}
        )
        if login_response.status_code == 200:
            return login_response.json().get("token")
        
        pytest.skip("Could not create or login regular user")
    
    def test_segments_requires_admin(self, regular_user_token):
        """Regular user should not be able to access customer segments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /api/admin/customer-segments returns 403 for non-admin")


class TestCustomerSegmentsData:
    """Test customer segments data retrieval with admin authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json().get("token")
    
    def test_get_customer_segments(self, admin_token):
        """GET /api/admin/customer-segments returns segment data with customers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "segments" in data
        assert "summary" in data
        assert isinstance(data["segments"], list)
        
        # Verify summary fields
        assert "total_customers" in data["summary"]
        assert "total_revenue" in data["summary"]
        assert "segment_count" in data["summary"]
        
        print(f"✓ GET /api/admin/customer-segments returns {len(data['segments'])} segments")
        print(f"  - Total customers: {data['summary']['total_customers']}")
        print(f"  - Total revenue: ${data['summary']['total_revenue']}")
        
        return data
    
    def test_segments_have_required_fields(self, admin_token):
        """Each segment has required fields: segment, label, description, color, customer_count, total_revenue, customers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["segment", "label", "description", "color", "customer_count", "total_revenue", "customers"]
        
        for segment in data["segments"]:
            for field in required_fields:
                assert field in segment, f"Segment {segment.get('segment')} missing field: {field}"
        
        print("✓ All segments have required fields")
    
    def test_valid_segment_types(self, admin_token):
        """Segments should only be: vip, loyal, at_risk, new, dormant"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_segments = ["vip", "loyal", "at_risk", "new", "dormant"]
        
        for segment in data["segments"]:
            assert segment["segment"] in valid_segments, f"Invalid segment: {segment['segment']}"
            print(f"  - {segment['label']}: {segment['customer_count']} customers")
        
        print("✓ All segments are valid types")


class TestSegmentDetail:
    """Test individual segment detail endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json().get("token")
    
    def test_get_segment_detail_new(self, admin_token):
        """GET /api/admin/customer-segments/new returns detailed segment info"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments/new",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["segment"] == "new"
        assert "label" in data
        assert "description" in data
        assert "color" in data
        assert "customers" in data
        assert "customer_count" in data
        
        print(f"✓ GET /api/admin/customer-segments/new returns {data['customer_count']} customers")
    
    def test_get_segment_detail_vip(self, admin_token):
        """GET /api/admin/customer-segments/vip returns VIP segment info"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments/vip",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["segment"] == "vip"
        print(f"✓ GET /api/admin/customer-segments/vip returns {data['customer_count']} customers")
    
    def test_get_segment_detail_invalid(self, admin_token):
        """GET /api/admin/customer-segments/invalid returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customer-segments/invalid_segment",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print("✓ GET /api/admin/customer-segments/invalid_segment returns 400 for invalid segment")


class TestCampaignGeneration:
    """Test campaign template generation"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json().get("token")
    
    def test_generate_campaign_new_segment(self, admin_token):
        """POST /api/admin/customer-segments/new/campaign generates campaign template"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/new/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["segment"] == "new"
        assert "label" in data
        assert "customer_count" in data
        assert "campaign" in data
        
        campaign = data["campaign"]
        assert "subject" in campaign
        assert "discount" in campaign
        assert "promo_code" in campaign
        assert "message" in campaign
        assert "preview_html" in campaign
        
        # Verify new segment campaign content
        assert campaign["promo_code"] == "WELCOME10"
        
        print(f"✓ Campaign generated for 'new' segment: {campaign['subject']}")
        print(f"  - Discount: {campaign['discount']}, Code: {campaign['promo_code']}")
    
    def test_generate_campaign_vip_segment(self, admin_token):
        """POST /api/admin/customer-segments/vip/campaign generates VIP campaign"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/vip/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["segment"] == "vip"
        campaign = data["campaign"]
        assert campaign["promo_code"] == "VIP20"
        
        print(f"✓ VIP campaign generated: {campaign['subject']}")
    
    def test_generate_campaign_at_risk_segment(self, admin_token):
        """POST /api/admin/customer-segments/at_risk/campaign generates at-risk campaign"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/at_risk/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["segment"] == "at_risk"
        campaign = data["campaign"]
        assert campaign["promo_code"] == "COMEBACK25"
        
        print(f"✓ At-Risk campaign generated: {campaign['subject']}")
    
    def test_generate_campaign_loyal_segment(self, admin_token):
        """POST /api/admin/customer-segments/loyal/campaign generates loyal campaign"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/loyal/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["segment"] == "loyal"
        campaign = data["campaign"]
        assert campaign["promo_code"] == "LOYAL15"
        
        print(f"✓ Loyal campaign generated: {campaign['subject']}")
    
    def test_generate_campaign_dormant_segment(self, admin_token):
        """POST /api/admin/customer-segments/dormant/campaign generates dormant campaign"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/dormant/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["segment"] == "dormant"
        campaign = data["campaign"]
        assert campaign["promo_code"] == "WINBACK30"
        
        print(f"✓ Dormant campaign generated: {campaign['subject']}")
    
    def test_generate_campaign_invalid_segment(self, admin_token):
        """POST /api/admin/customer-segments/invalid/campaign returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/invalid/campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print("✓ Invalid segment returns 400 for campaign generation")


class TestSendCampaign:
    """Test sending campaign emails (MOCKED - emails won't actually send)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json().get("token")
    
    def test_send_campaign_new_segment(self, admin_token):
        """POST /api/admin/customer-segments/new/send-campaign sends emails (MOCKED)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/new/send-campaign",
            params={
                "subject": "Test Campaign Subject",
                "message": "Test campaign message for new customers",
                "promo_code": "TESTNEW10",
                "discount": "10% off"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Since RESEND_API_KEY is not configured, it should return message about not configured
        # OR if configured, it returns sent_count
        assert "message" in data or "sent_count" in data
        
        print(f"✓ Send campaign to 'new' segment: {data}")
    
    def test_send_campaign_invalid_segment(self, admin_token):
        """POST /api/admin/customer-segments/invalid/send-campaign returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/admin/customer-segments/invalid/send-campaign",
            params={
                "subject": "Test",
                "message": "Test",
                "promo_code": "TEST",
                "discount": "10%"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print("✓ Invalid segment returns 400 for send campaign")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
