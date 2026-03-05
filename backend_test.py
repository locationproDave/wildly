#!/usr/bin/env python3

import requests
import sys
import time
import json
import uuid
from datetime import datetime

class PetPulseAPITester:
    def __init__(self, base_url="https://pet-care-curator.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test_result(self, test_name, passed, response_time, status_code, message=""):
        """Log test result for analysis"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "response_time": response_time,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name} - {response_time:.2f}s - {message}")
        else:
            print(f"❌ {test_name} - {response_time:.2f}s - Status {status_code} - {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test with timing"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('/') else f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=timeout)

            response_time = time.time() - start_time
            
            success = response.status_code == expected_status
            
            # Try to get JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}
                
            message = f"Response: {json.dumps(response_data, indent=2)[:100]}..."
            self.log_test_result(name, success, response_time, response.status_code, message)
            
            return success, response_data, response_time

        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            self.log_test_result(name, False, response_time, 0, "Request timeout")
            return False, {}, response_time
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test_result(name, False, response_time, 0, f"Error: {str(e)}")
            return False, {}, response_time

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_user_registration(self):
        """Test user registration with discount code"""
        print("\n=== USER REGISTRATION TEST ===")
        
        # Create unique user for this test
        timestamp = int(time.time())
        test_email = f"test_user_{timestamp}@petpulse.com"
        
        user_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        success, response, response_time = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            user_data,
            timeout=60  # Allow more time for registration
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            discount_code = response.get('user', {}).get('discount_code')
            
            print(f"   📝 Registration successful!")
            print(f"   🎫 Discount code: {discount_code}")
            print(f"   👤 User ID: {self.user_id}")
            return True
        else:
            print(f"   ❌ Registration failed - {response}")
            return False

    def test_user_login(self):
        """Test user login with existing demo user"""
        print("\n=== USER LOGIN TEST ===")
        
        login_data = {
            "email": "demo@petpulse.com",
            "password": "demo123456"
        }
        
        success, response, response_time = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            login_data,
            timeout=30
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   📝 Login successful!")
            print(f"   👤 User: {response.get('user', {}).get('name')}")
            print(f"   🎫 Discount: {response.get('user', {}).get('discount_code')}")
            return True
        else:
            print(f"   ❌ Login failed - {response}")
            return False

    def test_protected_route(self):
        """Test protected route authentication"""
        print("\n=== PROTECTED ROUTE TEST ===")
        
        success, response, response_time = self.run_test(
            "Get Current User (/auth/me)",
            "GET",
            "auth/me",
            200
        )
        
        if success:
            print(f"   ✅ Protected route working - User: {response.get('name')}")
            return True
        return False

    def test_chat_functionality(self):
        """Test chat API with AI response"""
        print("\n=== CHAT AI INTEGRATION TEST ===")
        
        self.session_id = str(uuid.uuid4())
        
        # Test simple chat query
        chat_data = {
            "query": "Hello, I need help finding premium dog anxiety relief products under $50.",
            "session_id": self.session_id
        }
        
        print("   🤖 Sending AI query (this may take 30-60 seconds)...")
        success, response, response_time = self.run_test(
            "Send Chat Message",
            "POST",
            "chat/send",
            200,
            chat_data,
            timeout=90  # AI responses can be slow
        )
        
        if success and 'response' in response:
            ai_response = response['response']
            print(f"   ✅ AI Response received ({len(ai_response)} chars)")
            print(f"   📝 Preview: {ai_response[:150]}...")
            return True
        else:
            print(f"   ❌ Chat failed - {response}")
            return False

    def test_search_history(self):
        """Test search history saving and retrieval"""
        print("\n=== SEARCH HISTORY TEST ===")
        
        success, response, response_time = self.run_test(
            "Get Search History",
            "GET",
            "history",
            200,
            timeout=30
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ History retrieved - {len(response)} items")
            if len(response) > 0:
                latest = response[0]
                print(f"   📝 Latest search: {latest.get('query', 'N/A')}")
            return True
        else:
            print(f"   ❌ History retrieval failed - {response}")
            return False

    def test_user_stats(self):
        """Test user statistics endpoint"""
        print("\n=== USER STATS TEST ===")
        
        success, response, response_time = self.run_test(
            "Get User Statistics",
            "GET",
            "stats",
            200,
            timeout=30
        )
        
        if success and 'saved_products' in response:
            print(f"   ✅ Stats retrieved:")
            print(f"   📊 Saved products: {response.get('saved_products', 0)}")
            print(f"   🔍 Total searches: {response.get('total_searches', 0)}")
            print(f"   ⭐ Recommended: {response.get('recommended_products', 0)}")
            return True
        else:
            print(f"   ❌ Stats retrieval failed - {response}")
            return False

    def test_chat_sessions(self):
        """Test chat sessions endpoint"""
        print("\n=== CHAT SESSIONS TEST ===")
        
        success, response, response_time = self.run_test(
            "Get Chat Sessions",
            "GET", 
            "chat/sessions",
            200,
            timeout=30
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Sessions retrieved - {len(response)} sessions")
            if len(response) > 0:
                session = response[0]
                print(f"   💬 Latest session has {len(session.get('messages', []))} messages")
            return True
        else:
            print(f"   ❌ Sessions retrieval failed - {response}")
            return False

    def test_unauthorized_access(self):
        """Test that protected routes require authentication"""
        print("\n=== UNAUTHORIZED ACCESS TEST ===")
        
        # Save current token
        saved_token = self.token
        self.token = None  # Remove token
        
        # Should get 401
        success, response, response_time = self.run_test(
            "Access Protected Route Without Token",
            "GET",
            "auth/me",
            401
        )
        
        # Restore token
        self.token = saved_token
        
        if success:
            print(f"   ✅ Properly rejected unauthorized access")
            return True
        else:
            print(f"   ❌ Security issue - should have returned 401")
            return False

    def save_test_results(self):
        """Save detailed test results to file"""
        results = {
            "test_run_summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "success_rate": f"{(self.tests_passed/self.tests_run*100):.1f}%",
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }
        
        with open('/app/test_results_backend.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📋 Detailed test results saved to: /app/test_results_backend.json")

def main():
    print("🚀 Starting PetPulse Sourcing Agent API Tests")
    print("=" * 60)
    
    tester = PetPulseAPITester()
    
    # Run test suite
    tests_passed = []
    
    # Health checks
    tester.test_health_check()
    
    # Authentication flow
    login_success = tester.test_user_login()
    if login_success:
        tests_passed.append("login")
        
        # Test protected routes
        if tester.test_protected_route():
            tests_passed.append("protected_routes")
        
        # Test AI chat
        if tester.test_chat_functionality():
            tests_passed.append("ai_chat")
        
        # Test data endpoints
        if tester.test_search_history():
            tests_passed.append("search_history")
            
        if tester.test_user_stats():
            tests_passed.append("user_stats")
            
        if tester.test_chat_sessions():
            tests_passed.append("chat_sessions")
    
    # Test security
    if tester.test_unauthorized_access():
        tests_passed.append("security")
    
    # Try registration (might fail if user exists)
    print("\n=== OPTIONAL: NEW USER REGISTRATION ===")
    if tester.test_user_registration():
        tests_passed.append("registration")
    
    # Save detailed results
    tester.save_test_results()
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"🏁 FINAL RESULTS")
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"📈 Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    print(f"✅ Working features: {', '.join(tests_passed)}")
    
    if tester.tests_passed < tester.tests_run:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed - check logs above")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())