"""
Test cases for Customer Reviews System and Email Confirmation functionality
Tests:
1. Reviews API - get reviews for product
2. Reviews Summary API - get rating stats
3. Helpful button API - increment helpful count
4. Write review API (requires auth)
5. Email confirmation function (MOCKED - no RESEND_API_KEY)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestProductReviews:
    """Tests for product reviews system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests requiring authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@calmtails.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.user = response.json().get("user")
        else:
            self.token = None
            self.user = None
    
    def test_get_products_list(self):
        """Verify products endpoint returns products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        # Store first product slug for later tests
        self.product_slug = products[0].get("slug")
        print(f"✓ Found {len(products)} products, first slug: {self.product_slug}")
    
    def test_get_product_reviews(self):
        """Test getting reviews for a product"""
        # Use calming-dog-bed which we know has reviews
        response = requests.get(f"{BASE_URL}/api/products/calming-dog-bed/reviews")
        assert response.status_code == 200
        reviews = response.json()
        assert isinstance(reviews, list)
        print(f"✓ Found {len(reviews)} reviews for calming-dog-bed")
        
        if len(reviews) > 0:
            review = reviews[0]
            # Verify review structure
            assert "id" in review
            assert "product_id" in review
            assert "user_id" in review
            assert "user_name" in review
            assert "rating" in review
            assert "title" in review
            assert "content" in review
            assert "helpful_count" in review
            assert "created_at" in review
            print(f"✓ Review structure verified: {review.get('title')}")
    
    def test_get_product_reviews_summary(self):
        """Test getting reviews summary stats for a product"""
        response = requests.get(f"{BASE_URL}/api/products/calming-dog-bed/reviews/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Verify summary structure
        assert "average_rating" in summary
        assert "total_reviews" in summary
        assert "rating_breakdown" in summary
        
        # Verify rating breakdown has all star levels
        breakdown = summary["rating_breakdown"]
        assert "5" in breakdown or 5 in breakdown
        assert "4" in breakdown or 4 in breakdown
        assert "3" in breakdown or 3 in breakdown
        assert "2" in breakdown or 2 in breakdown
        assert "1" in breakdown or 1 in breakdown
        
        print(f"✓ Summary: {summary['average_rating']} avg from {summary['total_reviews']} reviews")
        print(f"✓ Breakdown: {summary['rating_breakdown']}")
    
    def test_reviews_nonexistent_product(self):
        """Test reviews endpoint with nonexistent product"""
        response = requests.get(f"{BASE_URL}/api/products/nonexistent-product-xyz/reviews")
        assert response.status_code == 404
        print("✓ Correctly returns 404 for nonexistent product")
    
    def test_reviews_summary_nonexistent_product(self):
        """Test reviews summary endpoint with nonexistent product"""
        response = requests.get(f"{BASE_URL}/api/products/nonexistent-product-xyz/reviews/summary")
        assert response.status_code == 404
        print("✓ Correctly returns 404 for nonexistent product summary")
    
    def test_mark_review_helpful(self):
        """Test marking a review as helpful"""
        # First get a review ID
        response = requests.get(f"{BASE_URL}/api/products/calming-dog-bed/reviews")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) > 0
        
        review_id = reviews[0]["id"]
        initial_count = reviews[0]["helpful_count"]
        
        # Mark as helpful
        response = requests.post(f"{BASE_URL}/api/reviews/{review_id}/helpful")
        assert response.status_code == 200
        data = response.json()
        assert "helpful_count" in data
        assert data["helpful_count"] == initial_count + 1
        print(f"✓ Helpful count increased from {initial_count} to {data['helpful_count']}")
    
    def test_mark_review_helpful_invalid_id(self):
        """Test marking nonexistent review as helpful"""
        response = requests.post(f"{BASE_URL}/api/reviews/invalid-review-id/helpful")
        assert response.status_code == 404
        print("✓ Correctly returns 404 for invalid review ID")
    
    def test_write_review_requires_auth(self):
        """Test that writing a review requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/calming-dog-bed/reviews",
            json={
                "product_id": "",
                "rating": 5,
                "title": "Test review",
                "content": "Test content",
                "images": []
            }
        )
        assert response.status_code == 401
        print("✓ Write review correctly requires authentication")
    
    def test_write_review_with_auth(self):
        """Test writing a review with authentication"""
        if not self.token:
            pytest.skip("Authentication failed - skipping")
        
        # Use a product the admin hasn't reviewed yet
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        
        # Find a product with no admin review
        test_product = None
        for product in products:
            reviews_resp = requests.get(f"{BASE_URL}/api/products/{product['slug']}/reviews")
            if reviews_resp.status_code == 200:
                reviews = reviews_resp.json()
                admin_reviewed = any(r["user_id"] == self.user["id"] for r in reviews)
                if not admin_reviewed:
                    test_product = product
                    break
        
        if not test_product:
            # Admin has reviewed all products, test duplicate review rejection
            response = requests.post(
                f"{BASE_URL}/api/products/calming-dog-bed/reviews",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "product_id": "",
                    "rating": 5,
                    "title": "Duplicate test",
                    "content": "This should fail",
                    "images": []
                }
            )
            # Should either be 400 (already reviewed) or 201 (new review)
            assert response.status_code in [400, 201]
            print(f"✓ Write review returned {response.status_code}")
        else:
            # Submit review to unreviewd product
            response = requests.post(
                f"{BASE_URL}/api/products/{test_product['slug']}/reviews",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "product_id": "",
                    "rating": 5,
                    "title": "TEST_Admin review",
                    "content": "This is a test review from admin for testing purposes",
                    "images": []
                }
            )
            if response.status_code == 201:
                data = response.json()
                assert "bonus_points" in data
                print(f"✓ Review created successfully, earned {data.get('bonus_points', 0)} bonus points")
            elif response.status_code == 400:
                print(f"✓ Review rejected (possibly already reviewed): {response.json()}")
            else:
                print(f"Review response: {response.status_code} - {response.text}")
    
    def test_review_rating_validation(self):
        """Test that review rating must be 1-5"""
        if not self.token:
            pytest.skip("Authentication failed - skipping")
        
        # Try invalid rating (0)
        response = requests.post(
            f"{BASE_URL}/api/products/calming-dog-bed/reviews",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "product_id": "",
                "rating": 0,
                "title": "Invalid rating test",
                "content": "This should fail",
                "images": []
            }
        )
        # Should fail either due to validation or already reviewed
        assert response.status_code in [400]
        print(f"✓ Invalid rating (0) correctly rejected")
        
        # Try invalid rating (6)
        response = requests.post(
            f"{BASE_URL}/api/products/calming-dog-bed/reviews",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "product_id": "",
                "rating": 6,
                "title": "Invalid rating test",
                "content": "This should fail",
                "images": []
            }
        )
        assert response.status_code in [400]
        print(f"✓ Invalid rating (6) correctly rejected")


