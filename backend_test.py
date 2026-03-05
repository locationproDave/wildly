#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime

class PetPulseAPITester:
    def __init__(self):
        # Use the public backend URL for testing
        self.base_url = "https://pet-care-curator.preview.emergentagent.com/api"
        self.token = None
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "status": "PASSED" if success else "FAILED",
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if headers:
            request_headers.update(headers)
        
        if self.token and 'Authorization' not in request_headers:
            request_headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=request_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        self.run_test("API Root", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)

    def test_authentication_flow(self):
        """Test user registration and login"""
        print("\n🔍 Testing Authentication Flow...")
        
        # Generate unique test user
        timestamp = datetime.now().strftime("%H%M%S")
        test_email = f"test{timestamp}@example.com"
        test_password = "TestPass123!"
        test_name = f"Test User {timestamp}"
        
        # Test registration
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": test_email, "password": test_password, "name": test_name}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   📝 Registered user: {test_email}")
            print(f"   🎟️  Discount code: {response.get('user', {}).get('discount_code', 'N/A')}")
        
        # Test login with new user
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data={"email": test_email, "password": test_password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   🔑 Login successful, token acquired")
        
        # Test get current user
        self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_chat_functionality(self):
        """Test chat API with Claude Opus 4.6"""
        print("\n🔍 Testing Chat Functionality...")
        
        # Test send chat message
        test_query = "Find calming products for anxious dogs"
        success, response = self.run_test(
            "Send Chat Message",
            "POST",
            "chat/send", 
            200,
            data={"query": test_query}
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            print(f"   💬 Chat session created: {self.session_id}")
            
            # Check if AI response contains expected content
            ai_response = response.get('response', '')
            if 'PRODUCT NAME:' in ai_response or 'calming' in ai_response.lower():
                print("   🤖 AI response contains product analysis")
            else:
                print("   ⚠️  AI response may not contain expected product analysis")
        
        # Test get chat sessions
        if self.token:
            self.run_test("Get Chat Sessions", "GET", "chat/sessions", 200)
        
        # Test get specific session
        if self.session_id:
            self.run_test(
                "Get Chat Session",
                "GET", 
                f"chat/session/{self.session_id}",
                200
            )

    def test_product_management(self):
        """Test product saving and management"""
        print("\n🔍 Testing Product Management...")
        
        if not self.token:
            print("   ⚠️  Skipping product tests - no auth token")
            return
        
        # Test save product
        test_product = {
            "product_name": "Calming Dog Treat",
            "supplier": "CJdropshipping",
            "supplier_rating": "4.5 stars",
            "us_warehouse": "Yes",
            "supplier_cost": "$8.50",
            "estimated_shipping": "$2.50",
            "landed_cost": "$11.00",
            "recommended_retail_price": "$28.99",
            "gross_margin": "62%",
            "emotional_angle": "Help your anxious dog feel calm and secure",
            "best_ad_hook": "Finally, peace for your anxious pup",
            "safety_check": "No issues found",
            "risk_flags": "None identified",
            "verdict": "RECOMMEND",
            "verdict_rationale": "High demand, good margins, verified supplier"
        }
        
        success, response = self.run_test(
            "Save Product",
            "POST",
            "products/save",
            200,
            data=test_product
        )
        
        product_id = response.get('product_id') if success else None
        
        # Test get saved products
        self.run_test("Get Saved Products", "GET", "products/saved", 200)
        
        # Test update verdict
        if product_id:
            success, response = self.run_test(
                "Update Product Verdict",
                "PATCH",
                f"products/{product_id}/verdict?verdict=INVESTIGATE FURTHER",
                200
            )

    def test_history_and_stats(self):
        """Test history and stats endpoints"""
        print("\n🔍 Testing History and Stats...")
        
        if not self.token:
            print("   ⚠️  Skipping history/stats tests - no auth token")
            return
        
        # Test get history
        self.run_test("Get Search History", "GET", "history", 200)
        
        # Test get user stats
        self.run_test("Get User Stats", "GET", "stats", 200)

    def test_error_handling(self):
        """Test API error handling"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid login
        self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"email": "nonexistent@example.com", "password": "wrongpass"}
        )
        
        # Test accessing protected endpoint without auth
        original_token = self.token
        self.token = None
        self.run_test("Unauthorized Access", "GET", "products/saved", 401)
        self.token = original_token
        
        # Test invalid endpoint
        success, _ = self.run_test("Invalid Endpoint", "GET", "nonexistent", 404)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting PetPulse API Tests...")
        print(f"📍 Testing against: {self.base_url}")
        
        try:
            self.test_health_check()
            self.test_authentication_flow()
            self.test_chat_functionality()
            self.test_product_management()
            self.test_history_and_stats()
            self.test_error_handling()
            
        except Exception as e:
            print(f"💥 Test suite failed with error: {str(e)}")
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = PetPulseAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    try:
        with open("/app/test_results_backend.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": tester.tests_run,
                    "passed": tester.tests_passed,
                    "failed": tester.tests_run - tester.tests_passed,
                    "success_rate": f"{(tester.tests_passed/tester.tests_run)*100:.1f}%"
                },
                "detailed_results": tester.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        print(f"📄 Detailed results saved to: /app/test_results_backend.json")
    except Exception as e:
        print(f"⚠️  Could not save detailed results: {str(e)}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())