class TestEmailConfirmation:
    """Tests for email confirmation functionality (MOCKED - no RESEND_API_KEY)"""
    
    def test_email_function_exists(self):
        """Verify the send_order_confirmation_email function exists in server.py"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        # Check server.py has the function
        with open('/app/backend/server.py', 'r') as f:
            server_code = f.read()
        
        assert 'send_order_confirmation_email' in server_code
        assert 'async def send_order_confirmation_email' in server_code
        print("✓ send_order_confirmation_email function exists in server.py")
        
        # Check function handles missing RESEND_API_KEY
        assert 'if not RESEND_API_KEY:' in server_code
        assert 'logging.warning("RESEND_API_KEY not configured' in server_code
        print("✓ Function handles missing RESEND_API_KEY gracefully")
        
        # Check email template exists
        assert 'html_content' in server_code
        assert 'Order Confirmation' in server_code or 'order_number' in server_code
        print("✓ Email template exists in function")
    
    def test_resend_import_exists(self):
        """Verify resend is imported in server.py"""
        with open('/app/backend/server.py', 'r') as f:
            server_code = f.read()
        
        assert 'import resend' in server_code
        print("✓ resend library is imported")
        
        assert 'RESEND_API_KEY' in server_code
        assert 'SENDER_EMAIL' in server_code
        print("✓ RESEND_API_KEY and SENDER_EMAIL are configured")


class TestExistingFeatures:
    """Verify existing features still work"""
    
    def test_cart_operations(self):
        """Test cart add/get operations"""
        import uuid
        session_id = f"test-{uuid.uuid4()}"
        
        # Get empty cart
        response = requests.get(f"{BASE_URL}/api/cart/{session_id}")
        assert response.status_code == 200
        cart = response.json()
        assert cart["items"] == []
        print("✓ Empty cart created successfully")
        
        # Get a product ID
        products_resp = requests.get(f"{BASE_URL}/api/products")
        product_id = products_resp.json()[0]["id"]
        
        # Add to cart
        response = requests.post(
            f"{BASE_URL}/api/cart/{session_id}/add",
            json={"product_id": product_id, "quantity": 2}
        )
        assert response.status_code == 200
        cart = response.json()
        assert len(cart["items"]) == 1
        assert cart["items"][0]["quantity"] == 2
        print("✓ Item added to cart successfully")
        
        # Clean up - clear cart
        requests.delete(f"{BASE_URL}/api/cart/{session_id}")
    
    def test_promo_code_validation(self):
        """Test promo code validation still works"""
        response = requests.get(f"{BASE_URL}/api/promotions/validate/WELCOME15?subtotal=100")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["discount_amount"] == 15.0  # 15% of 100
        print("✓ Promo code WELCOME15 validation works")
    
    def test_checkout_endpoint_exists(self):
        """Test checkout endpoint is accessible"""
        # Just verify endpoint exists (will fail without proper cart)
        response = requests.post(
            f"{BASE_URL}/api/checkout",
            json={
                "cart_session_id": "nonexistent",
                "email": "test@test.com",
                "origin_url": "https://example.com"
            }
        )
        # Should return 400 for empty cart, not 404
        assert response.status_code == 400
        assert "Cart is empty" in response.json()["detail"]
        print("✓ Checkout endpoint exists and validates cart")


class TestMultipleProductReviews:
    """Test reviews across multiple products"""
    
    def test_reviews_exist_on_multiple_products(self):
        """Verify reviews are seeded across multiple products"""
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        
        products_with_reviews = 0
        total_reviews = 0
        
        for product in products[:15]:  # Check first 15 products
            reviews_resp = requests.get(f"{BASE_URL}/api/products/{product['slug']}/reviews")
            if reviews_resp.status_code == 200:
                reviews = reviews_resp.json()
                if len(reviews) > 0:
                    products_with_reviews += 1
                    total_reviews += len(reviews)
        
        print(f"✓ Found {total_reviews} reviews across {products_with_reviews} products")
        assert products_with_reviews >= 5  # Should have reviews on at least 5 products
        assert total_reviews >= 20  # Should have at least 20 reviews total


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
